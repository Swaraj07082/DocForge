from fastapi import FastAPI
from pydantic import BaseModel
import uvicorn
from fastapi.middleware.cors import CORSMiddleware
import logging
from celery.result import AsyncResult

from tasks import celery_app, run_analysis, resume_analysis

app = FastAPI()
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

origins = [
    "http://localhost:5500",
    "http://127.0.0.1:5500/",
    "http://127.0.0.1:5500",
    "http://localhost:58149",
    "http://localhost:58149/",
]

app.add_middleware(
    CORSMiddleware,
    allow_origins=origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


class AnalyseRequest(BaseModel):
    clone_url: str
    file_path: str
    branch: str = "master"


class ApproveRequest(BaseModel):
    thread_id: str
    decision: str


@app.post("/analyse")
async def analyse(request: AnalyseRequest):
    """Enqueue analysis and return a task_id for polling."""
    task = run_analysis.delay(
        request.clone_url,
        request.file_path,
        request.branch or "master",
    )
    return {"status": "queued", "task_id": task.id}


@app.post("/approve")
async def approve(request: ApproveRequest):
    """Enqueue approve/reject resume and return a task_id for polling."""
    task = resume_analysis.delay(request.thread_id, request.decision)
    return {"status": "queued", "task_id": task.id}


@app.get("/tasks/{task_id}")
async def get_task_status(task_id: str):
    """Poll Celery for task state and result."""
    result = AsyncResult(task_id, app=celery_app)

    if result.state == "PENDING":
        return {"status": "pending", "task_id": task_id}

    if result.state == "STARTED":
        return {"status": "started", "task_id": task_id}

    if result.state == "FAILURE":
        return {
            "status": "failed",
            "task_id": task_id,
            "error": str(result.result),
        }

    if result.state == "SUCCESS":
        # Keep Celery "success" separate from the task's own status
        # (e.g. awaiting_approval / completed / rejected).
        return {
            "status": "success",
            "task_id": task_id,
            "result": result.result or {},
        }

    return {"status": result.state.lower(), "task_id": task_id}


if __name__ == "__main__":
    uvicorn.run("server:app", host="0.0.0.0", port=8000, reload=True)
