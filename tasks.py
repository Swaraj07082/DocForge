from celery import Celery
import os
import sys
import json
import uuid
from pathlib import Path

from dotenv import load_dotenv
from langfuse import get_client, observe

# Ensure project root is importable when Celery starts from another cwd.
_ROOT = Path(__file__).resolve().parent
if str(_ROOT) not in sys.path:
    sys.path.insert(0, str(_ROOT))

load_dotenv(_ROOT / ".env")

# Redis is both the message broker (queue) and the result store.
REDIS_URL = os.getenv("REDIS_URL", "redis://localhost:6379/0")

celery_app = Celery(
    "docforge",
    broker=REDIS_URL,
    backend=REDIS_URL,
)

# broker — where tasks are queued (Redis)
# backend — where results are stored so you can check status later

celery_app.conf.update(
    task_serializer="json",
    result_serializer="json",
    accept_content=["json"],
    timezone="UTC",
    enable_utc=True,
)


@celery_app.task(bind=True, name="tasks.run_analysis")
@observe(name="run_analysis")
def run_analysis(self, clone_url: str, file_path: str, branch: str = "master"):
    """
    Background job: clone/analyse a repo file via the LangGraph pipeline.
    FastAPI can call this instead of blocking on graph.invoke(...).
    """
    # Import inside the task so the Celery worker only loads the heavy
    # graph stack when a job actually runs (not at worker startup import).
    from graph import app as graph
    from utilites.workspace import ensure_workspace

    try:
        thread_id = str(uuid.uuid4())
        workspace = ensure_workspace(thread_id)
        config = {"configurable": {"thread_id": thread_id}}
        initial_state = {
            "clone_url": clone_url,
            "file_path": file_path,
            "branch": branch or "master",
            "workspace_dir": str(workspace),
        }

        result = graph.invoke(initial_state, config=config)
        interrupts = result.get("__interrupt__")

        if interrupts:
            payload = interrupts[0].value
            return {
                "status": "awaiting_approval",
                "thread_id": thread_id,
                "report": json.loads(payload["judge_report"]),
            }

        return {
            "status": "completed",
            "thread_id": thread_id,
            "report": json.loads(result["final_report"]),
        }
    finally:
        get_client().flush()


@celery_app.task(bind=True, name="tasks.resume_analysis")
@observe(name="resume_analysis")
def resume_analysis(self, thread_id: str, decision: str):
    """Resume a paused graph after human approve/reject."""
    from langgraph.types import Command
    from graph import app as graph

    try:
        config = {"configurable": {"thread_id": thread_id}}
        result = graph.invoke(Command(resume=decision), config=config)

        final_report = result.get("final_report")
        if not final_report:
            return {"status": "rejected", "thread_id": thread_id}

        report = json.loads(final_report) if isinstance(final_report, str) else final_report
        return {"status": "completed", "thread_id": thread_id, "report": report}
    finally:
        get_client().flush()
