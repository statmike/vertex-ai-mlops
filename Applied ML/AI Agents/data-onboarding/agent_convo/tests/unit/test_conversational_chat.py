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
            "agent_convo.tools.function_tool_conversational_chat.geminidataanalytics",
            _mock_gda,
        ), patch(
            "agent_convo.tools.function_tool_conversational_chat.show_message"
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

            mock_show.return_value = "The answer is 42."

            ctx = _FakeToolContext()
            result = await conversational_chat(
                question="How many records?",
                chart=False,
                bigquery_tables=[
                    {"project_id": "p", "dataset_id": "d", "table_id": "t"}
                ],
                tool_context=ctx,
            )

            assert "42" in result
            assert "conversational_api_sessions" in ctx.state

    @pytest.mark.asyncio
    async def test_session_history_stored(self):
        with patch(
            "agent_convo.tools.function_tool_conversational_chat.geminidataanalytics",
            _mock_gda,
        ), patch(
            "agent_convo.tools.function_tool_conversational_chat.show_message"
        ) as mock_show, patch(
            "agent_convo.tools.function_tool_conversational_chat.MessageToDict"
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

            await conversational_chat("Q1", False, tables, ctx)

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
            "agent_convo.tools.function_tool_conversational_chat.geminidataanalytics",
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
                [{"project_id": "p", "dataset_id": "d", "table_id": "t"}],
                ctx,
            )
            assert "No responses" in result

    @pytest.mark.asyncio
    async def test_chart_response(self):
        with patch(
            "agent_convo.tools.function_tool_conversational_chat.geminidataanalytics",
            _mock_gda,
        ), patch(
            "agent_convo.tools.function_tool_conversational_chat.show_message"
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
                [{"project_id": "p", "dataset_id": "d", "table_id": "t"}],
                ctx,
            )

            assert "chart" in result.lower()
            ctx.save_artifact.assert_called_once()
