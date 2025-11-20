"""Tests for summary generation functions."""

import pytest
from unittest.mock import Mock
from langchain_core.messages import AIMessage, HumanMessage

from src.agents.walkandlearn_summary.nodes.summary import (
    generate_summary_with_agent,
)


class TestGenerateSummaryWithAgent:
    """Test generate_summary_with_agent function."""

    def test_invokes_agent_with_conversation(self):
        """Test that the agent is invoked with the correct conversation."""
        # Mock the agent
        mock_agent = Mock()
        mock_result = {
            "messages": [AIMessage(content="This is a summary of the conversation.")]
        }
        mock_agent.invoke.return_value = mock_result

        conversation = "Person A: Hello\nPerson B: Hi there!"

        result = generate_summary_with_agent(mock_agent, conversation)

        assert result == "This is a summary of the conversation."
        mock_agent.invoke.assert_called_once()

        # Check that the conversation was included in the message
        call_args = mock_agent.invoke.call_args[0][0]
        assert "messages" in call_args
        assert len(call_args["messages"]) == 1
        assert isinstance(call_args["messages"][0], HumanMessage)
        assert conversation in call_args["messages"][0].content

    def test_extracts_content_from_ai_message(self):
        """Test that it properly extracts content from the AI message."""
        mock_agent = Mock()
        expected_summary = "A detailed summary with multiple sentences."
        mock_result = {"messages": [AIMessage(content=expected_summary)]}
        mock_agent.invoke.return_value = mock_result

        result = generate_summary_with_agent(mock_agent, "Some conversation")

        assert result == expected_summary
