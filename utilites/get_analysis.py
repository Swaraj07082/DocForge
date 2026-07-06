import json 
from repo_analyser import analyse_symbol

def get_analysis(file_name: str) -> list:
    with open("symbol_index.json", "r") as f:
        symbol_index = json.load(f)

        # print(symbol_index)

        functions : list = []
        # getting all the functions from the symbol index that are in the file_name

        for symbol in symbol_index:
            if symbol_index[symbol][0] == f"{file_name}":
                functions.append(symbol)

        analysis = []
        for fn in functions:
            analysis.append(analyse_symbol(fn))
        return analysis