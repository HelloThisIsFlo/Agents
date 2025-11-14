from pathlib import Path
from src.agents.walkandlearn_summary.models import get_model_by_name

PROJECT_ROOT = Path(__file__).parent.parent.parent.parent


MODELS = {
    "normal": get_model_by_name("GPT 5.1"),
    "wip": get_model_by_name("GPT 5-nano"),
}

WIP_MODE = False
TECHNICAL_DISABLED = False


MODEL_NAME = MODELS["wip"] if WIP_MODE else MODELS["normal"]
MODEL_TEMPERATURE = 0
PRINT_SUMMARY_IN_CHAT = True

INPUT_FILENAME = "input-wip.md" if WIP_MODE else "input.md"
OUTPUT_FILENAME = "output-wip.md" if WIP_MODE else "output.md"


INPUT_FILE_PATH = PROJECT_ROOT / "agent_files" / "walkandlearn_summary" / INPUT_FILENAME
OUTPUT_FILE_PATH = (
    PROJECT_ROOT / "agent_files" / "walkandlearn_summary" / OUTPUT_FILENAME
)
