#!/usr/bin/env python3
"""Tear down the resources created by the BigQuery Feature Store series.

Reads parameters from cleanup.json (written by the Environment notebook), then
deletes the resources it lists. Safe by default: a dry run that only prints what
it *would* delete. Pass --yes to actually delete.

Unlike the other feature store series, BigQuery has NO separate online-serving
instance — the serving layer IS the dataset (Storage Read API straight from the
offline tables). So the only resource to remove is the BigQuery dataset, which
holds storage cost. It is deleted by --yes here (there is nothing cheaper to keep).

Usage (from this directory):
    uv run python cleanup.py                 # dry run — show what would be deleted
    uv run python cleanup.py --yes           # delete the BigQuery dataset and all tables

Every delete is idempotent: "already gone" is reported, not an error.
"""
import argparse
import json
import os
import subprocess
import sys

CONFIG_PATH = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'cleanup.json')


def load_config():
    if not os.path.exists(CONFIG_PATH):
        sys.exit(
            f'cleanup.json not found at {CONFIG_PATH}\n'
            'Run the Environment notebook first — it writes this file '
            'with the parameters used to create the resources.'
        )
    with open(CONFIG_PATH) as f:
        return json.load(f)


def run(cmd, dry_run):
    """Run a bq command; treat 'not found' as already-deleted."""
    printable = ' '.join(cmd)
    if dry_run:
        print(f'  [dry-run] {printable}')
        return
    result = subprocess.run(cmd, capture_output=True, text=True)
    if result.returncode == 0:
        print('  deleted.')
    else:
        err = (result.stderr or '').strip()
        if 'NOT_FOUND' in err or 'not found' in err.lower() or 'does not exist' in err.lower():
            print('  already gone.')
        else:
            print(f'  WARNING: {err}')


def check_jobs(project):
    """List running BigQuery query jobs (continuous queries appear here while active).

    The teardown scripts intentionally don't kill jobs they didn't create — continuous
    queries and EXPORT DATA reservations are transient, stopped within their own notebook
    runs. This is a verification aid: confirm nothing is left billing from BQ compute.
    """
    print(f'Checking for running BigQuery jobs in project {project} '
          '(continuous queries appear here while active)...')
    result = subprocess.run(
        ['bq', 'ls', '-j', '-a', '--max_results=200', '--format=json', f'--project_id={project}'],
        capture_output=True, text=True)
    if result.returncode != 0:
        print(f'  could not list jobs: {(result.stderr or "").strip().splitlines()[0] if result.stderr else "unknown error"}')
        return
    try:
        jobs = json.loads(result.stdout or '[]')
    except json.JSONDecodeError:
        print('  could not parse job list.')
        return
    running = [j for j in jobs if (j.get('state') or j.get('status', {}).get('state')) == 'RUNNING']
    if not running:
        print('  no running jobs — nothing left billing from continuous queries.')
        return
    print(f'  {len(running)} running job(s) — these may be continuous queries:')
    for j in running:
        jid = j.get('id') or j.get('jobReference', {}).get('jobId', '?')
        print(f'    RUNNING  {jid}')
    print('  To stop a continuous query, cancel its job:  bq cancel <job_id>')


def main():
    ap = argparse.ArgumentParser(description='Tear down BigQuery Feature Store resources.')
    ap.add_argument('--yes', action='store_true', help='actually delete (default is a dry run)')
    ap.add_argument('--check-jobs', action='store_true',
                    help='list running BigQuery jobs (e.g. continuous queries) and exit; deletes nothing')
    args = ap.parse_args()
    dry_run = not args.yes

    cfg = load_config()
    project = cfg['project_id']

    if args.check_jobs:
        check_jobs(project)
        return

    print(f'BigQuery Feature Store cleanup — project {project}')
    print('DRY RUN (no changes). Re-run with --yes to delete.\n' if dry_run else 'DELETING resources...\n')

    print(f'BigQuery dataset: {cfg["bq_dataset"]} (dataset + all tables within it)')
    run(['bq', 'rm', '-r', '-f', f'{project}:{cfg["bq_dataset"]}'], dry_run)

    print('\nDry run complete. Re-run with --yes to delete.' if dry_run else '\nCleanup complete.')


if __name__ == '__main__':
    main()
