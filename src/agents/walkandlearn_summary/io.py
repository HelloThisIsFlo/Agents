"""File I/O utilities for the summarization workflow."""

from datetime import datetime
from pathlib import Path
from typing import Union


def get_frontmatter(
    config_template: str, dt: datetime, input_filename: str, summary_type: str
) -> str:
    """Generate frontmatter with config template, generated_at timestamp, input filename, and summary type."""
    generated_at = dt.strftime("%Y-%m-%dT%H:%M:%S")

    return f"""---
locked: true
config_template: {config_template}
generated_at: {generated_at}
input_file: {input_filename}
summary_type: {summary_type}

---

"""


def read_file(file_path: Union[Path, str]) -> str:
    try:
        path = Path(file_path) if isinstance(file_path, str) else file_path
        with open(path, "r", encoding="utf-8") as f:
            return f.read()
    except FileNotFoundError:
        return f"File not found: {file_path}. Please set the correct file path in the configuration constants."


def write_file(file_path: Union[Path, str], content: str) -> None:
    path = Path(file_path) if isinstance(file_path, str) else file_path
    with open(path, "w", encoding="utf-8") as f:
        f.write(content)
