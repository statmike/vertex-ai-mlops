"""Create BQ datasets, views, and Knowledge Catalog enrichment.

Run once before using the agents or the benchmark:
    uv run python scripts/setup.py

Idempotent — safe to run multiple times. Skips resources that already exist.

Knowledge Catalog is the product formerly called Dataplex Universal Catalog
(renamed April 2026). The API/SDK/IAM namespace remains ``dataplex``.

Tier-replicated experiment design
---------------------------------
The benchmark isolates *catalog enrichment* as the single independent variable.
To do that cleanly, the **identical corpus** of tables is replicated into one
dataset per enrichment tier — same tables, same data, differing only in how much
Knowledge Catalog metadata each carries:

    Dataset                Tier                 Profiling  Glossary  Guidelines
    ---------------------  -------------------  ---------  --------  ----------
    {prefix}_tier0         0 schema-only        no         no        no
    {prefix}_tier1         1 + profiling        yes        no        no
    {prefix}_tier2         2 + glossary         yes        yes       no
    {prefix}_tier3         3 + guidelines       yes        yes       yes

Because every topic appears at every tier, "tier N recalls better" is no longer
confounded with "topic N is easier" — the replication *is* the ablation.

- **Profiling** publishes column stats (nullRatio, distinctValues, sampleValues).
- **Glossary** terms link to columns; they surface as ``related_terms`` in the capsule.
- **Guidelines** (a system aspect) embed NL→SQL hints; they surface as ``guidelines``.

``lookupContext`` surfaces each tier's enrichment automatically, so the five
discovery approaches see richer candidate metadata as the tier rises.
"""

import hashlib
import os
import re
import time
from pathlib import Path

from dotenv import load_dotenv

load_dotenv(Path(__file__).resolve().parent.parent / ".env")

# ---------------------------------------------------------------------------
# Environment
# ---------------------------------------------------------------------------
PROJECT_ID = os.getenv("GOOGLE_CLOUD_PROJECT", "")
BQ_LOCATION = os.getenv("BQ_LOCATION", "US")
DATAPLEX_LOCATION = os.getenv("DATAPLEX_LOCATION", "us-central1")
RESOURCE_PREFIX = os.getenv("RESOURCE_PREFIX", "bigquery_context")

# Region for glossary/term/entry-link resources. Entry links require every
# referenced entry to live in the link's region (or in ``global``). The BQ table
# entries are created in ``BQ_LOCATION`` (e.g. the ``us`` multi-region), which is
# fixed and cannot move, so the glossary, its terms, and the definition links
# must all be co-located there — NOT in the DataScan region (DATAPLEX_LOCATION,
# which must be a single region like ``us-central1``). See create_glossary_and_links.
CATALOG_LOCATION = BQ_LOCATION.lower()

# The four enrichment tiers. Every tier holds the identical CORPUS below.
TIERS = [0, 1, 2, 3]


def tier_dataset(tier: int) -> str:
    """Dataset id holding the corpus at a given enrichment tier."""
    return f"{RESOURCE_PREFIX}_tier{tier}"


def _project_number() -> str:
    """Resolve the project *number* (glossary-term entry names require it).

    A glossary term's catalog entry name embeds ``projects/<number>`` — the
    project *number*, not the ID. Resolve it once via Resource Manager; fall
    back to PROJECT_ID (best effort) if the lookup is unavailable.
    """
    global _PROJECT_NUMBER
    if _PROJECT_NUMBER is None:
        try:
            from google.cloud import resourcemanager_v3

            client = resourcemanager_v3.ProjectsClient()
            proj = client.get_project(name=f"projects/{PROJECT_ID}")
            _PROJECT_NUMBER = proj.name.split("/")[-1]
        except Exception as e:  # pragma: no cover - best-effort fallback
            print(f"    Could not resolve project number ({e}); using project ID.")
            _PROJECT_NUMBER = PROJECT_ID
    return _PROJECT_NUMBER


_PROJECT_NUMBER: str | None = None

