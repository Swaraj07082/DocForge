from langgraph.graph import StateGraph, START, END
from typing import TypedDict
from ingestion.github_loader import load_repo
from langchain_core.documents import Document
from constants.languages import CODE_EXTENSIONS, EXTENSION_TO_LANGUAGE
from parsing.global_parser import extract_file_metadata
import json
from chunking.code_chunker import chunk_code

class DocForgeState(TypedDict):
    clone_url: str
    file_path : str 
    branch : str = "master"
    files : list[Document]
    output_path : str
    chunked_files : list[dict]


graph = StateGraph(DocForgeState)

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

    for file in state["files"]:
        ending = "." + file.split(".")[-1]
        if ending in CODE_EXTENSIONS:
            try:
                file_metadata = extract_file_metadata(file, ending)
                output_path = f"./parsed_files/parsed_{file}.json"
                state["output_path"] = output_path
                with open(output_path, "w") as f:
                    json.dump(file_metadata, f)
            except (ValueError, OSError, RuntimeError, TypeError) as e:
                raise e
    return state

def chunk_documents(state : DocForgeState) -> DocForgeState:
    state["chunked_files"] = chunk_code(state["output_path"])
    return state




# graph.add_node("load_documents" , load_documents)


