# Manipal Vector

A vector search engine built from scratch in Python, using only the standard library.
It stores vectors and finds the nearest records with exact search. No vector database,
NumPy, or external service is required. Python 3.10 or later is required.

**Status: early prototype, not production-ready.** The first product targets
developers embedding search in Python applications. The priorities are simple
setup, predictable behavior, and transparent scoring. See [the release roadmap](ROADMAP.md)
for the work required before a supported release.

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
Its interface includes planned capabilities. PostgreSQL and Redis are not required
for the Python engine. CI currently validates the engine and its packaging only.
The scaffold's dependency and security review is still pending; do not expose it
as a production service.

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
