"""Summary generation functions."""

from langchain_core.messages import HumanMessage


def generate_summary_with_agent(agent, conversation: str) -> str:
    """Generate a summary using the provided agent.

    Args:
        agent: The LangChain agent to use for generation
        conversation: The conversation text to summarize

    Returns:
        The generated summary as a string
    """
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
