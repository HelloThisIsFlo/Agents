import uuid
from pathlib import Path
from typing import Iterator, List, Tuple, Optional
import json
from datetime import datetime

from agno.agent import Agent
from agno.models.message import Message
from agno.playground import serve_playground_app, Playground
from agno.storage.agent.sqlite import SqliteAgentStorage
from agno.storage.workflow.sqlite import SqliteWorkflowStorage
from agno.utils.log import get_logger
from agno.utils.pprint import pprint_run_response
from agno.workflow import Workflow, RunResponse
from dotenv import load_dotenv
from rich import print
from rich.box import HEAVY
from rich.panel import Panel

from agents.common import get_model

LOGGER = get_logger(__name__)

load_dotenv()

SCRIPT_DIR = Path(__file__).resolve().parent
SQLITE_DB = str(SCRIPT_DIR / "tmp/agent_storage.db")

DEBUG = False


def patched_get_message_pairs(
    self, user_role: str = "user", assistant_role: Optional[List[str]] = None
) -> List[Tuple[Message, Message]]:
    """Returns a list of tuples of (user message, assistant response)."""

    if assistant_role is None:
        assistant_role = ["assistant", "model", "CHATBOT"]

    runs_as_message_pairs: List[Tuple[Message, Message]] = []
    for run in self.runs:
        if run.response and run.response.messages:
            user_messages_from_run = None
            assistant_messages_from_run = None

            # Start from the END <- HOTFIX to look for the user message
            for message in run.response.messages[::-1]:
                if message.role == user_role:
                    user_messages_from_run = message
                    break

            # Start from the end to look for the assistant response
            for message in run.response.messages[::-1]:
                if message.role in assistant_role:
                    assistant_messages_from_run = message
                    break

            if user_messages_from_run and assistant_messages_from_run:
                runs_as_message_pairs.append(
                    (user_messages_from_run, assistant_messages_from_run)
                )
    return runs_as_message_pairs


def get_storage(agent_name: str, workflow=False):
    if workflow:
        return SqliteWorkflowStorage(
            table_name=f"{__name__}_{agent_name}_sessions",
            db_file=SQLITE_DB,
        )
    else:
        return SqliteAgentStorage(
            table_name=f"chatbot_{agent_name}_sessions",
            db_file=SQLITE_DB,
        )


