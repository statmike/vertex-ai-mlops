"""Publish governance into the Knowledge Catalog for tier 1.

Three things get published, and only to tier 1 — tier 0 is the ungoverned
control and must stay bare:

1. **Profile scans** (`create_and_run_profile_scans`) — gives the metadata
   battery category real findings to report, and springs the T4 null/outlier
   trap. Reachable via the Toolbox `dataplex` source only (DESIGN.md F3/F4).
1b. **Quality scans** (`create_and_run_quality_scans`) — the traps restated as
   executable rules, so their calibration arrives as a measured failure rate
   rather than as prose. Without these, `get_data_quality_results` returns the
   *profile* scan with the quality block simply absent: an HTTP 200 carrying
   nothing, which an agent can read as "no quality problems found" against a
   corpus built entirely out of them.
2. **Business rules** (`attach_business_rules`) — published as the system
   `overview` aspect. This is the only governance on the agent's critical path
   for Path 3 Managed, because it is what `lookup_context` returns.
3. **Glossary terms + definition links** (`create_glossary_and_links`) — console
   fidelity only. No MCP surface reads glossaries (DESIGN.md F5).

Preview APIs are used throughout, so every enrichment call is non-fatal: a
failure is printed and setup continues. Check the printed summary rather than
assuming success — a silent FAILED here means missing governance, which reads as
a bad score rather than a broken run.
"""

import contextlib
import time

from google.api_core.exceptions import AlreadyExists, InvalidArgument, NotFound
from google.cloud import dataplex_v1

import config
import corpus

# Governance is published only at these tiers. Tier 0 is the control.
GOVERNED_TIERS = tuple(t for t in config.TIERS if t >= 1)

GLOSSARY_ID = config.bounded_id(f"{config.RESOURCE_PREFIX}-glossary")

# System aspect types published by Google in the shared `dataplex-types` project.
#
# `overview` is where the business rules go: its `content` field is the only
# free-text slot on a system aspect. The similarly-named `guidelines` aspect is
# NOT a text container — its template holds a single boolean, `userManaged`. It
# is listed here so `strip_governance_aspects` can clear it, not to write to.
OVERVIEW_ASPECT_TYPE = "projects/dataplex-types/locations/global/aspectTypes/overview"
OVERVIEW_ASPECT_KEY = "dataplex-types.global.overview"
OVERVIEW_TEXT_FIELD = "content"
GUIDELINES_ASPECT_KEY = "dataplex-types.global.guidelines"

DEFINITION_ENTRY_LINK_TYPE = "projects/dataplex-types/locations/global/entryLinkTypes/definition"

# Dataplex admin APIs cap at 30 requests/minute; scans are created in a loop.
SCAN_THROTTLE_SECONDS = 5

_project_number_cache: str | None = None


def project_number() -> str:
    """Resolve the project *number*. Glossary term entry names embed it, not the id."""
    global _project_number_cache  # noqa: PLW0603
    if _project_number_cache is None:
        from google.cloud import resourcemanager_v3

        client = resourcemanager_v3.ProjectsClient()
        project = client.get_project(name=f"projects/{config.require_project()}")
        _project_number_cache = project.name.split("/")[-1]
    return _project_number_cache


# --- 1. Profile scans --------------------------------------------------------