# Glossary + guidelines resource names.
GLOSSARY_ID = RESOURCE_PREFIX.replace("_", "-") + "-glossary"
# System aspect type published by Google in the shared ``dataplex-types`` project.
GUIDELINES_ASPECT_TYPE = (
    "projects/dataplex-types/locations/global/aspectTypes/guidelines"
)
GUIDELINES_ASPECT_KEY = "dataplex-types.global.guidelines"
# Fallback if the guidelines aspect schema differs at runtime (preview feature).
OVERVIEW_ASPECT_TYPE = (
    "projects/dataplex-types/locations/global/aspectTypes/overview"
)
OVERVIEW_ASPECT_KEY = "dataplex-types.global.overview"
# Term↔asset definition link type (published by Google).
DEFINITION_ENTRY_LINK_TYPE = (
    "projects/dataplex-types/locations/global/entryLinkTypes/definition"
)

# ---------------------------------------------------------------------------
# CORPUS — the single set of tables, replicated into every tier dataset.
#
# Each view is free (zero storage cost) and places the table in your project's
# Knowledge Catalog so all five discovery approaches work equally. A ``role`` of
# "distractor" marks look-alike tables that are never a correct answer — they
# exist so precision and trap questions are meaningful (see examples/questions.json).
# ---------------------------------------------------------------------------
CORPUS = [
    # --- Transportation ---
    {
        "name": "austin_bikeshare_trips",
        "source": "bigquery-public-data.austin_bikeshare.bikeshare_trips",
        "description": (
            "Bike share trip records from Austin, Texas. Each row is a single "
            "bike trip with start/end times, stations, duration, and subscriber type."
        ),
    },
    {
        "name": "austin_bikeshare_stations",
        "source": "bigquery-public-data.austin_bikeshare.bikeshare_stations",
        "description": (
            "Bike share station locations in Austin, Texas. Each row is a station "
            "with name, status, latitude/longitude, and number of docks."
        ),
    },
    {
        "name": "nyc_taxi_trips_2022",
        "source": "bigquery-public-data.new_york_taxi_trips.tlc_yellow_trips_2022",
        "description": (
            "NYC yellow taxi trip records for 2022. Includes pickup/dropoff times "
            "and locations, fare amounts, tip amounts, and payment types."
        ),
    },
    # --- Weather ---
    {
        "name": "hurricanes",
        "source": "bigquery-public-data.noaa_hurricanes.hurricanes",
        "description": (
            "International Best Track Archive for Climate Stewardship (IBTrACS). "
            "Historical hurricane and tropical cyclone tracks with wind speed, "
            "pressure, position, and storm classification from multiple agencies."
        ),
    },
    {
        "name": "weather_stations",
        "source": "bigquery-public-data.ghcn_d.ghcnd_stations",
        "description": (
            "Global Historical Climatology Network weather station inventory. "
            "Station locations with latitude, longitude, elevation, and name."
        ),
    },
    # --- Demographics ---
    {
        "name": "population_by_zip_2010",
        "source": "bigquery-public-data.census_bureau_usa.population_by_zip_2010",
        "description": (
            "US Census 2010 population counts by ZIP code. Includes total "
            "population, minimum and maximum age, and gender breakdowns."
        ),
    },
    {
        "name": "usa_names_1910_current",
        "source": "bigquery-public-data.usa_names.usa_1910_current",
        "description": (
            "US baby name popularity from Social Security applications. "
            "Each row is a name-state-year-gender combination with occurrence count."
        ),
    },
    # --- Geography ---
    {
        "name": "us_counties",
        "source": "bigquery-public-data.geo_us_boundaries.counties",
        "description": (
            "US county boundaries with FIPS codes, names, state associations, "
            "land/water area, and geographic coordinates."
        ),
    },
    {
        "name": "austin_crime",
        "source": "bigquery-public-data.austin_crime.crime",
        "description": (
            "Austin, Texas crime reports. Each row is a reported crime incident "
            "with type, description, location, timestamp, and clearance status."
        ),
    },
    # --- Health & environment by geography (new themed group) ---
    {
        "name": "county_natality",
        "source": "bigquery-public-data.sdoh_cdc_wonder_natality.county_natality",
        "description": (
            "CDC WONDER natality (birth) statistics by US county and year. Each row "
            "aggregates births with average mother age, gestational age, birth weight, "
            "and pre-pregnancy BMI, keyed by county FIPS code."
        ),
    },
    {
        "name": "air_quality_annual_summary",
        "source": "bigquery-public-data.epa_historical_air_quality.air_quality_annual_summary",
        "description": (
            "EPA annual air-quality summaries by monitoring site. Each row is a "
            "pollutant measured at a site (state/county code, lat/long) for a year, "
            "with the annual arithmetic mean, maxima, and exceedance counts."
        ),
    },
    {
        "name": "zip_codes",
        "source": "bigquery-public-data.geo_us_boundaries.zip_codes",
        "description": (
            "US ZIP code geographic boundaries and attributes: city, county, state, "
            "land/water area, and centroid latitude/longitude. A crosswalk between "
            "ZIP codes and counties/states."
        ),
    },
    # --- Distractors (look-alike; never a correct answer) ---
    {
        "name": "taxi_zone_geom",
        "role": "distractor",
        "source": "bigquery-public-data.new_york_taxi_trips.taxi_zone_geom",
        "description": (
            "NYC taxi zone lookup: zone id, name, borough, and boundary geometry. "
            "A reference table for taxi zones — it holds no trip, fare, or tip records."
        ),
    },
    {
        "name": "citibike_stations",
        "role": "distractor",
        "source": "bigquery-public-data.new_york.citibike_stations",
        "description": (
            "New York City Citi Bike station status: capacity, bikes/docks available, "
            "and real-time availability flags. NYC bike share — not Austin — and holds "
            "no trip history."
        ),
    },
    {
        "name": "unemployment_cps",
        "role": "distractor",
        "source": "bigquery-public-data.bls.unemployment_cps",
        "description": (
            "US Bureau of Labor Statistics national unemployment time series from the "
            "Current Population Survey. National monthly series — not broken down by "
            "ZIP code or county."
        ),
    },
]

