from langgraph.graph import StateGraph, START, END
from langgraph.types import Send, interrupt, Command
from typing import TypedDict, Annotated
import operator
from ingestion.github_loader import load_repo
from langchain_core.documents import Document
from langchain_core.runnables import RunnableConfig
from constants.languages import CODE_EXTENSIONS, EXTENSION_TO_LANGUAGE
from parsing.global_parser import extract_file_metadata
import json
import glob
import os
from chunking.code_chunker import chunk_code
from embedding.embedding_service import load_all_documents, build_index, save_vector_store
from queries import CREATE_REPO_TABLE_QUERY, INSERT_REPO_QUERY
from symbol_index import build_symbol_index, build_call_graph, build_reverse_call_graph
from tools.refactoring_tools import get_radon_findings, get_ruff_findings, get_vulture_findings
from utilites.get_analysis import get_analysis
from utilites.b2_utils import upload_report
from utilites.workspace import (
    call_graph_path,
    chunked_dir,
    parsed_dir,
    repos_dir,
    reverse_call_graph_path,
    symbol_index_path,
    vector_store_dir,
)
from agents.architecture_agent import ArchitectureAgent
from agents.security_agent import SecurityAgent
from agents.refactoring_agent import RefactoringAgent
from agents.test_agent import TestAgent
from agents.judge_agent import JudgeAgent
from langgraph.checkpoint.postgres import PostgresSaver
from psycopg.rows import dict_row
from psycopg_pool import ConnectionPool
from dotenv import load_dotenv
from datetime import datetime

load_dotenv()

class DocForgeState(TypedDict):
    clone_url: str
    file_path: str
    branch: str
    workspace_dir: str
    files: list[Document]
    output_path: str
    chunked_files: list[dict]
    symbol_index: dict
    call_graph: dict
    reverse_call_graph: dict
    functions: list[str]
    file_name: str
    static_tools_findings: list[dict]
    agent_findings: Annotated[list[dict], operator.add]
    judge_report: str
    approved: bool
    final_report: str


graph = StateGraph(DocForgeState)

def get_file_name(state : DocForgeState) -> DocForgeState:
    state['file_name'] = state["file_path"].split("/")[-1]
    return state


def load_documents(state: DocForgeState) -> DocForgeState:
    if state["clone_url"] is None:
        raise ValueError("Repo path is required")

    if state["file_path"] is None:
        raise ValueError("File path is required")

    if not state.get("workspace_dir"):
        raise ValueError("workspace_dir is required")

    files = load_repo(
        state["clone_url"],
        state.get("branch") or "master",
        repos_root=repos_dir(state["workspace_dir"]),
    )
    return {"files": files}


def parse_documents(state: DocForgeState) -> DocForgeState:
    if state["files"] is None:
        raise ValueError("Files are required")

    ws = state["workspace_dir"]
    parsed_root = parsed_dir(ws)
    parsed_root.mkdir(parents=True, exist_ok=True)

    repo_name = state["clone_url"].split("/")[-1]
    repo_dir = str(repos_dir(ws) / repo_name)

    for document in state["files"]:
        file = document.metadata["file_path"]
        ending = "." + file.split(".")[-1]
        if ending in CODE_EXTENSIONS:
            file_metadata = extract_file_metadata(file, ending, repo_dir)
            output_path = parsed_root / f"parsed_{file}.json"
            with open(output_path, "w") as f:
                json.dump(file_metadata, f)
    return state


def chunk_documents(state: DocForgeState) -> DocForgeState:
    ws = state["workspace_dir"]
    out = chunked_dir(ws)
    chunked_files: list[dict] = []
    for parsed_path in sorted(glob.glob(str(parsed_dir(ws) / "parsed_*.json"))):
        chunked_files.extend(chunk_code(parsed_path, output_dir=out))
    state["chunked_files"] = chunked_files
    return state


def embed_documents(state: DocForgeState) -> DocForgeState:
    ws = state["workspace_dir"]
    pattern = str(chunked_dir(ws) / "chunked_*.json")
    documents = load_all_documents(pattern)
    index = build_index(documents)
    save_vector_store(index, documents, store_dir=vector_store_dir(ws))
    return state


def analyse_documents(state: DocForgeState) -> DocForgeState:
    ws = state["workspace_dir"]
    symbol_index: dict = {}
    for chunk_file in sorted(glob.glob(str(chunked_dir(ws) / "chunked_*.json"))):
        build_symbol_index(
            chunk_file,
            symbol_index,
            output_path=symbol_index_path(ws),
        )

    call_graph: dict = {}
    build_call_graph(
        call_graph,
        parsed_dir=parsed_dir(ws),
        output_path=call_graph_path(ws),
    )

    reverse_call_graph: dict = {}
    build_reverse_call_graph(
        call_graph,
        reverse_call_graph,
        output_path=reverse_call_graph_path(ws),
    )

    state["symbol_index"] = symbol_index
    state["call_graph"] = call_graph
    state["reverse_call_graph"] = reverse_call_graph
    state["functions"] = get_analysis(state["file_path"], workspace_dir=ws)
    return state


MAX_STATIC_FINDINGS = 30


