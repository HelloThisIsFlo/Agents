"""LangGraph agent for summarizing conversations with emotional and technical summaries."""

import operator
from typing import Annotated, Optional
from src.agents.walkandlearn_summary.config import (
    EVAL_DISABLED,
    MODELS,
    EMOTIONAL_DISABLED,
    NUM_EMOTIONAL_ITERATIONS,
    NUM_TECHNICAL_ITERATIONS,
    TECHNICAL_DISABLED,
    PRINT_SUMMARY_IN_CHAT,
    CONFIG_TEMPLATE,
    DEFAULT_INPUT_FILENAME,
    OUTPUT_FILE_PATH_OBSIDIAN_BASE,
    get_input_file_path,
)
from langchain.agents import create_agent
from langchain_core.messages import AIMessage, HumanMessage
from langgraph.graph import StateGraph, START, END, MessagesState

from src.agents.walkandlearn_summary.io import read_file, write_file, get_frontmatter
from src.agents.walkandlearn_summary.prompts import (
    EMOTIONAL_SUMMARY_PROMPT,
    TECHNICAL_SUMMARY_PROMPT,
    EVALUATION_PROMPT,
)


def keep_last_value(left, right):
    """Reducer that keeps the last non-None value."""
    return right if right is not None else left


class SummaryState(MessagesState):
    input_filename: Annotated[Optional[str], keep_last_value]
    conversation: Annotated[str, keep_last_value]
    emotional_summaries: Annotated[list[str], operator.add]
    technical_summaries: Annotated[list[str], operator.add]
    emotional_best_idx: Annotated[Optional[int], keep_last_value]
    emotional_best_reasoning: Annotated[Optional[str], keep_last_value]
    technical_best_idx: Annotated[Optional[int], keep_last_value]
    technical_best_reasoning: Annotated[Optional[str], keep_last_value]


def generate_summary_with_agent(agent, conversation: str) -> str:
    result = agent.invoke(
        {
            "messages": [
                HumanMessage(
                    content=f"Here is the conversation to summarize:\n\n{conversation}"
                )
            ]
        }
    )
    return result["messages"][-1].content


def build_summary_subgraph(
    summary_type: str,
    model,
    system_prompt: str,
    num_iterations: int,
    summary_disabled: bool,
    eval_disabled: bool,
    evaluation_model,
):
    """Build a subgraph for generating summaries in parallel.

    Args:
        summary_type: "emotional" or "technical"
        model: The model to use for the agent
        system_prompt: The system prompt for the agent
        num_iterations: Number of parallel iterations
        is_disabled: Whether this summary type is disabled
        evaluation_model: The model to use for evaluation
    """
    agent = create_agent(model=model, system_prompt=system_prompt)
    evaluation_agent = create_agent(
        model=evaluation_model, system_prompt=EVALUATION_PROMPT
    )
    state_key = f"{summary_type}_summaries"

    # Create dynamic summary nodes
    def make_summary_node(index):
        def summary_node(state: SummaryState) -> dict:
            if summary_disabled:
                return {
                    state_key: [
                        f"[{summary_type.capitalize()} summary {index} is disabled]"
                    ]
                }
            summary = generate_summary_with_agent(agent, state["conversation"])
            return {state_key: [summary]}

        return summary_node

    def wait_for_all_summaries_node(state: SummaryState) -> dict:
        return {}

    # Create evaluation node
    def evaluation_node(state: SummaryState) -> dict:
        if eval_disabled:
            return {
                f"{summary_type}_best_idx": 0,
                f"{summary_type}_best_reasoning": f"[{summary_type.capitalize()} evaluation disabled]",
            }

        summaries = state.get(state_key, [])
        if not summaries:
            return {
                f"{summary_type}_best_idx": None,
                f"{summary_type}_best_reasoning": "No summaries to evaluate",
            }

        # Format summaries for evaluation
        formatted_summaries = "\n\n".join(
            [f"Summary {i}:\n{summary}" for i, summary in enumerate(summaries)]
        )

        # Get evaluation from agent
        evaluation_result = generate_summary_with_agent(
            evaluation_agent, formatted_summaries
        )

        # Parse the evaluation result
        best_idx = None
        reasoning = evaluation_result

        # Try to extract "Best summary: X" from the response
        import re

        match = re.search(r"Best summary:\s*(\d+)", evaluation_result, re.IGNORECASE)
        if match:
            best_idx = int(match.group(1))

        # Try to extract reasoning
        reasoning_match = re.search(
            r"Reasoning:\s*(.+)", evaluation_result, re.IGNORECASE | re.DOTALL
        )
        if reasoning_match:
            reasoning = reasoning_match.group(1).strip()

        return {
            f"{summary_type}_best_idx": best_idx,
            f"{summary_type}_best_reasoning": reasoning,
        }

    # Build the subgraph
    subgraph = StateGraph(SummaryState)

    # Add all summary nodes
    for i in range(num_iterations):
        node_name = f"{summary_type}_{i}"
        subgraph.add_node(node_name, make_summary_node(i))
        subgraph.add_edge(START, node_name)
        subgraph.add_edge(node_name, "wait_for_all_summaries")

    subgraph.add_node("wait_for_all_summaries", wait_for_all_summaries_node)
    subgraph.add_edge("wait_for_all_summaries", "evaluation")

    subgraph.add_node("evaluation", evaluation_node)
    subgraph.add_edge("evaluation", END)

    return subgraph.compile()


