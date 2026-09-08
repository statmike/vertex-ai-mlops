"""Provision the whole sandbox: corpus, governance, and prerequisite checks.

    uv run python scripts/setup.py [--skip-scans] [--skip-glossary] [--skip-looker]

Idempotent — safe to re-run. Every step prints what it did; read the output
rather than trusting the exit code, because catalog enrichment uses preview APIs
and treats failures as non-fatal (see `catalog_setup`).

Tear down with `scripts/cleanup.py`. This creates billable BigQuery storage and
Dataplex scans, so do that when you are done.
"""

import argparse
import sys

import _bootstrap  # noqa: F401 - import for the sys.path side effect
from google.cloud import bigquery

import bq_setup
import catalog_setup
import config
import corpus
import golden
import looker_check
import validate


def provision_bigquery(client: bigquery.Client) -> None:
    print("\n[1/5] BigQuery datasets:")
    bq_setup.create_datasets(client)

    print(f"\n[2/5] Generating corpus in tier {bq_setup.SOURCE_TIER}:")
    bq_setup.generate_source_tier(client)
    bq_setup.copy_to_other_tiers(client)

    print("\n[3/5] Applying governance to schemas:")
    # Strip first on every tier that should not carry descriptions, rather than
    # only on tier 0. The rungs are provisioned into the same datasets across
    # runs, so a tier that carried descriptions under an earlier configuration
    # keeps them unless something takes them away — and a rung silently holding
    # the rung above's governance flattens the step without failing anything.
    with_descriptions = config.tiers_with("descriptions")
    for tier in config.TIERS:
        if tier in with_descriptions:
            bq_setup.apply_descriptions(client, tier)
        else:
            bq_setup.strip_descriptions(client, tier)


def verify_corpus(client: bigquery.Client) -> bool:
    """Report row counts, trap calibration, and cross-tier golden agreement."""
    print("\n[4/5] Verifying corpus:")
    for tier in config.TIERS:
        counts = bq_setup.row_counts(client, tier)
        total = sum(counts.values())
        print(f"    Tier {tier}: {counts} ({total:,} rows)")

    traps = bq_setup.verify_traps(client, bq_setup.SOURCE_TIER)
    print("    Realized trap calibration (targets in corpus.py):")
    for name, value in traps.items():
        print(f"      {name}: {value:.1%}")

    # The tiers must hold identical data — governance is the only difference.
    # If the goldens disagree, the control is contaminated and every T1-T0 read
    # in the results is meaningless, so this is worth failing loudly on.
    baseline = golden.resolve_all(client, config.TIERS[0])
    print(f"    Golden truth (tier {config.TIERS[0]}):")
    for key, resolved in baseline.items():
        trap = f"   [trap answer: {resolved.trap_value:,.2f}]" if resolved.trap_value else ""
        print(f"      {key}: {resolved.value:,.2f}{trap}")

    ok = True
    for tier in config.TIERS[1:]:
        for key, resolved in golden.resolve_all(client, tier).items():
            if not golden.matches(baseline[key], resolved.value):
                print(
                    f"    MISMATCH {key}: tier {config.TIERS[0]} = {baseline[key].value} "
                    f"but tier {tier} = {resolved.value}. Tiers are not a clean control."
                )
                ok = False
    if ok:
        print(f"    Tiers agree on all {len(baseline)} golden values.")
    return ok


def verify_governance() -> bool:
    """Read the rules back, and confirm the control tier has none.

    Writing an aspect can succeed while storing nothing — a field the template
    does not recognize is dropped rather than rejected. Only a read-back proves
    the governance is actually there, and the whole T1-T0 contrast rests on it.
    """
    ok = True
    with_rules = config.tiers_with("rules")
    for tier in config.TIERS:
        for table in corpus.TABLE_NAMES:
            rule = catalog_setup.read_business_rule(tier, table)
            # Every tier is read back, including the rungs that should have no
            # rules. A rung that carries governance it was not meant to carry
            # collapses the step above it, and unlike a missing rule that shows
            # up as a low score, an extra one shows up as no finding at all.
            expected = corpus.GUIDELINES[table] if tier in with_rules else None
            if rule != expected:
                got = f"{rule[:60]!r}..." if rule else "nothing"
                print(f"    WRONG {config.tier_dataset(tier)}.{table}: stored {got}")
                ok = False
    print("    Rules verified by read-back." if ok else "    Governance is NOT as designed.")
    return ok


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "--skip-scans", action="store_true", help="Skip Dataplex profile and quality scans"
    )
    parser.add_argument("--skip-glossary", action="store_true", help="Skip glossary + links")
    parser.add_argument("--skip-looker", action="store_true", help="Skip the Looker check")
    args = parser.parse_args()

    # First, and before anything billable exists. If the corpus, the oracle and
    # the questions disagree, the sweep still runs and still costs money — it
    # just scores the disagreement as wrong answers. Cheapest possible failure.
    print("Checking corpus / oracle / questions:")
    if not validate.report(include_looker=not args.skip_looker):
        print("\nFix the above before provisioning. Nothing was created.")
        return 1

    project = config.require_project()
    print(f"\nProvisioning data-mcp-sandbox in {project}")
    for tier in config.RUNG_ORDER:
        if tier in config.TIERS:
            print(f"  Tier:   {config.tier_label(tier)}")
    print(f"  Corpus: {len(corpus.CORPUS)} tables x {len(config.TIERS)} tiers")

    client = bigquery.Client(project=project)
    provision_bigquery(client)
    corpus_ok = verify_corpus(client)

    print("\n[5/5] Knowledge Catalog governance (tier 1+):")
    if args.skip_scans:
        print("    Profile + quality scans: SKIPPED")
    else:
        catalog_setup.create_and_run_profile_scans()
        catalog_setup.create_and_run_quality_scans()
    # Clear first: aspects are additive, so a stale one from an earlier run
    # would otherwise linger alongside the intended governance.
    for tier in config.TIERS:
        catalog_setup.strip_governance_aspects(tier)
    catalog_setup.attach_business_rules()
    governance_ok = verify_governance()
    if args.skip_glossary:
        print("    Glossary: SKIPPED")
    else:
        catalog_setup.create_glossary_and_links()

    if not args.skip_looker:
        print("\nLooker prerequisites (Path 2, p4_looker_ca):")
        looker_check.report()

    print("\nDone. Tear down with: uv run python scripts/cleanup.py")
    return 0 if corpus_ok and governance_ok else 1


if __name__ == "__main__":
    sys.exit(main())
