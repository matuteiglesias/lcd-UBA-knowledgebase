from __future__ import annotations

import json
from pathlib import Path


def load_jsonl(path: Path) -> list[dict]:
    if not path.exists():
        return []
    with path.open("r", encoding="utf-8") as handle:
        return [json.loads(line) for line in handle if line.strip()]


def stats(paths: dict[str, Path]) -> dict[str, int]:
    return {name: len(load_jsonl(path)) for name, path in paths.items()}


def search_records(path: Path, query: str, *, limit: int = 10) -> list[dict]:
    needle = query.casefold()
    matches = []
    for record in load_jsonl(path):
        haystack = " ".join(
            str(record.get(field, "")) for field in ("title", "slug", "text", "chunk_id", "page_id")
        ).casefold()
        if needle in haystack:
            matches.append(record)
        if len(matches) >= limit:
            break
    return matches


def get_record_by_slug(path: Path, slug: str) -> dict | None:
    for record in load_jsonl(path):
        if record.get("slug") == slug:
            return record
    return None
