from langgraph.graph import StateGraph, START, END
from typing import TypedDict
from ingestion.github_loader import load_repo
from langchain_core.documents import Document
from constants.languages import CODE_EXTENSIONS, EXTENSION_TO_LANGUAGE
from parsing.global_parser import extract_file_metadata
import json
import glob
import os
from chunking.code_chunker import chunk_code
from embedding.embedding_service import load_all_documents, build_index, save_vector_store , load_chunks_and_create_documents
from symbol_index import build_symbol_index, build_call_graph, build_reverse_call_graph
from tools.refactoring_tools import get_radon_findings, get_ruff_findings, get_vulture_findings
from utilites.get_analysis import get_analysis

class DocForgeState(TypedDict):
    clone_url: str
    file_path : str 
    branch : str = "master"
    files : list[Document]
    output_path : str
    chunked_files : list[dict]
    symbol_index : dict
    call_graph : dict
    reverse_call_graph : dict
    functions : list[str]
    file_name : str
    static_tools_findings : list[dict]


graph = StateGraph(DocForgeState)

def get_file_name(state : DocForgeState) -> DocForgeState:
    state['file_name'] = state["file_path"].split("/")[-1]
    return state


def load_documents(state : DocForgeState) -> DocForgeState:
    
    if state["clone_url"] is None:
        raise ValueError("Repo path is required")

    if state["file_path"] is None:
        raise ValueError("File path is required")

    files = load_repo(state["clone_url"] , state["branch"])

    return {"files" : files}

def parse_documents(state : DocForgeState) -> DocForgeState:

    if state["files"] is None:
        raise ValueError("Files are required")

    os.makedirs("./parsed_files", exist_ok=True)

    for document in state["files"]:
        file = document.metadata["file_path"]
        ending = "." + file.split(".")[-1]
        if ending in CODE_EXTENSIONS:
            file_metadata = extract_file_metadata(file, ending)
            output_path = f"./parsed_files/parsed_{file}.json"
            with open(output_path, "w") as f:
                json.dump(file_metadata, f)
    return state

def chunk_documents(state : DocForgeState) -> DocForgeState:
    chunked_files: list[dict] = []
    for parsed_path in sorted(glob.glob("./parsed_files/parsed_*.json")):
        chunked_files.extend(chunk_code(parsed_path))
    state["chunked_files"] = chunked_files
    return state

def embed_documents(state : DocForgeState) -> DocForgeState:
    documents = load_all_documents()
    index = build_index(documents)
    save_vector_store(index, documents)
    return state

def analyse_documents(state : DocForgeState) -> DocForgeState:
    symbol_index: dict = {}
    for chunk_file in sorted(glob.glob("./chunked_files/chunked_*.json")):
        build_symbol_index(chunk_file, symbol_index)

    call_graph: dict = {}
    build_call_graph(call_graph)

    reverse_call_graph: dict = {}
    build_reverse_call_graph(call_graph, reverse_call_graph)

    functions : list[str] = []
    

    functions = get_analysis(state["symbol_index"] , state["file_path"])
    state["functions"] = functions
    return state

def run_static_tools(state : DocForgeState) -> DocForgeState:
    findings: list[dict] = []
    findings.extend(get_ruff_findings(state["file_path"]))
    findings.extend(get_radon_findings(state["file_path"]))
    findings.extend(get_vulture_findings(state["file_path"]))
    state["static_tools_findings"] = findings
    return state





# graph.add_node("load_documents" , load_documents)


