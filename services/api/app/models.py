from enum import StrEnum
from pydantic import BaseModel, Field


class SupportStatus(StrEnum):
    supported = "supported"
    inference = "inference"
    unsupported = "unsupported"


class ChatRequest(BaseModel):
    query: str = Field(min_length=3, max_length=4000)
    workspace_id: str = Field(min_length=1, max_length=128)
    session_id: str | None = None


class Citation(BaseModel):
    document_id: str
    document_name: str
    chunk_id: str
    quote: str
    page: int | None = None
    retrieval_score: float = Field(ge=0, le=1)
    reranker_score: float = Field(ge=0, le=1)


class Claim(BaseModel):
    text: str
    status: SupportStatus
    confidence: float = Field(ge=0, le=1)
    citations: list[Citation] = []


class TraceStep(BaseModel):
    agent: str
    summary: str
    duration_ms: int = Field(ge=0)


class AgentTrace(BaseModel):
    run_id: str
    loop_count: int = Field(ge=0)
    steps: list[TraceStep]


class ChatResponse(BaseModel):
    answer: str
    claims: list[Claim]
    limitations: list[str]
    trace: AgentTrace
