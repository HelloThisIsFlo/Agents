"""Tests for package-level import behavior."""

import importlib
import sys


def test_package_import_does_not_require_model_api_keys(monkeypatch):
    """Importing the package should not build graph/model clients."""
    for key in ("OPENAI_API_KEY", "ANTHROPIC_API_KEY", "GOOGLE_API_KEY"):
        monkeypatch.delenv(key, raising=False)

    sys.modules.pop("src.agents.walkandlearn_summary", None)

    package = importlib.import_module("src.agents.walkandlearn_summary")

    assert package.__all__ == ["graph"]
