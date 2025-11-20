"""Output formatting functions for evaluation results."""

from typing import Optional


def format_evaluation_file_content(
    emotional_best_idx: Optional[int],
    emotional_reasoning: str,
    technical_best_idx: Optional[int],
    technical_reasoning: str,
) -> str:
    """Format evaluation results for file output.

    Args:
        emotional_best_idx: Best emotional summary index
        emotional_reasoning: Reasoning for emotional choice
        technical_best_idx: Best technical summary index
        technical_reasoning: Reasoning for technical choice

    Returns:
        Formatted markdown content for evaluation file
    """
    content = "# Emotional Summaries Evaluation\n\n"
    content += f"**Best Summary Index:** {emotional_best_idx if emotional_best_idx is not None else 'N/A'}\n\n"
    content += (
        f"**Reasoning:**\n\n{emotional_reasoning if emotional_reasoning else 'N/A'}\n\n"
    )
    content += "---\n\n"
    content += "# Technical Summaries Evaluation\n\n"
    content += f"**Best Summary Index:** {technical_best_idx if technical_best_idx is not None else 'N/A'}\n\n"
    content += (
        f"**Reasoning:**\n\n{technical_reasoning if technical_reasoning else 'N/A'}\n\n"
    )
    return content


def format_evaluation_chat_output(
    emotional_best_idx: Optional[int],
    emotional_reasoning: str,
    technical_best_idx: Optional[int],
    technical_reasoning: str,
) -> str:
    """Format evaluation results for chat output.

    Args:
        emotional_best_idx: Best emotional summary index
        emotional_reasoning: Reasoning for emotional choice
        technical_best_idx: Best technical summary index
        technical_reasoning: Reasoning for technical choice

    Returns:
        Formatted markdown content for chat display
    """
    output = "# Summary Evaluation Results\n\n"
    output += "## Emotional Summaries\n\n"
    output += f"**Best:** Summary {emotional_best_idx if emotional_best_idx is not None else 'N/A'}\n\n"
    output += f"**Why:** {emotional_reasoning if emotional_reasoning else 'N/A'}\n\n"
    output += "---\n\n"
    output += "## Technical Summaries\n\n"
    output += f"**Best:** Summary {technical_best_idx if technical_best_idx is not None else 'N/A'}\n\n"
    output += f"**Why:** {technical_reasoning if technical_reasoning else 'N/A'}\n\n"
    return output
