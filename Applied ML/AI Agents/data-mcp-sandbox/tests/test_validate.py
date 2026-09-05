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


def test_a_table_with_no_looker_view_is_caught(monkeypatch):
    # render_all() looks every corpus table up in VIEW_NAMES and PRIMARY_KEYS, so
    # a table added without touching lookml.py raises KeyError — but not until
    # `make lookml`, which is after BigQuery has been provisioned.
    import dataclasses

    import lookml

    extra = dataclasses.replace(corpus.USERS, name="campaigns")
    monkeypatch.setattr(corpus, "CORPUS", [*corpus.CORPUS, extra])
    found = validate.looker_problems()
    assert any("VIEW_NAMES" in line and "campaigns" in line for line in found)
    assert any("PRIMARY_KEYS" in line and "campaigns" in line for line in found)
    assert lookml.VIEW_NAMES  # the real mapping is untouched


def test_a_stale_primary_key_is_caught(monkeypatch):
    # A renamed key column leaves PRIMARY_KEYS pointing at nothing. Looker then
    # cannot use symmetric aggregates and summed measures fan out across the
    # join, which inflates them silently rather than erroring.
    import lookml

    monkeypatch.setitem(lookml.PRIMARY_KEYS, corpus.USERS.name, "user_pk")
    assert any("user_pk" in line for line in validate.looker_problems())


def test_a_column_type_lookml_cannot_render_is_caught(monkeypatch):
    import dataclasses

    table = corpus.TRANSACTIONS
    columns = [dataclasses.replace(table.columns[0], type="NUMERIC"), *table.columns[1:]]
    swapped = dataclasses.replace(table, columns=columns)
    monkeypatch.setattr(
        corpus, "CORPUS", [swapped if t is table else t for t in corpus.CORPUS]
    )
    assert any("NUMERIC" in line for line in validate.looker_problems())


def test_the_explore_must_name_a_real_view(monkeypatch):
    import config

    monkeypatch.setattr(config, "LOOKER_EXPLORE", "orders")
    assert any("LOOKER_EXPLORE" in line for line in validate.looker_problems())


def test_looker_checks_can_be_skipped(monkeypatch):
    # A BigQuery-only adapter running SKIP_LOOKER should not be blocked by a
    # seam only Path 2 and p4_looker_ca use.
    import lookml

    monkeypatch.setitem(lookml.PRIMARY_KEYS, corpus.USERS.name, "user_pk")
    assert any("user_pk" in line for line in validate.problems())
    assert not [line for line in validate.problems(include_looker=False) if "user_pk" in line]
