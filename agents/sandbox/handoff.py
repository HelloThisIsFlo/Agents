import uuid
from pathlib import Path
from typing import Iterator

from agno.agent import Agent
from agno.models.openai import OpenAIChat, OpenAILike
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

LOGGER = get_logger(__name__)

load_dotenv()

SCRIPT_DIR = Path(__file__).resolve().parent
SQLITE_DB = str(SCRIPT_DIR / "tmp/agent_storage.db")

DEBUG = False


def get_model():
    local = False
    if local:
        return OpenAILike(
            id="qwen2.5-7b-instruct-1m@q8_0",
            api_key="not-used",
            base_url="http://127.0.0.1:1234/v1",
        )
    else:
        return OpenAIChat(id="gpt-4o-mini")
        # return OpenAIChat(id="gpt-4o")


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
            You are a triage agent. You handoff queries to either agent A or agent B. Do not let the users you're handing off to another agent.
            """,
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
            You are agent A, also referred to as simply 'A'. You start all your answers with "I am agent A: ". Do not greet the user upon first talking to them.
            """,
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
            You are agent B, also referred to as simply 'B'. You start all your answers with "I am agent B: ". Do not greet the user upon first talking to them.
            """,
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

    def _handoff_to_agents(self, agent_name):
        if agent_name not in ["agent_a", "agent_b", "triage"]:
            return "Error: Invalid agent name. The agent name must be 'agent_a' or 'agent_b'."

        if self.session_state["just_handed_off"]:
            return "Error: You can only hand off once per query."
        self.session_state["just_handed_off"] = True

        self.session_state["previous_agent"] = self.session_state["current_agent"]
        self.session_state["current_agent"] = agent_name
        LOGGER.info(f"Handing off to {agent_name}")
        return f"Handed off to {agent_name}"

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

    def _run_current_agent(self, user_message: str) -> Iterator[RunResponse]:
        current_agent = self.session_state["current_agent"]
        LOGGER.info(f"Running agent: {current_agent}")

        if current_agent == "triage":
            yield from self._run_triage(user_message)
        elif current_agent == "agent_a":
            yield from self._run_agent_a(user_message)
        elif current_agent == "agent_b":
            yield from self._run_agent_b(user_message)
        else:
            raise ValueError(f"Unknown agent: {current_agent}")

    def run(self, user_message: str) -> Iterator[RunResponse]:
        self.session_state.setdefault("current_agent", "triage")
        self.session_state.setdefault("previous_agent", "triage")
        self.session_state.setdefault("just_handed_off", False)

        # Run the initial agent
        yield from self._run_current_agent(user_message)

        # If there was a handoff, run the new agent
        while self.session_state["just_handed_off"]:
            self.session_state["just_handed_off"] = False
            previous_agent: Agent = self.agents[self.session_state["previous_agent"]]
            current_agent: Agent = self.agents[self.session_state["current_agent"]]

            # yield current_agent.create_run_response(content="\n\n")
            summary = previous_agent.memory.update_summary()
            LOGGER.info(f"Summary of previous conversation: {summary}")
            yield from self._run_current_agent(
                f"""
                You've been handed off this conversation between the user and {current_agent.name}. 
                Please consult the summary and take it from there.
                
                <summary>
                {summary}
                </summary>
                """
            )

    def _run_triage(self, message: str) -> Iterator[RunResponse]:
        yield from self.triage.run(message, stream=True)

    def _run_agent_a(self, message: str) -> Iterator[RunResponse]:
        yield from self.agent_a.run(message, stream=True)

    def _run_agent_b(self, message: str) -> Iterator[RunResponse]:
        yield from self.agent_b.run(message, stream=True)


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
        "I want to talk to B",
        "Who are you?",
    ],
}


def run_in_cli():
    # use_case = "maintenance"
    # use_case = "onboarding"
    # use_case = "jailbreak_attempt"
    use_case = "human"
    use_case = "First A then B"
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
