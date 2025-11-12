"""A super simple LangGraph agent example."""

from langchain.agents import create_agent
from langchain_openai import ChatOpenAI
from langchain_core.tools import tool


# Define tools
@tool
def add(a: int, b: int) -> int:
    """Add two numbers together."""
    return a + b


@tool
def multiply(a: int, b: int) -> int:
    """Multiply two numbers together."""
    return a * b


@tool
def subtract(a: int, b: int) -> int:
    """Subtract b from a."""
    return a - b


# Create the agent using create_agent with tools
graph = create_agent(
    model=ChatOpenAI(model="gpt-4o-mini", temperature=0),
    tools=[add, multiply, subtract],
    system_prompt="You are a helpful assistant that performs arithmetic operations. "
    "Use the available tools to solve math problems.",
)
