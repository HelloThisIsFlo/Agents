from pathlib import Path
from textwrap import dedent

from agno.agent import Agent
from agno.playground import Playground
from agno.run.response import RunResponse
from agno.utils.log import get_logger, logger
from agno.utils.pprint import pprint_run_response
from agno.workflow import Workflow
from dotenv import load_dotenv
from pydantic import BaseModel

from agents.common import get_model


load_dotenv()


class Questions(BaseModel):
    question_for_agent_a: str
    question_for_agent_b: str


class PoliticalDebate(Workflow):
    agent_a: Agent = Agent(
        name="Agent A",
        model=get_model(),
        description=dedent(
            """
            You are a pro-trump, and pro-putin. You love tesla! You express yourself like trump: Use a lot of made up claims and hyperbole. 
            You say things 'like it is" and don't care about political correctness.
            """
        ),
        add_history_to_messages=True,
        num_history_responses=100,
    )

    agent_b: Agent = Agent(
        name="Agent B",
        model=get_model(),
        description=dedent(
            """
            You are rational and educated, with the wisdom of the dalai lama.
            """
        ),
        add_history_to_messages=True,
        num_history_responses=100,
    )

    debater: Agent = Agent(
        name="Debater",
        model=get_model(),
        description=dedent(
            """
            You analyze the answers of A and B and generate the next question to ask them both.
            If they haven't answered anything yet, you ask them a starting question.
            Agents A and B can't hear each other, so include as much context as needed in your question to keep the debate going.
            """
        ),
        response_model=Questions,
        structured_outputs=True,
        add_history_to_messages=True,
        num_history_responses=100,
    )

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
        # self.agent_a.expected_output = "Answer in one short sentence only!"
        # self.agent_b.expected_output = "Answer in one short sentence only!"

        questions: Questions = self.debater.run(topic).content
        for _ in range(NUM_OF_ROUNDS):
            logger.info(f"Question for A: {questions.question_for_agent_a}")
            logger.info(f"Question for B: {questions.question_for_agent_b}")

            a_resp = self.agent_a.run(questions.question_for_agent_a).content
            logger.info(f"Agent A response: {a_resp}")

            b_resp = self.agent_b.run(questions.question_for_agent_b).content
            logger.info(f"Agent B response: {b_resp}")

            questions = self.debater.run(
                dedent(
                    f"""
                    A and B responded, here's their answers:
                    
                    ## Agent A:
                    {a_resp}
                    
                    
                    
                    ## Agent B:
                    {b_resp}
                    """
                )
            ).content

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
        return "\n-------------------------------\n".join(
            [
                f"Role: '{m.role}' |  Message: '{m.content}'"
                for m in self.debater.memory.messages
                if m.role != "system"
            ]
        )


debate = PoliticalDebate(workflow_id="political_debate")
app = Playground(workflows=[debate]).get_app()


if __name__ == "__main__":
    while True:
        msg = input("Enter a message: ")
        resp = debate.run(topic=msg)
        pprint_run_response(resp)
