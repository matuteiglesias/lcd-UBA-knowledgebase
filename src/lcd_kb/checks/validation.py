from __future__ import annotations

import json
from pathlib import Path


def load_jsonl(path: Path) -> list[dict]:
    if not path.exists():
        return []
    with path.open("r", encoding="utf-8") as handle:
        return [json.loads(line) for line in handle if line.strip()]


def load_raw_items(path: Path) -> tuple[list[dict], list[dict]]:
    if not path.exists():
        return [], []

    envelopes: list[dict] = []
    items: list[dict] = []
    for raw_file in sorted(path.glob("*.json")):
        payload = json.loads(raw_file.read_text(encoding="utf-8"))
        envelopes.append(payload)
        items.extend(payload.get("items", []))
    return envelopes, items


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


def source_urls(items: list[dict]) -> set[str]:
    return {str(item.get("link")) for item in items if item.get("link")}


def normalized_urls(records: list[dict], *, entity: str) -> set[str]:
    return {str(record.get("source_url")) for record in records if record.get("entity_type") == entity and record.get("source_url")}


def source_reported_total(envelopes: list[dict]) -> int | None:
    totals = []
    for envelope in envelopes:
        headers = envelope.get("headers") or {}
        total = headers.get("x-wp-total")
        if total is None:
            continue
        try:
            totals.append(int(total))
        except (TypeError, ValueError):
            continue
    if not totals:
        return None
    return max(totals)


def coverage_for_entity(*, entity: str, records: list[dict], raw_dir: Path | None) -> dict:
    entity_records = [record for record in records if record.get("entity_type") == entity]
    coverage = {
        "entity": entity,
        "normalized_count": len(entity_records),
        "raw_files": 0,
        "fetched_item_count": 0,
        "reported_total": None,
        "missing_normalized_urls": [],
        "extra_normalized_urls": [],
        "warnings": [],
    }
    if raw_dir is None:
        return coverage

    envelopes, items = load_raw_items(raw_dir)
    fetched_urls = source_urls(items)
    landed_urls = normalized_urls(records, entity=entity)
    coverage.update(
        {
            "raw_files": len(envelopes),
            "fetched_item_count": len(items),
            "reported_total": source_reported_total(envelopes),
            "missing_normalized_urls": sorted(fetched_urls - landed_urls),
            "extra_normalized_urls": sorted(landed_urls - fetched_urls),
        }
    )
    reported_total = coverage["reported_total"]
    if reported_total is not None and reported_total != len(items):
        coverage["warnings"].append(
            f"raw fetch captured {len(items)} items but source reported total {reported_total}; this looks like a bounded or partial fetch"
        )
    return coverage


def validate_corpus(
    *,
    page_path: Path,
    post_path: Path,
    page_chunk_path: Path,
    post_chunk_path: Path,
    raw_page_dir: Path | None = None,
    raw_post_dir: Path | None = None,
) -> dict:
    page_records = load_jsonl(page_path)
    post_records = load_jsonl(post_path)
    page_chunks = load_jsonl(page_chunk_path)
    post_chunks = load_jsonl(post_chunk_path)

    document_records = page_records + post_records
    chunk_records = page_chunks + post_chunks
    coverage = {
        "page": coverage_for_entity(entity="page", records=document_records, raw_dir=raw_page_dir),
        "post": coverage_for_entity(entity="post", records=document_records, raw_dir=raw_post_dir),
    }

    checks = {
        "duplicate_source_urls": duplicate_source_urls(document_records),
        "empty_text_with_html": empty_text_with_html(document_records),
        "missing_chunk_parents": missing_chunk_parents(document_records, chunk_records),
        "empty_chunks": empty_chunks(chunk_records),
        "page_count_mismatch_vs_raw": [] if raw_page_dir is None or coverage["page"]["normalized_count"] == coverage["page"]["fetched_item_count"] else [
            f"normalized={coverage['page']['normalized_count']} raw_fetched={coverage['page']['fetched_item_count']}"
        ],
        "post_count_mismatch_vs_raw": [] if raw_post_dir is None or coverage["post"]["normalized_count"] == coverage["post"]["fetched_item_count"] else [
            f"normalized={coverage['post']['normalized_count']} raw_fetched={coverage['post']['fetched_item_count']}"
        ],
        "page_missing_normalized_urls": coverage["page"]["missing_normalized_urls"],
        "post_missing_normalized_urls": coverage["post"]["missing_normalized_urls"],
        "page_extra_normalized_urls": coverage["page"]["extra_normalized_urls"],
        "post_extra_normalized_urls": coverage["post"]["extra_normalized_urls"],
    }
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
        "coverage": coverage,
    }


def write_validation_report(path: Path, report: dict) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(report, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")
