"""Explicit A2A skills for the discovery agent's agent card.

A2A agents advertise their capabilities as a list of ``AgentSkill`` entries on
their agent card (served at ``/.well-known/agent-card.json`` locally, embedded in
the Runtime resource when deployed). A consumer — or a human browsing an agent
gallery — reads these skills to decide *whether and how* to call the agent.

ADK can auto-derive skills from the agent (one "model" skill plus one per tool),
but the auto-generated entries are generic: the model skill is tagged ``llm`` and
the tool skill just mirrors the Python function name. This module instead declares
the skills **explicitly** — with a stable id, a human-readable name, a description
written for a caller (not a maintainer), discovery ``tags``, and ``examples`` that
show the kind of question the skill answers. That is the real "skills" surface of
the platform: there is no separate skills registry — an agent's skills *are* the
``skills`` array on its A2A card — so making them rich is how you make the agent
discoverable and correctly routable.

Both serving paths reuse these:

- **Local** (``agent_discovery/agent.py``) — ``to_a2a(..., agent_card=...)``.
- **Deployed** (``agent_discovery/a2a_app.py``) — the ``A2aAgent`` card.

Both build a protobuf ``AgentCard`` (``a2a_pb2``) whose ``skills`` is a *repeated*
field: it cannot be reassigned, so :func:`apply_skills` clears and re-extends it.
"""

from __future__ import annotations

from typing import TYPE_CHECKING

from a2a.types import AgentSkill

if TYPE_CHECKING:
    from a2a.types import AgentCard

# The discovery agent's advertised skills. Kept small and honest: it has exactly
# one capability — semantic search over theLook's data catalog — so it advertises
# one well-described skill rather than padding the card. Descriptions and examples
# mirror what agent_discovery/prompts.py actually instructs the agent to do and
# what tools/function_tool_search_catalog.py actually returns.
DISCOVERY_SKILLS: list[AgentSkill] = [
    AgentSkill(
        id="catalog_search",
        name="Data catalog search",
        description=(
            "Find datasets and tables in theLook's data catalog and explain what "
            "each contains. Answers 'what data do you have about X?' by returning "
            "matching BigQuery tables with their descriptions — metadata only, "
            "never the values inside the data."
        ),
        tags=["catalog", "discovery", "metadata", "bigquery", "knowledge-catalog"],
        examples=[
            "What data do you have about orders?",
            "Which tables cover customer demographics?",
            "Where would I find product inventory information?",
        ],
    ),
]


def apply_skills(card: AgentCard, skills: list[AgentSkill] | None = None) -> AgentCard:
    """Replace a card's skills with the explicit list, in place.

    The card is a protobuf message whose ``skills`` is a repeated field, so it
    can't be assigned (``card.skills = [...]`` raises); clear it and extend with
    the explicit entries. Returns the same card for call-site convenience.
    """
    chosen = DISCOVERY_SKILLS if skills is None else skills
    del card.skills[:]
    card.skills.extend(chosen)
    return card
