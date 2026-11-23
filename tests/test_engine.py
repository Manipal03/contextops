import json
from pathlib import Path
import random
import subprocess
import sys
import tempfile
import unittest

from vector_engine import VectorIndex


class VectorIndexTests(unittest.TestCase):
    def test_metric_rankings(self):
        for metric, expected in [("cosine", ["aligned", "large", "opposite"]),
                                 ("dot", ["large", "aligned", "opposite"]),
                                 ("euclidean", ["aligned", "opposite", "large"])]:
            with self.subTest(metric=metric):
                index = VectorIndex(2, metric)
                index.upsert("aligned", [1, 0])
                index.upsert("large", [10, 10])
                index.upsert("opposite", [-1, 0])
                self.assertEqual([hit.id for hit in index.search([1, 0])], expected)

    def test_top_k_matches_independent_full_sort(self):
        rng = random.Random(42)
        index = VectorIndex(5, "dot")
        records = {str(i): [rng.uniform(-2, 2) for _ in range(5)] for i in range(100)}
        for id, vector in records.items():
            index.upsert(id, vector)
        for _ in range(10):
            query = [rng.uniform(-2, 2) for _ in range(5)]
            expected = sorted(records, key=lambda id: (-sum(a*b for a, b in zip(query, records[id])), id))[:7]
            self.assertEqual([hit.id for hit in index.search(query, 7)], expected)

    def test_filters_before_selection_and_missing_null(self):
        index = VectorIndex(2)
        index.upsert("best", [1, 0], {"course": "math"})
        index.upsert("match", [1, 1], {"course": "physics", "optional": None})
        self.assertEqual(index.search([1, 0], 1, {"course": "physics"})[0].id, "match")
        self.assertEqual([hit.id for hit in index.search([1, 0], filters={"optional": None})], ["match"])
        self.assertEqual(index.search([1, 0], filters={"course": "missing"}), [])

    def test_upsert_delete_and_copy_isolation(self):
        index = VectorIndex(2)
        metadata = {"tags": ["a"]}
        index.upsert("a", [1, 0], metadata)
        metadata["tags"].append("b")
        hit = index.search([1, 0])[0]
        self.assertEqual(hit.metadata, {"tags": ["a"]})
        hit.metadata["tags"].append("c")
        self.assertEqual(index.search([1, 0])[0].metadata, {"tags": ["a"]})
        with self.assertRaises(ValueError):
            index.upsert("a", [0, 0])
        self.assertEqual(index.search([1, 0])[0].score, 1)
        index.upsert("a", [-1, 0], text="replacement")
        self.assertEqual(len(index), 1)
        self.assertEqual(index.search([1, 0])[0].score, -1)
        self.assertTrue(index.delete("a"))
        self.assertFalse(index.delete("a"))
        self.assertEqual(index.search([1, 0]), [])

    def test_invalid_vectors_and_settings(self):
        for dimension in [0, -1, True, 1.5]:
            with self.assertRaises(ValueError):
                VectorIndex(dimension)
        with self.assertRaises(ValueError):
            VectorIndex(2, "unknown")
        index = VectorIndex(2)
        for vector in [[1], [1, 2, 3], [True, 1], [float("nan"), 1],
                       [float("inf"), 1], [0, 0], "12", None, [10**400, 1]]:
            with self.subTest(vector=vector), self.assertRaises(ValueError):
                index.upsert("a", vector)
        for k in [0, -1, True, 1.5]:
            with self.assertRaises(ValueError):
                index.search([1, 0], k)
        for metadata in [[], {1: "key"}, {"bad": float("nan")}, {"bad": (1, 2)}]:
            with self.assertRaises(ValueError):
                index.upsert("a", [1, 0], metadata)

    def test_extreme_vectors(self):
        index = VectorIndex(2)
        index.upsert("huge", [1e308, 1e308])
        self.assertAlmostEqual(index.search([1e-308, 1e-308])[0].score, 1)
        dot = VectorIndex(2, "dot")
        dot.upsert("huge", [1e308, 1e308])
        with self.assertRaisesRegex(ValueError, "overflow"):
            dot.search([1e308, 1e308])
        for metric in ["dot", "euclidean"]:
            index = VectorIndex(2, metric)
            index.upsert("zero", [0, 0])
            self.assertEqual(index.search([0, 0])[0].score, 0)

    def test_ties_are_deterministic(self):
        index = VectorIndex(2)
        for id in ["c", "a", "b"]:
            index.upsert(id, [1, 0])
        self.assertEqual([hit.id for hit in index.search([1, 0], 2)], ["a", "b"])

    def test_snapshot_round_trip_and_corruption(self):
        with tempfile.TemporaryDirectory() as directory:
            path = Path(directory) / "index.json"
            for metric in VectorIndex.METRICS:
                index = VectorIndex(2, metric)
                index.upsert("lecture", [2, 1], {"course": "物理"}, "Lecture notes")
                index.save(path)
                restored = VectorIndex.load(path)
                self.assertEqual(restored.metric, metric)
                self.assertEqual(restored.search([1, 0]), index.search([1, 0]))
            payload = json.loads(path.read_text(encoding="utf-8"))
            payload["records"].append(payload["records"][0])
            path.write_text(json.dumps(payload), encoding="utf-8")
            with self.assertRaises(ValueError):
                VectorIndex.load(path)
            for payload in [{"version": 2}, {"version": 1}, [], {"version": True}]:
                path.write_text(json.dumps(payload), encoding="utf-8")
                with self.assertRaises(ValueError):
                    VectorIndex.load(path)

    def test_cli_persistence_across_processes(self):
        with tempfile.TemporaryDirectory() as directory:
            path = str(Path(directory) / "index.json")

            def run(*args):
                return subprocess.run([sys.executable, "-m", "vector_engine", "--index", path, *args],
                                      capture_output=True, text=True)

            self.assertEqual(run("init", "--dimension", "2").returncode, 0)
            self.assertEqual(run("upsert", "--id", "a", "--vector", "[1,0]").returncode, 0)
            found = run("search", "--vector", "[1,0]", "-k", "1")
            self.assertEqual(found.returncode, 0, found.stderr)
            self.assertEqual(json.loads(found.stdout)[0]["id"], "a")
            self.assertEqual(run("init", "--dimension", "3").returncode, 2)
            self.assertEqual(json.loads(run("stats").stdout)["count"], 1)
            self.assertTrue(json.loads(run("delete", "--id", "a").stdout)["deleted"])
            self.assertEqual(json.loads(run("stats").stdout)["count"], 0)
            self.assertEqual(run("search", "--vector", "[1]").returncode, 2)


if __name__ == "__main__":
    unittest.main()
