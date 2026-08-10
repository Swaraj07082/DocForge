# DocForge

> **Status: complete** — multi-agent code review for a target file in a GitHub repository

DocForge clones a repo, parses it with Tree-sitter, chunks functions and classes, builds a FAISS index, symbol index, and call graph, runs static analyzers (Ruff, Radon, Vulture), then fans out parallel LLM review agents (architecture, security, refactoring, tests). A judge agent merges findings; a human approves or rejects via the Next.js UI. Approved reports are stored in Postgres and uploaded to Backblaze B2.

Originally scoped as a docs/RAG tool; the shipped product is **file-level multi-agent code review** with graph-backed context, async workers, and authenticated human-in-the-loop approval.

## Table of Contents

- [What it does](#what-it-does)
- [Key features](#key-features)
- [Context: graph vs vector store](#context-graph-vs-vector-store)
- [System architecture](#system-architecture)
- [Tech stack](#tech-stack)
- [Project structure](#project-structure)
- [Running locally](#running-locally)
- [API](#api)
- [Evaluation](#evaluation)
- [Out of scope](#out-of-scope)
- [Skills demonstrated](#skills-demonstrated)

---

## What it does

1. Authenticate with Google (Auth.js) → Next.js BFF mints a short-lived JWT for FastAPI
2. Submit a GitHub clone URL + file path
3. Celery worker runs the LangGraph pipeline (parse → chunk → embed → analyse → agents → judge)
4. Pipeline pauses for human approval
5. On approve: report uploaded to B2 and recorded in Postgres

---

## Key features

### Repository ingestion & parsing

- Clone a GitHub repo (branch configurable)
- Tree-sitter metadata extraction for supported languages
- Function- and class-level chunking into a per-run workspace

### Embeddings & FAISS index

- Chunks → LangChain `Document`s → **BGE-small** embeddings (L2-normalized)
- **FAISS IndexFlatIP** under the workspace `vector_store/`
- Index is built during the pipeline; agents today use call-graph context (see below)

### Graph-based code context (used by agents)

- Symbol index (symbol → file, kind, source)
- Forward and reverse call graphs
- Per-function payloads via `get_analysis` / `repo_analyser`

### Static analysis grounding

- Ruff, Radon, and Vulture findings (capped) injected into agent prompts

### Multi-agent review + judge

| Agent | Focus |
|-------|--------|
| Architecture | Design and structure |
| Security | Security issues |
| Refactoring | Maintainability |
| Test | Test coverage and quality |
| Judge | Consolidates agent outputs |

LangGraph `interrupt` for human approve/reject before finalization.

### Product surface

- **FastAPI** + **Celery** + **Redis** (async analyse / approve + task polling)
- **Postgres** checkpointer (LangGraph) and report metadata
- **Next.js** UI with Google OAuth and BFF proxy (`web/`)
- **Langfuse** tracing on analysis tasks
- **Backblaze B2** for approved report storage

---

## Context: graph vs vector store

| Component | Role in `/analyse` pipeline |
|-----------|----------------------------|
| Symbol index + call graphs | **Yes** — primary context for review agents |
| FAISS vector store | **Built** in `embed_documents`; **not queried** by agents |

Optional offline FAISS demo: `python app.py` after an index exists. No hybrid BM25 + vector retrieval in the shipped pipeline.

---

## System architecture

```text
Browser → Next.js (:3000)  [Google OAuth, httpOnly session]
              │
              │  BFF: short-lived JWT (Authorization: Bearer)
              ▼
         FastAPI (:8000)  → enqueue Celery task
              │
              ▼
         Celery worker + Redis
              │
              ▼
    LangGraph pipeline (Postgres checkpointer)
              │
   clone → parse → chunk → FAISS → symbol/call graph
              │
              ▼
   static tools → parallel agents → judge
              │
              ▼
        human approval (interrupt)
              │
         approve → B2 + Postgres
```

Auth detail and security notes: [`web/README.md`](web/README.md).

---

## Tech stack

| Layer | Technologies |
|-------|--------------|
| **API / workers** | FastAPI, Uvicorn, Celery, Redis |
| **Workflow** | LangGraph + PostgresSaver |
| **LLM** | Groq (structured JSON), Langfuse observability |
| **Embeddings** | sentence-transformers (BGE-small), FAISS |
| **Code analysis** | Tree-sitter, Ruff, Radon, Vulture, Semgrep |
| **Auth** | Auth.js (Google), BFF JWT (PyJWT / jose) |
| **Storage** | Postgres, Backblaze B2 |
| **Frontend** | Next.js 15, React 19 |
| **Ops** | Docker Compose (api, worker, redis, postgres) |

---

## Project structure

```text
DocForge/
├── server.py                 # FastAPI: /analyse, /approve, /tasks/{id}, /me
├── tasks.py                  # Celery jobs + Langfuse
├── graph.py                  # LangGraph pipeline
├── app.py                    # Standalone FAISS query demo
├── embedding/
├── ingestion/
├── parsing/
├── chunking/
├── agents/                   # architecture, security, refactor, test, judge
├── tools/                    # static analysis wrappers
├── utilites/                 # auth, workspace, B2, Groq helpers
├── evals/                    # groundedness LLM-judge + JWT smoke tests
├── web/                      # Next.js Auth.js + BFF + analyse UI
├── docker-compose.yml
├── Dockerfile
└── requirements.txt
```

---

## Running locally

### Backend (Docker)

1. Set env in `.env` (at least `GROQ_API_KEY`, `AUTH_SECRET`, plus B2 keys if uploading reports). Compose sets `DATABASE_URL` / `REDIS_URL`.
2. Start infrastructure and API/worker:

   ```bash
   docker compose up --build
   ```

   API: `http://localhost:8000` · Redis · Postgres

### Frontend

```bash
cd web
cp .env.local.example .env.local   # AUTH_GOOGLE_*, AUTH_SECRET (same as API), etc.
npm install
npm run dev
```

Open `http://localhost:3000` → Google sign-in → analyse UI. See [`web/README.md`](web/README.md) for OAuth redirect setup.

### Without Docker (API only)

```bash
pip install -r requirements.txt
# Redis + Postgres running; DATABASE_URL and REDIS_URL set
uvicorn server:app --reload --port 8000
celery -A tasks.celery_app worker --loglevel=info --concurrency=1
```

---

## API

All analyse/approve/task routes require `Authorization: Bearer <JWT>` from the Next.js BFF (shared `AUTH_SECRET`).

| Method | Path | Purpose |
|--------|------|---------|
| `GET` | `/health` | Liveness |
| `GET` | `/me` | JWT claims smoke check |
| `POST` | `/analyse` | `{ clone_url, file_path, branch? }` → `{ status: "queued", task_id }` |
| `POST` | `/approve` | `{ thread_id, decision }` → queued resume |
| `GET` | `/tasks/{task_id}` | Poll Celery state / result (`awaiting_approval`, etc.) |

---

## Evaluation

- **Groundedness (LLM-as-judge):** `python -m evals.llm_judge` over report findings vs `affected_code`
- **Auth contract:** `python -m evals.test_auth_jwt`

---

## Out of scope

Not implemented in this completed scope (possible extensions):

- Querying FAISS / hybrid BM25 from inside review agents
- Auto documentation generation and drift detection
- PR webhooks and incremental re-indexing
- Graph DB (e.g. Neo4j) for very large dependency graphs

---

## Skills demonstrated

- LangGraph multi-agent workflows with human-in-the-loop interrupts
- Celery async jobs + Redis + Postgres checkpointing
- Tree-sitter parsing, chunking, and call-graph context for LLMs
- Static analysis grounded into structured LLM review
- Next.js BFF auth (Google OAuth → short-lived API JWT)
- Observability (Langfuse) and offline groundedness eval
- Dockerized API + worker stack with object storage for reports
