"""The adaptation guard: does `validate` actually catch a broken edit?

A checker that passes on everything is worse than none, because it converts
"nobody looked" into "something looked and was happy". Each test here breaks the
corpus/oracle/questions triple in one of the ways an adapter really breaks it and
asserts the specific complaint comes back.
"""

import json

import corpus
import golden
import validate


def _write(tmp_path, questions):
    path = tmp_path / "questions.json"
    path.write_text(json.dumps(questions))
    return path


def _question(**overrides):
    """A minimal valid question, so each test perturbs exactly one thing."""
    base = {
        "id": "q1",
        "category": "direct",
        "question": "How many users?",
        "golden_key": "total_users",
        "evidence": {"must_have": ["users"], "nice_to_have": [], "distractor": []},
    }
    return base | overrides


def test_the_shipped_experiment_is_coherent():
    assert validate.problems() == []


def test_a_golden_key_that_matches_nothing_is_caught(tmp_path):
    # The motivating bug: build_results does `.get(golden_key)`, so this resolves
    # to None, which is a legal state for a prose question. Every cell then
    # scores wrong and nothing says why until the sweep is paid for.
    path = _write(tmp_path, [_question(golden_key="total_userz")])
    found = validate.problems(path)
    assert any("total_userz" in line and "matches no golden" in line for line in found)


def test_an_empty_golden_key_is_allowed(tmp_path):
    # "" is the explicit way to declare a question with no numeric answer, and
    # must stay distinguishable from a typo.
    path = _write(tmp_path, [_question(golden_key="")])
    assert not [line for line in validate.problems(path) if "golden" in line.lower()
                and "orphan" not in line and "asked by no question" not in line]


def test_an_evidence_term_that_is_not_a_column_is_caught(tmp_path):
    # Silently unrecallable: the arm's evidence score becomes a floor forever,
    # which reads as a finding rather than a typo.
    path = _write(tmp_path, [_question(
        evidence={"must_have": ["users"], "nice_to_have": [], "distractor": ["revenue_amt"]}
    )])
    found = validate.problems(path)
    assert any("revenue_amt" in line and "distractor" in line for line in found)


def test_real_corpus_names_are_accepted_from_every_bucket(tmp_path):
    path = _write(tmp_path, [_question(evidence={
        "must_have": [corpus.TRANSACTIONS.name],
        "nice_to_have": ["txn_amt_x2"],
        "distractor": ["revenue_amount"],
    })])
    assert not [line for line in validate.problems(path) if "evidence" in line]


def test_duplicate_ids_are_caught(tmp_path):
    # Cell keys are built from the question id, so duplicates silently halve the
    # replicate count for both.
    path = _write(tmp_path, [_question(), _question(golden_key="refunded_txn_count")])
    assert any("duplicate id" in line for line in validate.problems(path))


def test_a_question_with_no_must_have_terms_is_caught(tmp_path):
    path = _write(tmp_path, [_question(
        evidence={"must_have": [], "nice_to_have": [], "distractor": []}
    )])
    assert any("must_have" in line for line in validate.problems(path))


def test_unasked_goldens_are_reported(tmp_path):
    # Every shipped golden but one goes unreferenced here.
    path = _write(tmp_path, [_question()])
    found = validate.problems(path)
    assert any("asked by no question" in line for line in found)
    assert "total_users" not in [line for line in found if "asked by no question" in line][0]


def test_the_message_lists_the_keys_that_would_have_worked(tmp_path):
    # An adapter who mistyped needs the candidate list in the error, not a
    # second round trip through the source.
    path = _write(tmp_path, [_question(golden_key="nope")])
    line = next(x for x in validate.problems(path) if "nope" in x)
    assert all(key in line for key in sorted(golden.BY_KEY))


def test_a_rule_trigger_naming_a_dead_column_is_caught(monkeypatch):
    # Renaming a column without updating RULE_TRIGGERS makes rules_for() return
    # [], so every governed question reports "no rule to acquire" — a finding
    # shaped like a result.
    import scoring
    monkeypatch.setitem(scoring.RULE_TRIGGERS, "net-revenue", frozenset({"txn_amt_x3"}))
    found = validate.problems()
    assert any("txn_amt_x3" in line and "RULE_TRIGGERS" in line for line in found)
