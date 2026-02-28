"""Utilities for resolving JSON Schema $ref references.

Pydantic's `.model_json_schema()` produces schemas with `$defs` and `$ref`
references (e.g., `{"$ref": "#/$defs/FlowchartNode"}`). The tools in this
package need to inspect `items.properties` and `items.required` for nodes
and edges, so this module resolves those references to inline definitions.
"""


def resolve_items(schema: dict, element_key: str) -> dict:
    """Resolve the items schema for 'nodes' or 'edges', following $ref if present.

    Args:
        schema: The full JSON Schema dict (top-level).
        element_key: Either 'nodes' or 'edges'.

    Returns:
        The resolved items schema dict with 'properties' and 'required',
        or an empty dict if not found.
    """
    props = schema.get("properties", {})
    items = props.get(element_key, {}).get("items", {})

    if not items:
        return {}

    # If items is a $ref, resolve it
    ref = items.get("$ref")
    if ref:
        items = _resolve_ref(schema, ref)

    return items


def _resolve_ref(schema: dict, ref: str) -> dict:
    """Resolve a JSON Schema $ref string like '#/$defs/FlowchartNode'."""
    if not ref.startswith("#/"):
        return {}

    path_parts = ref[2:].split("/")
    current = schema
    for part in path_parts:
        if isinstance(current, dict):
            current = current.get(part, {})
        else:
            return {}

    return current if isinstance(current, dict) else {}
