import uuid
from pathlib import Path
from typing import Iterator, List, Tuple, Optional, Dict, Any, Set
from enum import Enum
import re
import json

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

# Define agent capabilities and roles for better role awareness
AGENT_CAPABILITIES = {
    "triage": {
        "description": "General purpose triage agent that can handle basic queries and route to specialized agents",
        "can_handle": ["general_queries", "routing", "meta_requests"],
        "cannot_handle": []
    },
    "agent_a": {
        "description": "Specialized agent A",
        "can_handle": ["agent_a_specific_tasks"],
        "cannot_handle": ["agent_b_specific_tasks"]
    },
    "agent_b": {
        "description": "Specialized agent B",
        "can_handle": ["agent_b_specific_tasks"],
        "cannot_handle": ["agent_a_specific_tasks"]
    }
}

# Request types for intent classification
class RequestType(Enum):
    GENERAL_QUERY = "general_query"
    AGENT_REQUEST = "agent_request"
    META_REQUEST = "meta_request"
    MULTI_INTENT = "multi_intent"

# Patterns for detecting agent references and requests
AGENT_REFERENCE_PATTERNS = {
    "agent_a": [r"(?i)agent\s*a\b", r"(?i)\bagent\s*a\b", r"(?i)\ba\b"],
    "agent_b": [r"(?i)agent\s*b\b", r"(?i)\bagent\s*b\b", r"(?i)\bb\b"],
    "triage": [r"(?i)triage", r"(?i)main agent", r"(?i)first agent"],
    "previous": [r"(?i)previous agent", r"(?i)last agent", r"(?i)go back", r"(?i)other agent"],
}

# Meta-request patterns
META_REQUEST_PATTERNS = [
    r"(?i)tell\s+(agent\s*[ab]|the\s+other\s+agent)",
    r"(?i)ask\s+(agent\s*[ab]|the\s+other\s+agent)",
    r"(?i)what\s+did\s+(agent\s*[ab]|the\s+other\s+agent)\s+say",
    r"(?i)who\s+(handled|answered|responded)",
]

