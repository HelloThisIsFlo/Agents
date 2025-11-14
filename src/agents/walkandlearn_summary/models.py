import pandas as pd

# Where to find models
# - https://platform.openai.com/docs/pricing

MODELS_DF = pd.DataFrame(
    [
        ("GPT 5-nano", "gpt-5-nano", "OpenAI", "nano"),
        ("GPT 5-mini", "gpt-5-mini", "OpenAI", "mini"),
        ("GPT 5", "gpt-5", "OpenAI", "main"),
        ("GPT 5.1", "gpt-5.1", "OpenAI", "main"),
        ("GPT 5.1-chat", "gpt-5.1-chat-latest", "OpenAI", "main"),
        ("GPT 5-chat", "gpt-5-chat-latest", "OpenAI", "main"),
        ("Sonnet 4.5", "claude-sonnet-4-5", "Anthropic", "main"),
        ("Haiku 4.5", "claude-haiku-4-5", "Anthropic", "mini"),
        ("Opus 4.1", "claude-opus-4-1", "Anthropic", "main"),
        ("Gemini 2.5 Pro", "gemini-2.5-pro", "Google", "main"),
        ("Gemini 2.5 Flash", "gemini-2.5-flash", "Google", "mini"),
        ("Gemini 2.5 Flash Lite", "gemini-2.5-flash-lite", "Google", "nano"),
    ],
    columns=["friendly_name", "slug", "provider", "type"],
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


def get_model_by_name(name: str) -> str:
    try:
        return MODELS_DF[MODELS_DF["friendly_name"] == name]["slug"].values[0]
    except IndexError:
        raise ValueError(f"Model {name} not found")


if __name__ == "__main__":
    print_available_models()