# ---------------------------------------------------------------------------
# GLOSSARY_TERMS (tiers >= 2) — corpus-wide business terms, authored once.
#   term-id → {display, description, columns: {table view-name → [column names]}}
# Links are created against the table entries in every enriched tier dataset.
# ---------------------------------------------------------------------------
GLOSSARY_TERMS = {
    "subscriber-type": {
        "display": "Subscriber Type",
        "description": (
            "Rider membership category. Distinguishes annual/monthly "
            "members from single-ride and walk-up casual users."
        ),
        "columns": {"austin_bikeshare_trips": ["subscriber_type"]},
    },
    "trip-duration": {
        "display": "Trip Duration",
        "description": (
            "Elapsed time of a single trip in minutes, from checkout "
            "to return (bike share) or pickup to dropoff (taxi)."
        ),
        "columns": {"austin_bikeshare_trips": ["duration_minutes"]},
    },
    "docking-station": {
        "display": "Docking Station",
        "description": (
            "Physical kiosk where shared bikes are checked out and "
            "returned. Identified by station ID and name."
        ),
        "columns": {
            "austin_bikeshare_stations": ["station_id", "name"],
            "austin_bikeshare_trips": ["start_station_id", "end_station_id"],
        },
    },
    "fare-and-tip": {
        "display": "Fare and Tip",
        "description": (
            "Monetary amounts on a taxi trip: metered fare plus the "
            "gratuity paid by the passenger."
        ),
        "columns": {"nyc_taxi_trips_2022": ["fare_amount", "tip_amount"]},
    },
    "tropical-cyclone": {
        "display": "Tropical Cyclone",
        "description": (
            "Rotating storm system originating over tropical waters. "
            "Classified by sustained wind speed into depressions, storms, "
            "and hurricanes."
        ),
        "columns": {"hurricanes": ["name", "usa_sshs"]},
    },
    "wind-speed": {
        "display": "Wind Speed",
        "description": (
            "Maximum sustained surface wind associated with a storm "
            "observation, reported in knots by the reporting agency."
        ),
        "columns": {"hurricanes": ["usa_wind"]},
    },
    "landfall": {
        "display": "Landfall",
        "description": (
            "Point where a storm's center crosses a coastline. "
            "Inferred from the storm track's position over time."
        ),
        "columns": {"hurricanes": ["latitude", "longitude"]},
    },
    "ghcn-station": {
        "display": "GHCN Station",
        "description": (
            "Weather observation site in the Global Historical Climatology "
            "Network, identified by a unique station ID."
        ),
        "columns": {"weather_stations": ["id", "name"]},
    },
    "county-fips": {
        "display": "County FIPS Code",
        "description": (
            "Federal Information Processing Standards code uniquely identifying "
            "a US county. The join key between county-level datasets."
        ),
        "columns": {
            "us_counties": ["county_fips_code", "geo_id"],
            "county_natality": ["County_of_Residence_FIPS"],
            "zip_codes": ["county"],
        },
    },
    "natality": {
        "display": "Natality",
        "description": (
            "Birth statistics for a population: counts of live births and "
            "associated maternal and infant measures, aggregated by geography."
        ),
        "columns": {
            "county_natality": ["Births", "Ave_Age_of_Mother", "Ave_Birth_Weight_gms"],
        },
    },
    "air-quality-measure": {
        "display": "Air Quality Measure",
        "description": (
            "A pollutant concentration measured at a monitoring site, summarized "
            "over a year (e.g. annual arithmetic mean), used to assess air quality."
        ),
        "columns": {
            "air_quality_annual_summary": ["parameter_name", "arithmetic_mean"],
        },
    },
}

