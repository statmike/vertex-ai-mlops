"""Shared fixtures for agent_graph_qa tests."""

from unittest.mock import MagicMock

import pytest


@pytest.fixture
def mock_tool_context():
    """A MagicMock that behaves like tools.ToolContext with a dict state."""
    ctx = MagicMock()
    ctx.state = {}
    return ctx


@pytest.fixture
def sample_graph():
    """A valid graph with 2 nodes, 1 edge, and metadata."""
    return {
        "diagram_type": "flowchart",
        "nodes": [
            {
                "id": "n1",
                "label": "Start",
                "element_type": "terminal",
                "shape": "oval",
                "bounding_box": [50, 400, 120, 600],
                "confidence": "high",
            },
            {
                "id": "n2",
                "label": "Process",
                "element_type": "process",
                "shape": "rectangle",
                "bounding_box": [200, 350, 300, 650],
                "confidence": "medium",
            },
        ],
        "edges": [
            {
                "id": "e1",
                "source": "n1",
                "target": "n2",
                "label": None,
                "edge_type": "flow",
                "confidence": "high",
            },
        ],
        "metadata": {
            "source_file": "/tmp/test.png",
            "image_width": 1920,
            "image_height": 1080,
            "status": "complete",
        },
    }


@pytest.fixture
def sample_schema():
    """A valid JSON Schema with nodes/edges items (hand-written style)."""
    return {
        "title": "TestGraph",
        "description": "A test graph schema",
        "type": "object",
        "properties": {
            "diagram_type": {"type": "string"},
            "nodes": {
                "type": "array",
                "items": {
                    "type": "object",
                    "properties": {
                        "id": {"type": "string"},
                        "label": {"type": "string"},
                        "element_type": {"type": "string"},
                        "shape": {"type": "string"},
                        "bounding_box": {"type": "array"},
                        "confidence": {"type": "string"},
                    },
                    "required": ["id", "label"],
                },
            },
            "edges": {
                "type": "array",
                "items": {
                    "type": "object",
                    "properties": {
                        "id": {"type": "string"},
                        "source": {"type": "string"},
                        "target": {"type": "string"},
                        "label": {"type": "string"},
                        "edge_type": {"type": "string"},
                    },
                    "required": ["id", "source", "target"],
                },
            },
        },
        "required": ["diagram_type", "nodes", "edges"],
    }
