"""In-memory flat index with explicit, atomic JSON snapshots."""

from dataclasses import dataclass
import heapq
import json
import math
import os
from pathlib import Path
import tempfile


def _json_object(value):
    if not isinstance(value, dict):
        raise ValueError("metadata and filters must be JSON objects")

    def validate(item):
        if item is None or isinstance(item, (str, bool, int)):
            return
        if isinstance(item, float) and math.isfinite(item):
            return
        if isinstance(item, list):
            for child in item:
                validate(child)
            return
        if isinstance(item, dict) and all(isinstance(key, str) for key in item):
            for child in item.values():
                validate(child)
            return
        raise ValueError("metadata must contain only finite JSON values and string keys")

    validate(value)
    return json.loads(json.dumps(value, allow_nan=False))


@dataclass(frozen=True)
class SearchResult:
    id: str
    score: float
    metadata: dict
    text: str | None


class VectorIndex:
    """Exact top-k search. Larger scores are always better.

    Cosine uses unit vectors; dot uses raw vectors; euclidean returns negative
    distance. Instances are intended for single-process, sequential use.
    """

    METRICS = ("cosine", "dot", "euclidean")

    def __init__(self, dimension: int, metric: str = "cosine"):
        if type(dimension) is not int or dimension < 1:
            raise ValueError("dimension must be a positive integer")
        if metric not in self.METRICS:
            raise ValueError(f"metric must be one of {self.METRICS}")
        self._dimension = dimension
        self._metric = metric
        self._records = {}

    @property
    def dimension(self):
        return self._dimension

    @property
    def metric(self):
        return self._metric

    def __len__(self):
        return len(self._records)

    def _vector(self, vector):
        try:
            values = list(vector)
        except TypeError as exc:
            raise ValueError("vector must be an iterable of numbers") from exc
        if len(values) != self.dimension:
            raise ValueError(f"expected {self.dimension} vector components, got {len(values)}")
        if any(type(value) not in (int, float) for value in values):
            raise ValueError("vector components must be numbers, excluding booleans")
        try:
            values = tuple(float(value) for value in values)
        except (OverflowError, ValueError) as exc:
            raise ValueError("vector components must be finite floats") from exc
        if not all(math.isfinite(value) for value in values):
            raise ValueError("vector components must be finite")
        return values

    def _prepare(self, vector):
        if self.metric != "cosine":
            return vector
        # Scale first to avoid overflow and underflow in normalization.
        scale = max(abs(value) for value in vector)
        if scale == 0:
            raise ValueError("cosine similarity is undefined for a zero vector")
        scaled = tuple(value / scale for value in vector)
        norm = math.sqrt(math.fsum(value * value for value in scaled))
        return tuple(value / norm for value in scaled)

    def upsert(self, id: str, vector, metadata=None, text=None):
        """Insert or fully replace a record with this ID after validation."""
        if not isinstance(id, str) or not id:
            raise ValueError("id must be a nonempty string")
        if text is not None and not isinstance(text, str):
            raise ValueError("text must be a string or None")
        raw = self._vector(vector)
        prepared = self._prepare(raw)
        copied_metadata = _json_object({} if metadata is None else metadata)
        self._records[id] = (raw, prepared, copied_metadata, text)

    def delete(self, id: str) -> bool:
        """Return whether an existing record was removed."""
        return self._records.pop(id, None) is not None

    def search(self, vector, k: int = 10, filters=None) -> list[SearchResult]:
        """Match all top-level filter fields, then return the best k records.

        Ties are ordered by ID. Filtering happens before top-k selection.
        """
        if type(k) is not int or k < 1:
            raise ValueError("k must be a positive integer")
        query = self._prepare(self._vector(vector))
        filters = _json_object({} if filters is None else filters)

        def candidates():
            for id, (_, stored, metadata, text) in self._records.items():
                if any(key not in metadata or metadata[key] != value
                       for key, value in filters.items()):
                    continue
                try:
                    score = (-math.dist(query, stored) if self.metric == "euclidean"
                             else math.fsum(a * b for a, b in zip(query, stored)))
                except (OverflowError, ValueError) as exc:
                    raise ValueError("score overflow; rescale your vectors") from exc
                if not math.isfinite(score):
                    raise ValueError("score overflow; rescale your vectors")
                if self.metric == "cosine":
                    score = max(-1.0, min(1.0, score))
                yield (id, score, metadata, text)

        best = heapq.nsmallest(k, candidates(), key=lambda item: (-item[1], item[0]))
        return [SearchResult(id, score, _json_object(metadata), text)
                for id, score, metadata, text in best]

    def save(self, path):
        """Atomically replace a snapshot; the parent directory must exist."""
        path = Path(path)
        payload = {
            "version": 1,
            "dimension": self.dimension,
            "metric": self.metric,
            "records": [
                {"id": id, "vector": raw, "metadata": metadata, "text": text}
                for id, (raw, _, metadata, text) in self._records.items()
            ],
        }
        temporary = None
        try:
            with tempfile.NamedTemporaryFile(mode="w", encoding="utf-8", dir=path.parent,
                                             prefix=path.name + ".", suffix=".tmp",
                                             delete=False) as stream:
                temporary = stream.name
                json.dump(payload, stream, ensure_ascii=False, allow_nan=False)
                stream.flush()
                os.fsync(stream.fileno())
            os.replace(temporary, path)
        finally:
            if temporary is not None and os.path.exists(temporary):
                os.unlink(temporary)

    @classmethod
    def load(cls, path):
        """Load and validate a versioned snapshot; reject duplicate IDs."""
        with open(path, encoding="utf-8") as stream:
            payload = json.load(stream)
        if not isinstance(payload, dict) or type(payload.get("version")) is not int or payload["version"] != 1:
            raise ValueError("unsupported index snapshot version")
        try:
            index = cls(payload["dimension"], payload["metric"])
            if not isinstance(payload["records"], list):
                raise ValueError("snapshot records must be a list")
            for record in payload["records"]:
                if not isinstance(record, dict):
                    raise ValueError("snapshot records must be objects")
                id = record["id"]
                if not isinstance(id, str) or id in index._records:
                    raise ValueError("snapshot IDs must be unique strings")
                index.upsert(id, record["vector"], record["metadata"], record["text"])
        except (KeyError, TypeError) as exc:
            raise ValueError("invalid index snapshot structure") from exc
        return index
