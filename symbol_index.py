import json
from pathlib import Path


def build_symbol_id(chunk: dict) -> str:
    file = chunk.get("file", "Unknown")
    kind = chunk.get("kind", "Unknown")
    name = chunk.get("name", "Unknown")
    span = chunk.get("span", {})
    start_line = span.get("start_line", -1)
    start_column = span.get("start_column", -1)
    return f"{file}::{kind}::{name}::{start_line}:{start_column}"


def build_symbol_index(
    chunk_file: str,
    symbol_index: dict | None = None,
    *,
    output_path: str | Path = "symbol_index.json",
) -> dict:
    if symbol_index is None:
        symbol_index = {}

    with open(chunk_file, "r", encoding="utf-8") as f:
        chunks = json.load(f)

    for chunk in chunks["chunks"]:
        name = chunk.get("name", "Unknown")
        kind = chunk.get("kind", "Unknown")
        code = chunk.get("text", "No code available")
        file = chunk.get("file", "Unknown")
        symbol_id = build_symbol_id(chunk)
        symbol_index[symbol_id] = (file, kind, code, name)

    output = Path(output_path)
    output.parent.mkdir(parents=True, exist_ok=True)
    with open(output, "w", encoding="utf-8") as f:
        json.dump(symbol_index, f, indent=4)

    return symbol_index


def build_call_graph(
    call_graph: dict | None = None,
    *,
    parsed_dir: str | Path = "parsed_files",
    output_path: str | Path = "call_graph.json",
) -> dict:
    if call_graph is None:
        call_graph = {}

    parsed_root = Path(parsed_dir)
    for parsed_path in sorted(parsed_root.glob("parsed_*.json")):
        with open(parsed_path, "r", encoding="utf-8") as f:
            parsed_data = json.load(f)

        nodes = parsed_data["nodes"]
        for node in nodes:
            if node["kind"] == "function_definition":
                parent_name = node["children"][0]["text"]
                children = node["children"]
                for child in children:
                    traverse_children(child, call_graph, parent_name)

    output = Path(output_path)
    output.parent.mkdir(parents=True, exist_ok=True)
    with open(output, "w", encoding="utf-8") as f:
        json.dump(call_graph, f, indent=4)

    return call_graph


def traverse_children(node, call_graph, parent_name):
    if node["kind"] == "call":
        child_name = node["children"][0]["text"]
        if parent_name not in call_graph:
            call_graph[parent_name] = [child_name]
        else:
            call_graph[parent_name].append(child_name)

    if node["children"] != []:
        for child in node["children"]:
            traverse_children(child, call_graph, parent_name)
    else:
        return


def build_reverse_call_graph(
    call_graph: dict,
    reverse_call_graph: dict | None = None,
    *,
    output_path: str | Path = "reverse_call_graph.json",
) -> dict:
    if reverse_call_graph is None:
        reverse_call_graph = {}

    for parent, children in call_graph.items():
        for child in children:
            if child not in reverse_call_graph:
                reverse_call_graph[child] = [parent]
            else:
                reverse_call_graph[child].append(parent)

    output = Path(output_path)
    output.parent.mkdir(parents=True, exist_ok=True)
    with open(output, "w", encoding="utf-8") as f:
        json.dump(reverse_call_graph, f, indent=4)

    return reverse_call_graph


if __name__ == "__main__":
    symbol_index: dict = {}
    call_graph: dict = {}
    reverse_call_graph: dict = {}
    build_symbol_index("chunked_files/chunked_app.py.json", symbol_index)
    build_call_graph(call_graph)
    build_reverse_call_graph(call_graph, reverse_call_graph)
