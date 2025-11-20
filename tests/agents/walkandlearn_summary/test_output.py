"""Tests for output formatting functions."""

from src.agents.walkandlearn_summary.nodes.output import (
    format_evaluation_file_content,
    format_evaluation_chat_output,
)


class TestFormatEvaluationFileContent:
    """Test format_evaluation_file_content function."""

    def test_formats_evaluation_content_with_both_types(self):
        """Test formatting evaluation file content with both emotional and technical."""
        emotional_best_idx = 1
        emotional_reasoning = "Clear and concise"
        technical_best_idx = 2
        technical_reasoning = "Comprehensive coverage"

        result = format_evaluation_file_content(
            emotional_best_idx=emotional_best_idx,
            emotional_reasoning=emotional_reasoning,
            technical_best_idx=technical_best_idx,
            technical_reasoning=technical_reasoning,
        )

        expected = """# Emotional Summaries Evaluation

**Best Summary Index:** 1

**Reasoning:**

Clear and concise

---

# Technical Summaries Evaluation

**Best Summary Index:** 2

**Reasoning:**

Comprehensive coverage

"""
        assert result == expected

    def test_formats_evaluation_content_with_none_values(self):
        """Test formatting when indices are None."""
        emotional_best_idx = None
        emotional_reasoning = "No summaries"
        technical_best_idx = None
        technical_reasoning = "No summaries"

        result = format_evaluation_file_content(
            emotional_best_idx=emotional_best_idx,
            emotional_reasoning=emotional_reasoning,
            technical_best_idx=technical_best_idx,
            technical_reasoning=technical_reasoning,
        )

        assert "**Best Summary Index:** N/A" in result
        assert "No summaries" in result


class TestFormatEvaluationChatOutput:
    """Test format_evaluation_chat_output function."""

    def test_formats_chat_output_with_results(self):
        """Test formatting chat output with evaluation results."""
        emotional_best_idx = 0
        emotional_reasoning = "Best choice"
        technical_best_idx = 1
        technical_reasoning = "Most technical"

        result = format_evaluation_chat_output(
            emotional_best_idx=emotional_best_idx,
            emotional_reasoning=emotional_reasoning,
            technical_best_idx=technical_best_idx,
            technical_reasoning=technical_reasoning,
        )

        expected = """# Summary Evaluation Results

## Emotional Summaries

**Best:** Summary 0

**Why:** Best choice

---

## Technical Summaries

**Best:** Summary 1

**Why:** Most technical

"""
        assert result == expected

    def test_formats_chat_output_with_na_values(self):
        """Test formatting chat output with N/A values."""
        result = format_evaluation_chat_output(
            emotional_best_idx=None,
            emotional_reasoning=None,
            technical_best_idx=None,
            technical_reasoning=None,
        )

        assert "**Best:** Summary N/A" in result
        assert "**Why:** N/A" in result