def create_and_run_profile_scans(wait: bool = True) -> None:
    """Create and run one profile scan per governed-tier table."""
    client = dataplex_v1.DataScanServiceClient()
    parent = f"projects/{config.require_project()}/locations/{config.DATAPLEX_LOCATION}"
    jobs: list[tuple[str, str]] = []

    targets = [(tier, table) for tier in GOVERNED_TIERS for table in corpus.TABLE_NAMES]
    for i, (tier, table) in enumerate(targets):
        if i > 0:
            time.sleep(SCAN_THROTTLE_SECONDS)

        scan_id = config.profile_scan_id(tier, table)
        scan_name = f"{parent}/dataScans/{scan_id}"
        resource = (
            f"//bigquery.googleapis.com/projects/{config.PROJECT_ID}"
            f"/datasets/{config.tier_dataset(tier)}/tables/{table}"
        )
        scan = dataplex_v1.DataScan(
            data=dataplex_v1.DataSource(resource=resource),
            data_profile_spec=dataplex_v1.DataProfileSpec(
                sampling_percent=0.0,  # 0 = full scan; the corpus is small
                catalog_publishing_enabled=True,
            ),
            execution_spec=dataplex_v1.DataScan.ExecutionSpec(
                trigger=dataplex_v1.Trigger(on_demand=dataplex_v1.Trigger.OnDemand()),
            ),
            description=f"Profile scan for {config.tier_dataset(tier)}.{table}",
        )

        try:
            operation = client.create_data_scan(
                request=dataplex_v1.CreateDataScanRequest(
                    parent=parent, data_scan=scan, data_scan_id=scan_id
                )
            )
            operation.result()  # type: ignore[no-untyped-call]
            print(f"    Scan created: {scan_id}")
        except AlreadyExists:
            print(f"    Scan exists:  {scan_id}")

        try:
            response = client.run_data_scan(request=dataplex_v1.RunDataScanRequest(name=scan_name))
            jobs.append((scan_id, response.job.name))
        except Exception as e:  # noqa: BLE001 - preview API, non-fatal
            print(f"    Scan run FAILED (non-fatal): {scan_id} - {e}")

    if wait and jobs:
        _wait_for_scan_jobs(client, jobs)


def _wait_for_scan_jobs(
    client: dataplex_v1.DataScanServiceClient, jobs: list[tuple[str, str]]
) -> None:
    """Poll each scan job to completion. States 3/4/5 = CANCELLED/SUCCEEDED/FAILED."""
    print("    Waiting for profile scans...")
    for scan_id, job_name in jobs:
        for _ in range(30):  # up to 5 minutes per scan
            time.sleep(10)
            job = client.get_data_scan_job(request=dataplex_v1.GetDataScanJobRequest(name=job_name))
            if job.state in (3, 4, 5):
                print(f"    {scan_id}: {'OK' if job.state == 4 else f'state={job.state}'}")
                break
        else:
            print(f"    {scan_id}: TIMEOUT")


def delete_profile_scans() -> None:
    """Tear down every profile scan this project created."""
    client = dataplex_v1.DataScanServiceClient()
    parent = f"projects/{config.require_project()}/locations/{config.DATAPLEX_LOCATION}"
    for tier in GOVERNED_TIERS:
        for table in corpus.TABLE_NAMES:
            scan_id = config.profile_scan_id(tier, table)
            try:
                operation = client.delete_data_scan(name=f"{parent}/dataScans/{scan_id}")
                operation.result()  # type: ignore[no-untyped-call]
                print(f"    Scan deleted: {scan_id}")
            except NotFound:
                pass


# --- 1b. Data-quality scans --------------------------------------------------
#
# Every rule below is expected to FAIL, except the uniqueness control. That is
# the design, not a misconfiguration: each one asserts the property a naive
# reader assumes the corpus has, so its failure rate *is* the trap's calibration
# — 7% null, 12% refunded, 5-in-1000 outliers, 20% dormant. An agent that reads
# these gets the trap sizes as measured findings rather than as prose.
#
# `txn_id_unique` passes, and is here for that reason. A scan on which every
# rule fails is easy to dismiss as a broken scan.
#
# Tier 1 only, like every other enrichment in this module. A quality scan on
# tier 0 would hand the control arm the governed definitions and flatten the one
# contrast the experiment measures.


# Normal `revenue_amount` is net x 1.25, so at most ~249 for the generator's
# largest net. Outliers are net x 1000, so at least ~5000. Anything in the gap
# separates them; 1000 is chosen to be obviously between rather than tuned.
_OUTLIER_THRESHOLD = 1000

# Only the two tables that carry traps. `raw_events_2026` is plain clickstream —
# a scan there would publish rules with nothing to say.
QUALITY_SCAN_TABLES = (corpus.TRANSACTIONS.name, corpus.USERS.name)


