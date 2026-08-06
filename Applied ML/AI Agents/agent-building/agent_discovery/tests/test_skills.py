"""Tests for the discovery agent's explicit A2A skills.

Import-light on purpose: importing agent_discovery.agent would pull in the ADK
Claude client. Here we pin the skill declarations and the in-place mutation
contract of apply_skills against a real protobuf AgentCard (its `skills` is a
repeated field that can't be reassigned, only cleared and extended).
"""

from a2a.types import AgentCard, AgentSkill

from agent_discovery.skills import DISCOVERY_SKILLS, apply_skills


def test_discovery_skills_are_complete():
    """Every advertised skill has the fields a consumer needs to route to it."""
    assert DISCOVERY_SKILLS, "discovery must advertise at least one skill"
    ids = [s.id for s in DISCOVERY_SKILLS]
    assert len(ids) == len(set(ids)), "skill ids must be unique"
    for skill in DISCOVERY_SKILLS:
        assert isinstance(skill, AgentSkill)
        assert skill.id and skill.name and skill.description
        assert skill.tags, f"{skill.id} must carry discovery tags"
        assert skill.examples, f"{skill.id} should show example questions"


def test_apply_skills_replaces_existing_in_place():
    """apply_skills clears auto-derived skills and installs the explicit ones."""
    card = AgentCard()
    # Simulate an auto-derived skill the builder would have produced.
    card.skills.extend([AgentSkill(id="agent_discovery", name="model", description="d", tags=["llm"])])

    returned = apply_skills(card)

    assert returned is card  # mutates and returns the same card
    assert [s.id for s in card.skills] == [s.id for s in DISCOVERY_SKILLS]
    assert "llm" not in {t for s in card.skills for t in s.tags}


def test_apply_skills_accepts_explicit_override():
    card = AgentCard()
    custom = [AgentSkill(id="x", name="X", description="d", tags=["t"])]
    apply_skills(card, custom)
    assert [s.id for s in card.skills] == ["x"]
