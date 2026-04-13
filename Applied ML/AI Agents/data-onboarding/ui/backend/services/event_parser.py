"""Parse agent stream events into frontend-friendly JSON.

Works with both local ADK Runner events (normalized to dicts by
agent_engine._event_to_dict) and remote Agent Engine events.

Frontend event types:
    transfer  — agent routing (agent_chat → agent_context)
    thinking  — progress indicator (schema resolution, query planning)
    sql       — generated SQL query
    data      — query result rows (table)
    text      — text response (thought, progress, or final answer)
    chart     — rendered chart image (base64 PNG)
    error     — error message from the agent
    status    — connection/session status updates
"""

import json
import logging
import re

logger = logging.getLogger(__name__)


def parse_event(raw_event: dict) -> list[dict]:
    """Parse a raw event into frontend events.

    A single event can produce multiple frontend events
    (e.g., a content event with both a function_call and text).

    Returns a list of frontend event dicts, each with at minimum a
    ``type`` field.
    """
    events = []

    content = raw_event.get("content")
    actions = raw_event.get("actions")
    author = raw_event.get("author", "")

    # Agent transfers
    if actions and isinstance(actions, dict):
        transfer_to = actions.get("transfer_to_agent")
        if transfer_to:
            events.append({
                "type": "transfer",
                "from": author,
                "to": transfer_to,
            })

    # Content parts
    if content and isinstance(content, dict):
        role = content.get("role", "")
        parts = content.get("parts", [])

        for part in parts:
            if not isinstance(part, dict):
                continue

            # Text content
            text = part.get("text")
            if text:
                events.append({
                    "type": "text",
                    "author": author,
                    "role": role,
                    "content": text,
                })

            # Function calls — thinking/progress indicators
            fc = part.get("functionCall") or part.get("function_call")
            if fc:
                name = fc.get("name", "")
                args = fc.get("args", {})
                events.append({
                    "type": "thinking",
                    "author": author,
                    "tool": name,
                    "args": _safe_args(args),
                    "label": _tool_label(name),
                })

            # Function responses — may contain structured data
            fr = part.get("functionResponse") or part.get("function_response")
            if fr:
                name = fr.get("name", "")
                response = fr.get("response", {})
                parsed = _parse_tool_response(name, response, author)
                if parsed:
                    events.extend(parsed)

    # Fallback: raw content string
    if not events and isinstance(content, str) and content.strip():
        events.append({
            "type": "text",
            "author": author,
            "role": "model",
            "content": content,
        })

    # Post-process: extract Vega-Lite specs from text events
    final = []
    for ev in events:
        if ev.get("type") == "text" and ev.get("content"):
            extracted = _extract_vega_from_text(ev["content"], ev.get("author", ""))
            final.extend(extracted)
        else:
            final.append(ev)

    return final


def _tool_label(tool_name: str) -> str:
    """Human-readable label for a tool call."""
    labels = {
        "rerank_tables": "Finding relevant tables...",
        "conversational_chat": "Analyzing data...",
        "meta_chat": "Checking pipeline metadata...",
        "search_context": "Searching documentation...",
        "get_table_columns": "Looking up column details...",
        "list_all_tables": "Listing available tables...",
    }
    return labels.get(tool_name, f"Running {tool_name}...")


def _safe_args(args: dict) -> dict:
    """Truncate large argument values for frontend display."""
    safe = {}
    for k, v in args.items():
        s = str(v)
        safe[k] = s[:200] + "..." if len(s) > 200 else s
    return safe


def _parse_tool_response(
    tool_name: str, response: dict, author: str,
) -> list[dict]:
    """Parse a function response into frontend events."""
    events = []

    if not isinstance(response, dict):
        return events

    result = response.get("result", "")

    if tool_name in ("conversational_chat", "meta_chat"):
        events.extend(_parse_convo_response(result, author))

    elif tool_name in ("search_context", "get_table_columns", "list_all_tables"):
        if isinstance(result, str) and result.strip():
            events.append({
                "type": "text",
                "author": author,
                "role": "model",
                "content": result,
                "is_answer": True,
            })

    elif tool_name == "rerank_tables":
        if isinstance(result, str) and result.strip():
            events.append({
                "type": "thinking",
                "author": author,
                "tool": tool_name,
                "label": "Tables identified",
                "detail": result[:500],
            })

    return events