def _quality_rules(tier: int) -> dict[str, list[dataplex_v1.DataQualityRule]]:
    """The rules to publish, keyed by table. Each maps to a documented trap."""
    events = f"`{config.PROJECT_ID}.{config.tier_dataset(tier)}.{corpus.RAW_EVENTS.name}`"
    return {
        corpus.TRANSACTIONS.name: [
            dataplex_v1.DataQualityRule(
                column="txn_amt_x2",
                dimension="COMPLETENESS",
                threshold=1.0,
                name="net-revenue-recorded",
                description=(
                    f"Net revenue must be recorded. Fails on the ~{corpus.PCT_NULL_REVENUE}% "
                    "of rows where txn_amt_x2 is NULL and revenue was never captured (T4)."
                ),
                non_null_expectation=dataplex_v1.DataQualityRule.NonNullExpectation(),
            ),
            dataplex_v1.DataQualityRule(
                column="revenue_amount",
                dimension="VALIDITY",
                threshold=1.0,
                ignore_null=True,
                name="gross-price-plausible",
                description=(
                    "Gross list price should sit in the same order of magnitude as net. "
                    f"Fails on the seeded {corpus.OUTLIERS_PER_1000}-in-1000 outliers, which "
                    "are what make SUM(revenue_amount) wrong by far more than the "
                    f"{int((corpus.GROSS_MULTIPLIER - 1) * 100)}% per-row markup (T1, T4)."
                ),
                range_expectation=dataplex_v1.DataQualityRule.RangeExpectation(
                    max_value=str(_OUTLIER_THRESHOLD)
                ),
            ),
            dataplex_v1.DataQualityRule(
                dimension="VALIDITY",
                threshold=1.0,
                name="not-refunded",
                description=(
                    f"Refunded rows must be excluded from net revenue. Fails on the "
                    f"~{corpus.PCT_REFUNDED}% where status_flg is TRUE — note the flag reads "
                    "as a status, not as a refund marker (T2)."
                ),
                row_condition_expectation=dataplex_v1.DataQualityRule.RowConditionExpectation(
                    sql_expression="NOT status_flg"
                ),
            ),
            dataplex_v1.DataQualityRule(
                column="txn_id",
                dimension="UNIQUENESS",
                threshold=1.0,
                name="txn-id-unique",
                description="Control. Expected to pass, so a scan of all-failures is legible.",
                uniqueness_expectation=dataplex_v1.DataQualityRule.UniquenessExpectation(),
            ),
        ],
        corpus.USERS.name: [
            dataplex_v1.DataQualityRule(
                dimension="CONSISTENCY",
                # No `threshold`: the API rejects one on a SqlAssertion, because
                # the assertion is already all-or-nothing — any returned row fails
                # the rule. Setting it is a 400, not a silently ignored field.
                name="is-active-matches-governed-definition",
                description=(
                    "The governed Active rule as an executable check: flagged AND seen in "
                    f"the trailing {corpus.ACTIVE_WINDOW_DAYS} days. Fails on the "
                    f"~{corpus.PCT_DORMANT}% of flagged users who are dormant, which is "
                    "exactly the gap between is_active and Active (T3)."
                ),
                sql_assertion=dataplex_v1.DataQualityRule.SqlAssertion(
                    sql_statement=(
                        "SELECT user_id FROM ${data()} u WHERE u.is_active AND NOT EXISTS ("
                        f"SELECT 1 FROM {events} e WHERE e.user_id = u.user_id "
                        "AND e.event_ts >= TIMESTAMP_SUB(CURRENT_TIMESTAMP(), "
                        f"INTERVAL {corpus.ACTIVE_WINDOW_DAYS} DAY))"
                    )
                ),
            ),
        ],
    }


