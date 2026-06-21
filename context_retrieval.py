import json

def get_context(function_name : str):
    context : dict = {}

    with open("call_graph.json" , "r" , encoding="utf-8") as f:
        call_graph = json.load(f)
    with open("reverse_call_graph.json" , "r" , encoding="utf-8") as f:
        reverse_call_graph = json.load(f)

    context["function_name"] = function_name

    if function_name in call_graph:
        context["calls"] = call_graph[function_name]

    if function_name in reverse_call_graph:
        context["called_by"] = reverse_call_graph[function_name]

    return context


context = get_context("remove_tags")

# print(context)
