import os
import json
from constants.languages import CODE_EXTENSIONS, EXTENSION_TO_LANGUAGE
from tree_sitter_language_pack import Node, Parser, Tree, get_parser as get_ts_parser, has_language

repo_path = "C:/Users/Swaraj/OneDrive/Desktop/DocForge/repos/Amazon-Reviews-Sentiment-Analysis"

files = os.listdir(repo_path)
# lists files in the repo_path folder

_parser_cache: dict[str, Parser] = {}



def get_parser(language: str) -> Parser:
    if language not in _parser_cache:
        if not has_language(language):
            raise ValueError(f"Language not supported by parser: {language}")
        _parser_cache[language] = get_ts_parser(language)
    return _parser_cache[language]


def parse(file: str, ending: str) -> list[Tree, bytes]:
    language = EXTENSION_TO_LANGUAGE.get(ending)

    if language is None:
        raise ValueError(f"Language not supported: {ending}")

    file_path = repo_path + "/" + file
    with open(file_path, "rb") as f:
        source_code = f.read()
        print(type(source_code))
        # print(source_code)

    parser = get_parser(language)
    tree = parser.parse(source_code.decode("utf-8"))
    if tree is None:
        raise RuntimeError(f"Failed to parse {file}")

    # os.makedirs("./parsed_files", exist_ok=True)
    # with open(f"./parsed_files/parsed_{file}.json", "w") as f:
    #     f.write(tree.root_node().to_sexp())

    return [tree , source_code]




def node_to_metadata(node: Node, source_code: bytes) -> dict:
    start_byte = node.start_byte()
    end_byte = node.end_byte()
    start_pos = node.start_position()
    end_pos = node.end_position()

    return {
        "kind": node.kind(),
        "kind_id": node.kind_id(),
        "span": {
            "start_byte": start_byte,
            "end_byte": end_byte,
            "start_line": start_pos.row,
            "start_column": start_pos.column,
            "end_line": end_pos.row,
            "end_column": end_pos.column,
        },
        "text": source_code[start_byte:end_byte].decode("utf-8"),
        "flags": {
            "is_named": node.is_named(),
            "is_error": node.is_error(),
            "has_error": node.has_error(),
            "is_missing": node.is_missing(),
            "is_extra": node.is_extra(),
        },
        "child_count": node.child_count(),
        "named_child_count": node.named_child_count(),
    }


def walk_tree(node: Node, source_code: bytes) -> list[dict]:
    nodes: list[dict] = []
    for i in range(node.named_child_count()):
        child = node.named_child(i)
        if child is None:
            continue
        meta = node_to_metadata(child, source_code)
        meta["children"] = walk_tree(child, source_code)
        nodes.append(meta)
    return nodes


def extract_file_metadata(file: str, ending: str) -> dict:
    tree, source_code = parse(file, ending)
    language = EXTENSION_TO_LANGUAGE[ending]
    return {
        "file": file,
        "language": language,
        "nodes": walk_tree(tree.root_node(), source_code),
    }

for file in files:
    ending = "." + file.split(".")[-1]
    if ending in CODE_EXTENSIONS:
        try:
            file_metadata = extract_file_metadata(file, ending)
            
            with open(f"./parsed_files/parsed_{file}.json", "w") as f:
                json.dump(file_metadata, f)
            # chunking step: filter nodes by kind, then attach file/language
            # e.g. function_definition, class_definition, method_definition
        except (ValueError, OSError, RuntimeError, TypeError) as e:
            raise e
