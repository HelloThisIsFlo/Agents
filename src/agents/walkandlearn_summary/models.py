import logging
import pandas as pd
from langchain.chat_models import init_chat_model

# Where to find models
# - https://platform.openai.com/docs/pricing

USING_GOOGLE_VERTEXAI = False

MODELS_DF = pd.DataFrame(
    [
        (
            "GPT 5-nano",
            "gpt-5-nano",
            "OpenAI",
            "nano",
            "openai",
            1.0,
        ),
        (
            "GPT 5-mini",
            "gpt-5-mini",
            "OpenAI",
            "mini",
            "openai",
            1.0,
        ),
        (
            "GPT 5",
            "gpt-5",
            "OpenAI",
            "main",
            "openai",
            1.0,
        ),
        (
            "GPT 5.1",
            "gpt-5.1",
            "OpenAI",
            "main",
            "openai",
            1.0,
        ),
        (
            "GPT 5.1-chat",
            "gpt-5.1-chat-latest",
            "OpenAI",
            "main",
            "openai",
            1.0,
        ),
        (
            "GPT 5.2",
            "gpt-5.2",
            "OpenAI",
            "main",
            "openai",
            1.0,
        ),
        (
            "GPT 5.2-chat",
            "gpt-5.2-chat-latest",
            "OpenAI",
            "main",
            "openai",
            1.0,
        ),
        (
            "GPT 5-chat",
            "gpt-5-chat-latest",
            "OpenAI",
            "main",
            "openai",
            1.0,
        ),
        (
            "Sonnet 4.5",
            "claude-sonnet-4-5",
            "Anthropic",
            "main",
            "anthropic",
            1.0,
        ),
        (
            "Haiku 4.5",
            "claude-haiku-4-5",
            "Anthropic",
            "mini",
            "anthropic",
            1.0,
        ),
        (
            "Opus 4.1",
            "claude-opus-4-1",
            "Anthropic",
            "main",
            "anthropic",
            1.0,
        ),
        (
            "Gemini 2.5 Pro",
            "gemini-2.5-pro",
            "Google",
            "main",
            "google_vertexai" if USING_GOOGLE_VERTEXAI else "google_genai",
            1.0,
        ),
        (
            "Gemini 2.5 Flash",
            "gemini-2.5-flash",
            "Google",
            "mini",
            "google_vertexai" if USING_GOOGLE_VERTEXAI else "google_genai",
            1.0,
        ),
        (
            "Gemini 2.5 Flash Lite",
            "gemini-2.5-flash-lite",
            "Google",
            "nano",
            "google_vertexai" if USING_GOOGLE_VERTEXAI else "google_genai",
            1.0,
        ),
    ],
    columns=[
        "friendly_name",
        "slug",
        "provider",
        "type",
        "langchain_provider",
        "temperature",
    ],
)


def print_available_models():
    print("MODELS BY PROVIDER")
    print("------------------")
    for provider, group in MODELS_DF.groupby("provider"):
        friendly_names = list(group["friendly_name"])
        print(f"{provider}")
        for friendly_name in friendly_names:
            print(f"  - {friendly_name}")

    print()
    print("MODELS BY TYPE")
    print("------------------")
    for type_, group in MODELS_DF.groupby("type"):
        friendly_names = list(group["friendly_name"])
        print(f"{type_}")
        for friendly_name in friendly_names:
            print(f"  - {friendly_name}")


def get_model_by_name(name: str, temp: float | None = None):
    """
    Get a LangChain chat model by friendly name.

    Args:
        name: Friendly name of the model (e.g., "Sonnet 4.5", "GPT 5-nano")
        temp: Temperature setting for the model. If None, uses the value from the DataFrame.

    Returns:
        LangChain chat model instance
    """
    try:
        row = MODELS_DF[MODELS_DF["friendly_name"] == name].iloc[0]
        slug = row["slug"]
        langchain_provider = row["langchain_provider"]

        if temp is None:
            temp = row["temperature"]

        # Configure retry and timeout settings, especially for Anthropic
        kwargs = {
            "model": slug,
            "model_provider": langchain_provider,
            "temperature": temp,
        }

        if langchain_provider == "anthropic":
            # Anthropic-specific settings for rate limiting
            logging.info(
                "Using Anthropic-specific settings for rate limiting | model: %s", name
            )
            kwargs.update(
                {
                    "max_retries": 10,  # We're hitting the token/min limit => So, quick hack to keep retrying until it works
                }
            )

        return init_chat_model(**kwargs)
    except IndexError:
        raise ValueError(f"Model {name} not found")


if __name__ == "__main__":
    print_available_models()