def run_static_tools(state: DocForgeState) -> DocForgeState:
    ws = state["workspace_dir"]
    repo_name = state["clone_url"].split("/")[-1]
    disk_path = str(repos_dir(ws) / repo_name / state["file_path"])
    index_path = str(symbol_index_path(ws))
    findings: list[dict] = []
    findings.extend(get_ruff_findings(disk_path, index_path))
    findings.extend(get_radon_findings(disk_path, index_path))
    findings.extend(get_vulture_findings(disk_path, index_path))
    state["static_tools_findings"] = findings[:MAX_STATIC_FINDINGS]
    return state


AGENT_MODEL = "openai/gpt-oss-20b"


def architecture_agent(state: DocForgeState) -> dict:
    result = ArchitectureAgent(AGENT_MODEL).get_code(
        state["file_path"],
        state["static_tools_findings"],
        workspace_dir=state["workspace_dir"],
    )
    return {"agent_findings": [result]}


def security_agent(state: DocForgeState) -> dict:
    result = SecurityAgent(AGENT_MODEL).get_code(
        state["file_path"],
        state["static_tools_findings"],
        workspace_dir=state["workspace_dir"],
    )
    return {"agent_findings": [result]}


def refactoring_agent(state: DocForgeState) -> dict:
    result = RefactoringAgent(AGENT_MODEL).get_code(
        state["file_path"],
        state["static_tools_findings"],
        workspace_dir=state["workspace_dir"],
    )
    return {"agent_findings": [result]}


def test_agent(state: DocForgeState) -> dict:
    result = TestAgent(AGENT_MODEL).get_code(
        state["file_path"],
        state["static_tools_findings"],
        workspace_dir=state["workspace_dir"],
    )
    return {"agent_findings": [result]}


def router(state : DocForgeState) -> list[Send]:
    return [
        Send("architecture_agent", state),
        Send("security_agent", state),
        Send("refactoring_agent", state),
        Send("test_agent", state),
    ]


JUDGE_MODEL = "openai/gpt-oss-20b"


def judge_agent(state : DocForgeState) -> dict:
    judge = JudgeAgent(JUDGE_MODEL)
    report = judge.review(state["agent_findings"], state["functions"])
    return {"judge_report": report}


def human_approval(state : DocForgeState) -> dict:
    decision = interrupt({
        "judge_report": state["judge_report"],
        "action": "Approve to finalize the report, or reject.",
    })
    approved = str(decision).strip().lower() in {"approve", "approved", "yes", "y", "true"}
    return {"approved": approved}


def approval_router(state : DocForgeState) -> str:
    return "finalize_report" if state["approved"] else END


def finalize_report(state : DocForgeState, config: RunnableConfig) -> dict:
    thread_id = config["configurable"]["thread_id"]
    now = datetime.now()

    report_file_name = f"report_{state['file_name']}_{thread_id}.json"
    b2_result = upload_report(state["judge_report"], report_file_name)
    report_url = b2_result["publicUrl"]

    with _pool.connection() as conn:
        with conn.cursor() as cursor:
            cursor.execute(CREATE_REPO_TABLE_QUERY)
            cursor.execute(
                INSERT_REPO_QUERY,
                (
                    state["clone_url"],
                    state["file_path"],
                    thread_id,
                    report_url,
                    state["approved"],
                    now,
                    now,
                ),
            )

    print(f"[b2] uploaded {report_url}", flush=True)
    return {"final_report": state["judge_report"], "output_path": report_url}


graph.add_node("get_file_name", get_file_name)
graph.add_node("load_documents", load_documents)
graph.add_node("parse_documents", parse_documents)
graph.add_node("chunk_documents", chunk_documents)
graph.add_node("embed_documents", embed_documents)
graph.add_node("analyse_documents", analyse_documents)
graph.add_node("run_static_tools", run_static_tools)
graph.add_node("architecture_agent", architecture_agent)
graph.add_node("security_agent", security_agent)
graph.add_node("refactoring_agent", refactoring_agent)
graph.add_node("test_agent", test_agent)
graph.add_node("judge_agent", judge_agent)
graph.add_node("human_approval", human_approval)
graph.add_node("finalize_report", finalize_report)

graph.add_edge(START, "get_file_name")
graph.add_edge("get_file_name", "load_documents")
graph.add_edge("load_documents", "parse_documents")
graph.add_edge("parse_documents", "chunk_documents")
graph.add_edge("chunk_documents", "embed_documents")
graph.add_edge("embed_documents", "analyse_documents")
graph.add_edge("analyse_documents", "run_static_tools")

graph.add_conditional_edges(
    "run_static_tools",
    router,
    ["architecture_agent", "security_agent", "refactoring_agent", "test_agent"],
)

graph.add_edge("architecture_agent", "judge_agent")
graph.add_edge("security_agent", "judge_agent")
graph.add_edge("refactoring_agent", "judge_agent")
graph.add_edge("test_agent", "judge_agent")

graph.add_edge("judge_agent", "human_approval")

graph.add_conditional_edges(
    "human_approval",
    approval_router,
    ["finalize_report", END],
)

graph.add_edge("finalize_report", END)

_db_url = os.getenv("DATABASE_URL")
if not _db_url:
    raise ValueError("DATABASE_URL is not set in the environment")

_pool = ConnectionPool(
    conninfo=_db_url,
    max_size=10,
    kwargs={
        "autocommit": True,
        "prepare_threshold": 0,
        "row_factory": dict_row,
    },
)
_checkpointer = PostgresSaver(_pool)
_checkpointer.setup()

app = graph.compile(checkpointer=_checkpointer)


