"""Deterministic scoring of captured cells. No model calls happen here.

Everything that can be decided by parsing is decided by parsing — docs/questions.md
sends only semantic adherence to the judge, because an LLM asked to compare two
numbers adds variance for no gain.

The central decomposition is §9.1: **acquisition** (did the governed rule ever
reach the agent?) versus **application** (did the emitted query honour it?). A
single accuracy number conflates "the architecture never surfaced the rule" with
"the agent read the rule and ignored it", which are different failures with
different fixes.

Two things here are deliberately allowed to be *unmeasured* rather than zero,
because the alternative is a fabricated finding:

* **Evidence on opaque paths.** Conversational Analytics narrates itself in
  prose and never names the field it used, so `p4_looker_ca` has no inspectable
  query. Scoring it 0.0 recall next to Toolbox's 1.0 would report "Path 4
  ignores the semantic layer" when the truth is "Path 4 does not show its work".
* **Acquisition at tier 0.** There is no governed description to acquire, so the
  marker check returns False by construction and every tier-0 miss is an
  acquisition failure. That is the intended reading, not a gap.

Scores live here and never in `traces.Cell`, so a rubric change re-scores the
existing capture instead of re-running it.
"""

import json
import re
from dataclasses import dataclass, field

import corpus
import golden
import mcp_clients
import traces

# Tool arguments that carry SQL as a plain string. Toolbox calls it `sql`; the
# managed BigQuery endpoint calls it `query`. Both are read, and only when the
# value really is a string — `query` is *also* the name of a Looker tool whose
# arguments are a structured field list, handled below. Dropping `query` from
# here scored every managed arm at 0.00 evidence recall while it was answering
# 67% of questions correctly, which is the shape an extraction bug takes.
SQL_ARG_KEYS = ("sql", "query", "statement")

# Looker's MCP does not take SQL — it takes a field list, and `query_sql`
# compiles one to SQL without running it. The `fields`/`dynamic_fields` args are
# therefore the same evidence as a SELECT list and are read as such. Only the
# field-bearing keys are serialized: `user_query_with_context` echoes the user's
# own question, and scanning that would score an agent as "used the `users`
# table" for a question with the word "users" in it.
LOOKER_QUERY_TOOLS = frozenset({"query", "query_sql", "run_query", "run_inline_query"})
LOOKER_FIELD_KEYS = ("fields", "dynamic_fields", "filters", "pivots", "sorts")

# CA puts whatever SQL it ran inside its THOUGHT stream, when it mentions it at
# all. For the Looker-backed variant it usually does not.
CA_SQL_PATTERN = re.compile(r"(SELECT\b.*?)(?:\\n\"|\"\]|$)", re.IGNORECASE | re.DOTALL)

# Conversational Analytics reachable from a non-Path-4 arm. `ask_data_insights`
# ships in TOOLBOX_BIGQUERY_TOOLS, so p1_toolbox and p3_toolbox *can* call it and
# quietly become Path 4 for that cell. Flagged rather than blocked: it is a real
# behaviour of the as-shipped surface, and the report should say how often it
# happens instead of pretending the arms are hermetic.
CA_TOOLS = frozenset({"ask_data_insights", "looker_conversational_analytics"})

# Phrases that appear in a tool result only if a *tier-1 governed description*
# came back — not merely a column name, which any schema dump at either tier
# contains. Getting this wrong is not subtle: keying acquisition on the column
# names in `questions.json` scored acquisition at 100% on tier 0, where there is
# by construction nothing to acquire, and flattened the §9.1 split to noise.
#
# Kept as short literals rather than sliced out of the corpus text, and pinned to
# it by `test_governance_markers_are_in_the_corpus`, so rewording a description
# fails a test instead of silently zeroing acquisition.
GOVERNANCE_MARKERS = {
    "net-revenue": ("gross list price", "misnamed", "excluded from net revenue"),
    "active-user": ("not the governed definition", "dormant"),
}

# Which rule a question depends on, inferred from the columns its evidence names.
# A question that touches none of these (a plain row count) has no governed rule,
# and acquisition is reported as not-applicable rather than as a failure.
RULE_TRIGGERS = {
    "net-revenue": frozenset({"txn_amt_x2", "status_flg", "revenue_amount"}),
    "active-user": frozenset({"is_active", "event_ts"}),
}


