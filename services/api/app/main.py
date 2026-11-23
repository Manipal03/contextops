from __future__ import annotations

import json
from collections.abc import AsyncIterator

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import StreamingResponse

from app.config import settings
from app.models import ChatRequest
from app.services.agent import agent_service

app = FastAPI(
    title="ContextOps API",
    version="0.1.0",
    description="Evidence-first, explainable multi-agent knowledge API.",
)
app.add_middleware(
    CORSMiddleware,
    allow_origins=[settings.web_origin],
    allow_credentials=True,
    allow_methods=["GET", "POST", "DELETE"],
    allow_headers=["Authorization", "Content-Type", "Idempotency-Key"],
)


@app.get("/v1/health", tags=["system"])
async def health() -> dict[str, str]:
    return {"status": "ok", "service": "contextops-api", "environment": settings.environment}


@app.post("/v1/chat", tags=["chat"])
async def chat(request: ChatRequest) -> StreamingResponse:
    response = agent_service.run(request)

    async def stream() -> AsyncIterator[str]:
        for step in response.trace.steps:
            yield f"event: agent_step\ndata: {json.dumps({'type': 'agent_step', 'data': step.model_dump()})}\n\n"
        yield f"event: complete\ndata: {json.dumps({'type': 'complete', 'data': response.model_dump()})}\n\n"

    return StreamingResponse(stream(), media_type="text/event-stream", headers={"Cache-Control": "no-cache", "X-Accel-Buffering": "no"})