class HandoffExperiment(Workflow):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)

        self.triage = Agent(
            name="Triage Agent",
            model=get_model(),
            description="""
            You are a triage agent responsible for managing complex user requests and coordinating between specialized agents.
            Your key responsibilities:
            1. Handle general queries that don't require specialized agents
            2. Detect and parse multi-intent requests (e.g., "Talk to Agent A about X and Agent B about Y")
            3. Handle meta-communication (e.g., "Tell Agent B about this", "What did Agent A say earlier?")
            4. Manage ambiguous agent references (e.g., "the other agent", "him", "her")
            5. Prioritize and sequence multiple requests appropriately
            6. Maintain context across handoffs and ensure smooth transitions
            
            When handling requests:
            - If a request is clear and single-intent, handle it directly or hand off to the appropriate agent
            - If a request has multiple intents, break it down and handle each part sequentially
            - If a request is ambiguous, ask for clarification before proceeding
            - If a request references previous conversations, ensure relevant context is preserved
            - If a request is out of scope for all agents, explain why and suggest alternatives
            
            Remember: Your goal is to provide a seamless experience while ensuring each request is handled by the most appropriate agent(s).
            """,
            instructions=[
                "You start all your answers with 'Triage: '",
                "When handling multiple requests, acknowledge each part and explain your approach",
                "If a request is ambiguous, ask clarifying questions before proceeding",
                "When handing off, provide relevant context to the receiving agent",
                "Maintain a professional and helpful tone throughout",
            ],
            tools=[self.handoff_to_specialized_agents],
            storage=get_storage("triage"),
            add_history_to_messages=True,
            num_history_responses=10,
            debug_mode=DEBUG,
        )

        self.agent_a = Agent(
            name="Agent A",
            model=get_model(),
            description="""
            You are Agent A, a specialized agent with expertise in specific domains.
            Your key responsibilities:
            1. Handle specialized queries within your domain
            2. Maintain context from previous interactions
            3. Recognize when a request is better handled by another agent
            4. Handle meta-requests about your capabilities or previous responses
            5. Work collaboratively with other agents when needed
            
            When handling requests:
            - Focus on your specialized domain
            - If a request is outside your scope, hand off to the triage agent
            - If a request references previous conversations, ensure you have the full context
            - If a request is ambiguous, ask for clarification
            - If a request involves multiple agents, coordinate through the triage agent
            
            Remember: Your goal is to provide expert assistance while ensuring smooth collaboration with other agents.
            """,
            instructions=[
                "You start all your answers with 'Agent A: '",
                "Clearly communicate your capabilities and limitations",
                "When handing off, explain why and suggest next steps",
                "Maintain context awareness across interactions",
                "Be proactive in identifying when collaboration is needed",
            ],
            tools=[self.handoff_back_to_triage],
            storage=get_storage("agent_a"),
            add_history_to_messages=True,
            num_history_responses=10,
            debug_mode=DEBUG,
        )

        self.agent_b = Agent(
            name="Agent B",
            model=get_model(),
            description="""
            You are Agent B, a specialized agent with expertise in specific domains.
            Your key responsibilities:
            1. Handle specialized queries within your domain
            2. Maintain context from previous interactions
            3. Recognize when a request is better handled by another agent
            4. Handle meta-requests about your capabilities or previous responses
            5. Work collaboratively with other agents when needed
            
            When handling requests:
            - Focus on your specialized domain
            - If a request is outside your scope, hand off to the triage agent
            - If a request references previous conversations, ensure you have the full context
            - If a request is ambiguous, ask for clarification
            - If a request involves multiple agents, coordinate through the triage agent
            
            Remember: Your goal is to provide expert assistance while ensuring smooth collaboration with other agents.
            """,
            instructions=[
                "You start all your answers with 'Agent B: '",
                "Clearly communicate your capabilities and limitations",
                "When handing off, explain why and suggest next steps",
                "Maintain context awareness across interactions",
                "Be proactive in identifying when collaboration is needed",
            ],
            tools=[self.handoff_back_to_triage],
            storage=get_storage("agent_b"),
            add_history_to_messages=True,
            num_history_responses=10,
            debug_mode=DEBUG,
        )

        self.agents = {
            "triage": self.triage,
            "agent_a": self.agent_a,
            "agent_b": self.agent_b,
        }

        # TMP: Hotfix
        for agent in self.agents.values():
            agent.initialize_agent()
            agent.memory.__class__.get_message_pairs = patched_get_message_pairs

    def _handoff_to_agents(self, agent_name):
        if agent_name not in ["agent_a", "agent_b", "triage"]:
            return "Error: Invalid agent name. The agent name must be 'agent_a' or 'agent_b'."

        if self.session_state["just_handed_off"]:
            return "Error: You can only hand off once per query."
        self.session_state["just_handed_off"] = True

        self.session_state["previous_agent"] = self.session_state["current_agent"]
        self.session_state["current_agent"] = agent_name
        
        # Track handoff history for context
        if "handoff_history" not in self.session_state:
            self.session_state["handoff_history"] = []
        self.session_state["handoff_history"].append({
            "from": self.session_state["previous_agent"],
            "to": agent_name,
            "timestamp": datetime.now().isoformat()
        })
        
        LOGGER.info(f"Handing off to {agent_name}")
        return f"The conversation will be handed over to {agent_name}. No need to respond!"

    def handoff_to_specialized_agents(self, agent_name):
        """
        Hand off to the specified agent.
        :param agent_name: 'agent_a' or 'agent_b'
        :return: Success or Error message
        """
        if agent_name not in ["agent_a", "agent_b"]:
            return "Error: Invalid agent name. The agent name must be 'agent_a' or 'agent_b'."
        return self._handoff_to_agents(agent_name)

    def handoff_back_to_triage(self):
        """
        Hand off to the triage agent. The triage agent is able to hand off queries to agent A or agent B.
        :return: Success or Error message
        """
        return self._handoff_to_agents("triage")

    def run(self, user_message: str) -> Iterator[RunResponse]:
        self.session_state.setdefault("current_agent", "triage")
        self.session_state.setdefault("previous_agent", "triage")
        self.session_state.setdefault("just_handed_off", False)
        self.session_state.setdefault("summary", None)
        self.session_state.setdefault("handoff_history", [])
        self.session_state.setdefault("conversation_context", {})

        # Run the initial agent
        resp = self._run_current_agent(user_message)
        if not self.session_state["just_handed_off"]:
            print("Not handed off")
            yield resp

        # If there was a handoff, run the new agent
        while self.session_state["just_handed_off"]:
            self.session_state["just_handed_off"] = False
            previous_agent: Agent = self.agents[self.session_state["previous_agent"]]
            current_agent: Agent = self.agents[self.session_state["current_agent"]]

            # Update conversation summary
            summary = previous_agent.memory.update_summary()
            LOGGER.info(f"Summary of previous conversation: {summary}")
            self.session_state["summary"] = summary

            # Build comprehensive context for the receiving agent
            handoff_message = f"""
            You've been handed off this conversation from {previous_agent.name}.
            Please consult the following information before answering:
            
            <conversation_summary>
            {summary}
            </conversation_summary>
            
            <handoff_history>
            {json.dumps(self.session_state["handoff_history"], indent=2)}
            </handoff_history>
            
            <conversation_context>
            {json.dumps(self.session_state["conversation_context"], indent=2)}
            </conversation_context>
            
            <last_user_message>
            {user_message}
            </last_user_message>
            
            <previous_agent_context>
            {previous_agent.name} was handling this conversation. Their last response was:
            {previous_agent.memory.get_last_response() if previous_agent.memory.get_last_response() else "No previous response"}
            </previous_agent_context>
            
            Please:
            1. Review the conversation summary and context
            2. Consider the handoff history to understand the flow
            3. Check if the user's question has already been answered
            4. Maintain consistency with previous responses
            5. If needed, ask for clarification about ambiguous points
            """
            
            LOGGER.info(f"Running agent: {current_agent.name}")
            resp = current_agent.run(handoff_message)
            
            # Update conversation context with the new response
            if resp and resp.content:
                self.session_state["conversation_context"].update({
                    "last_response": resp.content,
                    "last_agent": current_agent.name,
                    "timestamp": datetime.now().isoformat()
                })
            
            if not self.session_state["just_handed_off"]:
                yield resp

    def _run_current_agent(self, user_message: str) -> RunResponse:
        current_agent = self.agents[self.session_state["current_agent"]]
        LOGGER.info(f"Running agent: {current_agent.name}")
        
        # Add conversation context to the message
        context_message = f"""
        <conversation_context>
        {json.dumps(self.session_state.get("conversation_context", {}), indent=2)}
        </conversation_context>
        
        <handoff_history>
        {json.dumps(self.session_state.get("handoff_history", []), indent=2)}
        </handoff_history>
        
        {user_message}
        """
        
        return current_agent.run(context_message)


