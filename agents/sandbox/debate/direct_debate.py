from textwrap import dedent

from agno.agent import Agent
from agno.playground import Playground
from agno.run.response import RunResponse
from agno.utils.log import logger
from agno.utils.pprint import pprint_run_response
from agno.workflow import Workflow
from dotenv import load_dotenv
from pydantic import BaseModel

from agents.common import get_model

load_dotenv()


class Questions(BaseModel):
    question_for_agent_a: str
    question_for_agent_b: str


def debater_agent(name, persona):
    return Agent(
        name=name,
        model=get_model(),
        description=dedent(
            f"""
            You think, act and speak like {persona}. If anything push it on the caricature side.
            """
        ),
        goal="You're debating about a topic, and you're trying to convince the other agent that your point of view is correct.",
        instructions=[
            "You can ask questions, make claims, and respond to the other agent.",
            "You can use any information you want to support your argument.",
            "IMPORTANT: You always end your messages with a question for the other agent.",
            "IMPORTANT: You should only answer in two to three short sentences (not including the follow-up question).",
        ],
        add_history_to_messages=True,
        num_history_responses=100,
    )


class PoliticalDebate(Workflow):
    agent_a: Agent = debater_agent("Agent A", "Trump")

    agent_b: Agent = debater_agent("Agent B", "Dalai Lama")

    summarizer: Agent = Agent(
        name="Summarizer",
        model=get_model(),
        description=dedent(
            """
            You analyze the debate and bring everything together in a nice readable summary.
            Please make the debate feel alive! Include the most interesting parts of the debate.
            Include quotes! Include key moments! Fun moments! Include anything that's compelling!
            """
        ),
        add_history_to_messages=True,
        num_history_responses=100,
    )

    def run(self, topic: str) -> RunResponse:
        NUM_OF_ROUNDS = 10
        self.agent_a.additional_context = "TOPIC: " + topic
        self.agent_b.additional_context = "TOPIC: " + topic
        # self.agent_a.expected_output = "Answer in one short sentence only!"
        # self.agent_b.expected_output = "Answer in one short sentence only!"

        a_resp = self.agent_a.run("Let's start with you").content
        for _ in range(NUM_OF_ROUNDS):
            logger.info(f"Agent A: {a_resp}")
            b_resp = self.agent_b.run(a_resp).content
            logger.info(f"Agent B: {b_resp}")
            a_resp = self.agent_a.run(b_resp).content
            logger.info("")
            logger.info("")

        full_debate = self.get_full_debate()
        return self.summarizer.run(
            dedent(
                f"""
                The debate is over, summarize it.
                
                # Debate
                {full_debate}
                """
            )
        )

    def get_full_debate(self):
        return (
            "This is the conversation from the point of view of Agent A\n---------\n"
            + "\n-------------------------------\n".join(
                [
                    f"Role: '{m.role}' |  Message: '{m.content}'"
                    for m in self.agent_a.memory.messages
                    if m.role != "system"
                ]
            )
        )


debate = PoliticalDebate(workflow_id="political_debate")
app = Playground(workflows=[debate]).get_app()


if __name__ == "__main__":
    while True:
        msg = input("Enter a message: ")
        resp = debate.run(topic=msg)
        pprint_run_response(resp)
