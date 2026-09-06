"""Invariants for attributing Conversational Analytics' server-side tokens.

Everything here guards the same weakness: attribution is by *time window*, because
the metric carries no caller label. That works only while the sweep keeps each CA
arm in one contiguous block, and it produces a plausible-looking wrong answer the
moment it does not. These tests pin the two places that judgement lives.

No network. `measure()` is the only function that talks to Monitoring, and the
logic worth testing was deliberately kept out of it.
"""

import pytest

import service_tokens
import traces


def _cell(key, config, tier, started_at, ended_at):
    return traces.Cell(
        cell_key=key, question_id="q", category="direct", question="?",
        config=config, tier=tier, run=1, started_at=started_at, ended_at=ended_at,
    )


def _block_cells(config, tier, hour, count=3):
    return [
        _cell(f"{config}-{tier}-{i}", config, tier,
              f"2026-09-04T{hour:02d}:{i * 10:02d}:00+00:00",
              f"2026-09-04T{hour:02d}:{i * 10 + 5:02d}:00+00:00")
        for i in range(count)
    ]


def test_blocks_collapses_a_contiguous_run_into_one_window():
    blocks = service_tokens.blocks(_block_cells("p4_looker_ca", 0, 20))
    assert len(blocks) == 1
    assert blocks[0].cells == 3
    assert blocks[0].started_at == "2026-09-04T20:00:00+00:00"
    assert blocks[0].ended_at == "2026-09-04T20:25:00+00:00"


def test_a_split_ca_arm_refuses_rather_than_guessing():
    # The failure this prevents is silent. If a CA arm runs, something else runs,
    # then the CA arm resumes, a single [first start, last end] window swallows
    # the gap and bills the neighbour's tokens to it. The number that comes out
    # is large, plausible, and wrong, so this raises instead.
    split = (
        _block_cells("p4_looker_ca", 0, 20)
        + _block_cells("p1_toolbox", 0, 21)
        + _block_cells("p4_looker_ca", 0, 22)
    )
    with pytest.raises(ValueError, match="more than one block"):
        service_tokens.blocks(split)


def test_a_split_non_ca_arm_is_not_an_error():
    # The M6 sweep ends with a retry pass that backfills failed MCP cells hours
    # after Path 4 finished. Those arms make no CA calls, so they cannot move a
    # token between CA blocks — failing the whole attribution over them would be
    # a false alarm that makes the tool useless on real captures.
    split = (
        _block_cells("p1_toolbox", 0, 2)
        + _block_cells("p4_looker_ca", 0, 20)
        + _block_cells("p1_toolbox", 0, 23)
    )
    blocks = service_tokens.blocks(split)
    assert [b.config for b in blocks] == ["p1_toolbox", "p4_looker_ca", "p1_toolbox"]


def test_attribution_keys_on_turns_not_tokens():
    # Blocks abut to the second and the finest alignment available is 60s, so the
    # bucket holding a handoff is credited to both neighbours. On M6 that gave
    # `p4_bq_ca` tier 1 1,725 tokens against zero turns — spillover from the arm
    # that started 2s later, which reported as a "1x understatement". A block
    # that ran no CA turn did no CA work, whatever the token column says.
    spillover = service_tokens.ServiceUsage(
        config="p4_bq_ca", tier=1, started_at="", ended_at="",
        input_tokens=1_700, output_tokens=25, turns=0, model_calls=2,
    )
    assert not spillover.attributed

    real = service_tokens.ServiceUsage(
        config="p4_looker_ca", tier=1, started_at="", ended_at="",
        input_tokens=13_859_212, output_tokens=881_148, turns=74, model_calls=385,
    )
    assert real.attributed
    assert real.total_tokens == 14_740_360


def test_a_zero_is_read_against_the_request_meter_not_alone():
    """`uninstrumented` is the difference between "did nothing" and "went uncounted".

    Both readings are zero on the CA usage metrics. Only the request meter — a
    different pipeline, published by the API front-end — can tell them apart, and
    on M6 it recorded 189 successful `DataChatService.Chat` calls for the block
    that reported no tokens at all.
    """
    uncounted = service_tokens.ServiceUsage(
        config="p4_bq_ca", tier=0, started_at="", ended_at="",
        turns=0, chat_requests=189,
    )
    assert not uncounted.attributed
    assert uncounted.uninstrumented

    idle = service_tokens.ServiceUsage(
        config="p1_toolbox", tier=0, started_at="", ended_at="",
        turns=0, chat_requests=0,
    )
    assert not idle.attributed
    assert not idle.uninstrumented, "no calls and no tokens is an idle block, not a gap"

    counted = service_tokens.ServiceUsage(
        config="p4_looker_ca", tier=0, started_at="", ended_at="",
        input_tokens=30_183_342, turns=133, chat_requests=133,
    )
    assert not counted.uninstrumented, "a metered arm is not a hole in the meter"


def test_the_spillover_block_is_still_not_a_measurement():
    # The 60s-boundary artifact from the test above now also carries a request
    # count, and must not start reading as a measured arm because of it.
    spillover = service_tokens.ServiceUsage(
        config="p4_bq_ca", tier=1, started_at="", ended_at="",
        input_tokens=1_700, output_tokens=25, turns=0, model_calls=2, chat_requests=117,
    )
    assert not spillover.attributed
    assert spillover.uninstrumented
