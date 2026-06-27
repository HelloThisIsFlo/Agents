"""WalkAndLearn summary agent package."""

from typing import Any


def __getattr__(name: str) -> Any:
    if name == "graph":
        from src.agents.walkandlearn_summary.graph import graph

        return graph
    raise AttributeError(f"module {__name__!r} has no attribute {name!r}")


__all__ = ["graph"]
