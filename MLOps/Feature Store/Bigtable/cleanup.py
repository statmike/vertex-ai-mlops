#!/usr/bin/env python3
"""Tear down the billable resources created by the Bigtable Feature Store series.

Reads parameters from cleanup.json (written by the Environment notebook), then
deletes the resources it lists. Safe by default: a dry run that only prints what
it *would* delete. Pass --yes to actually delete.

Usage (from this directory):
    uv run python cleanup.py                 # dry run — show what would be deleted
    uv run python cleanup.py --yes           # delete the Bigtable instance
    uv run python cleanup.py --yes --include-dataset   # also delete the BigQuery dataset

The BigQuery dataset is KEPT by default — it's cheap, holds the offline feature
data, and is reusable. The expensive resource is the Bigtable instance (deleting
it removes all clusters and tables within it).

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


def run(cmd, dry_run, ignore_fail=False):
    """Run a gcloud/bq command; treat 'not found' as already-deleted."""
    printable = ' '.join(cmd)
    if dry_run:
        print(f'  [dry-run] {printable}')
        return
    result = subprocess.run(cmd, capture_output=True, text=True)
    if result.returncode == 0:
        print('  done.')
    else:
        err = (result.stderr or '').strip()
        if 'NOT_FOUND' in err or 'not found' in err.lower() or 'does not exist' in err.lower():
            print('  already gone.')
        elif ignore_fail:
            print(f'  skipped: {err.splitlines()[0] if err else "no-op"}')
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
    ap = argparse.ArgumentParser(description='Tear down Bigtable Feature Store resources.')
    ap.add_argument('--yes', action='store_true', help='actually delete (default is a dry run)')
    ap.add_argument('--include-dataset', action='store_true',
                    help='also delete the BigQuery dataset (kept by default)')
    ap.add_argument('--check-jobs', action='store_true',
                    help='list running BigQuery jobs (e.g. continuous queries) and exit; deletes nothing')
    args = ap.parse_args()
    dry_run = not args.yes

    cfg = load_config()
    project = cfg['project_id']

    if args.check_jobs:
        check_jobs(project)
        return

    print(f'Bigtable Feature Store cleanup — project {project}')
    print('DRY RUN (no changes). Re-run with --yes to delete.\n' if dry_run else 'DELETING resources...\n')

    # A change stream on the writes table (NB5) blocks instance deletion — clear it first.
    writes_table = cfg.get('bt_writes_table')
    if writes_table:
        print(f'Change stream on table: {writes_table} (cleared if present)')
        run(['gcloud', 'bigtable', 'instances', 'tables', 'update', writes_table,
             '--instance', cfg['bt_instance'], '--project', project,
             '--clear-change-stream-retention-period', '--quiet'], dry_run, ignore_fail=True)

    # Deleting the instance removes all clusters and tables within it.
    print(f'Bigtable instance: {cfg["bt_instance"]} (includes clusters and all tables)')
    run(['gcloud', 'bigtable', 'instances', 'delete', cfg['bt_instance'],
         '--project', project, '--quiet'], dry_run)

    if args.include_dataset:
        print(f'BigQuery dataset: {cfg["bq_dataset"]} (--include-dataset)')
        run(['bq', 'rm', '-r', '-f', f'{project}:{cfg["bq_dataset"]}'], dry_run)
    else:
        print(f'BigQuery dataset: {cfg["bq_dataset"]} — KEPT (use --include-dataset to delete)')

    print('\nDry run complete. Re-run with --yes to delete.' if dry_run else '\nCleanup complete.')


if __name__ == '__main__':
    main()
