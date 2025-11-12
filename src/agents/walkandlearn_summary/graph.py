"""LangGraph agent for summarizing conversations with emotional and technical summaries."""

from pathlib import Path
from typing_extensions import TypedDict

from langchain.agents import create_agent
from langchain.chat_models import init_chat_model
from langchain_core.messages import HumanMessage
from langgraph.graph import StateGraph, START, END, MessagesState


MODEL_NAME = "gpt-4o-mini"
MODEL_TEMPERATURE = 0

INPUT_FILE_PATH = "TODO_INPUT_FILE_PATH.txt"  # TODO: Replace with actual input file path
OUTPUT_FILE_PATH = "TODO_OUTPUT_FILE_PATH.md"  # TODO: Replace with actual output file path

EMOTIONAL_SUMMARY_PROMPT = """You are the emotional summary agent.

TODO: Replace this placeholder with the actual system prompt for emotional summarization."""

TECHNICAL_SUMMARY_PROMPT = """You are the technical summary agent.

TODO: Replace this placeholder with the actual system prompt for technical summarization."""


class SummaryState(MessagesState):
    conversation: str
    emotional_summary: str
    technical_summary: str


model = init_chat_model(MODEL_NAME, temperature=MODEL_TEMPERATURE)

emotional_agent = create_agent(
    model=model,
    tools=[],
    system_prompt=EMOTIONAL_SUMMARY_PROMPT
)

technical_agent = create_agent(
    model=model,
    tools=[],
    system_prompt=TECHNICAL_SUMMARY_PROMPT
)


def _read_file(file_path: str) -> str:
    try:
        with open(Path(file_path), "r", encoding="utf-8") as f:
            return f.read()
    except FileNotFoundError:
        return f"File not found: {file_path}. Please set the correct file path in the configuration constants."


def _write_file(file_path: str, content: str) -> None:
    with open(Path(file_path), "w", encoding="utf-8") as f:
        f.write(content)


def load_conversation_node(state: SummaryState) -> dict:
    return {"conversation": _read_file(INPUT_FILE_PATH)}


def emotional_summary_node(state: SummaryState) -> dict:
    result = emotional_agent.invoke({
        "messages": [HumanMessage(content=f"Please provide an emotional summary of the following conversation:\n\n{state['conversation']}")]
    })
    return {"emotional_summary": result["messages"][-1].content}


def technical_summary_node(state: SummaryState) -> dict:
    # TODO: Uncomment below to enable technical agent (currently placeholder to save API costs)
    return {"technical_summary": "[Technical summary placeholder - agent commented out for cost savings]"}
    
    # result = technical_agent.invoke({
    #     "messages": [HumanMessage(content=f"Please provide a technical summary of the following conversation:\n\n{state['conversation']}")]
    # })
    # return {"technical_summary": result["messages"][-1].content}


def write_output_node(state: SummaryState) -> dict:
    content = f"""# Emotional Summary

{state['emotional_summary']}



================================================================
================================================================



# Technical Summary

{state['technical_summary']}
"""
    _write_file(OUTPUT_FILE_PATH, content)
    return {}


graph = (
    StateGraph(SummaryState)

    .add_node("load_conversation", load_conversation_node)
    .add_node("emotional_summary", emotional_summary_node)
    .add_node("technical_summary", technical_summary_node)
    .add_node("write_output", write_output_node)

    .add_edge(START, "load_conversation")
    .add_edge("load_conversation", "emotional_summary")
    .add_edge("load_conversation", "technical_summary")
    .add_edge("emotional_summary", "write_output")
    .add_edge("technical_summary", "write_output")
    .add_edge("write_output", END)

    .compile()
)