# ---------------------------------------------------------------------------
# GUIDELINES (tier 3 only) — table view-name → NL→SQL guidance text.
# ---------------------------------------------------------------------------
GUIDELINES = {
    "austin_bikeshare_trips": (
        "Trip duration is stored in minutes in 'duration_minutes' — do not "
        "recompute it from start/end timestamps. Filter casual vs. member "
        "ridership on 'subscriber_type'. Join to austin_bikeshare_stations "
        "on start_station_id / end_station_id to get station names and locations."
    ),
    "nyc_taxi_trips_2022": (
        "Total paid by a rider is fare_amount + tip_amount + tolls_amount; "
        "'total_amount' already sums these. Filter by pickup_datetime for "
        "time-based analysis. Pickup/dropoff locations are zone IDs, not lat/long."
    ),
    "county_natality": (
        "Join to us_counties on County_of_Residence_FIPS = county_fips_code (or "
        "geo_id) for boundaries and coordinates. 'Births' is a count; the Ave_* "
        "columns are already averages — do not average them again. Filter by 'Year'."
    ),
    "air_quality_annual_summary": (
        "A county is identified by the composite key state_code + county_code "
        "(both zero-padded strings), not a single FIPS column. 'arithmetic_mean' "
        "is the annual average concentration; filter one pollutant via "
        "'parameter_name' before comparing sites. Join to geography on the "
        "concatenated state_code||county_code FIPS."
    ),
}


def _corpus_tables() -> list[str]:
    """View names in the corpus."""
    return [t["name"] for t in CORPUS]


# ---------------------------------------------------------------------------
# Deterministic resource-id helpers — imported by cleanup.py so the two scripts
# reconstruct identical ids (no drift). Long ids are hash-suffixed to stay under
# the 63-char catalog limit while remaining globally unique across tiers.
# ---------------------------------------------------------------------------
def _bounded_id(base: str) -> str:
    """Return a Dataplex-valid id: lowercased, sanitized, and length-bounded.

    Dataplex entry-link / datascan ids allow only lowercase letters, digits, and
    hyphens, must start with a letter, and end with a letter or digit. Column and
    term names can carry uppercase and other punctuation (e.g. a natality column
    ``County_of_Residence_FIPS``), so we normalize before bounding length. The
    normalization is deterministic, so cleanup.py reconstructs identical ids.
    """
    # Lowercase, then collapse every run of non-[a-z0-9] into a single hyphen.
    sanitized = re.sub(r"[^a-z0-9]+", "-", base.lower()).strip("-")
    if len(sanitized) <= 63:
        return sanitized
    digest = hashlib.sha1(base.encode()).hexdigest()[:8]
    return f"{sanitized[:54].strip('-')}-{digest}"


