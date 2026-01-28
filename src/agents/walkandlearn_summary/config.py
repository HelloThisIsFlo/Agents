from pathlib import Path
from src.agents.walkandlearn_summary.models import get_model_by_name

PROJECT_ROOT = Path(__file__).parent.parent.parent.parent


MODELS = {
    "gpt-5.1": {
        "emotional": get_model_by_name("GPT 5.1", temp=1.0),
        "technical": get_model_by_name("GPT 5.1", temp=0.7),
        "evaluation": get_model_by_name("GPT 5.1", temp=0.3),
    },
    "gpt-5.1-chat": {
        "emotional": get_model_by_name("GPT 5.1-chat", temp=1.0),
        "technical": get_model_by_name("GPT 5.1-chat", temp=0.7),
        "evaluation": get_model_by_name("GPT 5.1-chat", temp=0.3),
    },
    "claude-sonnet-4.5": {
        "emotional": get_model_by_name("Sonnet 4.5", temp=1.0),
        "technical": get_model_by_name("Sonnet 4.5", temp=0.7),
        "evaluation": get_model_by_name("Sonnet 4.5", temp=0.3),
    },
    "gemini-pro": {
        "emotional": get_model_by_name("Gemini 2.5 Pro", temp=1.0),
        "technical": get_model_by_name("Gemini 2.5 Pro", temp=0.7),
        "evaluation": get_model_by_name("Gemini 2.5 Pro", temp=0.3),
    },
    "gpt-nano": {
        "emotional": get_model_by_name("GPT 5-nano", temp=1.0),
        "technical": get_model_by_name("GPT 5-nano", temp=0.7),
        "evaluation": get_model_by_name("GPT 5-nano", temp=0.3),
    },
    "gemini-nano": {
        "emotional": get_model_by_name("Gemini 2.5 Flash Lite", temp=1.0),
        "technical": get_model_by_name("Gemini 2.5 Flash Lite", temp=0.7),
        "evaluation": get_model_by_name("Gemini 2.5 Flash Lite", temp=0.3),
    },
    "thinking": {
        "emotional": get_model_by_name("Sonnet 4.5", temp=1.0),
        "technical": get_model_by_name("GPT 5-nano", temp=0.7),
        "evaluation": get_model_by_name("Sonnet 4.5", temp=0.3),
    },
    "wip-thinking": {
        "emotional": get_model_by_name("GPT 5-nano", temp=1.0),
        "technical": get_model_by_name("GPT 5-nano", temp=0.7),
        "evaluation": get_model_by_name("GPT 5-nano", temp=0.3),
    },
}

CONFIG_TEMPLATES = {
    "main-gpt": {
        "wip": False,
        "models": MODELS["gpt-5.1"],
    },
    "main-gpt-chat": {
        "wip": False,
        "models": MODELS["gpt-5.1-chat"],
    },
    "main-claude": {
        "wip": False,
        "models": MODELS["claude-sonnet-4.5"],
    },
    "main-gemini": {
        "wip": False,
        "models": MODELS["gemini-pro"],
    },
    "thinking": {
        "wip": False,
        "models": MODELS["thinking"],
    },
    "gemini-fast-nowip": {
        "wip": False,
        "models": MODELS["gemini-nano"],
    },
    "wip": {
        "wip": True,
        "models": MODELS["gpt-nano"],
    },
    "wip-gemini": {
        "wip": True,
        "models": MODELS["gemini-nano"],
    },
    "wip-thinking": {
        "wip": True,
        "models": MODELS["wip-thinking"],
    },
}


########################################################
# CONFIG
########################################################
# CONFIG_TEMPLATE = "main"
CONFIG_TEMPLATE = "gemini-fast-nowip"
# CONFIG_TEMPLATE = "wip-gemini"
# CONFIG_TEMPLATE = "main-gpt"
# CONFIG_TEMPLATE = "main-gemini"

# CONFIG_TEMPLATE = "main-claude"  # <- The MAIN one!

EMOTIONAL_DISABLED = False
TECHNICAL_DISABLED = False
EVAL_DISABLED = False

NUM_EMOTIONAL_ITERATIONS = 3
NUM_TECHNICAL_ITERATIONS = 3

# INPUT_FILENAME = "input.md"
INPUT_FILENAME = "input-shap.md"
# INPUT_FILENAME = "input-hessian.md"


########################################################
# CONFIG VALUES
########################################################
CONFIG = CONFIG_TEMPLATES[CONFIG_TEMPLATE]
WIP_MODE = CONFIG["wip"]

MODELS = CONFIG["models"]
PRINT_SUMMARY_IN_CHAT = True

# Default input filename (can be overridden via graph state)
INPUT_FILENAME = "input-wip.md" if WIP_MODE else INPUT_FILENAME
DEFAULT_INPUT_FILENAME = INPUT_FILENAME


OUTPUT_FILE_PATH_OBSIDIAN_BASE = Path(
    "/Users/flo/Work/Private/PKM/Obsidian/TheVault/WalkAndLearn/DebugSandbox"
)


def get_input_file_path(filename: str) -> Path:
    """Get the full path to an input file given its filename."""
    return PROJECT_ROOT / "agent_files" / "walkandlearn_summary" / filename
