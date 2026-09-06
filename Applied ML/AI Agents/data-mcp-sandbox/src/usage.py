"""Per-cell token accounting.

A process-local accumulator, reset at the start of every evaluation cell and
read at the end. Cells run strictly one at a time (docs/method.md), so a module
global is honest here — with concurrent cells it would silently blend them,
which is exactly why the battery never parallelizes.

Tokens are read off the ADK event stream rather than intercepted at the client,
so this counts what the model actually billed for, including thinking tokens.
`gemini-3.7-flash` is a reasoning model, and thoughts often dominate the output
count — collapsing them into one total would hide the most interesting cost
difference between architectures.
"""

from dataclasses import asdict, dataclass

from google.genai import types


@dataclass
class Usage:
    """Token totals for one cell."""

    prompt_tokens: int = 0
    output_tokens: int = 0
    thought_tokens: int = 0
    total_tokens: int = 0
    model_calls: int = 0

    def as_dict(self) -> dict[str, int]:
        return asdict(self)


_current = Usage()


def reset() -> None:
    """Start a new cell. Call before every run, not just the first."""
    global _current  # noqa: PLW0603
    _current = Usage()


def record(metadata: types.GenerateContentResponseUsageMetadata | None) -> None:
    """Add one model turn's `usage_metadata`. Missing fields count as zero.

    ADK omits a counter entirely when it is zero, and emits events with no usage
    metadata at all (tool results, partial streams). Both are skipped rather
    than treated as errors.
    """
    if metadata is None:
        return
    _current.prompt_tokens += getattr(metadata, "prompt_token_count", 0) or 0
    _current.output_tokens += getattr(metadata, "candidates_token_count", 0) or 0
    _current.thought_tokens += getattr(metadata, "thoughts_token_count", 0) or 0
    _current.total_tokens += getattr(metadata, "total_token_count", 0) or 0
    _current.model_calls += 1


def get() -> Usage:
    """Totals accumulated since the last `reset`."""
    return _current
