"""LangGraph agent for summarizing conversations with emotional and technical summaries."""

import operator
from typing import Annotated, Optional
from src.agents.walkandlearn_summary.config import (
    MODELS,
    EMOTIONAL_DISABLED,
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
)

# Number of iterations for each summary type
NUM_EMOTIONAL_ITERATIONS = 3
NUM_TECHNICAL_ITERATIONS = 3


def keep_last_value(left: Optional[str], right: Optional[str]) -> Optional[str]:
    """Reducer that keeps the last non-None value."""
    return right if right is not None else left


class SummaryState(MessagesState):
    input_filename: Annotated[Optional[str], keep_last_value]
    conversation: Annotated[str, keep_last_value]
    emotional_summaries: Annotated[list[str], operator.add]
    technical_summaries: Annotated[list[str], operator.add]


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
    is_disabled: bool,
):
    """Build a subgraph for generating summaries in parallel.

    Args:
        summary_type: "emotional" or "technical"
        model: The model to use for the agent
        system_prompt: The system prompt for the agent
        num_iterations: Number of parallel iterations
        is_disabled: Whether this summary type is disabled
    """
    agent = create_agent(model=model, system_prompt=system_prompt)
    state_key = f"{summary_type}_summaries"

    # Create dynamic summary nodes
    def make_summary_node(index):
        def summary_node(state: SummaryState) -> dict:
            if is_disabled:
                return {
                    state_key: [
                        f"[{summary_type.capitalize()} summary {index} is disabled]"
                    ]
                }
            summary = generate_summary_with_agent(agent, state["conversation"])
            return {state_key: [summary]}

        return summary_node

    # Build the subgraph
    subgraph = StateGraph(SummaryState)

    # Add all summary nodes
    for i in range(num_iterations):
        node_name = f"{summary_type}_{i}"
        subgraph.add_node(node_name, make_summary_node(i))
        subgraph.add_edge(START, node_name)
        subgraph.add_edge(node_name, END)

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

        # For chat output, combine all summaries
        combined_summary = "# Emotional Summaries\n\n"
        for i, summary in enumerate(emotional_summaries):
            combined_summary += f"## Iteration {i}\n\n{summary}\n\n"
        combined_summary += "\n\n# Technical Summaries\n\n"
        for i, summary in enumerate(technical_summaries):
            combined_summary += f"## Iteration {i}\n\n{summary}\n\n"

        return (
            {"messages": [AIMessage(content=combined_summary)]}
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
        is_disabled=EMOTIONAL_DISABLED,
    )
    technical_subgraph = build_summary_subgraph(
        summary_type="technical",
        model=MODELS["technical"],
        system_prompt=TECHNICAL_SUMMARY_PROMPT,
        num_iterations=NUM_TECHNICAL_ITERATIONS,
        is_disabled=TECHNICAL_DISABLED,
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