def _parse_convo_response(result, author: str) -> list[dict]:
    """Parse a conversational_chat / meta_chat response.

    The response is either:
      - A JSON string with ``answer`` + ``parts`` (structured format)
      - A plain text string (legacy / error fallback)
    """
    if not isinstance(result, str) or not result.strip():
        return []

    # Try structured JSON first
    try:
        data = json.loads(result)
        if isinstance(data, dict) and "parts" in data:
            return _parse_structured_parts(data, author)
    except (json.JSONDecodeError, TypeError):
        pass

    # Fallback: plain text
    return [{
        "type": "text",
        "author": author,
        "role": "model",
        "content": result.strip(),
        "is_answer": True,
    }]


def _parse_structured_parts(data: dict, author: str) -> list[dict]:
    """Convert structured parts into separate frontend events."""
    events = []

    for part in data.get("parts", []):
        part_type = part.get("type", "")

        if part_type == "sql":
            events.append({
                "type": "sql",
                "author": author,
                "content": part["content"],
            })

        elif part_type == "data":
            events.append({
                "type": "data",
                "author": author,
                "content": part["content"],
            })

        elif part_type == "chart":
            event = {"type": "chart", "author": author}
            if "vega_spec" in part:
                event["vega_spec"] = part["vega_spec"]
            if "image" in part:
                event["image_src"] = part["image"]
            events.append(event)

        elif part_type == "text":
            events.append({
                "type": "text",
                "author": author,
                "role": "model",
                "content": part["content"],
                "is_answer": True,
            })

    # If no text part came through, use the top-level answer
    has_text = any(e["type"] == "text" for e in events)
    if not has_text:
        answer = data.get("answer", "")
        if answer.strip():
            events.append({
                "type": "text",
                "author": author,
                "role": "model",
                "content": answer.strip(),
                "is_answer": True,
            })

    return events


def _extract_vega_from_text(text: str, author: str) -> list[dict]:
    """Split a text event into text + chart events if Vega-Lite JSON is found.

    Scans for JSON objects containing ``mark`` and ``encoding`` keys
    (the signature of a Vega-Lite spec).  Returns the surrounding text
    as text events and the spec as a chart event with ``vega_spec``.
    """
    has_mark = '"mark"' in text
    has_encoding = '"encoding"' in text
    logger.debug(
        "Vega check: has_mark=%s has_encoding=%s text_len=%d text_preview=%.200s",
        has_mark, has_encoding, len(text), text[:200],
    )

    if not has_mark or not has_encoding:
        return [{
            "type": "text",
            "author": author,
            "role": "model",
            "content": text,
        }]

    # Match JSON code blocks:  ```json ... ``` or `json ... `
    pattern = re.compile(
        r'[`]{1,3}(?:json)?\s*\n?(\{[\s\S]*?\})\s*\n?[`]{1,3}',
        re.IGNORECASE,
    )

    parts = []
    last_end = 0

    for m in pattern.finditer(text):
        json_str = m.group(1).strip()
        try:
            obj = json.loads(json_str)
            if isinstance(obj, dict) and "mark" in obj and "encoding" in obj:
                # Text before the chart
                before = text[last_end:m.start()].strip()
                if before:
                    parts.append({
                        "type": "text",
                        "author": author,
                        "role": "model",
                        "content": before,
                        "is_answer": True,
                    })
                # The chart
                parts.append({
                    "type": "chart",
                    "author": author,
                    "vega_spec": obj,
                })
                last_end = m.end()
        except (json.JSONDecodeError, TypeError):
            continue

    # If we found charts, add remaining text
    if parts:
        remaining = text[last_end:].strip()
        if remaining:
            parts.append({
                "type": "text",
                "author": author,
                "role": "model",
                "content": remaining,
                "is_answer": True,
            })
        return parts

    # No Vega-Lite found — return original text event unchanged
    return [{
        "type": "text",
        "author": author,
        "role": "model",
        "content": text,
    }]
