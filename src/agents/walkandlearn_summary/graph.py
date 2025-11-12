"""LangGraph agent for summarizing conversations with emotional and technical summaries."""

from pathlib import Path
from typing_extensions import TypedDict

from langchain.agents import create_agent
from langchain.chat_models import init_chat_model
from langchain_core.messages import HumanMessage
from langgraph.graph import StateGraph, START, END, MessagesState


# Define custom state extending MessagesState
class SummaryState(MessagesState):
    """State for the summarization workflow."""

    conversation: str
    emotional_summary: str
    technical_summary: str


# Initialize the model (cheap model for experimentation)
model = init_chat_model("gpt-4o-mini", temperature=0)


# Create agents for summarization
emotional_agent = create_agent(
    model=model,
    tools=[],
    system_prompt="""You are the emotional summary agent.
    
TODO: Replace this placeholder with the actual system prompt for emotional summarization.""",
)

technical_agent = create_agent(
    model=model,
    tools=[],
    system_prompt="""You are the technical summary agent.
    
TODO: Replace this placeholder with the actual system prompt for technical summarization.""",
)


# Node functions
def load_conversation_node(state: SummaryState) -> dict:
    """Load conversation from file.

    TODO: Replace placeholder path with actual file path.
    """
    # Placeholder file path - replace with actual path
    file_path = Path("TODO_INPUT_FILE_PATH.txt")

    # Read the conversation from file
    try:
        with open(file_path, "r", encoding="utf-8") as f:
            conversation = f.read()
    except FileNotFoundError:
        conversation = "File not found. Please set the correct file path."

    return {"conversation": conversation}


def emotional_summary_node(state: SummaryState) -> dict:
    """Generate emotional summary using the emotional agent."""
    conversation = state["conversation"]

    # Invoke the emotional agent with the conversation
    result = emotional_agent.invoke(
        {
            "messages": [
                HumanMessage(
                    content=f"Please provide an emotional summary of the following conversation:\n\n{conversation}"
                )
            ]
        }
    )

    # Extract the summary from the agent's response
    emotional_summary = result["messages"][-1].content

    return {"emotional_summary": emotional_summary}


def technical_summary_node(state: SummaryState) -> dict:
    """Generate technical summary using the technical agent.

    NOTE: Currently returns a placeholder to save API costs during development.
    Uncomment the code below to enable the actual technical agent.
    """
    # Placeholder response to avoid API costs
    return {
        "technical_summary": "[Technical summary placeholder - agent commented out for cost savings]"
    }

    # TODO: Uncomment below to enable technical agent
    # conversation = state["conversation"]
    #
    # # Invoke the technical agent with the conversation
    # result = technical_agent.invoke({
    #     "messages": [HumanMessage(content=f"Please provide a technical summary of the following conversation:\n\n{conversation}")]
    # })
    #
    # # Extract the summary from the agent's response
    # technical_summary = result["messages"][-1].content
    #
    # return {"technical_summary": technical_summary}


def write_output_node(state: SummaryState) -> dict:
    """Write the summaries to a markdown file.

    TODO: Replace placeholder path with actual output file path.
    """
    emotional_summary = state["emotional_summary"]
    technical_summary = state["technical_summary"]

    # Format the output as markdown
    output_content = f"""# Emotional Summary

{emotional_summary}



================================================================
================================================================



# Technical Summary

{technical_summary}
"""

    # Placeholder output file path - replace with actual path
    output_path = Path("TODO_OUTPUT_FILE_PATH.md")

    # Write to file
    with open(output_path, "w", encoding="utf-8") as f:
        f.write(output_content)

    return {}


# Build the graph
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

# TODO: Consider using structured output pattern in LangGraph for better control over summary format
# See: https://docs.langchain.com/oss/python/langgraph/ for structured output examples
