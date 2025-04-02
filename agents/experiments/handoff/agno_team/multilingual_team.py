from agno.agent import Agent
from agno.models.deepseek import DeepSeek
from agno.models.mistral.mistral import MistralChat
from agno.models.openai import OpenAIChat
from agno.team.team import Team

from agents.common import get_model

english_agent = Agent(
    name="English Agent",
    role="You only answer in English",
    model=get_model(),
    add_history_to_messages=True,
    num_history_responses=10,
)
chinese_agent = Agent(
    name="Chinese Agent",
    role="You only answer in Chinese",
    model=get_model(),
    add_history_to_messages=True,
    num_history_responses=10,
)
french_agent = Agent(
    name="French Agent",
    role="You can only answer in French",
    model=get_model(),
    add_history_to_messages=True,
    num_history_responses=10,
)

multi_language_team = Team(
    name="Multi Language Team",
    mode="route",
    model=get_model(),
    members=[english_agent, chinese_agent, french_agent],
    show_tool_calls=True,
    markdown=True,
    description="You are a language router that directs questions to the appropriate language agent.",
    instructions=[
        "Identify the language of the user's question and direct it to the appropriate language agent.",
        "If the user asks in a language whose agent is not a team member, respond in English with:",
        "'I can only answer in the following languages: English, Chinese, French. Please ask your question in one of these languages.'",
        "Always check the language of the user's input before routing to an agent.",
        "For unsupported languages like Italian, respond in English with the above message.",
    ],
    show_members_responses=True,
)


if __name__ == "__main__":
    multi_language_team.cli_app()
    # # Ask "How are you?" in all supported languages
    # multi_language_team.print_response("Comment allez-vous?", stream=True)  # French
    # multi_language_team.print_response("How are you?", stream=True)  # English
    # multi_language_team.print_response("你好吗？", stream=True)  # Chinese
    # multi_language_team.print_response("Come stai?", stream=True)  # Italian
