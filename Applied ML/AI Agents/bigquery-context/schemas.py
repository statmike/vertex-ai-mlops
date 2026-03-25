"""Pydantic schemas for the bigquery-context reranker output.

All three discovery approaches produce the same RerankerResponse,
making results directly comparable regardless of the discovery method.
"""

from pydantic import BaseModel, Field


class ColumnHint(BaseModel):
    """Key column information to help a downstream SQL-writing agent."""

    name: str = Field(description="Column name")
    data_type: str = Field(description="BigQuery data type (STRING, INTEGER, TIMESTAMP, etc.)")
    description: str = Field(default="", description="Column description if available")
    is_key: bool = Field(default=False, description="Whether this is a primary or foreign key")
    useful_for_filtering: bool = Field(
        default=False, description="Whether this column is useful in WHERE clauses"
    )
    useful_for_aggregation: bool = Field(
        default=False, description="Whether this column is useful in GROUP BY or aggregate functions"
    )


class JoinSuggestion(BaseModel):
    """A suggested join between the ranked table and another table."""

    target_table: str = Field(description="Fully qualified table ID (project.dataset.table)")
    join_keys: list[str] = Field(description="Column(s) to join on")
    relationship: str = Field(
        description="Join relationship type: one-to-one, one-to-many, many-to-many"
    )


class RankedTable(BaseModel):
    """A single table in the ranked results with metadata to guide SQL generation."""

    table_id: str = Field(description="Fully qualified table ID (project.dataset.table)")
    rank: int = Field(description="Rank position (1 = most relevant)")
    confidence: float = Field(
        ge=0.0, le=1.0, description="Confidence score from 0.0 to 1.0"
    )
    reasoning: str = Field(description="Why this table is relevant to the user's question")
    discovery_method: str = Field(
        description="Which approach found this table: bq_tools, dataplex_search, dataplex_context"
    )
    table_description: str = Field(
        default="", description="Business description of the table"
    )
    key_columns: list[ColumnHint] = Field(
        default_factory=list, description="Important columns for answering the question"
    )
    sql_hints: str = Field(
        default="",
        description=(
            "Suggested SQL patterns: useful WHERE filters, GROUP BY columns, "
            "aggregate functions, or JOIN conditions"
        ),
    )
    join_suggestions: list[JoinSuggestion] = Field(
        default_factory=list, description="Suggested joins to other tables in scope"
    )
    row_count: int | None = Field(default=None, description="Approximate row count if known")
    last_modified: str | None = Field(
        default=None, description="Last modification timestamp if known"
    )


class RerankerResponse(BaseModel):
    """Ranked list of BigQuery tables relevant to a user's question.

    Produced by the reranker tool after any discovery approach.
    All three approaches return this same schema.
    """

    question: str = Field(description="The original user question")
    top_k: int = Field(description="Maximum number of tables requested")
    ranked_tables: list[RankedTable] = Field(
        description="Tables ranked by relevance, most relevant first"
    )
    notes: str = Field(
        default="",
        description="Any caveats, suggestions, or observations about the results",
    )
