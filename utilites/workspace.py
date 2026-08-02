"""Per-run filesystem isolation under workspaces/{thread_id}/."""

from __future__ import annotations

from pathlib import Path

WORKSPACES_ROOT = Path("workspaces")


def workspace_root(thread_id: str) -> Path:
    return WORKSPACES_ROOT / thread_id


def ensure_workspace(thread_id: str) -> Path:
    """Create a run-scoped workspace and return its root path."""
    root = workspace_root(thread_id)
    for name in ("repos", "parsed_files", "chunked_files", "vector_store"):
        (root / name).mkdir(parents=True, exist_ok=True)
    return root


def parsed_dir(workspace_dir: str | Path) -> Path:
    return Path(workspace_dir) / "parsed_files"


def chunked_dir(workspace_dir: str | Path) -> Path:
    return Path(workspace_dir) / "chunked_files"


def repos_dir(workspace_dir: str | Path) -> Path:
    return Path(workspace_dir) / "repos"


def vector_store_dir(workspace_dir: str | Path) -> Path:
    return Path(workspace_dir) / "vector_store"


def symbol_index_path(workspace_dir: str | Path) -> Path:
    return Path(workspace_dir) / "symbol_index.json"


def call_graph_path(workspace_dir: str | Path) -> Path:
    return Path(workspace_dir) / "call_graph.json"


def reverse_call_graph_path(workspace_dir: str | Path) -> Path:
    return Path(workspace_dir) / "reverse_call_graph.json"
