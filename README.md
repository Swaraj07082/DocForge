# DocPilot AI

> **AI-Powered Documentation Engineer for Software Teams**

DocPilot AI is a production-grade Retrieval-Augmented Generation (RAG) system that automatically understands software repositories, answers codebase questions, generates documentation, detects outdated docs, and assists engineering teams in maintaining accurate technical knowledge.

The project combines **Hybrid Search**, **FAISS**, **LangGraph Agents**, **Code Parsing**, **Knowledge Graphs**, and **Large Language Models** to create an intelligent documentation assistant capable of understanding complex software systems.

## Table of Contents

- [Motivation](#motivation)
- [Key Features](#key-features)
- [System Architecture](#system-architecture)
- [Tech Stack](#tech-stack)
- [Project Structure](#project-structure)
- [Development Roadmap](#development-roadmap)
- [Example Queries](#example-queries)
- [Skills Demonstrated](#skills-demonstrated)
- [Resume Description](#resume-description)

---

## Motivation

Software documentation becomes outdated rapidly as repositories evolve. Engineering teams frequently face:

- Missing API documentation
- Stale README files
- Inconsistent architecture diagrams
- Difficult onboarding processes
- Time-consuming codebase exploration
- Lack of documentation reviews during pull requests

DocPilot AI addresses these problems by acting as an autonomous **Documentation Engineer**.

---

## Key Features

### Repository Intelligence

- Parse entire repositories
- Understand project structure
- Extract classes, functions, and APIs
- Track code relationships

### AI-Powered Code Search

Ask natural language questions about the codebase.

**Example query:**

```text
How is JWT authentication implemented?
```

The system retrieves relevant code and documentation before generating an answer with citations.

### Documentation Generation

Automatically generate:

- API documentation
- Function descriptions
- Class documentation
- README sections
- Usage examples

**Input:**

```python
@app.post("/users")
def create_user():
    pass
```

**Generated output:**

```markdown
### Create User

POST /users

Creates a new user.

Request Body:
{
    "email": "string",
    "name": "string"
}
```

### Documentation Drift Detection

Detect inconsistencies between source code and documentation.

| Documentation | Code |
|---------------|------|
| `POST /users` | `POST /api/v2/users` |

**Output:** Documentation appears outdated.

### Pull Request Review Assistant

Automatically analyze pull requests and identify:

- Missing documentation
- Changed API contracts
- Outdated examples
- Required README updates

### Knowledge Graph Retrieval

Build relationships between components:

```text
Controller
 └── Service
      └── Repository
           └── Database
```

This enables graph-based retrieval beyond simple vector search.

---

## System Architecture

```text
GitHub Repository
        │
        ▼
Repository Ingestion
        │
        ▼
Tree-Sitter Parsing
        │
        ▼
Metadata Extraction
        │
        ▼
Chunking
        │
        ▼
Embeddings
        │
        ▼
FAISS Vector Store
        │
        ▼
Hybrid Retrieval
(BM25 + Vector Search)
        │
        ▼
Cross Encoder Reranker
        │
        ▼
LangGraph Agent
        │
        ▼
Generated Answers
Documentation Updates
```

---

## Tech Stack

| Layer | Technologies |
|-------|--------------|
| **Backend** | Python, FastAPI |
| **RAG Framework** | LangChain, LangGraph |
| **Retrieval** | FAISS, BM25, Reciprocal Rank Fusion, Cross Encoder Reranker |
| **Code Analysis** | Tree-Sitter |
| **Graph Layer** | NetworkX, Neo4j *(future)* |
| **Embeddings** | OpenAI Embeddings, BGE Large |
| **Frontend** | Next.js, TypeScript, Tailwind CSS |
| **Database** | PostgreSQL, Redis |

---

## Project Structure

```text
docpilot-ai/
├── backend/
├── ingestion/
│   ├── github_loader.py
│   └── file_loader.py
├── parsing/
│   ├── tree_sitter_parser.py
│   └── metadata_extractor.py
├── chunking/
│   └── code_chunker.py
├── embeddings/
│   └── embedding_service.py
├── vectorstore/
│   └── faiss_store.py
├── retrieval/
│   ├── bm25.py
│   ├── hybrid_search.py
│   └── reranker.py
├── graph/
│   └── dependency_graph.py
├── agents/
│   ├── retriever_agent.py
│   ├── documentation_agent.py
│   └── reviewer_agent.py
├── api/
│   └── routes.py
├── frontend/
├── evaluations/
├── tests/
└── README.md
```

---

## Development Roadmap

### Phase 1 — Repository Ingestion

**Objectives:**

- Clone repositories
- Read project files
- Extract metadata
- Convert files into Documents

**Deliverable:**

```python
Document(
    page_content=chunk,
    metadata={
        "file": "auth.py",
        "language": "python"
    }
)
```

### Phase 2 — Code Chunking

- Function-level chunking
- Class-level chunking
- Documentation chunking

> Avoid naive fixed-length chunks.

### Phase 3 — Embeddings & FAISS

```text
Code Chunk → Embedding → L2 Normalization → FAISS IndexFlatIP
```

Store metadata separately.

### Phase 4 — Hybrid Search

1. BM25 Search
2. Vector Search
3. Reciprocal Rank Fusion

```text
Query → BM25 → FAISS → Fusion
```

### Phase 5 — Reranking

Model: `bge-reranker-large`

```text
Top 20 Retrieval Results → Reranker → Top 5 Results
```

### Phase 6 — Question Answering

```text
User Query → Retrieve → Rerank → LLM → Answer
```

Include source citations.

### Phase 7 — Documentation Generation

Generate API, function, and class documentation plus usage examples.

### Phase 8 — Drift Detection

Compare documentation against current source code. Detect:

- Endpoint changes
- Parameter changes
- Renamed functions
- Missing documentation

### Phase 9 — Knowledge Graph

Extract imports, dependencies, function calls, and module references. Build graph relationships for Graph RAG.

### Phase 10 — Multi-Agent Workflow

| Agent | Role |
|-------|------|
| **Retriever Agent** | Finds relevant context |
| **Documentation Agent** | Generates documentation |
| **Reviewer Agent** | Validates generated output |
| **Drift Agent** | Detects documentation inconsistencies |

```text
User Query → Retriever → Documentation Agent → Reviewer Agent → Final Output
```

---

## Future Enhancements

- GitHub Webhooks
- Incremental Indexing
- Neo4j Graph Database
- CI/CD Integration
- Slack Integration
- Confluence Integration
- Automated PR Comments
- Multi-Repository Support
- Codebase Visualization
- Architecture Diagram Generation

---

## Example Queries

- `How does authentication work?`
- `Which services call PaymentService?`
- `Generate documentation for UserController.`
- `Find outdated API documentation.`
- `Explain the checkout workflow.`

---

## Skills Demonstrated

- Retrieval-Augmented Generation (RAG)
- LangGraph Agents
- FAISS
- Hybrid Retrieval
- Tree-Sitter
- Graph RAG
- FastAPI
- Next.js
- Information Retrieval
- LLM Engineering
- Software Architecture
- Agentic Workflows
- Production AI Systems

---

## Resume Description

> Built a production-grade AI Documentation Engineer that automatically analyzes software repositories, generates technical documentation, detects documentation drift, and answers codebase-related questions. Implemented hybrid retrieval using BM25, FAISS, reranking models, and graph-based code understanding with LangGraph agent workflows for repository intelligence and automated documentation maintenance.
