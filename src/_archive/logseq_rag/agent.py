from agno.agent import Agent
from agno.document.chunking.document import DocumentChunking
from agno.document.chunking.semantic import SemanticChunking
from agno.knowledge.text import TextKnowledgeBase
from agno.models.openai import OpenAIChat, OpenAILike
from agno.tools.duckduckgo import DuckDuckGoTools
from agno.vectordb.pgvector import PgVector

LOGSEQ_GRAPH_PATH = "/Users/flo/Work/Private/PKM/LogSeq/The Graph"
# LOGSEQ_GRAPH_PATH = "/Users/flo/Work/Private/PKM/LogSeq/RagExperiment/journals"

DB_URL = "postgresql+psycopg://ai:ai@localhost:5532/ai"
RELOAD_KNOWLEDGE_BASE = False

knowledge_base = TextKnowledgeBase(
    path=LOGSEQ_GRAPH_PATH,
    # Table name: ai.text_documents
    vector_db=PgVector(
        table_name="logseq_the_graph",
        db_url=DB_URL,
    ),
    chunking_strategy=SemanticChunking(),
    formats=[".md"],
)


def get_model():
    local = True
    if local:
        return OpenAILike(
            id="qwen2.5-7b-instruct-1m@q8_0",
            api_key="not-used",
            base_url="http://127.0.0.1:1234/v1",
        )
    else:
        # return OpenAIChat(id="gpt-4o-mini")
        return OpenAIChat(id="gpt-4o")


if RELOAD_KNOWLEDGE_BASE:
    knowledge_base.load(recreate=True, upsert=True)

agent = Agent(
    model=get_model(),
    knowledge=knowledge_base,
    # Add a tool to read chat history.
    search_knowledge=True,
    add_history_to_messages=True,
    num_history_responses=10,
    show_tool_calls=True,
    markdown=True,
    tools=[DuckDuckGoTools()],
    description="""
    You are a helpful assistant who has access to a knowledge base and the internet.
    The knowledge base contains my personal notes written in LogSeq.
    The format is a variant of markdown used for LogSeq.
    
    You are very insightful and not only provide information but also help me to
    understand the context and implications of the information, or sometimes you 
    give me perspective and advices based on the information
    """,
    goal="Answer my queries in the most helpful way",
    instructions="""
    - You search the knowledge base for information.
    - You can do 1 or 2 initial searches
    - If nothing interesting is found, please do an additional 2-3 searches before concluding that the information is not available.
    - Be creative with your queries, to make sure you capture different angles and get a comprehensive overview.
    - You can combine search from knowledge base with search from the web. But ONLY search the web to complement information from the knowledge base, ALWAYS start with the knowledge base.
    - Don't worry about taking time, feel free to do many searches before answering.
    """,
    # debug_mode=True,
)


agent.cli_app(stream=True)
