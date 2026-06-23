"""
FastAPI entrypoint.

GET /api/search/stream?query=... — Server-Sent Events stream of the
live investigation feed (Section 10 of the build plan). The frontend
opens this with a plain EventSource and renders each event as it
arrives.
"""
import json

from fastapi import FastAPI, Query
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import StreamingResponse

from app.db import init_db
from app.orchestrator import run_search

app = FastAPI(title="EvidenceIQ")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["*"],
    allow_headers=["*"],
)


@app.on_event("startup")
def on_startup():
    init_db()


@app.get("/api/search/stream")
async def search_stream(
    query: str = Query(..., description='e.g. "Cardiologists in Birmingham"'),
    refresh: bool = False,
):
    async def event_generator():
        async for event in run_search(query, force_refresh=refresh):
            yield f"data: {json.dumps(event, default=str)}\n\n"

    return StreamingResponse(event_generator(), media_type="text/event-stream")


@app.get("/api/health")
def health():
    return {"status": "ok"}
