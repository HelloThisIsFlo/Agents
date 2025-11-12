"""File I/O utilities for the summarization workflow."""

from pathlib import Path


def read_file(file_path: str) -> str:
    try:
        with open(Path(file_path), "r", encoding="utf-8") as f:
            return f.read()
    except FileNotFoundError:
        return f"File not found: {file_path}. Please set the correct file path in the configuration constants."


def write_file(file_path: str, content: str) -> None:
    with open(Path(file_path), "w", encoding="utf-8") as f:
        f.write(content)


def format_summary(emotional_summary: str, technical_summary: str) -> str:
    return f"""# Emotional Summary

{emotional_summary}



================================================================
================================================================



# Technical Summary

{technical_summary}
"""
