import json
import os
from pathlib import Path

CHUNK_KINDS = {"function_definition", "class_definition", "method_definition",
    "module", "interface_declaration", "struct_specifier", "enum_specifier", "trait_item"}


def chunk_code(parsed_path: str) -> list[dict]:
    """Chunk parsed AST metadata into semantic units."""
    with open(parsed_path, "r", encoding="utf-8") as f:
        parsed_code = json.load(f)

    nodes = parsed_code["nodes"]

    chunks: list[dict] = []
    for node in nodes:
        if node["kind"] in CHUNK_KINDS:
            chunks.append({**node})

    output_dir = Path("./chunked_files")
    output_dir.mkdir(parents=True, exist_ok=True)
    output_path = output_dir / f"chunked_{parsed_code['file']}.json"

    with open(output_path, "w", encoding="utf-8") as f:
        json.dump({"file": parsed_code["file"], "chunks": chunks}, f, indent=2)

    return chunks


if __name__ == "__main__":
    chunk_code("./parsed_files/parsed_app.py.json")