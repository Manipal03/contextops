# ContextOps build roadmap

## Product and first release

Build an engineering-document investigation tool: compare specifications and
meeting notes, identify changes and conflicting decisions, and return evidence
with unresolved questions. Manipal Vector remains an independent Python library
and supplies the exact vector-search baseline.

Current state: working engine and CLI, experimental web/API scaffold, no ingestion,
real retrieval integration, agent execution, claim verification, or MCP server.
The gates below describe future work, not completed capabilities.

## Initial evaluation workload

- 30 fictional engineering documents across five project scenarios.
- Original/revised specifications, meeting notes, and decision records.
- Approximately 100 manually labeled questions, including conflicts and missing evidence.
- Initial development ceiling of 5,000 chunks; measure actual memory and latency.
- Separate development and held-out scenarios to avoid tuning on the final evaluation.
- Later engine benchmarks at 10,000 and 50,000 vectors, not promised capacity.

Record embedding model/revision, dimensions, tokenizer, chunking configuration,
dataset provenance, hardware, and query concurrency with each result.

## Phase 0: accurate foundation

- [ ] Replace placeholder UI/trace claims with accurate capability states.
- [ ] Make retrieval scores metric-aware; do not require all scores to be 0-1.
- [ ] Extend validation beyond the engine to the application and frontend.

Gate: documented status matches actual behavior and engine checks still pass.

## Phase 1: real document retrieval

- [ ] Select a local embedding model after a small hardware/quality experiment.
- [ ] Add TXT/Markdown and text-based PDF extraction with source references.
- [ ] Add document/version/chunk identifiers and tokenizer-aware chunking.
- [ ] Persist model identity and preprocessing settings; reject incompatible queries.
- [ ] Implement a shared retrieval service and `/v1/search` over Manipal Vector.
- [ ] Persist and reload index data; specify one controlled writer and crash behavior.
- [ ] Design workspace ownership and authorization before exposing private documents.

Gate: ingestion -> search -> exact source reference works after a restart.

## Phase 2: retrieval evaluation

- [ ] Build labeled questions and relevance judgments.
- [ ] Compare dense-only, keyword-only, hybrid fusion, and reranking.
- [ ] Report Recall@k/ranking quality, latency, memory, and failure cases.
- [ ] Separate text relevance from approximate-index recall against exact search.

Gate: reproducible results explain whether each added stage helps.

## Phase 3: evidence-backed investigations

- [ ] Generate structured changes, conflicts, and unresolved questions.
- [ ] Map factual claims to precise passages and document versions.
- [ ] Distinguish proposed, approved, superseded, and unresolved decisions.
- [ ] Build an evidence viewer and exportable report.
- [ ] Evaluate citation correctness, missed conflicts, false alarms, and abstention.

Gate: a user can inspect both sides of a conflict and verify each reported finding.

## Phase 4: real research and verification agents

- [ ] Research agent selects searches and gathers missing evidence.
- [ ] Verification agent challenges findings with specific evidence gaps.
- [ ] Coordinator enforces step/time/token budgets and stopping conditions.
- [ ] Emit actual execution events; support cancellation and persist run state.
- [ ] Compare ordinary RAG, one agent, and multiple agents on the same held-out tasks.

Gate: follow-up searches are real and their quality/cost/latency tradeoff is measured.

## Phase 5: API and MCP product

- [ ] Add versioned investigation/run endpoints and developer examples.
- [ ] Add authenticated MCP tools using the same application services.
- [ ] Add scoped API keys, limits, consistent errors, and run access checks.
- [ ] Add action preview/approval/execution only after read-only investigation works.

Gate: another developer completes the workflow using the documentation alone.

## Phase 6: public beta operations

- [ ] Test cross-workspace access denial, updates, deletion, and index consistency.
- [ ] Test retries, recovery, backups/restores, and interrupted ingestion.
- [ ] Add usage budgets, redacted logs, metrics, and operational alerts.
- [ ] Validate Docker deployment and publish measured supported limits.
- [ ] Run a small user pilot and address observed failures.

