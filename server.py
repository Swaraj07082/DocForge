from fastapi import FastAPI
from pydantic import BaseModel
import uvicorn
from graph import app as graph
import uuid
from fastapi.middleware.cors import CORSMiddleware
import logging
import json
from langgraph.graph import Command

app = FastAPI()
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

origins = [
    "http://localhost:5500",
    "http://127.0.0.1:5500/",
    "http://127.0.0.1:5500",
    "http://localhost:58149",
    "http://localhost:58149/"
]

# 2. Add the CORSMiddleware to your FastAPI application
app.add_middleware(
    CORSMiddleware,
    allow_origins=origins,           # Allowed domains list
    allow_credentials=True,          # Allow cookies and authentication headers
    allow_methods=["*"],             # Allow all standard HTTP methods (GET, POST, etc.)
    allow_headers=["*"],             # Allow all custom or standard HTTP headers
)



class AnalyseRequest(BaseModel):
    clone_url : str
    file_path : str
    branch : str = "master"

class ApproveRequest(BaseModel):
    thread_id : str
    decision : str

@app.post("/analyse")
async def analyse(request : AnalyseRequest):
    
    thread_id = str(uuid.uuid4())
    config = {"configurable" : {"thread_id" : thread_id}}
    initial_state = {
        "clone_url" : request.clone_url,
        "file_path" : request.file_path,
        "branch" : request.branch or "master"
    }
    result = graph.invoke(initial_state , config = config)

    # logger.info(f"Analysis completed for thread {thread_id}")
    # logger.info(f"Result: {result}")

    interrupts = result["__interrupt__"]
    # logger.info(f"Interrupts: {interrupts}")

    if interrupts:
        payload = interrupts[0].value
        
        return {
            "status" : "awaiting_approval",
            "thread_id" : thread_id,
            "report" : json.loads(payload["judge_report"])
            }
    else:
        return {"status": "completed", "report": json.loads(result["final_report"])}

@app.post("/approve")
async def approve(request : ApproveRequest):
    config = {"configurable": {"thread_id": request.thread_id}}
    result = graph.invoke(Command(resume=request.decision), config=config)

    # On reject the graph ends without finalize_report, so this key is absent.
    final_report = result.get("final_report")
    if not final_report:
        return {"status": "rejected", "thread_id": request.thread_id}

    report = json.loads(final_report) if isinstance(final_report, str) else final_report
    return {"status": "completed", "report": report}



if __name__ == "__main__":
    
    uvicorn.run("server:app" , host = "0.0.0.0" , port = 8000 , reload = True) 