def profile_scan_id(tier: int, view_name: str) -> str:
    """DataScan id for a table's profile scan at a given tier."""
    prefix = RESOURCE_PREFIX.replace("_", "-")
    return _bounded_id(f"{prefix}-t{tier}-profile-{view_name}")


def definition_link_id(tier: int, term_id: str, table: str, column: str) -> str:
    """Entry-link id for a term↔column definition link at a given tier.

    Tier is embedded so the same term/column across tier datasets yields distinct
    (and, when hashed, non-colliding) ids in the shared @bigquery entry group.
    """
    return _bounded_id(f"def-t{tier}-{term_id}-{table}-{column}")


def create_datasets_and_views():
    """Create one dataset per tier, each holding the full corpus as views."""
    from google.cloud import bigquery

    client = bigquery.Client(project=PROJECT_ID)

    for tier in TIERS:
        dataset_id = tier_dataset(tier)
        dataset_ref = f"{PROJECT_ID}.{dataset_id}"

        dataset = bigquery.Dataset(dataset_ref)
        dataset.location = BQ_LOCATION
        dataset.description = (
            f"bigquery-context corpus at enrichment tier {tier}. Identical tables "
            f"across all tiers; only catalog enrichment differs."
        )
        client.create_dataset(dataset, exists_ok=True)
        print(f"  Dataset: {dataset_ref}  (tier {tier})")

        for view_def in CORPUS:
            view_ref = f"{dataset_ref}.{view_def['name']}"
            expected_query = f"SELECT * FROM `{view_def['source']}`"

            # Idempotency: recreating a view (delete+create) churns its catalog
            # entry generation, which silently invalidates pre-existing glossary
            # entry links pointing at it. So only create the view when it is
            # missing or its query drifted — never delete+recreate a good view.
            try:
                existing = client.get_table(view_ref)
            except Exception:
                existing = None

            try:
                if existing is not None and existing.view_query == expected_query:
                    print(f"    View exists: {view_def['name']}")
                else:
                    if existing is not None:
                        client.delete_table(view_ref, not_found_ok=True)
                    view = bigquery.Table(view_ref)
                    view.view_query = expected_query
                    view.description = view_def["description"]
                    client.create_table(view)
                    print(f"    View: {view_def['name']} -> {view_def['source']}")

                # Copy column descriptions from source table to view (idempotent)
                try:
                    source_table = client.get_table(view_def["source"])
                    created_view = client.get_table(view_ref)
                    created_view.schema = source_table.schema
                    created_view.description = view_def["description"]
                    client.update_table(created_view, ["schema", "description"])
                except Exception:
                    pass  # column descriptions are nice-to-have
            except Exception as e:
                print(f"    View {view_def['name']}: FAILED - {e}")


