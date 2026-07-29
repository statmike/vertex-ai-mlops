# Agent Skills — Plan

Operating manual for this meta-project: the authoring standard, the backlog, and the audit log. Mirrors the `README.md` + `PLANS.md` + `RESOURCES.md` convention already used in `data+ai/bq-ml` and `data+ai/bq-ai-functions`.

## Vision

Package this repo's tested, verified content as Agent Skills usable from any tool that reads the `SKILL.md` convention (Claude Code, Antigravity, Codex, and others) — not just the two BigQuery projects that started this, but eventually the broader MLOps content across the repo (`MLOps/`, `Applied GenAI/`, etc.). Skills should be genuinely self-contained (usable standalone, outside this repo) and dependable to keep in sync as the source content evolves.

## Authoring standard

A new skill is a directory under `.agents/skills/<name>/`:

1. **`SKILL.md`** — frontmatter (`name` ≤64 chars lowercase/digits/hyphens, no "claude"/"anthropic"; `description` ≤1024 chars, this drives auto-matching so write it carefully) + a decision tree for the domain + cross-cutting gotchas that apply regardless of the specific choice + pointers to `reference/*.md`. Keep under ~500 lines.
2. **`reference/<bucket>.md`** — one file per use-case bucket (organize by what the user is trying to do, not by raw catalog order). Each: an options table, how to choose among them, verified gotchas (prioritize ones with concrete evidence — exact numbers, exact error messages — over generic advice a model already knows), a canonical snippet, and a "Go deeper" section with plain repo-relative path mentions (not clickable links — see README.md's "Skill anatomy"). Keep each under ~100 lines or add a table of contents.
3. **`narrative/<topic>.md`** — extracted markdown+code narrative from one flagship notebook per reference bucket, via `tooling/`'s `convert-notebook` command. Curate — one illustrative notebook per bucket, not every notebook in the project.
4. **`skill.manifest.json`** — generate via `tooling/`'s `manifest` command after any content change.
5. Run `agent-skills validate <skill-dir>` before considering a skill (or a change to one) done.

Content should be distilled and maintained, not duplicated — the source `RESOURCES.md`/notebooks remain the authoritative exhaustive detail; a skill's files are the deliberately-curated summary an agent actually needs.

## Change types and checklists

#### New skill
- [ ] Scaffold `.agents/skills/<name>/` per the authoring standard above.
- [ ] Wire the two repo-root symlinks: `.claude/skills/<name>` and `.agents/skills/<name>`, both → `agent-skills/.agents/skills/<name>`.
- [ ] Run `agent-skills validate` and fix anything flagged.
- [ ] Generate the manifest.
- [ ] Add a row to this file's "Current skills" list (README.md) and an audit-log entry below.
- [ ] If the skill documents a project with its own `PLANS.md` (e.g. `bq-ml`, `bq-ai-functions`), add the skill-maintenance checklist line there (see those files' "Change types and checklists" sections) so future content changes prompt a skill update.

#### Skill content update (source project added a model/function/workflow, a new gotcha, a new head-to-head comparison)
- [ ] Update the relevant `reference/<bucket>.md` and/or `SKILL.md` cross-cutting section.
- [ ] Re-run `agent-skills validate`.
- [ ] Bump the manifest (`agent-skills manifest <skill-dir>`).
- [ ] Audit-log entry.

#### Tooling change (`convert_notebook.py`, `validate.py`, `manifest.py`)
- [ ] Update `tooling/src/agent_skills_tooling/`.
- [ ] Re-run `uv sync` and re-validate all skills to confirm nothing regressed.
- [ ] Audit-log entry.

## Backlog / phases

**Phase 1 — local foundation (in progress)**: centralize skills in `agent-skills/`, notebook-narrative extraction, validation/manifest tooling. See the three current skills.

**Phase 2 — external hub + sync (not started, needs explicit go-ahead before creating external resources)**: a dedicated hub repo mirroring `.agents/skills/`, a GitHub Action that syncs on push to `main`, pre-push validation against the mirrored output.

**Phase 3 — distribution spokes (not started)**: the hub's `.claude-plugin/marketplace.json` (with the `dependencies` field for skills like the triage skill), submission to community catalogs (VoltAgent's `awesome-agent-skills`, the Antigravity-specific list, `skills.sh`), and a PyPI/`uv`-installable CLI for end users.

**Future skills** (candidates from this repo's broader content, not yet scoped): TBD — revisit once phase 1 is fully proven on the two BigQuery projects.

## Audit log

- **2026-07-29** — Phase 1 kickoff: scaffolded `agent-skills/`, built `tooling/` (`convert_notebook.py`, `validate.py`, `manifest.py`, CLI), proved the notebook-narrative extraction on `models/logistic_regression/logistic_regression.ipynb`.
