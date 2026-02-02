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
date: 2026-01-01
teaser: "PLACEHOLDER"
banner: "[[placeholder.png]]"
generated_at: {generated_at}
review-config_template: {config_template}
review-input_file: {input_filename}
review-summary_type: {summary_type}

---

"""


def read_file(file_path: Union[Path, str]) -> str:
    path = Path(file_path) if isinstance(file_path, str) else file_path
    with open(path, "r", encoding="utf-8") as f:
        return f.read()


def write_file(file_path: Union[Path, str], content: str) -> None:
    path = Path(file_path) if isinstance(file_path, str) else file_path
    with open(path, "w", encoding="utf-8") as f:
        f.write(content)
