"""Tests for the enriched Context builder utility."""

from agent_convo.tools.util_build_context import build_enriched_context


class TestBuildEnrichedContext:
    def _make_reranker_result(self, **overrides):
        base = {
            "question": "What is the highest VIX close?",
            "top_k": 5,
            "ranked_tables": [
                {
                    "table_id": "proj.bronze.vix_daily",
                    "rank": 1,
                    "confidence": 0.95,
                    "reasoning": "Contains VIX closing values",
                    "discovery_method": "table_documentation",
                    "table_description": "Daily VIX index values",
                    "key_columns": [
                        {
                            "name": "vix_close",
                            "data_type": "FLOAT64",
                            "description": "VIX closing value",
                            "is_key": False,
                            "useful_for_filtering": False,
                            "useful_for_aggregation": True,
                        },
                        {
                            "name": "trade_date",
                            "data_type": "DATE",
                            "description": "Trading date",
                            "is_key": False,
                            "useful_for_filtering": True,
                            "useful_for_aggregation": False,
                        },
                    ],
                    "sql_hints": "Use MAX(vix_close) for highest value",
                    "join_suggestions": [
                        {
                            "target_table": "proj.bronze.market_dates",
                            "join_keys": ["trade_date"],
                            "relationship": "many-to-one",
                        },
                    ],
                    "row_count": 5000,
                },
            ],
            "notes": "",
        }
        base.update(overrides)
        return base

    def test_builds_table_references(self):
        result = build_enriched_context(self._make_reranker_result())

        refs = result["datasource_references"]["bq"]["table_references"]
        assert len(refs) == 1
        assert refs[0]["project_id"] == "proj"
        assert refs[0]["dataset_id"] == "bronze"
        assert refs[0]["table_id"] == "vix_daily"

    def test_includes_schema_overrides(self):
        result = build_enriched_context(self._make_reranker_result())

        refs = result["datasource_references"]["bq"]["table_references"]
        schema = refs[0]["schema"]
        assert schema["description"] == "Daily VIX index values"
        assert len(schema["fields"]) == 2
        assert schema["fields"][0]["name"] == "vix_close"
        assert schema["fields"][0]["type"] == "FLOAT64"
        assert schema["fields"][0]["description"] == "VIX closing value"

    def test_includes_schema_relationships(self):
        result = build_enriched_context(self._make_reranker_result())

        assert "schema_relationships" in result
        rels = result["schema_relationships"]
        assert len(rels) == 1
        assert rels[0]["source_table"]["table_id"] == "vix_daily"
        assert rels[0]["target_table"]["table_id"] == "market_dates"
        assert rels[0]["join_keys"] == ["trade_date"]

    def test_includes_glossary_terms(self):
        result = build_enriched_context(self._make_reranker_result())

        # "VIX" should be extracted as a glossary term from column descriptions
        terms = result.get("glossary_terms", [])
        term_values = [t["displayName"] for t in terms]
        assert "VIX" in term_values

    def test_enhanced_system_instruction(self):
        result = build_enriched_context(self._make_reranker_result())

        instruction = result["system_instruction"]
        assert "MAX(vix_close)" in instruction
        assert "SQL Guidance" in instruction

    def test_custom_system_instruction(self):
        result = build_enriched_context(
            self._make_reranker_result(),
            system_instruction="Custom instructions here.",
        )

        assert result["system_instruction"].startswith("Custom instructions here.")
        assert "SQL Guidance" in result["system_instruction"]

    def test_empty_reranker_result(self):
        result = build_enriched_context({"ranked_tables": []})
        assert result == {}

    def test_fallback_no_reranker(self):
        result = build_enriched_context({})
        assert result == {}

    def test_no_join_suggestions(self):
        rr = self._make_reranker_result()
        rr["ranked_tables"][0]["join_suggestions"] = []

        result = build_enriched_context(rr)
        assert "schema_relationships" not in result

    def test_invalid_table_id_skipped(self):
        rr = self._make_reranker_result()
        rr["ranked_tables"].append({
            "table_id": "invalid_format",
            "rank": 2,
            "confidence": 0.5,
            "reasoning": "Bad format",
            "key_columns": [],
            "sql_hints": "",
            "join_suggestions": [],
        })

        result = build_enriched_context(rr)
        refs = result["datasource_references"]["bq"]["table_references"]
        # Only the valid table should be included
        assert len(refs) == 1

    def test_python_analysis_enabled(self):
        result = build_enriched_context(self._make_reranker_result())
        assert result["options"]["analysis"]["python"]["enabled"] is True

    def test_multiple_tables(self):
        rr = self._make_reranker_result()
        rr["ranked_tables"].append({
            "table_id": "proj.bronze.market_dates",
            "rank": 2,
            "confidence": 0.7,
            "reasoning": "Trading calendar",
            "discovery_method": "table_documentation",
            "table_description": "Market trading dates",
            "key_columns": [
                {
                    "name": "trade_date",
                    "data_type": "DATE",
                    "description": "Trading date",
                    "is_key": True,
                    "useful_for_filtering": True,
                    "useful_for_aggregation": False,
                },
            ],
            "sql_hints": "Filter by trade_date for date ranges",
            "join_suggestions": [],
            "row_count": 1000,
        })

        result = build_enriched_context(rr)
        refs = result["datasource_references"]["bq"]["table_references"]
        assert len(refs) == 2
        assert refs[1]["table_id"] == "market_dates"
