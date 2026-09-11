"""Command-line entry point: `agent-skills <subcommand> ...`."""

from __future__ import annotations

import argparse
import sys
from pathlib import Path

from agent_skills_tooling.convert_notebook import convert_notebook_to_file
from agent_skills_tooling.link_policy import check_project
from agent_skills_tooling.manifest import write_manifest
from agent_skills_tooling.narrative_drift import check_all_narratives
from agent_skills_tooling.reference_structure import check_reference
from agent_skills_tooling.validate import validate_all, validate_skill


def _cmd_convert_notebook(args: argparse.Namespace) -> int:
    convert_notebook_to_file(
        notebook_path=Path(args.notebook),
        subproject_root=Path(args.subproject_root),
        output_path=Path(args.output),
    )
    print(f"Wrote {args.output}")
    return 0


def _cmd_validate(args: argparse.Namespace) -> int:
    skill_dir = Path(args.skill_dir)
    results = validate_all(skill_dir) if args.all else {skill_dir.name: validate_skill(skill_dir)}

    exit_code = 0
    for name, result in results.items():
        for error in result.errors:
            print(f"ERROR [{name}] {error}")
            exit_code = 1
        for warning in result.warnings:
            print(f"WARN  [{name}] {warning}")
        if result.ok and not result.warnings:
            print(f"OK    [{name}]")
    return exit_code


def _cmd_check_links(args: argparse.Namespace) -> int:
    result = check_project(
        project_root=Path(args.project_root),
        sibling_roots=[Path(s) for s in args.sibling],
        repo_root=Path(args.repo_root),
    )
    for violation in result.violations:
        print(f"VIOLATION {violation.format(result.project_root)}")
    label = result.project_root.name
    print(f"{'OK   ' if result.ok else 'FAIL '} [{label}] {result.scanned} files scanned, {len(result.violations)} violations")
    return 0 if result.ok else 1


def _cmd_check_reference(args: argparse.Namespace) -> int:
    result = check_reference(Path(args.project_root))
    for error in result.errors:
        print(f"ERROR {error}")
    label = result.project_root.name
    print(f"{'OK   ' if result.ok else 'FAIL '} [{label}] {result.checked} reference pages, {len(result.errors)} errors")
    return 0 if result.ok else 1


def _cmd_check_narratives(args: argparse.Namespace) -> int:
    results = check_all_narratives(Path(args.skills_root), Path(args.repo_root))
    exit_code = 0
    for name, result in results.items():
        for stale in result.stale:
            print(f"STALE [{name}] narrative/{stale} — regenerate with convert-notebook")
            exit_code = 1
        for missing in result.missing_source:
            print(f"ERROR [{name}] narrative/{missing}")
            exit_code = 1
        if result.ok:
            print(f"OK    [{name}] {result.checked} narratives current")
    if not results:
        print("No skill declares a source_project — nothing to check")
    return exit_code


def _cmd_manifest(args: argparse.Namespace) -> int:
    path, version = write_manifest(
        Path(args.skill_dir), version=args.version, source_project=args.source_project
    )
    print(f"Wrote {path} (version {version})")
    return 0


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(prog="agent-skills")
    subparsers = parser.add_subparsers(dest="command", required=True)

    p_convert = subparsers.add_parser("convert-notebook", help="Extract a notebook's narrative markdown")
    p_convert.add_argument("notebook", help="Path to the source .ipynb")
    p_convert.add_argument("--subproject-root", required=True, help="Root that relative links resolve against")
    p_convert.add_argument("--output", required=True, help="Output .md path")
    p_convert.set_defaults(func=_cmd_convert_notebook)

    p_validate = subparsers.add_parser("validate", help="Lint one or all skills")
    p_validate.add_argument("skill_dir", help="A single skill directory, or the skills root with --all")
    p_validate.add_argument("--all", action="store_true", help="Treat skill_dir as a parent of multiple skills")
    p_validate.set_defaults(func=_cmd_validate)

    p_links = subparsers.add_parser("check-links", help="Enforce the outward-link policy on a source project")
    p_links.add_argument("project_root", help="e.g. data+ai/bq-ml")
    p_links.add_argument("--sibling", action="append", default=[], help="Sibling project root a link may also target (repeatable)")
    p_links.add_argument("--repo-root", required=True, help="Repository root, used to tell in-repo from out-of-repo")
    p_links.set_defaults(func=_cmd_check_links)

    p_manifest = subparsers.add_parser("manifest", help="Generate/update a skill's manifest")
    p_manifest.add_argument("skill_dir")
    p_manifest.add_argument(
        "--version",
        default=None,
        help="Set the version. Omit to keep the existing manifest's version (0.1.0 for a new skill).",
    )
    p_manifest.add_argument(
        "--source-project",
        default=None,
        help="Repo-relative project this skill is built from (e.g. data+ai/bq-ml). Omit to keep the existing value.",
    )
    p_manifest.set_defaults(func=_cmd_manifest)

    p_reference = subparsers.add_parser(
        "check-reference", help="Check a project's RESOURCES.md index against its reference/ pages"
    )
    p_reference.add_argument("project_root", help="e.g. data+ai/bq-ml")
    p_reference.set_defaults(func=_cmd_check_reference)

    p_narratives = subparsers.add_parser(
        "check-narratives", help="Regenerate every narrative and report the ones that have gone stale"
    )
    p_narratives.add_argument("skills_root", help="Parent of the skill directories")
    p_narratives.add_argument("--repo-root", required=True, help="Repository root that source_project resolves against")
    p_narratives.set_defaults(func=_cmd_check_narratives)

    args = parser.parse_args(argv)
    return args.func(args)


if __name__ == "__main__":
    sys.exit(main())
