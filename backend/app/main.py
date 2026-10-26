
import os
from pathlib import Path

from dotenv import load_dotenv
from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware

from .schemas import ProspectInput
from .database import (
    init_db,
    save_result,
    get_leads,
    get_runs,
    get_analytics,
)
from .agents import run_pipeline

# Load backend/.env
BACKEND_DIR = Path(__file__).resolve().parent.parent
load_dotenv(BACKEND_DIR / ".env")

CONTEXT_DEV_API_KEY = os.getenv("CONTEXT_DEV_API_KEY")

app = FastAPI(
    title="GTM Pulse API",
    version="1.0.0",
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=[
        "http://localhost:5173",
        "http://127.0.0.1:5173",
    ],
    allow_methods=["*"],
    allow_headers=["*"],
)


@app.on_event("startup")
def startup():
    init_db()


@app.get("/api/health")
def health():
    return {
        "status": "ok",
        "service": "GTM Pulse API",
        "context_api_configured": bool(CONTEXT_DEV_API_KEY),
    }


@app.post("/api/pipeline/run")
def pipeline_run(p: ProspectInput):
    try:
        result = run_pipeline(p)
        result["lead_id"] = save_result(p, result)
        return result
    except Exception as exc:
        raise HTTPException(
            status_code=500,
            detail=f"Pipeline execution failed: {exc}",
        )


@app.get("/api/leads")
def leads():
    return get_leads()


@app.get("/api/runs")
def runs():
    return get_runs()


@app.get("/api/analytics")
def analytics():
    return get_analytics()


@app.get("/")
def root():
    return {
        "message": "GTM Pulse API is running",
        "docs": "/docs",
    }