@dataclass
class Score:
    """One cell's deterministic scores. Attached beside a Cell, never inside it."""

    cell_key: str
    config: str
    tier: int
    question_id: str
    category: str

    answered: bool = False
    value: float | None = None
    correct: bool = False
    sprang_trap: bool = False
    trap_name: str = ""

    # None means *not measurable on this path*, and must stay distinct from 0.0.
    evidence_recall: float | None = None
    evidence_precision: float | None = None
    evidence_observable: bool = False
    used_distractor: bool = False

    rules_required: list[str] = field(default_factory=list)
    rules_acquired: list[str] = field(default_factory=list)
    acquisition_observable: bool = False

    tool_calls: int = 0
    failed_tool_calls: int = 0
    ca_leak: bool = False
    attempts: int = 1
    latency_s: float = 0.0
    # Copied off the capture so token reporting does not depend on the BigQuery
    # attribution pass. `cost.py` re-reads the same `cell.usage`; both derive
    # from one recorded value, so they cannot drift apart.
    total_tokens: int = 0
    prompt_tokens: int = 0
    output_tokens: int = 0
    thought_tokens: int = 0
    notes: list[str] = field(default_factory=list)

    @property
    def acquired(self) -> bool:
        """Every governed rule this question needs came back from a metadata tool.

        False when acquisition is unobservable, so this must never be read as
        "did not acquire" without checking `acquisition_observable` first.
        """
        return (
            self.acquisition_observable
            and bool(self.rules_required)
            and len(self.rules_acquired) == len(self.rules_required)
        )

    @property
    def application_loss(self) -> bool:
        """Acquired the rule and still got it wrong — the §9.1 gap, per cell."""
        return self.acquired and self.answered and not self.correct


# --- number extraction -------------------------------------------------------

# A number with optional thousands separators and decimals, optionally prefixed
# by a currency symbol.
_NUMBER = r"-?\$?\s?\d[\d,]*(?:\.\d+)?"
_BOLD_NUMBER = re.compile(rf"\*\*\s*({_NUMBER})\s*\*\*")
_ANY_NUMBER = re.compile(_NUMBER)
# SQL fences hold numbers that are *inputs* (row limits, date offsets), not the
# answer. Stripping them before extraction stops `LIMIT 1000` being read as the
# result.
_CODE_FENCE = re.compile(r"```.*?```", re.DOTALL)


def extract_number(answer: str) -> float | None:
    """The headline number from a prose answer, or None if there isn't one.

    The agent is told to state the number plainly and it almost always bolds it,
    so a bolded number outside a code fence wins. Validated against the 960-cell
    M3 capture: every wrong extraction found there was the agent genuinely
    answering with a different number, not a parse error.
    """
    prose = _CODE_FENCE.sub(" ", answer or "")

    bold = _BOLD_NUMBER.search(prose)
    if bold:
        return _to_float(bold.group(1))

    first = _ANY_NUMBER.search(prose)
    return _to_float(first.group(0)) if first else None


def _to_float(text: str) -> float | None:
    try:
        return float(text.replace(",", "").replace("$", "").strip())
    except ValueError:
        return None


# --- evidence ----------------------------------------------------------------


def evidence_text(cell: traces.Cell) -> str:
    """Everything in the trace that reveals *which fields* the cell queried.

    Four shapes, because the paths show their work four different ways: SQL the
    service reported about itself (`emitted_sql`, direct API), SQL as a tool
    argument (BigQuery `execute_sql`), a structured field list as a tool argument
    (Looker MCP), and SQL buried in a tool result (`query_sql` compiles rather
    than executes; CA narrates).

    `emitted_sql` comes first and short-circuits, because it is the only one of
    the four that is not an inference. The other three are the trace we scraped;
    this one is the query the service says it ran, carried alongside the job id
    that ran it (Amendment B.4.3). It is empty on every arm that predates the
    direct transport, so the fallback below is what scores the published capture
    — unchanged, and re-scoring it must keep producing the same numbers.
    """
    if cell.emitted_sql:
        return "\n".join(cell.emitted_sql)

    parts: list[str] = []
    for call in cell.tool_calls:
        for key in SQL_ARG_KEYS:
            value = call.args.get(key)
            if isinstance(value, str) and value.strip():
                parts.append(value)

        if call.name in LOOKER_QUERY_TOOLS:
            picked = {k: call.args[k] for k in LOOKER_FIELD_KEYS if k in call.args}
            if picked:
                parts.append(json.dumps(picked))

        if call.name in CA_TOOLS or "sql" in call.name.lower():
            parts.extend(CA_SQL_PATTERN.findall(call.result or ""))
    return "\n".join(parts)


def evidence_scores(text: str, evidence: dict[str, list[str]]) -> tuple[float, float, bool]:
    """Recall over `must_have`, precision against distractors, and a trap flag.

    Matched on whole identifiers, so `revenue_amount` does not count as a hit for
    a `revenue` term. That distinction is the entire T1 trap: the decoy column's
    name contains the real concept's.
    """
    haystack = (text or "").lower()
    must = [term.lower() for term in evidence.get("must_have", [])]
    distractors = [term.lower() for term in evidence.get("distractor", [])]

    hits = sum(1 for term in must if _mentions(haystack, term))
    recall = hits / len(must) if must else 1.0

    decoys = sum(1 for term in distractors if _mentions(haystack, term))
    denominator = hits + decoys
    precision = hits / denominator if denominator else (1.0 if not must else 0.0)
    return recall, precision, decoys > 0


