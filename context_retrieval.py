import json

def get_context(function_name : str):
    context : dict = {}

    with open("symbol_index.json" , "r" , encoding="utf-8") as f:
        symbol_index = json.load(f)
    with open("call_graph.json" , "r" , encoding="utf-8") as f:
        call_graph = json.load(f)
    with open("reverse_call_graph.json" , "r" , encoding="utf-8") as f:
        reverse_call_graph = json.load(f)


    if function_name in symbol_index:
        context["code"] = symbol_index[function_name][1]
    
    if function_name in call_graph:
        context["calls"] = call_graph[function_name]

    if function_name in reverse_call_graph:
        context["called_by"] = reverse_call_graph[function_name]

    return context


context = get_context("remove_tags")

# print(context)