def create_and_run_profile_scans():
    """Create + run profile scans for every corpus table in tiers >= 1."""
    from google.api_core.exceptions import AlreadyExists
    from google.cloud import bigquery
    from google.cloud.dataplex_v1 import (
        CreateDataScanRequest,
        DataProfileSpec,
        DataScan,
        DataScanServiceClient,
        DataSource,
        GetDataScanJobRequest,
        RunDataScanRequest,
        Trigger,
    )

    client = DataScanServiceClient()
    parent = f"projects/{PROJECT_ID}/locations/{DATAPLEX_LOCATION}"
    bq_client = bigquery.Client(project=PROJECT_ID)
    jobs = []

    # Collect (tier, view) pairs whose BQ view exists (tiers >= 1).
    targets = []
    for tier in TIERS:
        if tier < 1:
            print(f"    Skipping profiling (tier 0): {tier_dataset(tier)}")
            continue
        for view_def in CORPUS:
            view_ref = f"{PROJECT_ID}.{tier_dataset(tier)}.{view_def['name']}"
            try:
                bq_client.get_table(view_ref)
                targets.append((tier, view_def))
            except Exception:
                print(f"    Skipping scan (view not found): {view_ref}")

    for i, (tier, view_def) in enumerate(targets):
        scan_id = profile_scan_id(tier, view_def["name"])
        scan_name = f"{parent}/dataScans/{scan_id}"
        resource = (
            f"//bigquery.googleapis.com/projects/{PROJECT_ID}"
            f"/datasets/{tier_dataset(tier)}/tables/{view_def['name']}"
        )

        # Pause between iterations to stay under Dataplex 30 req/min quota
        if i > 0:
            time.sleep(5)

        scan = DataScan(
            data=DataSource(resource=resource),
            data_profile_spec=DataProfileSpec(
                sampling_percent=10.0,
                catalog_publishing_enabled=True,
            ),
            execution_spec=DataScan.ExecutionSpec(
                trigger=Trigger(on_demand=Trigger.OnDemand()),
            ),
            description=f"Profile scan for {tier_dataset(tier)}.{view_def['name']}",
        )

        try:
            operation = client.create_data_scan(
                request=CreateDataScanRequest(
                    parent=parent, data_scan=scan, data_scan_id=scan_id,
                )
            )
            operation.result()
            print(f"    Scan created: {scan_id}")
        except AlreadyExists:
            print(f"    Scan exists:  {scan_id}")

        try:
            response = client.run_data_scan(
                request=RunDataScanRequest(name=scan_name)
            )
            jobs.append((scan_id, response.job.name))
            print(f"    Scan started: {scan_id}")
        except Exception as e:
            print(f"    Scan run failed: {scan_id} - {e}")

    if jobs:
        print("\n  Waiting for profile scans to complete...")
        for scan_id, job_name in jobs:
            for _ in range(30):  # up to 5 minutes per scan
                time.sleep(10)
                job = client.get_data_scan_job(
                    request=GetDataScanJobRequest(name=job_name)
                )
                if job.state in (3, 4, 5):  # CANCELLED, SUCCEEDED, FAILED
                    status = "OK" if job.state == 4 else f"state={job.state}"
                    print(f"    {scan_id}: {status}")
                    break
            else:
                print(f"    {scan_id}: TIMEOUT")


def _table_entry_name(dataset: str, table: str) -> str:
    """Full @bigquery entry name for a BQ view (matches config.get_dataplex_entry_name)."""
    return (
        f"projects/{PROJECT_ID}/locations/{BQ_LOCATION.lower()}"
        f"/entryGroups/@bigquery/entries/bigquery.googleapis.com"
        f"/projects/{PROJECT_ID}/datasets/{dataset}/tables/{table}"
    )


