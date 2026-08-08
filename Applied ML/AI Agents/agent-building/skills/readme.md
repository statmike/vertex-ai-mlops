![tracker](https://us-central1-vertex-ai-mlops-369716.cloudfunctions.net/pixel-tracking?path=statmike%2Fvertex-ai-mlops%2FApplied+ML%2FAI+Agents%2Fagent-building%2Fskills&file=readme.md)
<!--- header table --->
<table>
<tr>     
  <td style="text-align: center">
    <a href="https://github.com/statmike/vertex-ai-mlops/blob/main/Applied%20ML/AI%20Agents/agent-building/skills/readme.md">
      <img width="32px" src="https://www.svgrepo.com/download/217753/github.svg" alt="GitHub logo">
      <br>View on<br>GitHub
    </a>
  </td>
</tr>
<tr>
  <td style="text-align: right">
    <b>Share On: </b> 
    <a href="https://www.linkedin.com/sharing/share-offsite/?url=https://github.com/statmike/vertex-ai-mlops/blob/main/Applied%2520ML/AI%2520Agents/agent-building/skills/readme.md"><img src="https://upload.wikimedia.org/wikipedia/commons/8/81/LinkedIn_icon.svg" alt="Linkedin Logo" width="20px"></a> 
    <a href="https://reddit.com/submit?url=https://github.com/statmike/vertex-ai-mlops/blob/main/Applied%2520ML/AI%2520Agents/agent-building/skills/readme.md"><img src="https://redditinc.com/hubfs/Reddit%20Inc/Brand/Reddit_Logo.png" alt="Reddit Logo" width="20px"></a> 
    <a href="https://bsky.app/intent/compose?text=https://github.com/statmike/vertex-ai-mlops/blob/main/Applied%2520ML/AI%2520Agents/agent-building/skills/readme.md"><img src="https://upload.wikimedia.org/wikipedia/commons/7/7a/Bluesky_Logo.svg" alt="BlueSky Logo" width="20px"></a> 
    <a href="https://twitter.com/intent/tweet?url=https://github.com/statmike/vertex-ai-mlops/blob/main/Applied%2520ML/AI%2520Agents/agent-building/skills/readme.md"><img src="https://upload.wikimedia.org/wikipedia/commons/5/5a/X_icon_2.svg" alt="X (Twitter) Logo" width="20px"></a> 
  </td>
</tr>
<tr>
  <td style="text-align: right">
    <b>Connect With Author On: </b> 
    <a href="https://www.linkedin.com/in/statmike"><img src="https://upload.wikimedia.org/wikipedia/commons/8/81/LinkedIn_icon.svg" alt="Linkedin Logo" width="20px"></a>
    <a href="https://www.github.com/statmike"><img src="https://www.svgrepo.com/download/217753/github.svg" alt="GitHub Logo" width="20px"></a> 
    <a href="https://www.youtube.com/@statmike-channel"><img src="https://upload.wikimedia.org/wikipedia/commons/f/fd/YouTube_full-color_icon_%282024%29.svg" alt="YouTube Logo" width="20px"></a>
    <a href="https://bsky.app/profile/statmike.bsky.social"><img src="https://upload.wikimedia.org/wikipedia/commons/7/7a/Bluesky_Logo.svg" alt="BlueSky Logo" width="20px"></a> 
    <a href="https://x.com/statmike"><img src="https://upload.wikimedia.org/wikipedia/commons/5/5a/X_icon_2.svg" alt="X (Twitter) Logo" width="20px"></a>
  </td>
</tr>
<tr>
  <td style="text-align: right">
    <a href="https://raw.githubusercontent.com/statmike/vertex-ai-mlops/main/Applied%20ML/AI%20Agents/agent-building/skills/readme.md"><img src="https://www.svgrepo.com/download/5445/download-button.svg" alt="Download icon" width="20px"></a> <a href="https://raw.githubusercontent.com/statmike/vertex-ai-mlops/main/Applied%20ML/AI%20Agents/agent-building/skills/readme.md">Download File</a> <i>(right-click and "Save As")</i>
  </td>
</tr>
</table><br/><br/>

---
# Skill Registry — publish reusable skills to the platform

The **[Skill Registry](https://docs.cloud.google.com/gemini-enterprise-agent-platform/build/skill-registry)**
(`client.skills`) is a platform-managed, semantically searchable repository of
*skill bundles*. A **skill bundle** is a directory with a `SKILL.md` at its root
(plus optional `reference/`, `narrative/`, and assets) that packages a reusable
capability — instructions, references, and examples an agent or a developer can
pull in on demand. Instead of hard-wiring a capability into one agent, you
publish it once and let any agent **discover** it by natural-language query.

This folder does not author throwaway skills. It **reuses the sibling
[`agent-skills/`](../../../../agent-skills) project's bundles** — the same
packaged BigQuery skills that project already ships — and registers them in the
platform, then demonstrates semantic retrieval.

## Two different "skills" — don't conflate them

The platform uses the word *skill* in two unrelated places, and this project
touches both:

| | **A2A `AgentCard.skills`** | **Skill Registry (`client.skills`)** |
|---|---|---|
| What | A field on **one agent's** A2A card | A **shared catalog** of packaged skill bundles |
| Scope | Advertises that agent's own capabilities | Cross-agent, versioned, semantically searchable |
| Where | [`agent_discovery/skills.py`](../agent_discovery/skills.py) | this folder |
| API | set on the card at build time | `create` / `list` / `retrieve` / `delete` |

The discovery agent's card *describes what that agent can do*; the Skill Registry
is *a library other agents shop from*. Both are legitimate uses of "skill" — they
just solve different problems.

## Run it

```bash
uv run python skills/registry.py publish      # upload every bundle under SKILLS_SOURCE_DIR
uv run python skills/registry.py list          # list registered skills
uv run python skills/registry.py retrieve "how do I forecast sales in BigQuery?"
uv run python skills/registry.py delete <skill_id>
```

`publish` discovers every bundle under `config.SKILLS_SOURCE_DIR` (defaulting to
the `agent-skills/` sibling), reads each `SKILL.md`'s front matter for the
display name and description, and creates the skill (replacing an existing one of
the same id so a changed bundle actually re-uploads). `retrieve` is the payoff:
a natural-language query is matched **semantically** against the registered
skills — asking about *forecasting* ranks the `bigquery-ml` bundle first, without
any keyword overlap.

## Region matters

Unlike loss clustering (`global`-only), the Skill Registry is served only in a
few regions — **`us-central1`, `europe-west4`, `us-east5`** — and the `global`
endpoint returns `INTERNAL`. `registry.py` pins its client to
`config.SKILL_REGISTRY_LOCATION` (default `us-central1`). The built-in
`gcp-skill-registry` skill always appears in `list`/`retrieve`; that's Google's
own registry-interaction skill, expected alongside yours.

Limits worth knowing: a bundle's license string must be under 1024 characters,
its instructions under 500K, and the zipped bundle under 10MB. The SDK zips the
local directory for you (`config.local_path`), so no manual packaging.

## Layout

```
skills/
├── bundles.py     # offline core: discover bundles, parse SKILL.md front matter (unit-tested)
├── registry.py    # thin CLI over client.skills: publish | list | retrieve | delete
└── tests/         # offline tests for bundles.py (no cloud, no SDK)
```

The split mirrors the rest of the project: **anything that needs no cloud is a
tested library, and each cloud call is a thin script over it.** `bundles.py` is
pure (discovery + a small YAML-front-matter parser) and covered by
`uv run pytest skills/tests`; `registry.py` wires it to the platform.

## Docs

- [Skill Registry overview](https://docs.cloud.google.com/gemini-enterprise-agent-platform/build/skill-registry)
- [`Skills` client reference (`create` / `retrieve`)](https://docs.cloud.google.com/python/docs/reference/agentplatform/latest/vertexai._genai.skills.Skills)
- [`agent-skills/` — the sibling project whose bundles this registers](../../../../agent-skills)
