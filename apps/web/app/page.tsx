"use client";

import { FormEvent, useState } from "react";

type Claim = { text: string; status: "supported" | "inference" | "unsupported"; citations: { document_name: string; quote: string }[] };
type ChatResponse = { answer: string; claims: Claim[]; limitations: string[]; trace: { run_id: string; loop_count: number; steps: { agent: string; summary: string; duration_ms: number }[] } };

const API = process.env.NEXT_PUBLIC_API_BASE_URL ?? "http://localhost:8000";

export default function Home() {
  const [question, setQuestion] = useState("What can ContextOps verify from my documents?");
  const [result, setResult] = useState<ChatResponse | null>(null);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);

  async function ask(event: FormEvent) {
    event.preventDefault();
    setLoading(true); setError(null);
    try {
      const response = await fetch(`${API}/v1/chat`, { method: "POST", headers: { "Content-Type": "application/json" }, body: JSON.stringify({ query: question, workspace_id: "demo" }) });
      if (!response.ok) throw new Error("The API could not complete this request.");
      const text = await response.text();
      const events = text.trim().split("\n\n");
      const complete = events.map((event) => event.split("\n").find((line) => line.startsWith("data: "))?.slice(6)).filter(Boolean).map((data) => JSON.parse(data!)).find((event) => event.type === "complete");
      setResult(complete?.data ?? null);
    } catch (cause) {
      setError(cause instanceof Error ? cause.message : "Unexpected error");
    } finally { setLoading(false); }
  }

  return <main>
    <nav><span className="brand">CONTEXT<span>OPS</span></span><a href={`${API}/docs`} target="_blank">API Docs</a></nav>
    <section className="hero"><p className="eyebrow">EXPLAINABLE AGENTIC RETRIEVAL</p><h1>Answers you can inspect, not just trust.</h1><p className="lede">ContextOps is an evidence-first knowledge API. It retrieves trusted context, verifies claims, and shows the source, agent trace, and limitations behind every answer.</p></section>
    <section className="workspace">
      <form onSubmit={ask}><label htmlFor="question">Ask the evidence layer</label><textarea id="question" value={question} onChange={(e) => setQuestion(e.target.value)} rows={3} /><button disabled={loading}>{loading ? "Verifying…" : "Run cited query"}</button></form>
      {error && <p className="error">{error}</p>}
      {result ? <article className="result"><div className="result-head"><p className="eyebrow">VERIFIED RESPONSE</p><span>Run {result.trace.run_id}</span></div><h2>{result.answer}</h2><div className="grid"><section><h3>Claims & evidence</h3>{result.claims.map((claim, index) => <div className="card" key={index}><span className={`badge ${claim.status}`}>{claim.status}</span><p>{claim.text}</p>{claim.citations.map((citation, c) => <blockquote key={c}><strong>{citation.document_name}</strong><br />“{citation.quote}”</blockquote>)}</div>)}</section><section><h3>Agent trace</h3>{result.trace.steps.map((step, index) => <div className="trace" key={index}><strong>{step.agent}</strong><span>{step.duration_ms}ms</span><p>{step.summary}</p></div>)}<h3>Limitations</h3>{result.limitations.map((limitation, index) => <p className="limitation" key={index}>{limitation}</p>)}</section></div></article> : <div className="empty"><p>Upload documents through the API, then use this panel to inspect claim support, citations, and the controlled agent loop.</p></div>}
    </section>
    <footer>REST + SSE · MCP-ready tools · claim-level evidence · human-approved actions</footer>
  </main>;
}
