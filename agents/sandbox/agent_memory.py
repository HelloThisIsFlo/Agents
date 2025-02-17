from pprint import pprint

from agno.agent import Agent
from agno.models.message import Message
from agno.models.openai import OpenAIChat
from agno.run.response import RunResponse
from agno.utils.pprint import pprint_run_response
from dotenv import load_dotenv

load_dotenv()

agent = Agent(
    model=OpenAIChat(id="gpt-4o-mini"),
    description="You are a helpful assistant. You always respond in one sentence. You never repeat the same answer, if the user asks for something different, you should provide a different answer.",
    markdown=True,
)


def print_debug_info():
    global history, run_messages
    pprint_run_response(resp)
    history = agent.memory.messages
    pprint(history)
    run_messages = agent.get_run_messages().messages
    pprint(run_messages)


resp: RunResponse = agent.run("Hi, my name is bob!")
print_debug_info()


resp: RunResponse = agent.run(
    "Do you know my name? If so I'd like you to tell me a fun fact about it!",
    messages=history,
)
print_debug_info()


agent.add_history_to_messages = True
agent.num_history_responses = 10
agent.memory.create_session_summary = False
agent.memory.update_session_summary_after_run = False
resp: RunResponse = agent.run("Tell me another fun fact about my name")
print_debug_info()


summary = agent.memory.update_summary()
print(summary)

agent.add_history_to_messages = False
resp: RunResponse = agent.run("How many letters are there on my name?")
print_debug_info()

print("Stop here")
