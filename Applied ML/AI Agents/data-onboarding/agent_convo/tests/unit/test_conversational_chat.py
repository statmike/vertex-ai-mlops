"""Tests for the conversational_chat tool — session management and response handling."""

import json
import sys
from unittest.mock import AsyncMock, MagicMock, patch

import pytest

# The conftest mocks geminidataanalytics_v1alpha in sys.modules.
from agent_convo.tools.function_tool_conversational_chat import conversational_chat

# Reference to the mock that conftest injected
_mock_gda = sys.modules["google.cloud.geminidataanalytics_v1alpha"]


class _FakeToolContext:
    def __init__(self):
        self.state = {}
        self.save_artifact = AsyncMock(return_value=1)


class TestConversationalChat:
    @pytest.mark.asyncio
    async def test_text_response(self):
        with patch(
            "agent_convo.tools.util_conversational_api.geminidataanalytics",
            _mock_gda,
        ), patch(
            "agent_convo.tools.util_conversational_api.handle_text_response",
            return_value="The answer is 42.",
        ), patch.dict(
            "os.environ", {"GOOGLE_CLOUD_PROJECT": "test-project"}
        ):
            mock_response = MagicMock()
            mock_response.system_message = MagicMock()
            mock_response.system_message.__contains__ = lambda self, key: key == "text"
            mock_response._pb = MagicMock()

            mock_client = MagicMock()
            mock_client.chat.return_value = [mock_response]
            _mock_gda.DataChatServiceClient.return_value = mock_client
            _mock_gda.DatasourceReferences = MagicMock()
            _mock_gda.Context = MagicMock()
            _mock_gda.Message = MagicMock()
            _mock_gda.types.Message = MagicMock

            ctx = _FakeToolContext()
            result = await conversational_chat(
                question="How many records?",
                chart=False,
                tool_context=ctx,
                bigquery_tables=[
                    {"project_id": "p", "dataset_id": "d", "table_id": "t"}
                ],
            )

            assert "42" in result
            assert "conversational_api_sessions" in ctx.state

    @pytest.mark.asyncio
    async def test_auto_pick_tables_from_reranker(self):
        """When bigquery_tables is not provided, tables come from reranker_result."""
        with patch(
            "agent_convo.tools.util_conversational_api.geminidataanalytics",
            _mock_gda,
        ), patch(
            "agent_convo.tools.util_conversational_api.show_message"
        ) as mock_show, patch.dict(
            "os.environ", {"GOOGLE_CLOUD_PROJECT": "test-project"}
        ):
            mock_response = MagicMock()
            mock_response.system_message = MagicMock()
            mock_response._pb = MagicMock()

            mock_client = MagicMock()
            mock_client.chat.return_value = [mock_response]
            _mock_gda.DataChatServiceClient.return_value = mock_client
            _mock_gda.DatasourceReferences = MagicMock()
            _mock_gda.Context = MagicMock()
            _mock_gda.Message = MagicMock()
            _mock_gda.types.Message = MagicMock

            mock_show.return_value = "Result from auto-picked tables."

            ctx = _FakeToolContext()
            ctx.state["reranker_result"] = {
                "question": "test",
                "top_k": 5,
                "ranked_tables": [
                    {
                        "table_id": "proj.dataset.my_table",
                        "rank": 1,
                        "confidence": 0.9,
                        "reasoning": "Relevant",
                    },
                ],
                "notes": "",
            }

            result = await conversational_chat(
                question="test question",
                chart=False,
                tool_context=ctx,
            )

            # Should succeed without explicit bigquery_tables
            assert "No tables available" not in result

    @pytest.mark.asyncio
    async def test_no_tables_returns_error(self):
        """When no tables are available and no reranker result, returns error."""
        ctx = _FakeToolContext()
        result = await conversational_chat(
            question="test",
            chart=False,
            tool_context=ctx,
        )
        assert "No tables available" in result

    @pytest.mark.asyncio
    async def test_session_history_stored(self):
        with patch(
            "agent_convo.tools.util_conversational_api.geminidataanalytics",
            _mock_gda,
        ), patch(
            "agent_convo.tools.util_conversational_api.show_message"
        ) as mock_show, patch(
            "agent_convo.tools.util_conversational_api.MessageToDict"
        ) as mock_to_dict, patch.dict(
            "os.environ", {"GOOGLE_CLOUD_PROJECT": "test-project"}
        ):
            mock_response = MagicMock()
            mock_response.system_message = MagicMock()
            mock_response._pb = MagicMock()

            mock_client = MagicMock()
            mock_client.chat.return_value = [mock_response]
            _mock_gda.DataChatServiceClient.return_value = mock_client
            _mock_gda.DatasourceReferences = MagicMock()
            _mock_gda.Context = MagicMock()
            _mock_gda.Message = MagicMock()
            _mock_gda.types.Message = MagicMock

            mock_to_dict.return_value = {"system_message": {"text": "reply"}}
            mock_show.return_value = "Answer"

            tables = [{"project_id": "p", "dataset_id": "d", "table_id": "t"}]
            ctx = _FakeToolContext()

            await conversational_chat("Q1", False, ctx, tables)

            sessions = ctx.state["conversational_api_sessions"]
            key = json.dumps(
                sorted(tables, key=lambda t: (t["project_id"], t["dataset_id"], t["table_id"])),
                sort_keys=True,
            )
            assert key in sessions
            assert len(sessions[key]) >= 1

    @pytest.mark.asyncio
    async def test_no_responses(self):
        with patch(
            "agent_convo.tools.util_conversational_api.geminidataanalytics",
            _mock_gda,
        ), patch.dict(
            "os.environ", {"GOOGLE_CLOUD_PROJECT": "test-project"}
        ):
            mock_client = MagicMock()
            mock_client.chat.return_value = []
            _mock_gda.DataChatServiceClient.return_value = mock_client
            _mock_gda.DatasourceReferences = MagicMock()
            _mock_gda.Context = MagicMock()
            _mock_gda.Message = MagicMock()
            _mock_gda.types.Message = MagicMock

            ctx = _FakeToolContext()
            result = await conversational_chat(
                "Q",
                False,
                ctx,
                [{"project_id": "p", "dataset_id": "d", "table_id": "t"}],
            )
            assert "No responses" in result

    @pytest.mark.asyncio
    async def test_chart_response(self):
        with patch(
            "agent_convo.tools.util_conversational_api.geminidataanalytics",
            _mock_gda,
        ), patch(
            "agent_convo.tools.util_conversational_api.show_message"
        ) as mock_show, patch.dict(
            "os.environ", {"GOOGLE_CLOUD_PROJECT": "test-project"}
        ):
            mock_response = MagicMock()
            mock_response.system_message = MagicMock()
            mock_response.system_message.__contains__ = lambda self, x: x == "chart"
            mock_response._pb = MagicMock()

            mock_client = MagicMock()
            mock_client.chat.return_value = [mock_response]
            _mock_gda.DataChatServiceClient.return_value = mock_client
            _mock_gda.DatasourceReferences = MagicMock()
            _mock_gda.Context = MagicMock()
            _mock_gda.Message = MagicMock()
            _mock_gda.types.Message = MagicMock

            # Return bytes for chart
            mock_show.return_value = b"\x89PNG\r\n"

            ctx = _FakeToolContext()
            result = await conversational_chat(
                "Show me a chart",
                True,
                ctx,
                [{"project_id": "p", "dataset_id": "d", "table_id": "t"}],
            )

            assert "chart" in result.lower()
            ctx.save_artifact.assert_called_once()
