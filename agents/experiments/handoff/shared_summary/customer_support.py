from agno.agent import Agent

from agents.common import get_model, get_storage

print(__name__)

DEBUG = False

Agent(
    name="Triage Agent",
    model=get_model(),
    description="""
            You are a triage agent. 
            You handoff queries to either agent A or agent B. 
            However, if the user doesn't specifically request to talk to agent A or agent B, you should handle the query yourself.
            Of course "A" refers to "Agent A" and "B" refers to "Agent B".
            Do not let the users know you're handing off to another agent, do it silently.
            """,
    # tools=[],
    storage=get_storage("customer_support", "triage"),
    add_history_to_messages=True,
    num_history_responses=10,
    debug_mode=DEBUG,
)


"""
Each agent can:
- 
"""