def _mentions(haystack: str, term: str) -> bool:
    return re.search(rf"(?<![a-z0-9_]){re.escape(term)}(?![a-z0-9_])", haystack) is not None


# --- acquisition -------------------------------------------------------------


def rules_for(evidence: dict[str, list[str]]) -> list[str]:
    """Which governed rules a question's answer depends on."""
    named = {term.lower() for term in evidence.get("must_have", [])} | {
        term.lower() for term in evidence.get("distractor", [])
    }
    return [rule for rule, columns in RULE_TRIGGERS.items() if named & columns]


def rules_acquired(cell: traces.Cell, required: list[str]) -> tuple[list[str], bool]:
    """Which of those rules came back from a metadata tool, and whether any could.

    Read from tool *results*, never from the answer: the point of §9.1 is to
    separate "the architecture never surfaced it" from "the agent was told and
    ignored it", and an answer that recites the rule proves only the second.

    CA's output is excluded, which is the whole reason this returns a second
    value. Its THOUGHT stream is model-generated prose, so a marker found there
    is not evidence that anything was delivered — at tier 0, where by
    construction no governed description exists, CA confabulated the column
    semantics and got them exactly backwards, describing `txn_amt_x2` as the
    gross list price and the `revenue_amount` decoy as net revenue (DEV_NOTES
    2026-09-03). That fired the `gross list price` marker on 15 tier-0 cells.
    An arm with nothing but CA tools therefore has *unmeasurable* acquisition,
    not zero acquisition.

    That is a property of the *tool*, not of Conversational Analytics. Toolbox's
    `bigquery-conversational-analytics` returns prose; the API beneath it streams
    a `DataMessage` carrying `generated_sql` and `big_query_job` (SDK 0.13.2 —
    docs/paths.md). `evidence_text` reads that SQL, so the direct arms *are*
    scorable for evidence.

    Acquisition is a different question and stays unobservable on them, which is
    why this function needs no direct-arm branch: it looks for governed text in
    tool results, and a direct arm has no tools. On `p4_bq_direct_ctx` the
    glossary is injected by construction rather than discovered, so there is
    nothing to measure — reporting it as acquired would be scoring our own
    request payload back to ourselves.
    """
    bodies = [
        (call.result or "").lower()
        for call in cell.tool_calls
        if not call.is_error and call.name not in CA_TOOLS
    ]
    if not bodies:
        return [], False
    joined = "\n".join(bodies)
    return [
        rule for rule in required if any(m in joined for m in GOVERNANCE_MARKERS[rule])
    ], True


# --- per-cell ----------------------------------------------------------------


def score_cell(
    cell: traces.Cell,
    evidence: dict[str, list[str]],
    resolved: golden.Resolved | None,
) -> Score:
    """Score one cell deterministically. `resolved` may be None for prose questions."""
    result = Score(
        cell_key=cell.cell_key,
        config=cell.config,
        tier=cell.tier,
        question_id=cell.question_id,
        category=cell.category,
        answered=cell.ok,
        tool_calls=len(cell.tool_calls),
        failed_tool_calls=sum(1 for call in cell.tool_calls if call.is_error),
        attempts=cell.attempts,
        latency_s=cell.latency_s,
        total_tokens=int(cell.usage.get("total_tokens", 0) or 0),
        prompt_tokens=int(cell.usage.get("prompt_tokens", 0) or 0),
        output_tokens=int(cell.usage.get("output_tokens", 0) or 0),
        thought_tokens=int(cell.usage.get("thought_tokens", 0) or 0),
    )
    result.rules_required = rules_for(evidence)

    if not cell.ok:
        # §9.4: an error cell is a failure, not a missing observation. Dropping
        # it would flatter whichever architecture crashes most.
        result.notes.append(cell.error[:120] if cell.error else "empty answer")
        return result

    spec = mcp_clients.CONFIGS.get(cell.config)
    used_ca = any(name in CA_TOOLS for name in cell.tool_names())
    if spec is not None and spec.path != 4:
        result.ca_leak = used_ca

    text = evidence_text(cell)
    if text.strip():
        result.evidence_observable = True
        recall, precision, used_decoy = evidence_scores(text, evidence)
        result.evidence_recall = recall
        result.evidence_precision = precision
        result.used_distractor = used_decoy
    elif used_ca or mcp_clients.is_direct(cell.config):
        # The path answered through an opaque service that did not disclose its
        # query. Unmeasured, not zero. A direct arm reaches that same service
        # with no tool call to detect it by, so the config is what identifies it
        # — without this, a direct cell that disclosed nothing would fall to the
        # branch below and be scored 0.0 for having "skipped the data", which is
        # the exact confusion Amendment A.3 built this split to prevent.
        result.notes.append("no inspectable query - CA did not disclose one")
    else:
        # A transparent path that wrote no query at all really did skip the data
        # — but a whole arm reading 0.0 means `evidence_text` does not know that
        # server's argument names, so the note is what tells the two apart.
        result.evidence_observable = True
        result.evidence_recall = 0.0
        result.evidence_precision = 0.0
        result.notes.append("no query text recovered")

    result.rules_acquired, result.acquisition_observable = rules_acquired(
        cell, result.rules_required
    )

    result.value = extract_number(cell.answer)
    if resolved is not None and result.value is not None:
        result.correct = golden.matches(resolved, result.value)
        result.sprang_trap = golden.sprang_trap(resolved, result.value)
        if result.sprang_trap:
            result.trap_name = resolved.trap_name
    elif resolved is not None:
        result.notes.append("no extractable number - needs judge")

    return result


