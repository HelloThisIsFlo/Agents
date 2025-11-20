"""Tests for evaluation functions."""

import pytest
from unittest.mock import Mock, MagicMock
from langchain_core.messages import AIMessage

from src.agents.walkandlearn_summary.nodes.evaluation import (
    format_summaries_for_evaluation,
    parse_evaluation_result,
    evaluate_summaries,
)


class TestFormatSummariesForEvaluation:
    """Test format_summaries_for_evaluation function."""

    def test_formats_single_summary(self):
        """Test formatting a single summary."""
        summaries = ["This is a summary."]
        result = format_summaries_for_evaluation(summaries)

        assert result == "Summary 0:\nThis is a summary."

    def test_formats_multiple_summaries(self):
        """Test formatting multiple summaries."""
        summaries = ["First summary.", "Second summary.", "Third summary."]
        result = format_summaries_for_evaluation(summaries)

        expected = "Summary 0:\nFirst summary.\n\nSummary 1:\nSecond summary.\n\nSummary 2:\nThird summary."
        assert result == expected

    def test_formats_empty_list(self):
        """Test formatting an empty list."""
        summaries = []
        result = format_summaries_for_evaluation(summaries)

        assert result == ""


class TestParseEvaluationResult:
    """Test parse_evaluation_result function."""

    def test_parses_best_summary_and_reasoning(self):
        """Test parsing a well-formatted evaluation result."""
        evaluation_text = """Best summary: 2

Reasoning: This summary is the best because it is clear and concise."""

        best_idx, reasoning = parse_evaluation_result(evaluation_text)

        assert best_idx == 2
        assert reasoning == "This summary is the best because it is clear and concise."

    def test_parses_case_insensitive(self):
        """Test parsing with different case."""
        evaluation_text = """BEST SUMMARY: 1

REASONING: Good choice."""

        best_idx, reasoning = parse_evaluation_result(evaluation_text)

        assert best_idx == 1
        assert reasoning == "Good choice."

    def test_handles_missing_best_summary(self):
        """Test parsing when best summary index is missing."""
        evaluation_text = "Reasoning: All summaries are good."

        best_idx, reasoning = parse_evaluation_result(evaluation_text)

        assert best_idx is None
        assert reasoning == "All summaries are good."

    def test_handles_missing_reasoning(self):
        """Test parsing when reasoning is missing."""
        evaluation_text = "Best summary: 0"

        best_idx, reasoning = parse_evaluation_result(evaluation_text)

        assert best_idx == 0
        assert reasoning == "Best summary: 0"

    def test_handles_multiline_reasoning(self):
        """Test parsing with multiline reasoning."""
        evaluation_text = """Best summary: 1

Reasoning: This is the best because:
- It's clear
- It's concise
- It captures all key points"""

        best_idx, reasoning = parse_evaluation_result(evaluation_text)

        assert best_idx == 1
        assert "It's clear" in reasoning
        assert "It's concise" in reasoning


class TestEvaluateSummaries:
    """Test evaluate_summaries function."""

    def test_returns_disabled_message_when_disabled(self):
        """Test that it returns a disabled message when eval is disabled."""
        mock_agent = Mock()
        summaries = ["Summary 1", "Summary 2"]

        best_idx, reasoning = evaluate_summaries(
            evaluation_agent=mock_agent,
            summaries=summaries,
            summary_type="emotional",
            eval_disabled=True,
        )

        assert best_idx == 0
        assert "evaluation disabled" in reasoning.lower()
        mock_agent.invoke.assert_not_called()

    def test_handles_empty_summaries(self):
        """Test handling of empty summaries list."""
        mock_agent = Mock()
        summaries = []

        best_idx, reasoning = evaluate_summaries(
            evaluation_agent=mock_agent,
            summaries=summaries,
            summary_type="technical",
            eval_disabled=False,
        )

        assert best_idx is None
        assert "No summaries" in reasoning
        mock_agent.invoke.assert_not_called()

    def test_evaluates_summaries_with_agent(self):
        """Test that it calls the agent and parses the result."""
        # Mock the agent
        mock_agent = Mock()
        mock_result = {
            "messages": [
                AIMessage(content="Best summary: 1\n\nReasoning: It's the clearest.")
            ]
        }
        mock_agent.invoke.return_value = mock_result

        summaries = ["Summary 0", "Summary 1", "Summary 2"]

        best_idx, reasoning = evaluate_summaries(
            evaluation_agent=mock_agent,
            summaries=summaries,
            summary_type="emotional",
            eval_disabled=False,
        )

        assert best_idx == 1
        assert reasoning == "It's the clearest."
        mock_agent.invoke.assert_called_once()
