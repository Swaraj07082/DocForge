import json
from pathlib import Path


def get_context(function_name: str, workspace_dir: str | Path = ".") -> dict:
    workspace = Path(workspace_dir)
    context: dict = {}

    with open(workspace / "call_graph.json", "r", encoding="utf-8") as f:
        call_graph = json.load(f)
    with open(workspace / "reverse_call_graph.json", "r", encoding="utf-8") as f:
        reverse_call_graph = json.load(f)

    context["function_name"] = function_name

    if function_name in call_graph:
        context["calls"] = call_graph[function_name]

    if function_name in reverse_call_graph:
        context["called_by"] = reverse_call_graph[function_name]

    return context


if __name__ == "__main__":
    print(get_context("remove_tags"))