def human_input_generator():
    while True:
        msg = input("User: ")
        if msg == "exit":
            break
        yield msg


USE_CASES = {
    "human": human_input_generator(),
    "Complex Multi-Agent Scenario": [
        "I need help with both my order and billing",
        "Tell me about my order status",
        "What did Agent A say about my order?",
        "I want to discuss billing with Agent B",
        "Can you summarize what we've discussed so far?",
        "Tell Agent B about my order details",
        "What's the next step?",
    ],
    "Ambiguous References": [
        "The other agent mentioned something about shipping",
        "Can you tell him about my order?",
        "What did she say about the delivery time?",
        "I want to talk to someone else about this",
    ],
    "Meta-Communication": [
        "Tell Agent B what we discussed",
        "What did Agent A think about my request?",
        "Can you connect me with someone who knows about shipping?",
        "Who handled my last request?",
    ],
    "Context Preservation": [
        "I have a question about my order",
        "What's the status?",
        "Tell me about the shipping options",
        "What did we decide about delivery?",
        "Can you remind me what we discussed earlier?",
    ],
    "Mixed Intent Handling": [
        "I need help with my order and want to discuss billing",
        "Can you tell me about shipping options and connect me with billing?",
        "I have questions about both delivery and payment",
        "Let's talk about my order and then billing",
    ],
    "Clarification Scenarios": [
        "I want to talk to the other agent",
        "Can someone help me with this?",
        "Who should I talk to about this?",
        "Is this something you can help with?",
    ],
}


def run_in_cli():
    use_case = "human"
    # use_case = "Question for Triage, and then handoff to A"
    # use_case = "First A then B"
    for msg in USE_CASES[use_case]:
        print(
            Panel(
                msg,
                title="User Message",
                title_align="left",
                border_style="yellow",
                box=HEAVY,
                expand=True,
                padding=(1, 1),
            )
        )
        run_resp_stream = handoff_experiment.run(user_message=msg)
        pprint_run_response(run_resp_stream, markdown=True)

        print("")
        print("")
        print("")


def run_in_playground():
    serve_playground_app("agents.sandbox.handoff:app", reload=True)


uuid4 = uuid.uuid4()
handoff_experiment = HandoffExperiment(
    workflow_id="handoff-experiment",
    storage=get_storage("handoff-experiment", workflow=True),
    session_id=str(uuid4),
)
app = Playground(workflows=[handoff_experiment]).get_app()

if __name__ == "__main__":
    # Testing Hand-off in a workflow via tool calling

    run_in_cli()
    # run_in_playground()
