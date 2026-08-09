from fastapi import Depends, FastAPI
from pydantic import BaseModel
import uvicorn
from fastapi.middleware.cors import CORSMiddleware
import logging
from celery.result import AsyncResult

from tasks import celery_app, run_analysis, resume_analysis
from utilites.auth import get_current_user

app = FastAPI()
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Browser talks to Next.js only; API is called server-to-server (BFF).
# Keep CORS tight — credentials not needed from the browser.
origins = [
    "http://localhost:3000",
    "http://127.0.0.1:3000",
]

app.add_middleware(
    CORSMiddleware,
    allow_origins=origins,
    allow_credentials=False,
    allow_methods=["GET", "POST", "OPTIONS"],
    allow_headers=["Authorization", "Content-Type"],
)


class AnalyseRequest(BaseModel):
    clone_url: str
    file_path: str
    branch: str = "master"


class ApproveRequest(BaseModel):
    thread_id: str
    decision: str


@app.get("/health")
async def health():
    return {"status": "ok"}


@app.get("/me")
async def me(user: dict = Depends(get_current_user)):
    """Return claims from the BFF JWT — useful for auth smoke tests."""
    return {
        "sub": user.get("sub"),
        "email": user.get("email"),
        "name": user.get("name"),
    }


@app.post("/analyse")
async def analyse(
    request: AnalyseRequest,
    user: dict = Depends(get_current_user),
):
    """Enqueue analysis and return a task_id for polling."""
    logger.info("analyse requested by sub=%s email=%s", user.get("sub"), user.get("email"))
    task = run_analysis.delay(
        request.clone_url,
        request.file_path,
        request.branch or "master",
    )
    return {"status": "queued", "task_id": task.id}


@app.post("/approve")
async def approve(
    request: ApproveRequest,
    user: dict = Depends(get_current_user),
):
    """Enqueue approve/reject resume and return a task_id for polling."""
    logger.info("approve requested by sub=%s decision=%s", user.get("sub"), request.decision)
    task = resume_analysis.delay(request.thread_id, request.decision)
    return {"status": "queued", "task_id": task.id}


@app.get("/tasks/{task_id}")
async def get_task_status(
    task_id: str,
    user: dict = Depends(get_current_user),
):
    """Poll Celery for task state and result."""
    _ = user  # auth required; task IDs are unguessable UUIDs
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