def create_glossary_and_links():
    """Create a glossary + terms, and link terms to columns in tiers >= 2.

    One glossary and one set of terms serve the whole corpus. Definition links,
    however, are created per enriched tier dataset (tier 2 and tier 3), so that a
    table's capsule surfaces glossary terms only at those tiers.

    Glossaries are regional. A definition link references two entries — the BQ
    table entry (SOURCE) and the glossary term entry (TARGET) — and the API
    requires every referenced entry to be in the *link's* region (or ``global``).
    The BQ entries are fixed in ``BQ_LOCATION`` (CATALOG_LOCATION), so the
    glossary, terms, and links all live there — NOT in DATAPLEX_LOCATION.

    NOTE (preview): the column ``path`` prefix for a definition link is not
    fully documented. We use the ``Schema.<column>`` notation surfaced by the
    tooling; if a link fails, it is logged and skipped (non-fatal).
    """
    from google.api_core.exceptions import AlreadyExists, InvalidArgument
    from google.cloud import dataplex_v1

    glossary_client = dataplex_v1.BusinessGlossaryServiceClient()
    catalog_client = dataplex_v1.CatalogServiceClient()

    loc = CATALOG_LOCATION
    glossary_parent = f"projects/{PROJECT_ID}/locations/{loc}"
    glossary_name = f"{glossary_parent}/glossaries/{GLOSSARY_ID}"

    enriched_tiers = [t for t in TIERS if t >= 2]
    if not enriched_tiers or not GLOSSARY_TERMS:
        return

    # 1. Glossary (LRO)
    try:
        op = glossary_client.create_glossary(
            request=dataplex_v1.CreateGlossaryRequest(
                parent=glossary_parent,
                glossary_id=GLOSSARY_ID,
                glossary=dataplex_v1.Glossary(
                    display_name="BigQuery Context Glossary",
                    description=(
                        "Business terms for the bigquery-context demo corpus."
                    ),
                ),
            )
        )
        op.result()
        print(f"    Glossary created: {GLOSSARY_ID}")
    except AlreadyExists:
        print(f"    Glossary exists:  {GLOSSARY_ID}")

    # 2. Terms (all first) — a term's catalog entry is not linkable until it
    #    propagates, so we create every term before creating any link.
    for term_id, term_def in GLOSSARY_TERMS.items():
        try:
            glossary_client.create_glossary_term(
                request=dataplex_v1.CreateGlossaryTermRequest(
                    parent=glossary_name,
                    term_id=term_id,
                    term=dataplex_v1.GlossaryTerm(
                        display_name=term_def["display"],
                        description=term_def["description"],
                        parent=glossary_name,
                    ),
                )
            )
            print(f"    Term created: {term_id}")
        except (AlreadyExists, InvalidArgument) as e:
            # The term API reports an existing term as InvalidArgument
            # ("already exists"), not AlreadyExists — treat both as idempotent.
            if isinstance(e, InvalidArgument) and "already exists" not in str(e):
                raise
            print(f"    Term exists:  {term_id}")

    # 3. Definition links (second pass), one set per enriched tier dataset.
    for tier in enriched_tiers:
        dataset = tier_dataset(tier)
        print(f"    Linking terms in {dataset} (tier {tier}):")
        for term_id, term_def in GLOSSARY_TERMS.items():
            term_entry_name = (
                f"projects/{PROJECT_ID}/locations/{loc}/entryGroups/@dataplex"
                f"/entries/projects/{_project_number()}/locations/{loc}"
                f"/glossaries/{GLOSSARY_ID}/terms/{term_id}"
            )
            for table, columns in term_def.get("columns", {}).items():
                asset_entry = _table_entry_name(dataset, table)
                for column in columns:
                    _create_definition_link(
                        catalog_client,
                        dataplex_v1,
                        loc=loc,
                        link_id=definition_link_id(tier, term_id, table, column),
                        asset_entry=asset_entry,
                        column=column,
                        term_entry=term_entry_name,
                    )


def _create_definition_link(
    catalog_client, dataplex_v1, *, loc, link_id, asset_entry, column, term_entry
):
    """Create one term↔column definition link. Non-fatal on failure (preview).

    A freshly created glossary term's catalog entry is not immediately linkable
    (the @dataplex entry lags the term by a few seconds), so a 404 NotFound on
    the term entry is retried with backoff before giving up.
    """
    from google.api_core.exceptions import AlreadyExists, NotFound

    link_parent = (
        f"projects/{PROJECT_ID}/locations/{loc}/entryGroups/@bigquery"
    )
    EntryReference = dataplex_v1.EntryLink.EntryReference
    source = EntryReference(
        name=asset_entry,
        path=f"Schema.{column}",
        type_=EntryReference.Type.SOURCE,
    )
    target = EntryReference(
        name=term_entry,
        type_=EntryReference.Type.TARGET,
    )
    request = dataplex_v1.CreateEntryLinkRequest(
        parent=link_parent,
        entry_link_id=link_id,
        entry_link=dataplex_v1.EntryLink(
            entry_link_type=DEFINITION_ENTRY_LINK_TYPE,
            entry_references=[source, target],
        ),
    )
    # Retry NotFound (term-entry propagation lag); other errors are non-fatal.
    for attempt in range(6):
        try:
            catalog_client.create_entry_link(request=request)
            print(f"      Link: {link_id}")
            return
        except AlreadyExists:
            print(f"      Link exists: {link_id}")
            return
        except NotFound:
            if attempt < 5:
                time.sleep(5)
                continue
            print(f"      Link FAILED (non-fatal): {link_id} - term entry not yet available")
            return
        except Exception as e:
            # Preview API — column path shape may differ; log and continue.
            print(f"      Link FAILED (non-fatal): {link_id} - {e}")
            return