def rule_statement(rules: list[str]) -> str:
    """The canonical prose for a question's governed rules, for the judge prompt.

    The glossary wording, not the union used for marker pinning — the judge is
    grading against the rule as a human governance owner would state it, and
    padding the prompt with every column description invites it to grade
    thoroughness instead of adherence.
    """
    wanted = set(rules)
    return "\n".join(
        term.description for term in corpus.GLOSSARY_TERMS if term.term_id in wanted
    )


def corpus_rule_text(rule: str) -> str:
    """All tier-1 prose a rule's markers may legitimately come from.

    The glossary term states the rule; the column descriptions restate the sharp
    edge of it right where an agent reading a schema will hit it. A marker only
    has to appear in one of them — the test pins markers to this union so that
    rewording a description fails loudly instead of silently zeroing acquisition.
    """
    parts = [
        term.description
        for term in corpus.GLOSSARY_TERMS
        if term.term_id == rule
    ]
    triggers = RULE_TRIGGERS[rule]
    for table in corpus.TABLE_NAMES:
        parts.extend(
            description
            for name, description in corpus.columns_with_descriptions(table).items()
            if name in triggers
        )
    return "\n".join(parts).lower()


# --- equivalence -------------------------------------------------------------
#
# Equivalence was originally scoped as a judge criterion. Comparing two traces is a
# sequence-and-number comparison, so it lives in code (docs/questions.md) — an LLM
# asked to do it adds variance and nothing else.


@dataclass
class ArmComparison:
    """How closely two configs behave on the same cells."""

    config_a: str
    config_b: str
    pairs: int = 0
    same_sequence: int = 0
    same_value: int = 0
    same_verdict: int = 0
    examples: list[str] = field(default_factory=list)

    def fraction(self, attribute: str) -> float | None:
        return getattr(self, attribute) / self.pairs if self.pairs else None


def _close(a: float | None, b: float | None) -> bool:
    if a is None or b is None:
        return a is b
    if a == b:
        return True
    scale = max(abs(a), abs(b))
    return scale > 0 and abs(a - b) / scale <= golden.DEFAULT_TOLERANCE


def compare_arms(
    cells: dict[str, traces.Cell],
    scores: dict[str, Score],
    config_a: str,
    config_b: str,
) -> ArmComparison:
    """Pair two configs cell-for-cell and report how often they agree.

    Paired by (question, tier, replicate), not pooled by arm: a pooled mean can
    hide two arms that are each right half the time on disjoint halves of the
    battery, which is the opposite of equivalence.

    `same_verdict` is the one that matters for a procurement decision — two arms
    that reach the same *correctness* through different tool sequences are
    interchangeable in practice, whatever their traces look like.
    """
    result = ArmComparison(config_a=config_a, config_b=config_b)
    for key_a, cell_a in cells.items():
        if cell_a.config != config_a:
            continue
        key_b = traces.cell_key(cell_a.question_id, config_b, cell_a.tier, cell_a.run)
        cell_b = cells.get(key_b)
        if cell_b is None:
            continue
        score_a, score_b = scores.get(key_a), scores.get(key_b)
        if score_a is None or score_b is None:
            continue

        result.pairs += 1
        if cell_a.tool_names() == cell_b.tool_names():
            result.same_sequence += 1
        if _close(score_a.value, score_b.value):
            result.same_value += 1
        if score_a.correct == score_b.correct:
            result.same_verdict += 1
        elif len(result.examples) < 5:
            winner = config_a if score_a.correct else config_b
            result.examples.append(
                f"{cell_a.question_id} tier{cell_a.tier} run{cell_a.run}: only {winner} correct"
            )
    return result
