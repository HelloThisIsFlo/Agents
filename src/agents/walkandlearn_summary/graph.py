"""LangGraph agent for summarizing conversations with emotional and technical summaries."""

from typing import Optional
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


class SummaryState(MessagesState):
    input_filename: Optional[str]
    conversation: str
    emotional_summary: str
    technical_summary: str


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


def build_graph():
    emotional_agent = create_agent(
        model=MODELS["emotional"],
        system_prompt=EMOTIONAL_SUMMARY_PROMPT,
    )
    technical_agent = create_agent(
        model=MODELS["technical"],
        system_prompt=TECHNICAL_SUMMARY_PROMPT,
    )

    def load_conversation_node(state: SummaryState) -> dict:
        input_filename = state.get("input_filename") or DEFAULT_INPUT_FILENAME
        input_file_path = get_input_file_path(input_filename)
        return {
            "conversation": read_file(input_file_path),
            "input_filename": input_filename,
        }

    def emotional_summary_node(state: SummaryState) -> dict:
        if EMOTIONAL_DISABLED:
            return {"emotional_summary": "[Emotional summary is disabled]"}
        return {
            "emotional_summary": generate_summary_with_agent(
                emotional_agent,
                state["conversation"],
            )
        }

    def technical_summary_node(state: SummaryState) -> dict:
        if TECHNICAL_DISABLED:
            return {"technical_summary": "[Technical summary is disabled]"}
        return {
            "technical_summary": generate_summary_with_agent(
                technical_agent,
                state["conversation"],
            )
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

        # Write emotional summary to emotional-{timestamp}.md with frontmatter
        emotional_frontmatter = get_frontmatter(
            CONFIG_TEMPLATE, now, input_filename, "emotional"
        )
        emotional_content = emotional_frontmatter + state["emotional_summary"]
        emotional_file_path = output_folder / f"emotional__{timestamp}.md"
        write_file(emotional_file_path, emotional_content)

        # Write technical summary to technical-{timestamp}.md with frontmatter
        technical_frontmatter = get_frontmatter(
            CONFIG_TEMPLATE, now, input_filename, "technical"
        )
        technical_content = technical_frontmatter + state["technical_summary"]
        technical_file_path = output_folder / f"technical__{timestamp}.md"
        write_file(technical_file_path, technical_content)

        # For chat output, combine both summaries
        combined_summary = f"# Emotional Summary\n\n{state['emotional_summary']}\n\n\n\n# Technical Summary\n\n{state['technical_summary']}"

        return (
            {"messages": [AIMessage(content=combined_summary)]}
            if PRINT_SUMMARY_IN_CHAT
            else {}
        )

    return (
        StateGraph(SummaryState)
        # Nodes
        .add_node("load_conversation", load_conversation_node)
        .add_node("emotional_summary", emotional_summary_node)
        .add_node("technical_summary", technical_summary_node)
        .add_node("write_output", write_output_node)
        # Edges
        .add_edge(START, "load_conversation")
        .add_edge("load_conversation", "emotional_summary")
        .add_edge("load_conversation", "technical_summary")
        .add_edge("emotional_summary", "write_output")
        .add_edge("technical_summary", "write_output")
        .add_edge("write_output", END)
        # Compile
        .compile()
    )


graph = build_graph()
