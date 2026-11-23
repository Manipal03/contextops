"""Run with python -m vector_engine --help."""

import argparse
from dataclasses import asdict
import json
from pathlib import Path

from .engine import VectorIndex


def main():
    parser = argparse.ArgumentParser(description="An exact vector search engine")
    parser.add_argument("--index", default="demo-index.json", help="snapshot file path")
    commands = parser.add_subparsers(dest="command", required=True)
    init = commands.add_parser("init", help="create a new empty index")
    init.add_argument("--dimension", type=int, required=True)
    init.add_argument("--metric", choices=VectorIndex.METRICS, default="cosine")
    upsert = commands.add_parser("upsert", help="insert or replace a vector")
    upsert.add_argument("--id", required=True)
    upsert.add_argument("--vector", type=json.loads, required=True)
    upsert.add_argument("--metadata", type=json.loads, default={})
    upsert.add_argument("--text")
    search = commands.add_parser("search", help="find nearest vectors")
    search.add_argument("--vector", type=json.loads, required=True)
    search.add_argument("-k", type=int, default=10)
    search.add_argument("--filter", type=json.loads, default={})
    delete = commands.add_parser("delete", help="remove a vector")
    delete.add_argument("--id", required=True)
    commands.add_parser("stats", help="show index settings and count")
    args = parser.parse_args()
    try:
        if args.command == "init":
            if Path(args.index).exists():
                raise ValueError("index already exists; choose a different --index path")
            index = VectorIndex(args.dimension, args.metric)
            index.save(args.index)
            result = {"created": args.index}
        else:
            index = VectorIndex.load(args.index)
            if args.command == "upsert":
                index.upsert(args.id, args.vector, args.metadata, args.text)
                index.save(args.index)
                result = {"upserted": args.id, "count": len(index)}
            elif args.command == "search":
                result = [asdict(hit) for hit in index.search(args.vector, args.k, args.filter)]
            elif args.command == "delete":
                deleted = index.delete(args.id)
                if deleted:
                    index.save(args.index)
                result = {"deleted": deleted}
            else:
                result = {"dimension": index.dimension, "metric": index.metric, "count": len(index)}
        print(json.dumps(result, indent=2, ensure_ascii=True, allow_nan=False))
    except (OSError, ValueError) as exc:
        parser.exit(2, f"error: {exc}\n")


if __name__ == "__main__":
    main()
