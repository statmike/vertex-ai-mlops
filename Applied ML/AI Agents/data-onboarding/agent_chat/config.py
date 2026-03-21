"""Chat agent configuration.

The chat agent discovers bronze datasets dynamically by querying
the ``data_catalog`` table in the shared meta dataset — no hardcoded
dataset list needed.
"""

from agent_orchestrator.config import (
    BQ_DATASET_LOCATION,
    BQ_META_DATASET,
    GOOGLE_CLOUD_PROJECT,
)

META_DATASET = BQ_META_DATASET
