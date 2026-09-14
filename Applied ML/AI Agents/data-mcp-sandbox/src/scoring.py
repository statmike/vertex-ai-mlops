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
* **Questions whose wording admits two defensible answers.** Three of this
  corpus's twelve say "trailing 30 days" without pinning what the window trails,
  and agents alternate between the two readings within one arm at temperature 0.
  The oracle holds one of them, so `correct` there measures agreement with an
  arbitrary choice. Those cells still run and are still captured; `graded()`
  drops them from every accuracy aggregate. See `battery.Question.scoreable`.

Scores live here and never in `traces.Cell`, so a rubric change re-scores the
existing capture instead of re-running it.
"""

import json
import re
from collections import Counter
from collections.abc import Iterable
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
    # Whether this question's oracle carries a trap value at all. Only `zero_scan`
    # reads it, to tell "everyone missed and nobody sprang the recorded trap" from
    # "everyone missed and there is no recorded trap to spring" — which are
    # opposite diagnoses. A `scores.json` written before this field existed reads
    # False and gets the more cautious of the two wordings, never a wrong one.
    trap_known: bool = False

    # Whether `correct` means anything for this question. False marks a question
    # whose wording admits two defensible answers; `correct` is still computed
    # and still recorded, but every accuracy aggregate excludes the cell rather
    # than crediting agreement with an arbitrary choice. See `battery.Question`.
    scoreable: bool = True

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
    # How many times *this process* called a model. Zero is meaningful rather
    # than boring: the direct-API arms have no local model turn at all, so their
    # token counts are truly 0 while the work still happened — server-side,
    # unmetered. `report.py` reads this to print `--` instead of `0` there,
    # because a 0 in a token column sorts to the top of "cheapest".
    #
    # `None` is *not recorded* and must never collapse into 0. A `scores.json`
    # written before this field existed re-renders through `--from-scores`, and
    # defaulting it to 0 would declare every arm in that file model-free — which
    # blanked all twenty token rows the first time this was tried.
    model_calls: int | None = None
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
        """Acquired the rule and still got it wrong — the §9.1 gap, per cell.

        Gated on `scoreable` for the same reason accuracy is: on an
        anchor-ambiguous question an agent can read the rule, apply it exactly,
        and still disagree with the oracle. Counting that as a loss would report
        the corpus's defect as the agent's.
        """
        return self.scoreable and self.acquired and self.answered and not self.correct


def graded(scores: Iterable["Score"]) -> list["Score"]:
    """The subset whose `correct` means something.

    Every accuracy aggregate in this repo runs over this rather than over the
    raw scores, and this is the one place that decision lives. A question whose
    wording admits two defensible answers is *unmeasured*: the cell ran, is in
    the capture, and carries a `correct` a reader can inspect — it just does not
    enter a rate, the same way an opaque path's evidence reads `--` rather than
    0.0. Unmeasured is not zero.
    """
    return [score for score in scores if score.scoreable]


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
    so a bolded number outside a code fence wins. Validated against the M3
    capture: every wrong extraction found there was the agent genuinely
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
    scoreable: bool = True,
) -> Score:
    """Score one cell deterministically. `resolved` may be None for prose questions."""
    result = Score(
        scoreable=scoreable,
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
        # No `or 0` — a capture that never recorded this reads None, not zero.
        model_calls=(
            None if cell.usage.get("model_calls") is None
            else int(cell.usage["model_calls"])
        ),
    )
    result.rules_required = rules_for(evidence)
    result.trap_known = resolved is not None and bool(golden.traps_of(resolved))

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
        # Which trap, not just whether one — a question with two traps in it has a
        # compound miss that springs both, and "sprang the trap" would name the
        # wrong failure. `trap_name` is what the report prints.
        sprung = golden.trap_sprung(resolved, result.value)
        result.sprang_trap = sprung is not None
        if sprung:
            result.trap_name = sprung
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
    # Of `pairs`, the ones on a gradeable question. `same_verdict` divides by
    # this and nothing else does: whether two arms ran the same tools, or landed
    # on the same number, is observable no matter how the question is worded.
    # Only the *verdict* inherits the oracle's arbitrary anchor choice.
    graded_pairs: int = 0
    same_sequence: int = 0
    same_value: int = 0
    same_verdict: int = 0
    examples: list[str] = field(default_factory=list)

    def fraction(self, attribute: str) -> float | None:
        total = self.graded_pairs if attribute == "same_verdict" else self.pairs
        return getattr(self, attribute) / total if total else None


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
        if not score_a.scoreable:
            continue
        result.graded_pairs += 1
        if score_a.correct == score_b.correct:
            result.same_verdict += 1
        elif len(result.examples) < 5:
            winner = config_a if score_a.correct else config_b
            result.examples.append(
                f"{cell_a.question_id} tier{cell_a.tier} run{cell_a.run}: only {winner} correct"
            )
    return result


# --- the 0/n scan -------------------------------------------------------------
#
# The anchor defect cost this project a day of chasing a failed replication check
# before anyone decomposed the disagreement per question. The signature was in
# the data the whole time: three questions at exactly 0/n across every arm, with
# the arms agreeing with each other and disagreeing only with us. This runs that
# decomposition automatically, so the next rubric bug announces itself.

# An arm can plausibly fail a hard question. Several arms independently landing
# on the same wrong number cannot be several independent failures, so a shutout
# is only interesting once enough arms are in it to rule that out.
MIN_ARMS_FOR_ZERO_SCAN = 3
# Distinct answer clusters allowed before the misses look like ordinary, varied
# wrongness rather than one shared cause. Three, not one, because the defect this
# was built for produced *two* clusters — the agents split between two defensible
# window anchors.
MAX_CLUSTERS_FOR_SUSPICION = 3


@dataclass
class ZeroScan:
    """One (question, tier) and the arms that went 0/n on it.

    Read per arm and not per question, because the defect this was built for did
    not shut out the whole factorial: ten arms scored 0/n on `governed-q1` at
    tier 1 while the two direct arms — merged in from a second run under a
    *second oracle* — scored normally. A check that only fired on a unanimous
    zero would have stayed silent on exactly that.

    Not every shutout is a bug. Tier 0 is *supposed* to produce them on
    governed-logic questions; that is the finding the experiment exists to show.
    What separates a finding from a defect is whether the shut-out arms agree
    with each other: a trap catches everyone by design, and a question the
    oracle grades wrongly leaves everyone clustered on a number it rejects.
    """

    question_id: str
    tier: int
    arms: int
    shutout_arms: tuple[str, ...] = ()
    answered: int = 0
    sprang_trap: int = 0
    trap_known: bool = False
    clusters: int = 0
    modal_value: float | None = None
    modal_share: int = 0
    modal_arms: int = 0
    # Cells that got this same question right at some *other* tier. A golden the
    # governed tier hits repeatedly is a golden that computes a reachable number,
    # which rules out the first of the two repairs below and leaves the second.
    # Nothing else in this scan can see across tiers, because every other
    # question it asks is about arms agreeing within one condition.
    graded_elsewhere: int = 0

    @property
    def shutouts(self) -> int:
        return len(self.shutout_arms)

    @property
    def by_design(self) -> bool:
        """Most of the misses are the trap value — the corpus working, not a bug."""
        return self.answered > 0 and self.sprang_trap * 2 > self.answered

    @property
    def suspect(self) -> bool:
        """The shut-out arms agree with each other and only the oracle dissents."""
        return (
            self.shutouts >= MIN_ARMS_FOR_ZERO_SCAN
            and self.answered > 0
            and not self.by_design
            and 0 < self.clusters <= MAX_CLUSTERS_FOR_SUSPICION
            and self.modal_arms >= MIN_ARMS_FOR_ZERO_SCAN
        )

    @property
    def reason(self) -> str:
        """Why this row is or is not being called a grading mismatch."""
        if self.shutouts < MIN_ARMS_FOR_ZERO_SCAN:
            return (
                f"only {self.shutouts} arm(s) shut out — too few to tell a shared "
                "cause from a hard question"
            )
        if self.answered == 0:
            return "no shut-out arm produced a number; a failure to answer, not a grading question"
        if self.by_design:
            return (
                f"{self.sprang_trap}/{self.answered} sprang the trap — "
                "the corpus working as designed"
            )
        if self.clusters > MAX_CLUSTERS_FOR_SUSPICION:
            return f"{self.clusters} distinct answers — varied wrongness, not one shared cause"
        if self.modal_arms < MIN_ARMS_FOR_ZERO_SCAN:
            return f"the modal answer spans only {self.modal_arms} arm(s)"
        partial = (
            f", while {self.arms - self.shutouts} other arm(s) scored normally"
            if self.shutouts < self.arms else ""
        )
        agreement = (
            f"{self.modal_arms} shut-out arms agree on {self.modal_value:,.0f} and the "
            f"oracle rejects it{partial}"
        )
        if self.graded_elsewhere:
            return (
                f"{agreement} — but the same question is answered correctly "
                f"{self.graded_elsewhere} time(s) at another tier, so the golden computes "
                "a reachable number. Read this as a naive answer the oracle has no trap "
                "recorded for, not as a bad golden"
            )
        if not self.trap_known:
            return (
                f"{agreement} — and this question's oracle records **no trap value**, so a "
                "trap-shaped miss here cannot be told from ordinary wrongness. Check "
                "whether that number is the naive answer before reading this as failure"
            )
        return f"{agreement} — suspect the golden or the question's wording, not the agents"


def _cluster(values: list[float]) -> list[list[int]]:
    """Group value indices by mutual agreement within the grading tolerance.

    The *same* tolerance the oracle grades with, deliberately: the claim being
    tested is "these arms computed the same quantity and the oracle disagrees",
    and that claim is only meaningful at the resolution the oracle itself uses.
    Greedy single pass — clusters here are far apart or identical, so the
    pathological chaining case a proper clustering would guard against does not
    arise, and a legible ten lines beats a correct hundred.
    """
    clusters: list[list[int]] = []
    for index, value in enumerate(values):
        for group in clusters:
            if _close(value, values[group[0]]):
                group.append(index)
                break
        else:
            clusters.append([index])
    return clusters


def zero_scan(scores: Iterable[Score], min_arms: int = MIN_ARMS_FOR_ZERO_SCAN) -> list[ZeroScan]:
    """Every (question, tier) where `min_arms` or more arms scored a clean 0/n.

    Returns the whole set, suspect or not, rather than only the flagged ones —
    a reader needs to see that the tier-0 governed questions were checked and
    cleared, or the check reads as having found nothing because it looked at
    nothing.

    A single replicate is not a shutout: an arm with n=1 is 0/1 half the time on
    anything hard, and counting it would flood the scan with noise from pilots.
    """
    buckets: dict[tuple[str, int], dict[str, list[Score]]] = {}
    correct_by_question: dict[str, Counter[int]] = {}
    for score in graded(scores):
        by_arm = buckets.setdefault((score.question_id, score.tier), {})
        by_arm.setdefault(score.config, []).append(score)
        if score.correct:
            correct_by_question.setdefault(score.question_id, Counter())[score.tier] += 1

    results = []
    for (question_id, tier), by_arm in sorted(buckets.items()):
        shut_out = {
            config: replicates for config, replicates in sorted(by_arm.items())
            if len(replicates) > 1 and not any(score.correct for score in replicates)
        }
        if len(shut_out) < min_arms:
            continue
        misses = [score for replicates in shut_out.values() for score in replicates]
        answered = [score for score in misses if score.answered and score.value is not None]
        scan = ZeroScan(
            question_id=question_id,
            tier=tier,
            arms=len(by_arm),
            shutout_arms=tuple(shut_out),
            answered=len(answered),
            sprang_trap=sum(1 for score in misses if score.sprang_trap),
            trap_known=any(score.trap_known for score in misses),
            graded_elsewhere=sum(
                count
                for other_tier, count in correct_by_question.get(question_id, {}).items()
                if other_tier != tier
            ),
        )
        clusters = _cluster([score.value for score in answered if score.value is not None])
        if clusters:
            modal = max(clusters, key=len)
            scan.clusters = len(clusters)
            scan.modal_value = answered[modal[0]].value
            scan.modal_share = len(modal)
            scan.modal_arms = len({answered[index].config for index in modal})
        results.append(scan)
    return results
