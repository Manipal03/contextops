# ContextOps

ContextOps is an early-stage project for investigating changes and conflicting
decisions across engineering specifications and meeting notes. The planned
product combines a dashboard, an API, and research/verification agents that
return findings with exact supporting passages and unresolved questions.

**Manipal Vector** is its independently usable Python vector search component,
built from scratch in this repository. The engine works today; connecting it
to the application is the next milestone.

This repository is a prototype and is not ready for production deployment.

## First product workflow (planned)

> Compare the original specification, revised specification, and meeting notes.
> What changed, what conflicts, and what needs clarification before release?

The intended workflow is upload -> retrieve passages -> investigate changes ->
verify findings -> inspect citations -> export a report. A later document is not
automatically authoritative: a proposed date change must not be reported as
approved without evidence.

## Design direction

- Ingestion: parsing, chunking, embeddings, document versions and source locations.
- Shared retrieval service: Manipal Vector, future keyword search and ranking.
- Investigation: research and verification agents with bounded follow-up searches.
- REST and MCP adapters: reuse application services and authorization checks.
- Next.js dashboard: document management, reports, and evidence inspection.

Embedding and agent dependencies belong outside the dependency-free engine.
The planned application owns workspace authorization; engine metadata filters
are not an authorization boundary. Similarity scores are not confidence
probabilities. Exact search stays the correctness baseline for future indexes.

## Repository contents

| Path | Status |
| --- | --- |
| `vector_engine/` | Working exact-search library and CLI |
| `tests/` | Engine correctness and CLI integration tests |
| `apps/web/` | Experimental ContextOps UI, separate from the engine |
| `services/api/` | Experimental chat API; retrieval is not implemented |
| `services/mcp/`, `packages/contracts/` | Plans for future adapters and contracts |
| `docker-compose.yml` | Development scaffold, not a production deployment |

The web/API scaffold does not yet use `VectorIndex` and cannot ingest documents.
Chat currently returns a placeholder; agent trace labels do not represent real
searches, claim verification, or LangGraph execution. SSE framing exists, but
processing currently finishes before events are emitted. MCP is not implemented.
PostgreSQL and Redis are development configuration only, not application persistence.
CI currently validates the engine and its packaging only. No live deployment is
claimed. See [the phased roadmap](ROADMAP.md) for acceptance criteria.

## Run the application scaffold locally

With Docker Compose available, run `docker compose up --build` from the repository
root. The dashboard is at `http://localhost:3000`, API documentation at
`http://localhost:8000/docs`, and health endpoint at `/v1/health`.
The Compose credentials are development defaults. This starts a prototype,
not a functional document investigation service.

## Manipal Vector

A Python 3.10+ vector search engine with no runtime dependencies. It stores
vectors and finds nearest records with exact search. It remains usable without
the ContextOps dashboard, an LLM, PostgreSQL, or Redis. Its first users are
developers embedding vector search in Python applications; priorities are
simple setup, predictable behavior, and transparent scoring.

## Run it

From this project directory, run these commands in PowerShell or a terminal:

```powershell
python -m vector_engine init --dimension 3
python -m vector_engine upsert --id lecture-1 --vector '[1,0,0]' --text 'Linear algebra notes'
python -m vector_engine upsert --id lecture-2 --vector '[0,1,0]' --text 'Thermodynamics notes'
python -m vector_engine search --vector '[0.9,0.1,0]' -k 2
python -m vector_engine stats
```

The first result is `lecture-1`, with cosine similarity about `0.994`.
These hand-written vectors demonstrate ranking; they are not text embeddings.
The default snapshot is `demo-index.json`. To choose another file, put
`--index path/to/index.json` before the subcommand. Its parent directory must exist.
Use `init --metric dot` or `init --metric euclidean` to select another metric.
`init` refuses to overwrite an existing index.

## Python API