# Handoff request patterns
HANDOFF_REQUEST_PATTERNS = [
    r"(?i)(connect|switch|transfer|hand\s*off|talk)\s+(me\s+)?(to|with)?\s+(agent\s*[ab]|triage)",
    r"(?i)I\s+(want|need|would\s+like)\s+to\s+(talk|speak|connect)\s+(to|with)\s+(agent\s*[ab]|triage)",
]


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
            You are a triage agent. 
            You handoff queries to either agent A or agent B based on their specialties.
            Agent A handles: agent_a_specific_tasks
            Agent B handles: agent_b_specific_tasks
            
            If the user doesn't specifically request to talk to agent A or agent B, you should handle the query yourself.
            "A" refers to "Agent A" and "B" refers to "Agent B".
            
            If a user message contains multiple requests or is ambiguous, ask for clarification.
            If a user asks about what another agent said, refer to the conversation history.
            """,
            instructions=[
                "You start all your answers with 'Triage: '",
                "When handling a handoff, explain to the user that you're connecting them to the appropriate agent",
                "If a user asks about previous conversations, refer to the conversation history",
            ],
            tools=[
                self.handoff_to_specialized_agents,
                self.handle_multi_agent_request,
                self.clarify_ambiguous_request
            ],
            storage=get_storage("triage"),
            add_history_to_messages=True,
            num_history_responses=10,
            debug_mode=DEBUG,
        )

        self.agent_a = Agent(
            name="Agent A",
            model=get_model(),
            description="""
            You are agent A, also referred to as simply 'A'.
            You specialize in agent_a_specific_tasks.
            You cannot handle agent_b_specific_tasks and should refer those to Agent B.
            
            If a user asks about what another agent said, refer to the conversation history.
            """,
            instructions=[
                "You start all your answers with 'Agent A: '",
                "You only hand off to the triage agent IF the user specifically asks for it, or if they ask to speak to another agent that's not you.",
                "Do not greet the user upon first talking to them",
                "When handling a handoff, explain to the user that you're connecting them to the appropriate agent",
                "If a user asks about previous conversations, refer to the conversation history",
            ],
            tools=[
                self.handoff_back_to_triage,
                self.handoff_to_other_agent,
                self.relay_message_to_agent
            ],
            storage=get_storage("agent_a"),
            add_history_to_messages=True,
            num_history_responses=10,
            debug_mode=DEBUG,
        )

        self.agent_b = Agent(
            name="Agent B",
            model=get_model(),
            description="""
            You are agent B, also referred to as simply 'B'.
            You specialize in agent_b_specific_tasks.
            You cannot handle agent_a_specific_tasks and should refer those to Agent A.
            
            If a user asks about what another agent said, refer to the conversation history.
            """,
            instructions=[
                "You start all your answers with 'Agent B: '",
                "You only hand off to the triage agent IF the user specifically asks for it, or if they ask to speak to another agent that's not you.",
                "Do not greet the user upon first talking to them",
                "When handling a handoff, explain to the user that you're connecting them to the appropriate agent",
                "If a user asks about previous conversations, refer to the conversation history",
            ],
            tools=[
                self.handoff_back_to_triage,
                self.handoff_to_other_agent,
                self.relay_message_to_agent
            ],
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
            
    def parse_user_intent(self, user_message: str) -> Dict[str, Any]:
        """
        Parse the user's message to identify intents, agent references, and potential handoffs.
        Returns a dictionary with parsed intent information.
        """
        intent_info = {
            "type": RequestType.GENERAL_QUERY,
            "agent_references": [],
            "handoff_requests": [],
            "meta_requests": [],
            "clarification_needed": False,
            "multiple_intents": False,
            "original_message": user_message,
            "parsed_intents": []
        }
        
        # Check for agent references
        for agent_name, patterns in AGENT_REFERENCE_PATTERNS.items():
            for pattern in patterns:
                if re.search(pattern, user_message):
                    if agent_name not in intent_info["agent_references"]:
                        intent_info["agent_references"].append(agent_name)
        
        # Check for handoff requests
        for pattern in HANDOFF_REQUEST_PATTERNS:
            matches = re.findall(pattern, user_message)
            if matches:
                intent_info["type"] = RequestType.AGENT_REQUEST
                intent_info["handoff_requests"].append(matches)
        
        # Check for meta-requests
        for pattern in META_REQUEST_PATTERNS:
            if re.search(pattern, user_message):
                intent_info["type"] = RequestType.META_REQUEST
                intent_info["meta_requests"].append(pattern)
        
        # Check for multiple intents (simple sentence splitting)
        sentences = re.split(r'[.!?]\s+', user_message)
        if len(sentences) > 1:
            # Check if different sentences have different intents
            sentence_intents = []
            for sentence in sentences:
                if sentence.strip():  # Skip empty sentences
                    sentence_intent = self.parse_user_intent(sentence)
                    if sentence_intent["type"] != RequestType.GENERAL_QUERY:
                        sentence_intents.append(sentence_intent)
            
            if len(sentence_intents) > 1:
                intent_info["type"] = RequestType.MULTI_INTENT
                intent_info["multiple_intents"] = True
                intent_info["parsed_intents"] = sentence_intents
        
        # Check if clarification is needed
        if len(intent_info["agent_references"]) > 1 and "previous" in intent_info["agent_references"]:
            intent_info["clarification_needed"] = True
        
        return intent_info
    
    def resolve_agent_reference(self, reference: str) -> str:
        """
        Resolve ambiguous agent references like "the other agent" or "previous agent"
        """
        if reference == "previous":
            return self.session_state.get("previous_agent", "triage")
        return reference
    
    def get_agent_conversation_history(self, agent_name: str) -> str:
        """
        Get a summary of the conversation history with a specific agent
        """
        agent = self.agents.get(agent_name)
        if not agent:
            return "No conversation history found for this agent."
        
        summary = agent.memory.update_summary()
        return summary
    
    def _handoff_to_agents(self, agent_name):
        if agent_name not in ["agent_a", "agent_b", "triage"]:
            return "Error: Invalid agent name. The agent name must be 'agent_a' or 'agent_b'."

        if self.session_state["just_handed_off"]:
            return "Error: You can only hand off once per query."
        self.session_state["just_handed_off"] = True

        self.session_state["previous_agent"] = self.session_state["current_agent"]
        self.session_state["current_agent"] = agent_name
        LOGGER.info(f"Handing off to {agent_name}")
        
        # Add transition message for better user experience
        agent_display_name = self.agents[agent_name].name
        return f"The conversation will be handed over to {agent_display_name}. No need to respond!"

    def handoff_to_specialized_agents(self, agent_name):
        """
        Hand off to the specified agent.
        :param agent_name: 'agent_a' or 'agent_b'
        :return: Success or Error message
        """
        if agent_name not in ["agent_a", "agent_b"]:
            return "Error: Invalid agent name. The agent name must be 'agent_a' or 'agent_b'."
        return self._handoff_to_agents(agent_name)

    def handoff_to_other_agent(self, agent_name):
        """
        Hand off to another specialized agent directly (without going through triage)
        :param agent_name: 'agent_a' or 'agent_b'
        :return: Success or Error message
        """
        if agent_name not in ["agent_a", "agent_b"]:
            return "Error: Invalid agent name. The agent name must be 'agent_a' or 'agent_b'."
        
        current_agent = self.session_state["current_agent"]
        if agent_name == current_agent:
            return f"Error: Already speaking with {agent_name}."
            
        return self._handoff_to_agents(agent_name)

    def handoff_back_to_triage(self):
        """
        Hand off to the triage agent. The triage agent is able to hand off queries to agent A or agent B.
        :return: Success or Error message
        """
        return self._handoff_to_agents("triage")
    
    def handle_multi_agent_request(self, primary_agent: str, secondary_agent: str, primary_message: str, secondary_message: str):
        """
        Handle a request that involves multiple agents
        :param primary_agent: The first agent to handle the request
        :param secondary_agent: The second agent to handle the request
        :param primary_message: The message for the primary agent
        :param secondary_message: The message for the secondary agent
        :return: Success or Error message
        """
        if primary_agent not in ["agent_a", "agent_b", "triage"] or secondary_agent not in ["agent_a", "agent_b", "triage"]:
            return "Error: Invalid agent name(s). Agent names must be 'agent_a', 'agent_b', or 'triage'."
        
        # Store the multi-agent request in session state for processing
        self.session_state["multi_agent_request"] = {
            "primary": {
                "agent": primary_agent,
                "message": primary_message
            },
            "secondary": {
                "agent": secondary_agent,
                "message": secondary_message
            },
            "processed": False
        }
        
        # Hand off to the primary agent first
        return self._handoff_to_agents(primary_agent)
    
    def clarify_ambiguous_request(self, ambiguity_type: str, options: List[str]):
        """
        Request clarification from the user for ambiguous requests
        :param ambiguity_type: The type of ambiguity (e.g., 'agent_reference', 'intent')
        :param options: List of possible options to present to the user
        :return: Clarification message
        """
        self.session_state["needs_clarification"] = {
            "type": ambiguity_type,
            "options": options
        }
        
        options_text = ", ".join([f"'{opt}'" for opt in options])
        return f"Clarification needed for {ambiguity_type}. Options: {options_text}"
    
    def relay_message_to_agent(self, target_agent: str, message: str):
        """
        Relay a message to another agent without fully handing off
        :param target_agent: The agent to relay the message to
        :param message: The message to relay
        :return: The response from the target agent
        """
        if target_agent not in ["agent_a", "agent_b", "triage"]:
            return "Error: Invalid agent name. The agent name must be 'agent_a', 'agent_b', or 'triage'."
        
        # Store current state
        current_agent = self.session_state["current_agent"]
        
        # Get response from target agent
        target = self.agents[target_agent]
        relay_message = f"""
        This is a relay message from {self.agents[current_agent].name}.
        Please respond to the following query without greeting the user:
        
        {message}
        """
        
        response = target.run(relay_message)
        content = response.content if hasattr(response, 'content') else str(response)
        
        # Format the relayed response
        return f"Relayed response from {target.name}: {content}"

    def run(self, user_message: str) -> Iterator[RunResponse]:
        self.session_state.setdefault("current_agent", "triage")
        self.session_state.setdefault("previous_agent", "triage")
        self.session_state.setdefault("just_handed_off", False)
        self.session_state.setdefault("summary", None)
        self.session_state.setdefault("conversation_history", {})
        self.session_state.setdefault("multi_agent_request", None)
        self.session_state.setdefault("needs_clarification", None)
        
        # Parse user intent to determine how to handle the request
        intent_info = self.parse_user_intent(user_message)
        LOGGER.info(f"Parsed intent: {intent_info}")
        
        # Check if we need clarification before proceeding
        if intent_info["clarification_needed"]:
            current_agent = self.agents[self.session_state["current_agent"]]
            clarification_message = f"""
            The user's request is ambiguous. They mentioned multiple agents or used ambiguous references.
            Original message: "{user_message}"
            
            Please ask for clarification about which agent they want to interact with.
            """
            clarification_response = current_agent.run(clarification_message)
            yield clarification_response
            return
            
        # Handle multi-intent requests
        if intent_info["type"] == RequestType.MULTI_INTENT:
            LOGGER.info("Handling multi-intent request")
            # Process the first intent
            first_intent = intent_info["parsed_intents"][0] if intent_info["parsed_intents"] else None
            if first_intent and first_intent["type"] == RequestType.AGENT_REQUEST:
                # If first intent is a handoff request, process it
                agent_refs = first_intent.get("agent_references", [])
                target_agent = agent_refs[0] if agent_refs else None
                if target_agent and target_agent != "previous":
                    # Store the remaining intents for processing after handoff
                    self.session_state["pending_intents"] = intent_info["parsed_intents"][1:]
                    # Perform the handoff
                    self._handoff_to_agents(target_agent)
                    
            # If no handoff in first intent, let the current agent handle it with awareness of multiple intents
            current_agent = self.agents[self.session_state["current_agent"]]
            multi_intent_message = f"""
            The user has multiple requests in their message:
            "{user_message}"
            
            Please address each part of their request separately and clearly.
            """
            resp = current_agent.run(multi_intent_message)
            yield resp
            return
            
        # Handle meta-requests about other agents
        if intent_info["type"] == RequestType.META_REQUEST:
            LOGGER.info("Handling meta-request")
            current_agent = self.agents[self.session_state["current_agent"]]
            
            # If asking about what another agent said
            if any("what did" in meta for meta in intent_info["meta_requests"]):
                # Find which agent they're asking about
                target_agent = None
                for agent_ref in intent_info.get("agent_references", []):
                    if agent_ref != self.session_state["current_agent"] and agent_ref != "previous":
                        target_agent = agent_ref
                
                if target_agent:
                    # Get conversation history for that agent
                    history = self.get_agent_conversation_history(target_agent)
                    meta_response_message = f"""
                    The user is asking about what {self.agents[target_agent].name} said.
                    Here is the conversation history with that agent:
                    
                    {history}
                    
                    Please summarize this information to answer the user's question: "{user_message}"
                    """
                    resp = current_agent.run(meta_response_message)
                    yield resp
                    return
            
            # If asking to relay a message to another agent
            if any(word in " ".join(intent_info["meta_requests"]) for word in ["tell", "ask"]):
                # Find which agent they're asking to relay to
                target_agent = None
                for agent_ref in intent_info.get("agent_references", []):
                    if agent_ref != self.session_state["current_agent"] and agent_ref != "previous":
                        target_agent = agent_ref
                
                if target_agent:
                    # Extract the message to relay (simple approach)
                    relay_message = user_message
                    for pattern in META_REQUEST_PATTERNS:
                        relay_message = re.sub(pattern, "", relay_message).strip()
                    
                    # Use the relay_message_to_agent tool
                    relay_response = self.relay_message_to_agent(target_agent, relay_message)
                    
                    # Format a response that includes the relay
                    relay_wrapper_message = f"""
                    The user asked you to relay a message to {self.agents[target_agent].name}.
                    You relayed: "{relay_message}"
                    
                    Here is the response:
                    {relay_response}
                    
                    Please format this information in a user-friendly way.
                    """
                    resp = current_agent.run(relay_wrapper_message)
                    yield resp
                    return
        
        # Handle direct handoff requests
        if intent_info["type"] == RequestType.AGENT_REQUEST and intent_info["agent_references"]:
            target_agent = None
            
            # Resolve references like "previous agent" or "other agent"
            for agent_ref in intent_info["agent_references"]:
                if agent_ref == "previous":
                    target_agent = self.resolve_agent_reference(agent_ref)
                else:
                    target_agent = agent_ref
                break
            
            if target_agent and target_agent != self.session_state["current_agent"]:
                # Run the handoff
                self._handoff_to_agents(target_agent)
        
        # Run the initial agent with enhanced context
        resp = self._run_current_agent(user_message, intent_info)
        if not self.session_state["just_handed_off"]:
            LOGGER.info("Not handed off")
            yield resp

        # If there was a handoff, run the new agent with context preservation
        while self.session_state["just_handed_off"]:
            self.session_state["just_handed_off"] = False
            previous_agent: Agent = self.agents[self.session_state["previous_agent"]]
            current_agent: Agent = self.agents[self.session_state["current_agent"]]

            # Get conversation summary from previous agent
            summary = previous_agent.memory.update_summary()
            LOGGER.info(f"Summary of previous conversation: {summary}")
            self.session_state["summary"] = summary
            
            # Store in conversation history for future reference
            if self.session_state["previous_agent"] not in self.session_state["conversation_history"]:
                self.session_state["conversation_history"][self.session_state["previous_agent"]] = []
            
            self.session_state["conversation_history"][self.session_state["previous_agent"]].append({
                "timestamp": str(uuid.uuid4()),  # Simple timestamp for ordering
                "summary": summary,
                "last_message": user_message
            })

            # Create an enhanced handoff message with better context
            handoff_message = f"""
            You've been handed off this conversation from {previous_agent.name}.
            
            <previous_conversation_summary>
            {summary}
            </previous_conversation_summary>
            
            <last_user_message>
            {user_message}
            </last_user_message>
            
            Please respond to the user's request. If their question has already been answered in the previous conversation,
            acknowledge that and provide additional information if appropriate.
            
            If the user asked about what was discussed with {previous_agent.name}, refer to the conversation summary.
            """
            
            # Check if there's a pending multi-agent request
            if self.session_state.get("multi_agent_request") and not self.session_state["multi_agent_request"].get("processed"):
                multi_req = self.session_state["multi_agent_request"]
                if multi_req["primary"]["agent"] == self.session_state["current_agent"]:
                    # Add the primary message to the handoff
                    handoff_message += f"""
                    
                    The user specifically wanted you to address this: {multi_req["primary"]["message"]}
                    """
                    # Mark as processed
                    multi_req["processed"] = True
                    # Set up for secondary agent if needed
                    if not self.session_state["just_handed_off"]:
                        self.session_state["just_handed_off"] = True
                        self.session_state["previous_agent"] = self.session_state["current_agent"]
                        self.session_state["current_agent"] = multi_req["secondary"]["agent"]
            
            # Check for pending intents from a multi-intent message
            if self.session_state.get("pending_intents"):
                pending = self.session_state["pending_intents"]
                if pending:
                    handoff_message += f"""
                    
                    The user also had these additional requests:
                    """
                    for intent in pending:
                        handoff_message += f"""
                        - {intent.get('original_message', '')}
                        """
                    # Clear pending intents
                    self.session_state["pending_intents"] = []
            
            LOGGER.info(f"Running agent: {current_agent.name}")
            resp = current_agent.run(handoff_message)
            if not self.session_state["just_handed_off"]:
                yield resp

    def _run_current_agent(self, user_message: str, intent_info=None) -> RunResponse:
        current_agent = self.agents[self.session_state["current_agent"]]
        LOGGER.info(f"Running agent: {current_agent.name}")
        
        # If we have intent info, enhance the message with context
        if intent_info:
            enhanced_message = user_message
            
            # If there are references to previous conversations
            if intent_info.get("meta_requests") and any("what did" in meta for meta in intent_info["meta_requests"]):
                # Find which agent they're asking about
                for agent_ref in intent_info.get("agent_references", []):
                    if agent_ref != self.session_state["current_agent"]:
                        # Get that agent's conversation history
                        history = self.get_agent_conversation_history(agent_ref)
                        enhanced_message = f"""
                        The user is asking about previous conversations with {self.agents[agent_ref].name}.
                        Here is the relevant conversation history:
                        
                        {history}
                        
                        User's question: {user_message}
                        
                        Please use this context to answer their question.
                        """
                        break
            
            # If the user needs clarification about agent capabilities
            if any("what can" in user_message.lower() or "what do" in user_message.lower() for agent_ref in intent_info.get("agent_references", [])):
                for agent_ref in intent_info.get("agent_references", []):
                    if agent_ref in AGENT_CAPABILITIES:
                        capabilities = AGENT_CAPABILITIES[agent_ref]
                        enhanced_message = f"""
                        The user is asking about {self.agents[agent_ref].name}'s capabilities.
                        
                        Here are the capabilities:
                        Description: {capabilities['description']}
                        Can handle: {', '.join(capabilities['can_handle'])}
                        Cannot handle: {', '.join(capabilities['cannot_handle'])}
                        
                        User's question: {user_message}
                        
                        Please use this information to answer their question.
                        """
                        break
            
            return current_agent.run(enhanced_message)
        else:
            return current_agent.run(user_message)


def human_input_generator():
    while True:
        msg = input("User: ")
        if msg == "exit":
            break
        yield msg


USE_CASES = {
    "human": human_input_generator(),
    "First A then B": [
        "I want to talk to A",
        "Who are you?",
        "What is the capital of France?",
        "I want to talk to B, please hand off",
        "Who are you?",
        "I want to talk to A again, please hand off",
        "What did we talk about?",
    ],
    "Question for Triage, and then handoff to A": [
        "What is the capital of France?",
        "I want to talk to A",
        "What's the best way to cook a steak?",
    ],
    "Multi-intent request": [
        "I want to talk to Agent A about cooking and then ask Agent B about travel",
    ],
    "Meta-communication": [
        "I want to talk to Agent A",
        "What's your favorite recipe?",
        "Now tell Agent B I need travel recommendations",
    ],
    "Ambiguous reference resolution": [
        "I want to talk to Agent A",
        "What's your specialty?",
        "I want to talk to Agent B",
        "What's your specialty?",
        "I want to talk to the previous agent",
    ],
    "Context preservation": [
        "I want to talk to Agent A",
        "What's the best way to make pasta?",
        "I want to talk to Agent B",
        "What did Agent A say about pasta?",
    ],
    "Clarification workflow": [
        "Can you tell the other agent something?",
    ],
    "Agent capability awareness": [
        "What can Agent A do?",
        "What can Agent B do?",
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
