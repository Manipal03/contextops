# Manipal Vector release roadmap

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

## Separate application track

The ContextOps web/API/MCP scaffold is experimental and currently disconnected
from the engine. Track its work separately: ingestion, embedding configuration,
real retrieval, accurate UI states, authentication, authorization, workspace
isolation, resource limits, dependency updates, observability, and deployment.
Passing engine tests does not validate this application stack.

## Working together

For each feature, agree on the user problem and acceptance criteria first.
Implement a small change, review the tradeoffs, verify it, and publish measured
progress. Keep the owner involved in the design so they can explain and maintain
the product. Avoid setting a release date until the supported scale and weekly
time budget are known.