def build_graph():
    def load_conversation_node(state: SummaryState) -> dict:
        input_filename = state.get("input_filename") or DEFAULT_INPUT_FILENAME
        input_file_path = get_input_file_path(input_filename)
        return {
            "conversation": read_file(input_file_path),
            "input_filename": input_filename,
            "emotional_summaries": [],
            "technical_summaries": [],
        }

    def write_output_node(state: SummaryState) -> dict:
        from datetime import datetime
        from pathlib import Path

        # Get filename without extension
        input_filename = state.get("input_filename") or DEFAULT_INPUT_FILENAME
        filename_without_ext = Path(input_filename).stem

        # Generate datetime for frontmatter and filename timestamp
        now = datetime.now()
        timestamp = now.strftime("%Y%m%d-%H%M%S")

        # Create output folder with just the filename (no timestamp, since we have generated_at in frontmatter)
        output_folder = OUTPUT_FILE_PATH_OBSIDIAN_BASE / filename_without_ext
        output_folder.mkdir(parents=True, exist_ok=True)

        # Write all emotional summaries
        emotional_summaries = state.get("emotional_summaries", [])
        for i, summary in enumerate(emotional_summaries):
            emotional_frontmatter = get_frontmatter(
                CONFIG_TEMPLATE, now, input_filename, "emotional"
            )
            emotional_content = emotional_frontmatter + summary
            emotional_file_path = output_folder / f"emotional_{i}__{timestamp}.md"
            write_file(emotional_file_path, emotional_content)

        # Write all technical summaries
        technical_summaries = state.get("technical_summaries", [])
        for i, summary in enumerate(technical_summaries):
            technical_frontmatter = get_frontmatter(
                CONFIG_TEMPLATE, now, input_filename, "technical"
            )
            technical_content = technical_frontmatter + summary
            technical_file_path = output_folder / f"technical_{i}__{timestamp}.md"
            write_file(technical_file_path, technical_content)

        # Write evaluation file
        evaluation_content = "# Emotional Summaries Evaluation\n\n"
        evaluation_content += (
            f"**Best Summary Index:** {state.get('emotional_best_idx', 'N/A')}\n\n"
        )
        evaluation_content += (
            f"**Reasoning:**\n\n{state.get('emotional_best_reasoning', 'N/A')}\n\n"
        )
        evaluation_content += "---\n\n"
        evaluation_content += "# Technical Summaries Evaluation\n\n"
        evaluation_content += (
            f"**Best Summary Index:** {state.get('technical_best_idx', 'N/A')}\n\n"
        )
        evaluation_content += (
            f"**Reasoning:**\n\n{state.get('technical_best_reasoning', 'N/A')}\n\n"
        )

        evaluation_frontmatter = get_frontmatter(
            CONFIG_TEMPLATE, now, input_filename, "evaluation"
        )
        evaluation_file_content = evaluation_frontmatter + evaluation_content
        evaluation_file_path = output_folder / f"evaluation__{timestamp}.md"
        write_file(evaluation_file_path, evaluation_file_content)

        # For chat output, only show evaluation results
        chat_output = "# Summary Evaluation Results\n\n"
        chat_output += "## Emotional Summaries\n\n"
        chat_output += f"**Best:** Summary {state.get('emotional_best_idx', 'N/A')}\n\n"
        chat_output += f"**Why:** {state.get('emotional_best_reasoning', 'N/A')}\n\n"
        chat_output += "---\n\n"
        chat_output += "## Technical Summaries\n\n"
        chat_output += f"**Best:** Summary {state.get('technical_best_idx', 'N/A')}\n\n"
        chat_output += f"**Why:** {state.get('technical_best_reasoning', 'N/A')}\n\n"

        return (
            {"messages": [AIMessage(content=chat_output)]}
            if PRINT_SUMMARY_IN_CHAT
            else {}
        )

    # Build the main graph
    graph_builder = StateGraph(SummaryState)

    # Add load conversation node
    graph_builder.add_node("load_conversation", load_conversation_node)

    # Add subgraphs
    emotional_subgraph = build_summary_subgraph(
        summary_type="emotional",
        model=MODELS["emotional"],
        system_prompt=EMOTIONAL_SUMMARY_PROMPT,
        num_iterations=NUM_EMOTIONAL_ITERATIONS,
        summary_disabled=EMOTIONAL_DISABLED,
        eval_disabled=EVAL_DISABLED,
        evaluation_model=MODELS["evaluation"],
    )
    technical_subgraph = build_summary_subgraph(
        summary_type="technical",
        model=MODELS["technical"],
        system_prompt=TECHNICAL_SUMMARY_PROMPT,
        num_iterations=NUM_TECHNICAL_ITERATIONS,
        summary_disabled=TECHNICAL_DISABLED,
        eval_disabled=EVAL_DISABLED,
        evaluation_model=MODELS["evaluation"],
    )

    graph_builder.add_node("emotional_summaries", emotional_subgraph)
    graph_builder.add_node("technical_summaries", technical_subgraph)

    # Add write output node
    graph_builder.add_node("write_output", write_output_node)

    # Connect the graph
    graph_builder.add_edge(START, "load_conversation")
    graph_builder.add_edge("load_conversation", "emotional_summaries")
    graph_builder.add_edge("load_conversation", "technical_summaries")
    graph_builder.add_edge("emotional_summaries", "write_output")
    graph_builder.add_edge("technical_summaries", "write_output")
    graph_builder.add_edge("write_output", END)

    return graph_builder.compile()


graph = build_graph()