Gate: the complete workflow operates reliably within documented limits.

## Planning cadence

Working estimate for full-time solo development: weeks 1-2 for integration and
retrieval evaluation, week 3 for reports, week 4 for agents, week 5 for API/MCP,
and week 6 onward for beta operations. Re-estimate after phase 1; this is not a
release commitment. Track each phase by its acceptance gate rather than a date.

## Manipal Vector component roadmap

## Product direction

Build an embeddable Python vector search engine for developers who value simple
setup and understandable results. Keep the engine usable without a server or
external service. The initial interface is `VectorIndex` plus a CLI.

This roadmap is a proposal, not a claim that the gates below have passed.

## Milestone 1: reproducible developer preview

- [x] Exact cosine, dot-product, and Euclidean search.
- [x] Metadata filtering, replacement, deletion, and versioned snapshots.
- [x] Correctness tests and CLI integration tests.
- [x] Define automated engine tests and installation checks for Windows and Linux.
- [ ] Choose an open-source license and confirm package naming availability.
- [ ] Add a reproducible example using real embeddings, with model and dataset provenance.
- [ ] Have three developers install the package and run a query without assistance.

Exit gate: a clean environment can install the package and execute the documented
example; first-user feedback identifies a concrete use case and confusing steps.

## Milestone 2: measure and explain search

- [ ] Record reproducible insertion, search, save, and load benchmarks.
- [ ] Report dataset size, dimensions, metric, filter selectivity, machine, memory,
      warmup, query count, and p50/p95/p99 query latency with each result.
- [ ] Add an explanation interface showing metric, candidate counts, applied
      filters, and deterministic tie handling.
- [ ] Define the initial supported vector count, dimensions, memory budget,
      latency target, and concurrency model from actual user needs.
- [ ] Test malformed snapshots, interrupted saves, and filesystem errors.

Exit gate: benchmark results are reproducible and the supported envelope is
documented with evidence. Do not advertise scale from synthetic timing alone.

## Milestone 3: reliable storage and larger indexes

- [ ] Design an explicit single-writer or coordinated-writer contract.
- [ ] Introduce packed numeric storage with a documented precision policy.
- [ ] Add recovery, backup/restore, and format migration tests before changing persistence.
- [ ] Preserve exact search as the correctness reference.
- [ ] Add an approximate index only after measurements justify it; measure
      recall@k against exact search alongside latency and memory.

Exit gate: supported failure scenarios recover without silent data loss;
performance and approximation tradeoffs are published.

## Milestone 4: supported release

- [ ] Stabilize the public API, error types, versioning, and compatibility policy.
- [ ] Publish installation docs, limitations, changelog, and migration guidance.
- [ ] Test wheel and source-distribution installation in clean environments.
- [ ] Complete dependency, license, and security reviews for the shipped components.
- [ ] Establish a private vulnerability-reporting channel and maintenance policy.
- [ ] Run a small beta against real applications and resolve release-blocking feedback.

Exit gate: every supported claim has test, benchmark, or beta evidence. Publish
to a package registry only after naming, licensing, and release approval are settled.

## ContextOps application track

The ContextOps web/API/MCP scaffold is experimental and currently disconnected
from the engine. Integrate the components through a retrieval interface; the
engine remains independently usable. Track application work: ingestion, embedding configuration,
real retrieval, accurate UI states, authentication, authorization, workspace
isolation, resource limits, dependency updates, observability, and deployment.
Passing engine tests does not validate this application stack.

## Working together

For each feature, agree on the user problem and acceptance criteria first.
Implement a small change, review the tradeoffs, verify it, and publish measured
progress. Keep the owner involved in the design so they can explain and maintain
the product. Avoid setting a release date until the supported scale and weekly
time budget are known.
