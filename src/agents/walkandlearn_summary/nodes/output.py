"""Output formatting functions for evaluation results."""

from datetime import datetime
from pathlib import Path
from typing import Optional
from src.agents.walkandlearn_summary.io import write_file, get_frontmatter


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


def generate_output_paths(output_folder: Path, emotional_idx: int, technical_idx: int):
    ti = technical_idx
    ei = emotional_idx
    return {
        "emotional": output_folder / f"emotional_{ei}.md",
        "technical": output_folder / f"technical_{ti}.md",
        "result": output_folder / f"result_e{ei}_t{ti}.md",
        "evaluation": output_folder / "evaluation.md",
    }


def write_file_with_frontmatter(
    config_template: str,
    now: datetime,
    input_filename: str,
    summary_type: str,
    summary: str,
    output_path: Path,
) -> None:

    # Ensure summary is a string (defensive check)
    if isinstance(summary, list):
        summary = "\n".join(str(item) for item in summary)
    summary = str(summary)

    frontmatter = get_frontmatter(config_template, now, input_filename, summary_type)
    content = frontmatter + summary
    write_file(output_path, content)


def write_all_output_files(
    output_folder: Path,
    input_filename: str,
    config_template: str,
    now: datetime,
    emotional_summaries: list[str],
    technical_summaries: list[str],
    emotional_best_idx: Optional[int],
    emotional_best_reasoning: str,
    technical_best_idx: Optional[int],
    technical_best_reasoning: str,
) -> None:
    """Write all output files: emotional, technical, combined results, and evaluation.

    Args:
        output_folder: Path to the output folder
        input_filename: Name of the input file
        config_template: Configuration template name
        now: Current datetime for frontmatter
        emotional_summaries: List of emotional summaries
        technical_summaries: List of technical summaries
        emotional_best_idx: Best emotional summary index
        emotional_best_reasoning: Reasoning for emotional choice
        technical_best_idx: Best technical summary index
        technical_best_reasoning: Reasoning for technical choice
    """

    # Write all combined result files (emotional × technical combinations)
    for e_idx, emotional_summary in enumerate(emotional_summaries):
        for t_idx, technical_summary in enumerate(technical_summaries):
            output_paths = generate_output_paths(output_folder, e_idx, t_idx)

            write_file_with_frontmatter(
                config_template,
                now,
                input_filename,
                "emotional",
                emotional_summary,
                output_paths["emotional"],
            )

            write_file_with_frontmatter(
                config_template,
                now,
                input_filename,
                "technical",
                technical_summary,
                output_paths["technical"],
            )

            #
            # Write combined result
            #
            # Replace [AHA_PLACEHOLDER] with emotional summary content
            if "[AHA_PLACEHOLDER]" in technical_summary:
                combined_content = technical_summary.replace(
                    "[AHA_PLACEHOLDER]", emotional_summary
                )
            else:
                # Placeholder missing - prepend warning at the top with emotional summary
                combined_content = (
                    "## ❌ ❌ Missing AHA Placeholder Section ❌ ❌\n\n"
                    + "> [!WARNING]\n"
                    + "> The technical summary did not include the `[AHA_PLACEHOLDER]` marker.\n"
                    + "> The emotional summary has been placed here at the top. Please manually move it to the correct location.\n\n"
                    + "---\n\n"
                    + emotional_summary
                    + "\n\n---\n\n"
                    + technical_summary
                )
            write_file_with_frontmatter(
                config_template,
                now,
                input_filename,
                "result",
                combined_content,
                output_paths["result"],
            )

    evaluation_content = format_evaluation_file_content(
        emotional_best_idx=emotional_best_idx,
        emotional_reasoning=emotional_best_reasoning,
        technical_best_idx=technical_best_idx,
        technical_reasoning=technical_best_reasoning,
    )
    write_file_with_frontmatter(
        config_template,
        now,
        input_filename,
        "evaluation",
        evaluation_content,
        output_paths["evaluation"],
    )