def create_and_run_quality_scans(wait: bool = True) -> None:
    """Create and run one data-quality scan per governed-tier table that has rules."""
    client = dataplex_v1.DataScanServiceClient()
    parent = f"projects/{config.require_project()}/locations/{config.DATAPLEX_LOCATION}"
    jobs: list[tuple[str, str]] = []

    targets = [(tier, table) for tier in GOVERNED_TIERS for table in QUALITY_SCAN_TABLES]
    for i, (tier, table) in enumerate(targets):
        if i > 0:
            time.sleep(SCAN_THROTTLE_SECONDS)

        scan_id = config.quality_scan_id(tier, table)
        scan_name = f"{parent}/dataScans/{scan_id}"
        resource = (
            f"//bigquery.googleapis.com/projects/{config.PROJECT_ID}"
            f"/datasets/{config.tier_dataset(tier)}/tables/{table}"
        )
        scan = dataplex_v1.DataScan(
            data=dataplex_v1.DataSource(resource=resource),
            data_quality_spec=dataplex_v1.DataQualitySpec(
                rules=_quality_rules(tier)[table],
                sampling_percent=0.0,  # 0 = full scan; the corpus is small
                catalog_publishing_enabled=True,
            ),
            execution_spec=dataplex_v1.DataScan.ExecutionSpec(
                trigger=dataplex_v1.Trigger(on_demand=dataplex_v1.Trigger.OnDemand()),
            ),
            description=f"Data-quality scan for {config.tier_dataset(tier)}.{table}",
        )

        try:
            operation = client.create_data_scan(
                request=dataplex_v1.CreateDataScanRequest(
                    parent=parent, data_scan=scan, data_scan_id=scan_id
                )
            )
            operation.result()  # type: ignore[no-untyped-call]
            print(f"    Quality scan created: {scan_id}")
        except AlreadyExists:
            # Rules are edited far more often than tables are added, so a stale
            # rule set is the likely state here rather than a matching one.
            existing = dataplex_v1.DataScan(
                name=scan_name, data_quality_spec=scan.data_quality_spec
            )
            with contextlib.suppress(Exception):
                client.update_data_scan(
                    request=dataplex_v1.UpdateDataScanRequest(
                        data_scan=existing, update_mask={"paths": ["data_quality_spec"]}
                    )
                ).result()  # type: ignore[no-untyped-call]
            print(f"    Quality scan exists, rules refreshed: {scan_id}")

        try:
            response = client.run_data_scan(request=dataplex_v1.RunDataScanRequest(name=scan_name))
            jobs.append((scan_id, response.job.name))
        except Exception as e:  # noqa: BLE001 - preview API, non-fatal
            print(f"    Quality scan run FAILED (non-fatal): {scan_id} - {e}")

    if wait and jobs:
        _wait_for_scan_jobs(client, jobs)


def delete_quality_scans() -> None:
    """Tear down every data-quality scan this project created."""
    client = dataplex_v1.DataScanServiceClient()
    parent = f"projects/{config.require_project()}/locations/{config.DATAPLEX_LOCATION}"
    for tier in GOVERNED_TIERS:
        for table in QUALITY_SCAN_TABLES:
            scan_id = config.quality_scan_id(tier, table)
            try:
                operation = client.delete_data_scan(name=f"{parent}/dataScans/{scan_id}")
                operation.result()  # type: ignore[no-untyped-call]
                print(f"    Quality scan deleted: {scan_id}")
            except NotFound:
                pass


def quality_scans_present() -> bool | None:
    """Do this sandbox's data-quality scans exist right now? None if we cannot tell.

    Recorded in every capture header, because it is a property of the *environment*
    Path 3 was measured in rather than of the code. `search_dq_scans` returns a
    different list depending on the answer, so a capture taken before these scans
    existed is not comparable to one taken after — and without this field, telling
    the two apart means archaeology on the header's `git_commit`.

    Returns `None` rather than `False` when the API cannot be reached: "we did not
    look" and "they are not there" are different facts, and collapsing them is how
    an unmeasured thing gets reported as a zero.
    """
    try:
        client = dataplex_v1.DataScanServiceClient()
        parent = f"projects/{config.require_project()}/locations/{config.DATAPLEX_LOCATION}"
        for tier in GOVERNED_TIERS:
            for table in QUALITY_SCAN_TABLES:
                scan_id = config.quality_scan_id(tier, table)
                try:
                    client.get_data_scan(name=f"{parent}/dataScans/{scan_id}")
                except NotFound:
                    return False
        return True
    except Exception:
        return None


# --- 2. Business-rule aspect -------------------------------------------------


def attach_business_rules() -> None:
    """Write the business rules onto governed-tier table entries as `overview`.

    This is the *only* governance Path 3 Managed can reach — `lookup_context` is
    the sole context tool the managed server exposes (DESIGN.md F3). If this step
    reports FAILED, tier 1 is not actually governed for that path, and its scores
    are meaningless rather than merely low.

    The text is stored as plain text, not HTML. The console renders `overview` as
    rich text and would accept markup, but the agent receives the raw string and
    should not have to read around tags.
    """
    client = dataplex_v1.CatalogServiceClient()
    for tier in GOVERNED_TIERS:
        for table, text in corpus.GUIDELINES.items():
            entry = dataplex_v1.Entry(name=config.dataplex_entry_name(tier, table))
            entry.aspects[OVERVIEW_ASPECT_KEY] = dataplex_v1.Aspect(
                aspect_type=OVERVIEW_ASPECT_TYPE, data={OVERVIEW_TEXT_FIELD: text}
            )
            try:
                client.update_entry(
                    request=dataplex_v1.UpdateEntryRequest(
                        entry=entry,
                        update_mask={"paths": ["aspects"]},
                        aspect_keys=[OVERVIEW_ASPECT_KEY],
                    )
                )
                print(f"    Rules set: {config.tier_dataset(tier)}.{table}")
            except Exception as e:  # noqa: BLE001 - preview API, non-fatal
                print(f"    Rules FAILED: {config.tier_dataset(tier)}.{table} - {e}")


