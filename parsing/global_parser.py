import os

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


def parse(file: str, ending: str) -> Tree:
    language = EXTENSION_TO_LANGUAGE.get(ending)

    if language is None:
        raise ValueError(f"Language not supported: {ending}")

    file_path = repo_path + "/" + file
    with open(file_path, "r") as f:
        source_code = f.read()

    parser = get_parser(language)
    tree = parser.parse(source_code)
    if tree is None:
        raise RuntimeError(f"Failed to parse {file}")

    # os.makedirs("./parsed_files", exist_ok=True)
    # with open(f"./parsed_files/parsed_{file}.json", "w") as f:
    #     f.write(tree.root_node().to_sexp())

    return tree


def walk_tree(node: Node) -> None:
    # print(node)
    # DFS implementation of walking the tree
    # could add a queue to BFS implementation
    for i in range(node.named_child_count()):
        child = node.named_child(i)
        if child is None:
            continue
        print(child.kind())
        walk_tree(child)

for file in files:
    print(file)
    ending = "." + file.split(".")[-1]
    if ending in CODE_EXTENSIONS:
        try:
            tree = parse(file, ending)
            walk_tree(tree.root_node())
        except (ValueError, OSError, RuntimeError, TypeError) as e:
            print(f"Skipped {file}: {e}")
