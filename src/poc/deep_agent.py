"""A deep LangGraph agent example with tools and conditional logic."""

from pathlib import Path

from deepagents import create_deep_agent
from deepagents.backends import FilesystemBackend
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


# Configure filesystem backend to save files in ./agent_files
agent_files_dir = Path(__file__).parent.parent.parent / "agent_files"
agent_files_dir.mkdir(exist_ok=True)
backend = FilesystemBackend(root_dir=str(agent_files_dir.absolute()), virtual_mode=True)

# Create the deep agent using create_deep_agent with tools
# Deep agents have unique capabilities: planning (write_todos), filesystem (ls, read_file, write_file, edit_file), and subagents (task)
graph = create_deep_agent(
    model=ChatOpenAI(model="gpt-5-mini"),
    tools=[add, multiply, subtract],
    backend=backend,
    system_prompt="""
    You are a helpful assistant that performs arithmetic operations.
    Use the available tools to solve math problems.
    Write intermediate steps and results to a file.
    """,
)