def _resolve_guidelines_aspect():
    """Return (aspect_type, aspect_key, data_builder) for the guidelines aspect.

    Introspects the guidelines aspect template from the shared dataplex-types
    project to build the correct ``data`` shape. Falls back to the overview
    aspect if guidelines is unavailable (preview feature).

    ``data_builder(text)`` returns the dict to store in ``Aspect(data=...)``.
    """
    from google.cloud import dataplex_v1

    catalog_client = dataplex_v1.CatalogServiceClient()

    for aspect_type, aspect_key in (
        (GUIDELINES_ASPECT_TYPE, GUIDELINES_ASPECT_KEY),
        (OVERVIEW_ASPECT_TYPE, OVERVIEW_ASPECT_KEY),
    ):
        try:
            at = catalog_client.get_aspect_type(name=aspect_type)
        except Exception as e:
            print(f"    Aspect type unavailable: {aspect_type} - {e}")
            continue

        # Discover the first string field in the template to hold the text.
        field_name = None
        template = at.metadata_template
        for f in getattr(template, "record_fields", []):
            if f.type_.lower() == "string":
                field_name = f.name
                break

        if field_name is None:
            # Template has no obvious string field; store under a common default.
            field_name = "content"

        def _builder(text, _fn=field_name):
            return {_fn: text}

        print(f"    Using aspect: {aspect_type} (field '{field_name}')")
        return aspect_type, aspect_key, _builder

    return None, None, None


def enrich_with_guidelines():
    """Attach the guidelines system aspect to tier-3 tables (NL→SQL hints)."""
    from google.cloud import dataplex_v1

    tier3_tables = [t for t in TIERS if t >= 3]
    if not tier3_tables or not GUIDELINES:
        return

    aspect_type, aspect_key, build_data = _resolve_guidelines_aspect()
    if not aspect_type:
        print("    Skipping guidelines — no usable aspect type.")
        return

    catalog_client = dataplex_v1.CatalogServiceClient()

    for tier in tier3_tables:
        dataset = tier_dataset(tier)
        for table, text in GUIDELINES.items():
            entry_name = _table_entry_name(dataset, table)
            entry = dataplex_v1.Entry(name=entry_name)
            entry.aspects[aspect_key] = dataplex_v1.Aspect(
                aspect_type=aspect_type,
                data=build_data(text),
            )
            try:
                catalog_client.update_entry(
                    request=dataplex_v1.UpdateEntryRequest(
                        entry=entry,
                        update_mask={"paths": ["aspects"]},
                        aspect_keys=[aspect_key],
                    )
                )
                print(f"    Guidelines set: {dataset}.{table}")
            except Exception as e:
                print(f"    Guidelines FAILED (non-fatal): {table} - {e}")


def main():
    print(f"Setting up bigquery-context resources in {PROJECT_ID}...")
    print(f"  Corpus: {len(CORPUS)} tables × {len(TIERS)} tiers "
          f"= {len(CORPUS) * len(TIERS)} views\n")

    print("Creating datasets and views:")
    create_datasets_and_views()

    print("\nCreating and running profile scans (tiers >= 1):")
    create_and_run_profile_scans()

    print("\nCreating glossary + column definition links (tiers >= 2):")
    create_glossary_and_links()

    print("\nAttaching guidelines aspect (tier 3):")
    enrich_with_guidelines()

    print("\nSetup complete!")


if __name__ == "__main__":
    main()
