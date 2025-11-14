"""LangGraph agent for summarizing conversations with emotional and technical summaries."""

from src.agents.walkandlearn_summary.config import (
    MODELS,
    TECHNICAL_DISABLED,
    PRINT_SUMMARY_IN_CHAT,
    INPUT_FILE_PATH,
    OUTPUT_FILE_PATH,
    get_output_file_path_octarine,
)
from langchain.agents import create_agent
from langchain_core.messages import AIMessage, HumanMessage
from langgraph.graph import StateGraph, START, END, MessagesState

from src.agents.walkandlearn_summary.io import read_file, write_file, format_summary
from src.agents.walkandlearn_summary.prompts import (
    EMOTIONAL_SUMMARY_PROMPT,
    TECHNICAL_SUMMARY_PROMPT,
)


class SummaryState(MessagesState):
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
        return {"conversation": read_file(INPUT_FILE_PATH)}

    def emotional_summary_node(state: SummaryState) -> dict:
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
        formatted_summary = format_summary(
            state["emotional_summary"], state["technical_summary"]
        )
        formatted_summary_octarine = format_summary(
            state["emotional_summary"], state["technical_summary"], for_octarine=True
        )

        write_file(OUTPUT_FILE_PATH, formatted_summary)
        write_file(get_output_file_path_octarine(), formatted_summary_octarine)

        return (
            {"messages": [AIMessage(content=formatted_summary)]}
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
