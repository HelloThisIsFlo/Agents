from src.agents.walkandlearn_summary.io import read_file
from pathlib import Path
from src.agents.walkandlearn_summary.config import WIP_MODE


PROMPTS_DIR = Path(__file__).parent / "prompts"

EMOTIONAL_SUMMARY_PROMPT = read_file(PROMPTS_DIR / "summary_emotional.md")
TECHNICAL_SUMMARY_PROMPT = read_file(PROMPTS_DIR / "summary_technical.md")
EVALUATION_PROMPT = read_file(PROMPTS_DIR / "evaluation.md")

if WIP_MODE:
    EMOTIONAL_SUMMARY_PROMPT = "This is a quick test. Generate a short 'emotional' summary of the conversation. Maximum 2 paragraphs."
    TECHNICAL_SUMMARY_PROMPT = "This is a quick test. Generate a short 'technical' summary of the conversation. Maximum 2 paragraphs. Include the placeholder [AHA_PLACEHOLDER] where the emotional summary section should go."
