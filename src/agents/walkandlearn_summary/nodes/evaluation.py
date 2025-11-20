"""Evaluation logic for summary generation."""

import re
from typing import Optional, Tuple
from langchain_core.messages import HumanMessage


def format_summaries_for_evaluation(summaries: list[str]) -> str:
    """Format a list of summaries for evaluation.

    Args:
        summaries: List of summary strings

    Returns:
        Formatted string with numbered summaries
    """
    return "\n\n".join(
        [f"Summary {i}:\n{summary}" for i, summary in enumerate(summaries)]
    )


def parse_evaluation_result(evaluation_result: str) -> Tuple[Optional[int], str]:
    """Parse the evaluation result to extract best summary index and reasoning.

    Args:
        evaluation_result: The raw evaluation text from the agent

    Returns:
        Tuple of (best_summary_index, reasoning)
    """
    best_idx = None
    reasoning = evaluation_result

    # Try to extract "Best summary: X" from the response
    match = re.search(r"Best summary:\s*(\d+)", evaluation_result, re.IGNORECASE)
    if match:
        best_idx = int(match.group(1))

    # Try to extract reasoning
    reasoning_match = re.search(
        r"Reasoning:\s*(.+)", evaluation_result, re.IGNORECASE | re.DOTALL
    )
    if reasoning_match:
        reasoning = reasoning_match.group(1).strip()

    return best_idx, reasoning


def evaluate_summaries(
    evaluation_agent,
    summaries: list[str],
    summary_type: str,
    eval_disabled: bool,
) -> Tuple[Optional[int], str]:
    """Evaluate summaries and return the best one.

    Args:
        evaluation_agent: The agent to use for evaluation
        summaries: List of summaries to evaluate
        summary_type: Type of summary (e.g., "emotional", "technical")
        eval_disabled: Whether evaluation is disabled

    Returns:
        Tuple of (best_summary_index, reasoning)
    """
    if eval_disabled:
        return (
            0,
            f"[{summary_type.capitalize()} evaluation disabled]",
        )

    if not summaries:
        return (None, "No summaries to evaluate")

    # Format summaries for evaluation
    formatted_summaries = format_summaries_for_evaluation(summaries)

    # Invoke the evaluation agent directly (not using the summary wrapper)
    result = evaluation_agent.invoke(
        {"messages": [HumanMessage(content=formatted_summaries)]}
    )
    evaluation_result = result["messages"][-1].content

    # Parse the evaluation result
    return parse_evaluation_result(evaluation_result)