def strip_governance_aspects(tier: int) -> None:
    """Remove every rule-bearing aspect from a tier's entries.

    Two jobs: keep the control genuinely ungoverned, and clear stale aspects on
    tier 1 so a rule left over from an earlier run cannot be mistaken for the
    current one.

    Two API details make this fiddly. A delete must name the key exactly as the
    API stores it — system aspect keys come back prefixed with the *hosting
    Google project's* number, not this project's and not the `dataplex-types`
    alias accepted on write — so the keys are read off the entry rather than
    constructed. And omitting an aspect from the entry does nothing on its own;
    `delete_missing_aspects` is what actually removes it.
    """
    client = dataplex_v1.CatalogServiceClient()
    managed = (OVERVIEW_ASPECT_KEY, GUIDELINES_ASPECT_KEY)
    suffixes = tuple(f".{key.rsplit('.', 1)[-1]}" for key in managed)

    for table in corpus.TABLE_NAMES:
        name = config.dataplex_entry_name(tier, table)
        current = client.get_entry(
            request=dataplex_v1.GetEntryRequest(name=name, view=dataplex_v1.EntryView.ALL)
        )
        keys = [key for key in current.aspects if key.endswith(suffixes)]
        if not keys:
            continue
        entry = dataplex_v1.Entry(name=name)
        try:
            client.update_entry(
                request=dataplex_v1.UpdateEntryRequest(
                    entry=entry,
                    update_mask={"paths": ["aspects"]},
                    aspect_keys=keys,
                    delete_missing_aspects=True,
                )
            )
            print(f"    Aspects cleared: {config.tier_dataset(tier)}.{table}")
        except Exception as e:  # noqa: BLE001 - preview API, non-fatal
            print(f"    Aspect clear FAILED (non-fatal): {table} - {e}")


def read_business_rule(tier: int, table: str) -> str | None:
    """Read back the published rule. Used by setup to verify governance landed."""
    client = dataplex_v1.CatalogServiceClient()
    entry = client.get_entry(
        request=dataplex_v1.GetEntryRequest(
            name=config.dataplex_entry_name(tier, table), view=dataplex_v1.EntryView.ALL
        )
    )
    for key, aspect in entry.aspects.items():
        if key.endswith(".overview"):
            text = dict(aspect.data).get(OVERVIEW_TEXT_FIELD)
            return str(text) if text else None
    return None


# --- 3. Glossary (console fidelity only) -------------------------------------


