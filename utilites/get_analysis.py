import json
from pathlib import Path

from repo_analyser import analyse_symbol


def get_analysis(file_name: str, workspace_dir: str | Path = ".") -> list:
    workspace = Path(workspace_dir)
    with open(workspace / "symbol_index.json", "r", encoding="utf-8") as f:
        symbol_index = json.load(f)

    functions: list = []
    for symbol in symbol_index:
        if symbol_index[symbol][0] == f"{file_name}":
            functions.append(symbol)

    analysis = []
    for fn in functions:
        analysis.append(analyse_symbol(fn, workspace_dir=workspace))
    return analysis
