"""System prompts for summarization agents."""

from src.agents.walkandlearn_summary.io import read_file
from pathlib import Path

PROMPTS_DIR = Path(__file__).parent / "prompts"

EMOTIONAL_SUMMARY_PROMPT = read_file(PROMPTS_DIR / "summary_emotional.md")
TECHNICAL_SUMMARY_PROMPT = read_file(PROMPTS_DIR / "summary_technical.md")