def create_glossary_and_links() -> None:
    """Create the glossary, its terms, and term-to-column links on governed tiers."""
    glossary_client = dataplex_v1.BusinessGlossaryServiceClient()
    catalog_client = dataplex_v1.CatalogServiceClient()

    loc = config.CATALOG_LOCATION
    glossary_parent = f"projects/{config.require_project()}/locations/{loc}"
    glossary_name = f"{glossary_parent}/glossaries/{GLOSSARY_ID}"

    try:
        operation = glossary_client.create_glossary(
            request=dataplex_v1.CreateGlossaryRequest(
                parent=glossary_parent,
                glossary_id=GLOSSARY_ID,
                glossary=dataplex_v1.Glossary(
                    display_name="Data MCP Sandbox Glossary",
                    description="Business terms for the data-mcp-sandbox trap corpus.",
                ),
            )
        )
        operation.result()  # type: ignore[no-untyped-call]
        print(f"    Glossary created: {GLOSSARY_ID}")
    except AlreadyExists:
        print(f"    Glossary exists:  {GLOSSARY_ID}")

    # Create every term before any link — a term's catalog entry lags the term
    # itself by a few seconds and is not linkable until it propagates.
    for term in corpus.GLOSSARY_TERMS:
        try:
            glossary_client.create_glossary_term(
                request=dataplex_v1.CreateGlossaryTermRequest(
                    parent=glossary_name,
                    term_id=term.term_id,
                    term=dataplex_v1.GlossaryTerm(
                        display_name=term.display,
                        description=term.description,
                        parent=glossary_name,
                    ),
                )
            )
            print(f"    Term created: {term.term_id}")
        except (AlreadyExists, InvalidArgument) as e:
            # The term API reports an existing term as InvalidArgument, not AlreadyExists.
            if isinstance(e, InvalidArgument) and "already exists" not in str(e):
                raise
            print(f"    Term exists:  {term.term_id}")

    for tier in GOVERNED_TIERS:
        for term in corpus.GLOSSARY_TERMS:
            term_entry = (
                f"projects/{config.PROJECT_ID}/locations/{loc}/entryGroups/@dataplex"
                f"/entries/projects/{project_number()}/locations/{loc}"
                f"/glossaries/{GLOSSARY_ID}/terms/{term.term_id}"
            )
            for table, columns in term.columns.items():
                for column in columns:
                    _create_definition_link(
                        catalog_client,
                        link_id=config.definition_link_id(tier, term.term_id, table, column),
                        asset_entry=config.dataplex_entry_name(tier, table),
                        column=column,
                        term_entry=term_entry,
                    )


def _create_definition_link(
    client: dataplex_v1.CatalogServiceClient,
    *,
    link_id: str,
    asset_entry: str,
    column: str,
    term_entry: str,
) -> None:
    """Create one term-to-column link, retrying the term-entry propagation lag."""
    reference = dataplex_v1.EntryLink.EntryReference
    request = dataplex_v1.CreateEntryLinkRequest(
        parent=f"projects/{config.PROJECT_ID}/locations/{config.CATALOG_LOCATION}"
        f"/entryGroups/@bigquery",
        entry_link_id=link_id,
        entry_link=dataplex_v1.EntryLink(
            entry_link_type=DEFINITION_ENTRY_LINK_TYPE,
            entry_references=[
                reference(name=asset_entry, path=f"Schema.{column}", type_=reference.Type.SOURCE),
                reference(name=term_entry, type_=reference.Type.TARGET),
            ],
        ),
    )
    for attempt in range(6):
        try:
            client.create_entry_link(request=request)
            print(f"      Link: {link_id}")
            return
        except AlreadyExists:
            print(f"      Link exists: {link_id}")
            return
        except NotFound:
            if attempt < 5:
                time.sleep(5)
                continue
            print(f"      Link FAILED (non-fatal): {link_id} - term entry never appeared")
            return
        except Exception as e:  # noqa: BLE001 - preview API, non-fatal
            print(f"      Link FAILED (non-fatal): {link_id} - {e}")
            return


def delete_glossary() -> None:
    """Delete the glossary and its links. Links must go first — they pin the terms."""
    catalog_client = dataplex_v1.CatalogServiceClient()
    parent = (
        f"projects/{config.require_project()}/locations/{config.CATALOG_LOCATION}"
        f"/entryGroups/@bigquery"
    )
    for tier in GOVERNED_TIERS:
        for term in corpus.GLOSSARY_TERMS:
            for table, columns in term.columns.items():
                for column in columns:
                    link_id = config.definition_link_id(tier, term.term_id, table, column)
                    try:
                        catalog_client.delete_entry_link(name=f"{parent}/entryLinks/{link_id}")
                        print(f"    Link deleted: {link_id}")
                    except NotFound:
                        pass

    glossary_client = dataplex_v1.BusinessGlossaryServiceClient()
    glossary_name = (
        f"projects/{config.PROJECT_ID}/locations/{config.CATALOG_LOCATION}"
        f"/glossaries/{GLOSSARY_ID}"
    )
    for term in corpus.GLOSSARY_TERMS:
        with contextlib.suppress(NotFound):
            glossary_client.delete_glossary_term(name=f"{glossary_name}/terms/{term.term_id}")
    try:
        operation = glossary_client.delete_glossary(name=glossary_name)
        operation.result()  # type: ignore[no-untyped-call]
        print(f"    Glossary deleted: {GLOSSARY_ID}")
    except NotFound:
        pass
