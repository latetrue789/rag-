import argparse
import json
from pathlib import Path

from app.services.container import ServiceContainer
from app.services.parsing import PARSERS


def expand_input_paths(paths: list[Path]) -> list[Path]:
    expanded: list[Path] = []
    for path in paths:
        if path.is_dir():
            expanded.extend(
                item
                for item in path.rglob("*")
                if item.is_file() and item.suffix.lower() in PARSERS
            )
        else:
            expanded.append(path)
    return sorted(set(expanded))


def main() -> int:
    parser = argparse.ArgumentParser(prog="rag-job-kb")
    subparsers = parser.add_subparsers(dest="command", required=True)
    ingest_parser = subparsers.add_parser("ingest", help="Index local documents")
    ingest_parser.add_argument("paths", nargs="+", type=Path)
    args = parser.parse_args()

    if args.command == "ingest":
        paths = expand_input_paths(args.paths)
        if not paths:
            parser.error("No supported Markdown, TXT, or PDF files found")
        outcomes = ServiceContainer().ingestion.ingest_many(paths)
        for outcome in outcomes:
            print(
                json.dumps(
                    {
                        "action": outcome.action,
                        "document_id": outcome.document.id,
                        "filename": outcome.document.filename,
                        "chunk_count": outcome.chunk_count,
                        "message": outcome.message,
                    },
                    ensure_ascii=False,
                )
            )
        return 1 if any(item.action == "failed" for item in outcomes) else 0
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
