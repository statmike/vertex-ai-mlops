"""Tools for the tools agent — lookup, calculate, and explain.

Demonstrates two patterns:
- lookup/calculate: pure programmatic tools (no LLM calls)
- explain: calls Gemini directly via google-genai for richer answers

The explain tool shows how a tool can make its own LLM call using the
TOOL_MODEL from config — separate from the agent's reasoning model.
"""

from google import genai

from config import TOOL_MODEL, TOOL_MODEL_LOCATION

# Create a Gemini client — used by the explain tool
_client = genai.Client(vertexai=True, location=TOOL_MODEL_LOCATION)

# A small knowledge base to demonstrate tool use
KNOWLEDGE_BASE = {
    "mercury": "Mercury is the closest planet to the Sun at 57.9 million km. It has no moons and a day lasts 59 Earth days.",
    "venus": "Venus is the hottest planet with surface temperatures of 465C. It rotates backwards compared to most planets.",
    "earth": "Earth is the third planet from the Sun, 149.6 million km away. It has one moon and is the only known planet with life.",
    "mars": "Mars is the Red Planet, 227.9 million km from the Sun. It has two moons: Phobos and Deimos.",
    "jupiter": "Jupiter is the largest planet with a mass of 1.898 x 10^27 kg. It has 95 known moons including Ganymede, the largest moon in the solar system.",
    "saturn": "Saturn is famous for its rings made of ice and rock. It has 146 known moons including Titan, which has a thick atmosphere.",
    "uranus": "Uranus rotates on its side with an axial tilt of 98 degrees. It has 28 known moons and 13 rings.",
    "neptune": "Neptune is the farthest planet at 4.5 billion km from the Sun. Its winds reach 2,100 km/h, the fastest in the solar system.",
    "sun": "The Sun is a G-type main-sequence star containing 99.86% of the solar system's mass. Its core temperature is about 15 million degrees Celsius.",
    "moon": "Earth's Moon is 384,400 km away. It's the fifth largest moon in the solar system and the only other world humans have visited.",
}


def lookup(query: str) -> dict:
    """Search the knowledge base for information about a topic.

    Args:
        query: The topic to look up (e.g., "mars", "jupiter", "sun").

    Returns:
        A dict with the search result or a not-found message.
    """
    query_lower = query.lower().strip()

    # Exact match
    if query_lower in KNOWLEDGE_BASE:
        return {"found": True, "topic": query_lower, "info": KNOWLEDGE_BASE[query_lower]}

    # Partial match — check if query appears in any key
    for key, info in KNOWLEDGE_BASE.items():
        if query_lower in key or key in query_lower:
            return {"found": True, "topic": key, "info": info}

    # Search in values
    for key, info in KNOWLEDGE_BASE.items():
        if query_lower in info.lower():
            return {"found": True, "topic": key, "info": info}

    available = ", ".join(sorted(KNOWLEDGE_BASE.keys()))
    return {"found": False, "message": f"No information found for '{query}'. Available topics: {available}"}


def calculate(expression: str) -> dict:
    """Evaluate a mathematical expression.

    Args:
        expression: A math expression to evaluate (e.g., "2 + 3", "149.6 * 1000").

    Returns:
        A dict with the result or an error message.
    """
    # Only allow safe math operations
    allowed_chars = set("0123456789+-*/.() eE")
    if not all(c in allowed_chars for c in expression.replace(" ", "")):
        return {"error": f"Invalid characters in expression: {expression}"}

    try:
        result = eval(expression)  # noqa: S307 — safe: input is restricted to numeric chars
        return {"expression": expression, "result": result}
    except Exception as e:
        return {"error": f"Could not evaluate '{expression}': {e}"}


def explain(topic: str) -> dict:
    """Get a detailed explanation of a solar system topic using Gemini.

    Unlike lookup (which searches a static knowledge base), this tool calls
    Gemini directly via the google-genai SDK for richer, more detailed answers.

    This demonstrates a common pattern: tools that make their own LLM calls
    using the TOOL_MODEL, separate from the agent's reasoning model.

    Args:
        topic: The topic to explain (e.g., "why is Mars red", "how do Saturn's rings form").

    Returns:
        A dict with Gemini's explanation.
    """
    response = _client.models.generate_content(
        model=TOOL_MODEL,
        contents=f"Explain this solar system topic in 2-3 concise sentences: {topic}",
    )
    return {"topic": topic, "explanation": response.text}
