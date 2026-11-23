from __future__ import annotations

from dataclasses import dataclass, field
from time import perf_counter
from uuid import uuid4

from app.config import settings
from app.models import AgentTrace, ChatRequest, ChatResponse, Claim, SupportStatus, TraceStep


@dataclass
class AgentState:
    """Serializable state designed for a future LangGraph graph."""

    query: str
    workspace_id: str
    run_id: str = field(default_factory=lambda: f"run_{uuid4().hex[:12]}")
    loop_count: int = 0
    steps: list[TraceStep] = field(default_factory=list)

    def trace(self, agent: str, summary: str, started: float) -> None:
        self.steps.append(TraceStep(agent=agent, summary=summary, duration_ms=round((perf_counter() - started) * 1000)))


class EvidenceFirstAgent:
    """Safe baseline: returns only information backed by indexed evidence.

    Retrieval and verifier implementations will replace the empty evidence list
    without changing the public API or the REST/MCP adapters.
    """

    def run(self, request: ChatRequest) -> ChatResponse:
        state = AgentState(query=request.query, workspace_id=request.workspace_id)
        started = perf_counter()
        evidence: list[dict[str, str]] = []
        state.trace("retrieval_agent", "Searched the workspace evidence index using the current query.", started)

        started = perf_counter()
        if not evidence and state.loop_count < settings.agent_max_loops:
            state.loop_count += 1
            state.trace("evidence_agent", "No indexed evidence is available yet; a refinement loop was not useful without documents.", started)
        else:
            state.trace("evidence_agent", "Verified candidate claims against retrieved evidence.", started)

        started = perf_counter()
        answer = "I cannot verify an answer yet because this workspace has no indexed source documents. Upload a PDF, CSV, TXT, or Markdown document first."
        claims = [Claim(text="The workspace has no indexed source documents.", status=SupportStatus.unsupported, confidence=0.0, citations=[])]
        state.trace("synthesis_agent", "Returned an evidence-insufficient response instead of generating an unsupported answer.", started)

        return ChatResponse(
            answer=answer,
            claims=claims,
            limitations=["No ingested documents are available for retrieval.", "No external action or MCP tool was called."],
            trace=AgentTrace(run_id=state.run_id, loop_count=state.loop_count, steps=state.steps),
        )


agent_service = EvidenceFirstAgent()
