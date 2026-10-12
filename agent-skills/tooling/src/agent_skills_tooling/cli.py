"""Command-line entry point: `agent-skills <subcommand> ...`."""

from __future__ import annotations

import argparse
import sys
from pathlib import Path

from agent_skills_tooling.link_policy import check_project
from agent_skills_tooling.manifest import write_manifest
from agent_skills_tooling.reference_structure import check_reference
from agent_skills_tooling.validate import validate_all, validate_skill

# `convert-notebook` and `check-narratives` read .ipynb files and need nbformat; everything else is
# standard library only. Those two import their modules on demand so the rest of the CLI runs on a
# bare interpreter.


def _cmd_convert_notebook(args: argparse.Namespace) -> int:
    from agent_skills_tooling.convert_notebook import convert_notebook_to_file

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
    from agent_skills_tooling.narrative_drift import check_all_narratives

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


def _cmd_check_pinned_models(args: argparse.Namespace) -> int:
    from agent_skills_tooling.pinned_models import check_pinned_models, load_allow_list

    allowed = set(args.allow)
    if args.allow_file:
        allowed |= load_allow_list(Path(args.allow_file), Path(args.project_root), Path(args.repo_root))
    result = check_pinned_models(Path(args.project_root), allowed)
    for finding in result.unlisted:
        print(f"UNLISTED {finding.format(result.project_root)}")
    label = result.project_root.name
    summary = ", ".join(f"{value} ×{count}" for value, count in sorted(result.counts.items(), key=lambda kv: -kv[1]))
    print(f"{'OK   ' if result.ok else 'FAIL '} [{label}] {result.scanned} files scanned; pinned: {summary or 'none'}")
    return 0 if result.ok else 1


def _cmd_sweep(args: argparse.Namespace) -> int:
    """Run every check in one go and return non-zero if any of them fails.

    Source projects come from each skill's `skill.manifest.json` (`source_project`), so a new
    skill is picked up without touching this command. Each project is checked with the other
    discovered projects as link siblings.
    """
    from agent_skills_tooling.manifest import source_projects

    skills_root = Path(args.skills_root)
    repo_root = Path(args.repo_root)
    projects = source_projects(skills_root)
    failures: list[str] = []

    def step(name: str, code: int) -> None:
        print(f"---- {name}: {'ok' if code == 0 else 'FAIL'}")
        if code != 0:
            failures.append(name)

    step("validate --all", _cmd_validate(argparse.Namespace(skill_dir=str(skills_root), all=True)))
    # The allow list lives beside the real collection (agent-skills/pinned-models.json). The skills
    # root may be the repo-root symlink directory, so discovery also walks up from each resolved skill.
    from agent_skills_tooling.pinned_models import find_allow_file

    allow_file = find_allow_file(skills_root)
    if allow_file is None and projects:
        print("ERROR check-pinned-models: no pinned-models.json found beside the skills collection")
        failures.append("check-pinned-models (allow list missing)")
    for project in projects:
        siblings = [str(repo_root / p) for p in projects if p != project]
        step(
            f"check-links {project}",
            _cmd_check_links(argparse.Namespace(project_root=str(repo_root / project), sibling=siblings, repo_root=str(repo_root))),
        )
        step(f"check-reference {project}", _cmd_check_reference(argparse.Namespace(project_root=str(repo_root / project))))
        if allow_file is not None:
            step(
                f"check-pinned-models {project}",
                _cmd_check_pinned_models(
                    argparse.Namespace(project_root=str(repo_root / project), allow=[], allow_file=str(allow_file), repo_root=str(repo_root))
                ),
            )
    step("check-narratives", _cmd_check_narratives(argparse.Namespace(skills_root=str(skills_root), repo_root=str(repo_root))))

    if failures:
        print(f"SWEEP FAIL — {len(failures)} step(s) failed: {', '.join(failures)}")
        return 1
    print(f"SWEEP OK — {len(projects)} project(s), all checks green")
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

    p_pinned = subparsers.add_parser(
        "check-pinned-models",
        help="List every model/endpoint literal a project pins and fail on any not in the allow list",
    )
    p_pinned.add_argument("project_root", help="e.g. data+ai/bq-ai-functions")
    p_pinned.add_argument("--allow", action="append", default=[], help="An allowed literal (repeatable)")
    p_pinned.add_argument("--allow-file", default=None, help="JSON allow list keyed by repo-relative project path")
    p_pinned.add_argument("--repo-root", default=".", help="Repository root, used to key the allow file")
    p_pinned.set_defaults(func=_cmd_check_pinned_models)

    p_sweep = subparsers.add_parser(
        "sweep", help="Run validate, check-links, check-reference, check-pinned-models and check-narratives together"
    )
    p_sweep.add_argument("skills_root", help="Parent of the skill directories")
    p_sweep.add_argument("--repo-root", required=True, help="Repository root that source_project resolves against")
    p_sweep.set_defaults(func=_cmd_sweep)

    args = parser.parse_args(argv)
    return args.func(args)


if __name__ == "__main__":
    sys.exit(main())
