from __future__ import annotations

import json
from pathlib import Path


def load_jsonl(path: Path) -> list[dict]:
    if not path.exists():
        return []
    with path.open("r", encoding="utf-8") as handle:
        return [json.loads(line) for line in handle if line.strip()]


def duplicate_source_urls(records: list[dict]) -> list[str]:
    counts: dict[str, int] = {}
    for record in records:
        source_url = record.get("source_url")
        if not source_url:
            continue
        counts[source_url] = counts.get(source_url, 0) + 1
    return sorted(url for url, count in counts.items() if count > 1)


def empty_text_with_html(records: list[dict]) -> list[str]:
    failures = []
    for record in records:
        html = (record.get("html") or "").strip()
        text = (record.get("text") or "").strip()
        if html and not text:
            failures.append(str(record.get("source_url") or record.get("slug") or record.get("source_id")))
    return failures


def missing_chunk_parents(page_records: list[dict], chunk_records: list[dict]) -> list[str]:
    parents = {f"{record.get('entity_type')}:{record.get('source_id')}" for record in page_records}
    failures = []
    for chunk in chunk_records:
        page_id = chunk.get("page_id")
        if page_id not in parents:
            failures.append(str(page_id))
    return sorted(set(failures))


def empty_chunks(chunk_records: list[dict]) -> list[str]:
    failures = []
    for chunk in chunk_records:
        if not (chunk.get("text") or "").strip():
            failures.append(str(chunk.get("chunk_id")))
    return failures


def anomaly_records(*, page_records: list[dict], post_records: list[dict], page_chunks: list[dict], post_chunks: list[dict]) -> dict[str, list[dict]]:
    document_records = page_records + post_records
    chunk_records = page_chunks + post_chunks

    duplicate_urls = set(duplicate_source_urls(document_records))
    orphan_ids = set(missing_chunk_parents(document_records, chunk_records))
    empty_chunk_ids = set(empty_chunks(chunk_records))

    return {
        "duplicate_source_urls": [record for record in document_records if record.get("source_url") in duplicate_urls],
        "empty_text_docs": [
            record
            for record in document_records
            if (record.get("html") or "").strip() and not (record.get("text") or "").strip()
        ],
        "orphan_chunks": [chunk for chunk in chunk_records if str(chunk.get("page_id")) in orphan_ids],
        "empty_chunks": [chunk for chunk in chunk_records if str(chunk.get("chunk_id")) in empty_chunk_ids],
        "fetch_failures": [],
    }


def validate_corpus(*, page_path: Path, post_path: Path, page_chunk_path: Path, post_chunk_path: Path) -> dict:
    page_records = load_jsonl(page_path)
    post_records = load_jsonl(post_path)
    page_chunks = load_jsonl(page_chunk_path)
    post_chunks = load_jsonl(post_chunk_path)

    document_records = page_records + post_records
    chunk_records = page_chunks + post_chunks

    checks = {
        "duplicate_source_urls": duplicate_source_urls(document_records),
        "empty_text_with_html": empty_text_with_html(document_records),
        "missing_chunk_parents": missing_chunk_parents(document_records, chunk_records),
        "empty_chunks": empty_chunks(chunk_records),
    }
    anomalies = anomaly_records(
        page_records=page_records,
        post_records=post_records,
        page_chunks=page_chunks,
        post_chunks=post_chunks,
    )
    ok = all(not failures for failures in checks.values())
    return {
        "ok": ok,
        "counts": {
            "page_docs": len(page_records),
            "post_docs": len(post_records),
            "page_chunks": len(page_chunks),
            "post_chunks": len(post_chunks),
        },
        "checks": checks,
        "anomaly_counts": {name: len(records) for name, records in anomalies.items()},
        "anomaly_records": anomalies,
    }
