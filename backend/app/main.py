from __future__ import annotations
from uuid import uuid4
from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel, Field
from pydantic_settings import BaseSettings, SettingsConfigDict
from .workflow import OperationsWorkflow

class Settings(BaseSettings):
    openai_api_key: str = ""
    openai_model: str = "gpt-4.1-mini"
    cors_origins: str = "http://localhost:5174"
    model_config = SettingsConfigDict(env_file=".env", extra="ignore")

class RunRequest(BaseModel):
    objective: str = Field(min_length=10, max_length=3000)

class DecisionRequest(BaseModel):
    feedback: str = Field(default="", max_length=1000)

settings = Settings()
app = FastAPI(title="Agentic AI Operations Hub", version="1.0.0")
app.add_middleware(CORSMiddleware, allow_origins=[x.strip() for x in settings.cors_origins.split(",")], allow_credentials=True, allow_methods=["*"], allow_headers=["*"])
workflow = OperationsWorkflow(settings.openai_model)
runs: dict[str, dict] = {}

@app.get("/health")
def health() -> dict:
    return {"status": "ok", "configured": bool(settings.openai_api_key)}

@app.post("/api/runs", status_code=201)
def create_run(payload: RunRequest) -> dict:
    if not settings.openai_api_key:
        raise HTTPException(503, "OPENAI_API_KEY is not configured.")
    run_id = str(uuid4())
    state = workflow.start(payload.objective)
    runs[run_id] = dict(state)
    return {"id": run_id, **runs[run_id]}

@app.get("/api/runs/{run_id}")
def get_run(run_id: str) -> dict:
    if run_id not in runs:
        raise HTTPException(404, "Run not found.")
    return {"id": run_id, **runs[run_id]}

@app.post("/api/runs/{run_id}/approve")
def approve_run(run_id: str, payload: DecisionRequest) -> dict:
    if run_id not in runs:
        raise HTTPException(404, "Run not found.")
    state = runs[run_id]
    if state["status"] != "awaiting_approval":
        raise HTTPException(409, "Run is not awaiting approval.")
    if payload.feedback:
        state["events"].append({"agent": "human", "message": payload.feedback})
    runs[run_id] = dict(workflow.execute(state))
    return {"id": run_id, **runs[run_id]}

@app.post("/api/runs/{run_id}/reject")
def reject_run(run_id: str, payload: DecisionRequest) -> dict:
    if run_id not in runs:
        raise HTTPException(404, "Run not found.")
    runs[run_id]["status"] = "rejected"
    runs[run_id]["events"].append({"agent": "human", "message": payload.feedback or "Run rejected."})
    return {"id": run_id, **runs[run_id]}
