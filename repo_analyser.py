import json

def analyse_symbol(symbol_id : str):

    response : dict = {}

    response["function_name"] = symbol_id
    symbol_name = symbol_id

    with open("symbol_index.json" , "r" , encoding="utf-8") as f:
        symbol_index = json.load(f)
        if symbol_id in symbol_index:
            response["file"] = symbol_index[symbol_id][0]
            response["code"] = symbol_index[symbol_id][2]
            # Tuple shape: (file, kind, code, name)
            if len(symbol_index[symbol_id]) > 3:
                symbol_name = symbol_index[symbol_id][3]
                response["symbol_name"] = symbol_name

    with open("call_graph.json" , "r" , encoding="utf-8") as f:
        call_graph = json.load(f)

        if symbol_name in call_graph:
            response["calls"] = call_graph[symbol_name]

    with open("reverse_call_graph.json" , "r" , encoding="utf-8") as f:
        reverse_call_graph = json.load(f)

        if symbol_name in reverse_call_graph:
            response["called_by"] = reverse_call_graph[symbol_name]

    return response

response = analyse_symbol("app.py::function_definition::remove_tags::0:0")
# print(response)