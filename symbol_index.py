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

def build_symbol_index(chunk_file : str , symbol_index : dict = {}):

    with open(chunk_file, "r" , encoding="utf-8") as f:
        chunks = json.load(f)

    # print(chunks)
    for chunk in chunks["chunks"]:
        name = chunk.get("name" , "Unknown")
        kind = chunk.get("kind" , "Unknown")
        code = chunk.get("text" , "No code available")
        file = chunk.get("file" , "Unknown")
        symbol_id = build_symbol_id(chunk)

        symbol_index[symbol_id] = ( file , kind , code , name )

    with open("symbol_index.json" , "w" , encoding="utf-8") as f:
        json.dump(symbol_index , f , indent=4)
    

def build_call_graph(call_graph : dict = {}):
    parsed_dir = Path("parsed_files")

    for parsed_path in sorted(parsed_dir.glob("parsed_*.json")):
        with open(parsed_path, "r", encoding="utf-8") as f:
            parsed_data = json.load(f)

        nodes = parsed_data["nodes"]
        for node in nodes:
            if node["kind"] == "function_definition":
                parent_name = node["children"][0]["text"]
                children = node["children"]
                for child in children:
                    traverse_children(child, call_graph, parent_name)

    with open("call_graph.json", "w", encoding="utf-8") as f:
        json.dump(call_graph, f, indent=4)

def traverse_children(node, call_graph, parent_name):
    
    if node["kind"] == "call":
        child_name = node["children"][0]["text"]
        if parent_name not in call_graph:
            call_graph[parent_name] = [child_name]
        else:
            call_graph[parent_name].append(child_name)

    if node["children"] != []:
        for child in node["children"]:
            traverse_children(child, call_graph , parent_name)
    else:
        return
    
def build_reverse_call_graph(call_graph : dict , reverse_call_graph : dict = {}):

    for parent, children in call_graph.items():
        for child in children:
            if child not in reverse_call_graph:
                reverse_call_graph[child] = [parent]
            else:
                reverse_call_graph[child].append(parent)

    with open("reverse_call_graph.json" , "w" , encoding = "utf-8") as f:
        json.dump(reverse_call_graph , f , indent=4)



symbol_index = {}
call_graph = {}
reverse_call_graph = {}

build_symbol_index("chunked_files/chunked_app.py.json" , symbol_index)
build_call_graph(call_graph)
build_reverse_call_graph(call_graph , reverse_call_graph)


