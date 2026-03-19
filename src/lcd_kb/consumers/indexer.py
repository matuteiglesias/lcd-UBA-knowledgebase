from __future__ import annotations

import json
from pathlib import Path


def load_jsonl(path: Path) -> list[dict]:
    if not path.exists():
        return []
    with path.open('r', encoding='utf-8') as handle:
        return [json.loads(line) for line in handle if line.strip()]


def build_title_slug_index(*, page_path: Path, post_path: Path) -> list[dict]:
    records = load_jsonl(page_path) + load_jsonl(post_path)
    index = []
    for record in records:
        index.append(
            {
                'slug': record.get('slug'),
                'title': record.get('title'),
                'source_url': record.get('source_url'),
                'entity_type': record.get('entity_type'),
                'source_id': record.get('source_id'),
                'content_hash': record.get('content_hash'),
            }
        )
    index.sort(key=lambda item: ((item.get('title') or '').casefold(), (item.get('slug') or '').casefold()))
    return index


def write_index(path: Path, rows: list[dict]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(rows, indent=2, ensure_ascii=False) + '\n', encoding='utf-8')