```python
from vector_engine import VectorIndex

index = VectorIndex(dimension=3, metric="cosine")
index.upsert("lecture-1", [1, 0, 0],
             metadata={"course": "math", "semester": 1},
             text="Linear algebra notes")
index.upsert("lecture-2", [0, 1, 0], metadata={"course": "physics"})

for hit in index.search([0.9, 0.1, 0], k=5, filters={"course": "math"}):
    print(hit.id, hit.score, hit.text, hit.metadata)

index.save("demo-index.json")
restored = VectorIndex.load("demo-index.json")
restored.delete("lecture-2")
restored.save("demo-index.json")  # API changes are saved explicitly.
```

Upserting an existing ID replaces its vector, metadata, and text. Metadata must be
a JSON object. Filters combine top-level exact equality conditions with AND;
missing fields do not match null. Values use Python equality semantics (so `1`
and `True` compare equal). Filtering happens before selecting the best results.
Ties are broken by ID in ascending lexicographic order. `k` must be positive;
fewer than `k` results are returned when fewer records match.

## How search works

1. Validate the query's dimension and numeric values.
2. Normalize it for cosine search; stored vectors are normalized at insertion.
3. Scan records that match the metadata filter and compute similarity.
4. Keep the best `k` candidates using a heap and return them in score order.

| Metric | Returned score | Use |
| --- | --- | --- |
| `cosine` | Dot product of unit vectors, from -1 to 1 | Compare vector direction |
| `dot` | Raw dot product | Include vector magnitude in similarity |
| `euclidean` | Negative Euclidean distance | Compare geometric distance |

Higher scores always rank first. Cosine rejects zero vectors. All metrics reject
nonfinite vector components; unrepresentable scores produce an error.
Scores are similarities, not probabilities.

For `N` vectors of dimension `D`, a query takes approximately
`O(N * D + N * log(k))` time and retains `O(k)` candidates (for `k <= N`).
The index stores both raw and prepared vectors in memory. This implementation is
intended for learning and small datasets; Python objects add substantial memory
overhead compared with packed numeric arrays.

Snapshots contain versioned JSON and are validated on load. Saving writes a
temporary file alongside the destination, flushes it, and atomically replaces
the snapshot. Every CLI command loads the entire index, and every mutation
rewrites it. There is no concurrent-writer locking, transaction log, server,
authentication, or guarantee of durability after a machine power loss. Use one
writer at a time. The API is not thread-safe.

## Text search and future development

The engine accepts vectors; it does not generate embeddings. For semantic text
search, split documents into chunks, embed each chunk, and insert its vector with
its text and metadata. Embed each query with the same model and preprocessing,
then call `search`. Equal dimensions alone do not make different embedding models
compatible.

The next implementation stages are packed vector storage, a benchmark against
this exact-search baseline, and an approximate index such as HNSW. Measure recall
against exact results as well as latency before trading accuracy for speed.
Document ingestion and an HTTP API can then build on the same search interface.

## Verify

```powershell
python -m unittest discover -s tests -v
```

Tests cover metric rankings, top-k against an independent full sort, filtering,
updates, deletion, input validation, numerical extremes, snapshot validation,
and CLI persistence across separate processes.

GitHub Actions runs the engine tests on Windows and Linux with Python 3.10 and
3.13, installs the package, and checks the installed CLI. Workflow setup follows
[GitHub's Python CI documentation](https://docs.github.com/en/actions/tutorials/build-and-test-code/python).

## Development and building in public

Keep changes small: describe one user problem, add a regression test for changes
to search behavior, implement it, and run the test suite before opening a pull
request. Include measured results and known limitations in the PR description.
Keep tokens, private documents, and real user vectors out of commits and demos.

For each milestone, share a runnable example, the test or benchmark evidence,
one design decision, and the next limitation to tackle. Early progress posts
should describe this as a prototype rather than a production database.

No open-source license has been selected yet. Choose one before inviting reuse
or publishing a package release. Public repository visibility alone is not a
license grant.
