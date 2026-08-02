import json
from pathlib import Path

CHUNK_KINDS = {
    "function_definition",
    "class_definition",
    "method_definition",
    "module",
    "interface_declaration",
    "struct_specifier",
    "enum_specifier",
    "trait_item",
}

DECORATED_WRAPPER_KINDS = {"decorated_definition"}


def _extract_name(node: dict) -> str | None:
    for child in node.get("children", []):
        if child["kind"] == "identifier":
            return child["text"]
    return None


def _extract_decorators(node: dict) -> list[str]:
    return [child["text"] for child in node.get("children", []) if child["kind"] == "decorator"]


def _make_chunk(
    *,
    file: str | None,
    language: str | None,
    kind: str,
    name: str | None,
    text: str,
    span: dict,
    flags: dict,
    parent: str | None = None,
    decorators: list[str] | None = None,
) -> dict:
    chunk: dict = {
        "file": file,
        "language": language,
        "kind": kind,
        "name": name,
        "text": text,
        "span": span,
        "flags": flags,
    }
    if parent is not None:
        chunk["parent"] = parent
    if decorators:
        chunk["decorators"] = decorators
    return chunk


def _collect_chunks(nodes: list[dict], chunks: list[dict], parent: str | None = None, file: str | None = None, language: str | None = None) -> None:
    for node in nodes:
        kind = node["kind"]

        if kind in DECORATED_WRAPPER_KINDS:
            inner = next(
                (child for child in node.get("children", []) if child["kind"] in CHUNK_KINDS),
                None,
            )
            chunks.append(
                _make_chunk(
                    file=file,
                    language=language,
                    kind=inner["kind"] if inner else kind,
                    name=_extract_name(inner) if inner else None,
                    text=node["text"],
                    span=node["span"],
                    flags=node["flags"],
                    parent=parent,
                    decorators=_extract_decorators(node),
                )
            )
            if inner is not None:
                _collect_chunks(inner.get("children", []), chunks, parent=parent , file=file , language=language)
            continue

        if kind in CHUNK_KINDS:
            name = _extract_name(node)
            chunks.append(
                _make_chunk(
                    file=file,
                    language=language,
                    kind=kind,
                    name=name,
                    text=node["text"],
                    span=node["span"],
                    flags=node["flags"],
                    parent=parent,
                )
            )
            child_parent = name if kind == "class_definition" else parent
            _collect_chunks(node.get("children", []), chunks, parent=child_parent, file=file, language=language)
            continue

        _collect_chunks(node.get("children", []), chunks, parent=parent, file=file, language=language)


def chunk_code(parsed_path: str, output_dir: str | Path = "./chunked_files") -> list[dict]:
    """Chunk parsed AST metadata into flat semantic units for retrieval."""
    with open(parsed_path, "r", encoding="utf-8") as f:
        parsed_code = json.load(f)

    chunks: list[dict] = []
    _collect_chunks(parsed_code["nodes"], chunks , None , parsed_code.get("file") , parsed_code.get("language"))

    out_dir = Path(output_dir)
    out_dir.mkdir(parents=True, exist_ok=True)
    output_path = out_dir / f"chunked_{parsed_code['file']}.json"

    payload = {
        "file": parsed_code["file"],
        "language": parsed_code.get("language"),
        "chunks": chunks,
    }

    with open(output_path, "w", encoding="utf-8") as f:
        json.dump(payload, f, indent=2)

    return chunks


if __name__ == "__main__":
    chunk_code("./parsed_files/parsed_app.py.json")
