import json

def analyse_symbol(function_name : str):

    response : dict = {}

    response["function_name"] = function_name

    with open("symbol_index.json" , "r" , encoding="utf-8") as f:
        symbol_index = json.load(f)
        if function_name in symbol_index:
            response["file"] = symbol_index[function_name][0]
            response["code"] = symbol_index[function_name][2]

    with open("call_graph.json" , "r" , encoding="utf-8") as f:
        call_graph = json.load(f)

        if function_name in call_graph:
            response["calls"] = call_graph[function_name]

    with open("reverse_call_graph.json" , "r" , encoding="utf-8") as f:
        reverse_call_graph = json.load(f)

        if function_name in reverse_call_graph:
            response["called_by"] = reverse_call_graph[function_name]

    return response

response = analyse_symbol("remove_tags")
# print(response)