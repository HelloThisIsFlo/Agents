from pathlib import Path

from agno.models.openai import OpenAIChat, OpenAILike
from agno.storage.agent.sqlite import SqliteAgentStorage
from agno.storage.workflow.sqlite import SqliteWorkflowStorage
from dotenv import load_dotenv

SCRIPT_DIR = Path(__file__).resolve().parent
SQLITE_DB = str(SCRIPT_DIR / "tmp/agent_storage.db")

load_dotenv()


def get_model(local=False):
    if local:
        return OpenAILike(
            id="qwen2.5-7b-instruct-1m@q8_0",
            # id="qwen2.5-7b-instruct-1m@q4_k_m",
            api_key="not-used",
            base_url="http://127.0.0.1:1234/v1",
        )
    else:
        # return OpenAIChat(id="gpt-4o-mini")
        return OpenAIChat(id="gpt-4o")


def get_storage(workflow_name: str, agent_name: str, workflow=False):
    if workflow:
        return SqliteWorkflowStorage(
            table_name=f"{workflow_name}_{agent_name}_sessions",
            db_file=SQLITE_DB,
        )
    else:
        return SqliteAgentStorage(
            table_name=f"{workflow_name}_{agent_name}_sessions",
            db_file=SQLITE_DB,
        )
