# Agent Skills

Packaged, cross-tool [Agent Skills](https://code.claude.com/docs/en/skills.md) distilled from this repo's tested notebooks and reference docs — built for AI coding agents (Claude Code, Google Antigravity, Codex, and any tool that reads the `SKILL.md` convention), not just human readers.

## Why this exists

`data+ai/bq-ml` and `data+ai/bq-ai-functions` carry a genuine knowledge asset: `RESOURCES.md` files and ~100 tested notebooks with real, live-verified gotchas (exact error messages, exact metric swings across retrains, exact option interactions) that no base model's training data knows about. These skills package that knowledge — use-case-organized decision trees, verified gotchas, canonical snippets, and extracted notebook narratives — so an agent can use it directly instead of re-deriving it from scratch.

## Current skills

| Skill | Scope | Path |
|---|---|---|
| [`bigquery-ml`](.agents/skills/bigquery-ml/SKILL.md) | Training, evaluating, deploying, and monitoring BigQuery ML models | `.agents/skills/bigquery-ml/` |
| [`bigquery-ai-functions`](.agents/skills/bigquery-ai-functions/SKILL.md) | Calling Gemini / generative AI functions from BigQuery SQL | `.agents/skills/bigquery-ai-functions/` |
| [`choosing-a-bigquery-ai-approach`](.agents/skills/choosing-a-bigquery-ai-approach/SKILL.md) | Triages between the two above when it's unclear which fits | `.agents/skills/choosing-a-bigquery-ai-approach/` |

More are planned from this repo's broader MLOps content — see `PLANS.md` for the backlog and authoring standard.

## How discovery works

Real skill content lives in `.agents/skills/<name>/` here in `agent-skills/`. At the repo root, per-skill symlinks make each skill discoverable by both conventions:

- **Claude Code**: `<repo-root>/.claude/skills/<name>` — Claude Code scans the working directory and every parent up to the repo root, so this is visible from anywhere in the monorepo.
- **Antigravity, Codex, and other `.agents/skills/`-convention tools**: `<repo-root>/.agents/skills/<name>`.

Both are per-skill symlinks pointing at the one real copy of the content in `agent-skills/.agents/skills/<name>/` — no duplication.

## Skill anatomy

Each skill is a self-contained directory:

- `SKILL.md` — frontmatter (`name`, `description`) + a decision tree + cross-cutting gotchas + pointers to `reference/*.md`.
- `reference/<bucket>.md` — one file per use-case bucket: options, how to choose among them, verified gotchas, a canonical snippet.
- `narrative/*.md` — extracted markdown-and-code narrative from a flagship notebook per bucket (via `tooling/`'s notebook converter), preserving the compare-contrast reasoning and debugging stories that don't fit a reference table.
- `skill.manifest.json` — version, source commit, and file inventory; the single source of truth other tooling (hub sync, marketplace listings, future PyPI packaging) reads from.

Links into the source repo (notebooks, `RESOURCES.md`) are written as plain repo-relative text, not clickable relative links — they inform an agent where more depth lives if it happens to be inside this repo, and do nothing (no broken link) otherwise. Links between skills in this same collection (e.g. the triage skill pointing at `bigquery-ml`) are real relative links, since the whole collection is meant to travel together.

## Tooling

`tooling/` is an installable `uv`/Python package (`agent-skills-tooling`) providing the `agent-skills` CLI:

```bash
cd agent-skills/tooling
uv sync
uv run agent-skills convert-notebook <notebook.ipynb> --subproject-root <root> --output <out.md>
uv run agent-skills validate .agents/skills/bigquery-ml
uv run agent-skills validate .agents/skills --all
uv run agent-skills manifest .agents/skills/bigquery-ml
```

See `PLANS.md` for the authoring standard, the backlog, and what's planned beyond this local-repo phase (external hub repo, GitHub Action sync, Claude Code plugin marketplace, community catalog submissions, PyPI installer).
