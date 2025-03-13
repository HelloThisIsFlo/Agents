import os
from typing import Iterable

from agno.agent import Agent
from agno.models.openai import OpenAIChat, OpenAILike
from agno.run.response import RunResponse
from agno.utils.pprint import pprint_run_response

RESEARCH_DIR = os.path.expanduser(
    "~/Work/Private/Dev/Finance/pf-simulations/DeepResearch/"
)


def load_text(filename) -> str:
    file_path = os.path.join(RESEARCH_DIR, filename)
    try:
        with open(file_path, "r", encoding="utf-8") as file:
            return file.read()
    except FileNotFoundError:
        print(f"File not found: {file_path}")
    except Exception as e:
        print(f"Error reading file: {e}")


def get_model():
    local = False
    if local:
        return OpenAILike(
            id="qwen2.5-7b-instruct-1m@q8_0",
            api_key="not-used",
            base_url="http://127.0.0.1:1234/v1",
        )
    else:
        # return OpenAIChat(id="gpt-4o-mini")
        return OpenAIChat(id="gpt-4o")


agent = Agent(
    model=get_model(),
    goal="You translate text from English to French in the best possible way",
    instructions="""
    - Keep the structure and the formatting as the original
    - Keep the formatting in markdown
    """,
    # debug_mode=True,
)

filename = "EfficientTransfer2.md"
text = load_text(filename)
response: Iterable[RunResponse] = agent.run(text, stream=True)

translated_chunks = []
for resp in response:
    chunk = resp.content
    print(chunk, end="")
    translated_chunks.append(chunk)

translated = "".join(translated_chunks)
## Write result to a file

with open(f"fr_{filename}", "w", encoding="utf-8") as file:
    file.write(translated)
