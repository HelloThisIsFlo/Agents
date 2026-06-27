# Repository Guidelines

## Project Structure & Module Organization

This repository is a Python agent experimentation workspace. Source code lives in `src/`, with active agent implementations under `src/agents/`. The main maintained workflow is `src/agents/walkandlearn_summary/`, which contains graph orchestration, config, models, I/O helpers, prompts, and node implementations.

Tests live in `tests/` and mirror the package structure, especially `tests/agents/walkandlearn_summary/`. Runtime inputs and generated working assets live under `agent_files/`. Archived experiments are kept in `src/_archive/`; treat them as reference material unless a task explicitly targets them.

## Build, Test, and Development Commands

Use `uv` for dependency and environment management.

- `uv sync`: install dependencies from `pyproject.toml` and `uv.lock`.
- `uv run pytest`: run the full test suite.
- `uv run pytest tests/agents/walkandlearn_summary/`: run the WalkAndLearn tests.
- `uv run python <script.py>`: execute Python scripts inside the managed environment.
- `uv add <package>` or `uv add --dev <package>`: add runtime or development dependencies.

## Coding Style & Naming Conventions

Target Python `>=3.12,<3.13`. Use 4-space indentation, type hints where they clarify interfaces, and small modules with explicit responsibilities. Prefer descriptive snake_case for files, functions, and variables. Keep prompts in Markdown files when they are substantial, rather than embedding large prompt strings in Python.

Do not edit `uv.lock` manually. Change dependencies through `uv add` or pyproject updates followed by `uv sync`.

## Testing Guidelines

Tests use `pytest`. Name test files `test_*.py` and test functions `test_*`. Keep tests close to the behavior they verify, mirroring `src/` paths when practical. For new workflow behavior, add or update focused tests before changing implementation when feasible.

## Commit & Pull Request Guidelines

Recent history uses short, imperative commit subjects such as `Update dependency lockfile` and `Tune WalkAndLearn emotional temperature`. Keep commits focused by theme: dependency lock refreshes, prompt edits, config tuning, and behavior changes should be separate when possible.

Pull requests should include a concise summary, verification commands run, and any configuration or environment notes. Include screenshots only for user-facing UI changes.

## Security & Configuration Tips

Keep secrets in a root `.env` file and do not commit it. Required local configuration includes `OPENAI_API_KEY`; optional integrations include `TAVILY_API_KEY`, `EXA_API_KEY`, and Agno tracing settings. Avoid committing generated outputs or personal Obsidian content unless the task explicitly requires it.
