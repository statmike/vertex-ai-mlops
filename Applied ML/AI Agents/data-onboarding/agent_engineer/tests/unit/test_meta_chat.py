"""Tests for function_tool_meta_chat."""

from unittest.mock import MagicMock, patch

import pytest


class TestMetaChatTool:
    """Tests for the meta_chat tool."""

    @pytest.mark.asyncio
    async def test_text_response_returned(self, mock_tool_context):
        mock_response = MagicMock()
        mock_response.system_message.__contains__ = lambda self, key: key == "text"
        mock_text = MagicMock()
        mock_text.parts = ["Pipeline processed 5 tables."]
        mock_response.system_message.text = mock_text
        type(mock_response.system_message).text = property(lambda self: mock_text)

        mock_client = MagicMock()
        mock_client.chat.return_value = [mock_response]

        with (
            patch("agent_convo.tools.util_conversational_api.geminidataanalytics") as mock_gda,
            patch("agent_engineer.tools.function_tool_meta_chat.GOOGLE_CLOUD_PROJECT", "test-proj"),
            patch("agent_convo.tools.util_conversational_api.handle_text_response",
                  return_value="Pipeline processed 5 tables."),
        ):
            mock_gda.DataChatServiceClient.return_value = mock_client
            mock_gda.DatasourceReferences.return_value = MagicMock()
            mock_gda.Context.return_value = MagicMock()
            mock_gda.Message.return_value = MagicMock()
            mock_gda.types.Message.return_value = MagicMock()

            from agent_engineer.tools.function_tool_meta_chat import meta_chat

            result = await meta_chat(
                question="Show me the processing log",
                chart=False,
                tool_context=mock_tool_context,
            )

            assert "Pipeline processed 5 tables" in result

    @pytest.mark.asyncio
    async def test_all_meta_tables_included(self, mock_tool_context):
        """Verify that all 6 meta tables are included in the request."""
        from agent_engineer.tools.function_tool_meta_chat import (
            META_TABLE_NAMES,
            _build_meta_table_refs,
        )

        expected = {
            "source_manifest", "processing_log", "table_lineage",
            "schema_decisions", "web_provenance", "data_catalog",
        }
        assert set(META_TABLE_NAMES) == expected

        with patch(
            "agent_engineer.tools.function_tool_meta_chat.GOOGLE_CLOUD_PROJECT", "test-proj"
        ):
            refs = _build_meta_table_refs()
            assert len(refs) == 6
            table_ids = {r["table_id"] for r in refs}
            assert table_ids == expected

    @pytest.mark.asyncio
    async def test_no_responses_handled(self, mock_tool_context):
        mock_client = MagicMock()
        mock_client.chat.return_value = []

        with (
            patch("agent_convo.tools.util_conversational_api.geminidataanalytics") as mock_gda,
            patch("agent_engineer.tools.function_tool_meta_chat.GOOGLE_CLOUD_PROJECT", "test-proj"),
        ):
            mock_gda.DataChatServiceClient.return_value = mock_client
            mock_gda.DatasourceReferences.return_value = MagicMock()
            mock_gda.Context.return_value = MagicMock()
            mock_gda.Message.return_value = MagicMock()
            mock_gda.types.Message.return_value = MagicMock()

            from agent_engineer.tools.function_tool_meta_chat import meta_chat

            result = await meta_chat(
                question="test", chart=False, tool_context=mock_tool_context,
            )
            assert "No responses" in result

    @pytest.mark.asyncio
    async def test_session_state_stored_under_meta_key(self, mock_tool_context):
        mock_response = MagicMock()
        mock_response.system_message.__contains__ = lambda self, key: key == "text"
        mock_response._pb = MagicMock()

        mock_client = MagicMock()
        mock_client.chat.return_value = [mock_response]

        with (
            patch("agent_convo.tools.util_conversational_api.geminidataanalytics") as mock_gda,
            patch("agent_engineer.tools.function_tool_meta_chat.GOOGLE_CLOUD_PROJECT", "test-proj"),
            patch("agent_convo.tools.util_conversational_api.handle_text_response",
                  return_value="answer"),
            patch("agent_convo.tools.util_conversational_api.MessageToDict",
                  return_value={"text": "answer"}),
        ):
            mock_gda.DataChatServiceClient.return_value = mock_client
            mock_gda.DatasourceReferences.return_value = MagicMock()
            mock_gda.Context.return_value = MagicMock()
            mock_gda.Message.return_value = MagicMock()
            mock_gda.types.Message.return_value = MagicMock()

            from agent_engineer.tools.function_tool_meta_chat import meta_chat

            await meta_chat(
                question="test", chart=False, tool_context=mock_tool_context,
            )

            # Session should be stored under meta_api_sessions, not conversational_api_sessions
            assert "meta_api_sessions" in mock_tool_context.state
            assert "conversational_api_sessions" not in mock_tool_context.state
