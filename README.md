# DocForge

> **Multi-agent code review for a target file in a GitHub repository**

DocForge clones a repository, parses it with Tree-sitter, chunks functions and classes, **embeds chunks into a local FAISS index**, builds a **symbol index** and **call graph**, runs static analyzers (Ruff, Radon, Vulture), and runs parallel LLM review agents (architecture, security, refactoring, tests). A judge agent merges findings; you approve or reject the report via the API and frontend.

## Table of Contents

- [Motivation](#motivation)
- [Key Features](#key-features)
- [Context: graph vs vector store](#context-graph-vs-vector-store)
- [System Architecture](#system-architecture)
- [Tech Stack](#tech-stack)
- [Project Structure](#project-structure)
- [Running locally](#running-locally)
- [Development Roadmap](#development-roadmap)
- [Skills Demonstrated](#skills-demonstrated)

---

## Motivation

Teams need consistent, multi-perspective review of a file without manually stitching static tools, call-graph context, and LLM prompts. DocForge automates that pipeline and returns a structured JSON report with human-in-the-loop approval.

---

## Key Features

### Repository ingestion & parsing

- Clone a GitHub repo (branch configurable)
- Tree-sitter metadata extraction per supported language
- Function- and class-level chunking written to `chunked_files/`

### Embeddings & FAISS index (build only)

After chunking, the LangGraph pipeline runs `embed_documents`:

- Chunks are turned into LangChain `Document` objects (`embedding/embedding_service.py`)
- **BGE-small** embeddings with L2 normalization
- **FAISS IndexFlatIP** saved under `vector_store/` (`index.faiss`, `documents.pkl`)

This prepares the repo for semantic search; see [Context: graph vs vector store](#context-graph-vs-vector-store) for what actually feeds the agents today.

### Graph-based code context (used by agents)

- Symbol index mapping symbols to file, kind, and source
- Forward and reverse call graphs for each function
- Per-function payloads fed to review agents via `get_analysis` / `repo_analyser`

### Static analysis grounding

- Ruff, Radon, and Vulture findings (capped) passed into agent prompts as grounding signals

### Multi-agent review + judge

| Agent | Focus |
|-------|--------|
| Architecture | Design and structure |
| Security | Security issues |
| Refactoring | Maintainability |
| Test | Test coverage and quality |
| Judge | Consolidates agent outputs |

Human approval step before the final report is written to `reports/`.

---

## Context: graph vs vector store

| Component | Role in `/analyse` pipeline |
|-----------|----------------------------|
| Symbol index + call graphs | **Yes** — primary context for all review agents |
| FAISS vector store | **Built** during `embed_documents`, **not queried** by agents or `server.py` |

**Experimental vector search:** after a run (or `python -m embedding.embedding_service`), you can query the index manually with `app.py` (loads `vector_store/` and runs a sample k-NN search). `load_vector_store()` in `embedding_service.py` is available for future retrieval code.

There is no hybrid BM25 + vector retrieval or reranker in this repo yet; the README roadmap below lists that as future work.

---

## System Architecture

```text
GitHub Repository
        │
        ▼
Repository Ingestion (GitPython)
        │
        ▼
Tree-Sitter Parsing → parsed JSON
        │
        ▼
Code Chunking
        │
        ▼
Embeddings → FAISS (vector_store/)     ← built, not used by agents yet
        │
        ▼
Symbol Index + Call Graphs               ← agent context
        │
        ▼
Static Tools (Ruff, Radon, Vulture)
        │
        ▼
Parallel Review Agents (Groq)
        │
        ▼
Judge Agent
        │
        ▼
Human Approval (LangGraph interrupt)
        │
        ▼
Final JSON Report
```

---

## Tech Stack

| Layer | Technologies |
|-------|--------------|
| **API** | FastAPI, Uvicorn |
| **Workflow** | LangGraph |
| **LLM** | Groq (structured JSON outputs) |
| **Embeddings / index** | sentence-transformers (BGE-small), FAISS |
| **Code analysis** | Tree-sitter, Ruff, Radon, Vulture, Semgrep (tools module) |
| **Frontend** | Static HTML/JS (`frontend/index.html`) |

---

## Project Structure

```text
DocForge/
├── server.py              # FastAPI: /analyse, /approve
├── graph.py               # LangGraph pipeline (includes embed_documents)
├── app.py                 # Standalone FAISS query demo (not used by API)
├── embedding/
│   └── embedding_service.py
├── ingestion/
│   └── github_loader.py
├── parsing/
│   └── global_parser.py
├── chunking/
│   └── code_chunker.py
├── symbol_index.py        # Symbol index & call graphs
├── repo_analyser.py       # Per-symbol context for agents
├── context_retrieval.py   # Call-graph helpers (optional utilities)
├── agents/                # Architecture, security, refactor, test, judge
├── tools/                 # Static analysis wrappers
├── utilites/
│   ├── get_analysis.py
│   └── groq_utils.py
├── frontend/
│   └── index.html
└── requirements.txt
```

---

## Running locally

1. Create a virtual environment and install dependencies:

   ```bash
   pip install -r requirements.txt
   ```

2. Set `GROQ_API_KEY` in a `.env` file.

3. Start the API:

   ```bash
   python server.py
   ```

4. Open `frontend/index.html` (e.g. with Live Server) and point it at `http://localhost:8000`.

**API**

- `POST /analyse` — body: `{ "clone_url", "file_path", "branch?" }` → returns judge report and `thread_id` when awaiting approval
- `POST /approve` — body: `{ "thread_id", "decision" }` → finalize or reject

**Optional — test vector search after indexing:**

```bash
python app.py
```

Requires an existing `vector_store/` from a prior `/analyse` run or `python embedding/embedding_service.py`.

---

## Development Roadmap

- **Wire retrieval into agents** — query FAISS (and optionally BM25) to augment symbol/call-graph context
- **Hybrid retrieval** — reciprocal rank fusion and cross-encoder reranking
- **Documentation generation & drift detection**
- **PR webhooks and incremental re-indexing**
- **Graph database** (e.g. Neo4j) for large dependency graphs

---

## Skills Demonstrated

- LangGraph multi-step and multi-agent workflows
- Tree-sitter code parsing and chunking
- Embedding pipelines and FAISS indexing
- Call-graph–driven context for LLM prompts
- Static analysis integration with LLM review
- FastAPI + human-in-the-loop interrupts
- Structured LLM outputs (JSON schema)
