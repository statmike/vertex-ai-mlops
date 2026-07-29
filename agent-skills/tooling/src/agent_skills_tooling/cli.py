"""Command-line entry point: `agent-skills <subcommand> ...`."""

from __future__ import annotations

import argparse
import sys
from pathlib import Path

from agent_skills_tooling.convert_notebook import convert_notebook_to_file
from agent_skills_tooling.manifest import write_manifest
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


def _cmd_manifest(args: argparse.Namespace) -> int:
    path = write_manifest(Path(args.skill_dir), version=args.version)
    print(f"Wrote {path}")
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

    p_manifest = subparsers.add_parser("manifest", help="Generate/update a skill's manifest")
    p_manifest.add_argument("skill_dir")
    p_manifest.add_argument("--version", default="0.1.0")
    p_manifest.set_defaults(func=_cmd_manifest)

    args = parser.parse_args(argv)
    return args.func(args)


if __name__ == "__main__":
    sys.exit(main())
