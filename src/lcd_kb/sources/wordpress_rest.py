from __future__ import annotations

import json
from dataclasses import dataclass
from pathlib import Path
from typing import Callable
from urllib.parse import urlencode
from urllib.request import Request, urlopen


SITE_ID = "lcd.exactas.uba.ar"
DEFAULT_BASE_URL = "https://lcd.exactas.uba.ar"
DEFAULT_FIELDS = [
    "id",
    "date_gmt",
    "modified_gmt",
    "slug",
    "status",
    "type",
    "link",
    "title",
    "content",
    "excerpt",
    "author",
    "featured_media",
    "parent",
    "menu_order",
    "categories",
    "tags",
]


@dataclass(slots=True)
class FetchResult:
    entity: str
    pages_fetched: int
    records_fetched: int
    raw_files: list[str]
    summary: dict
    errors: list[dict]


def default_request_json(url: str) -> tuple[list[dict], dict[str, str]]:
    request = Request(url, headers={"User-Agent": "lcd-kb/0.1", "Accept": "application/json"})
    with urlopen(request, timeout=30) as response:
        payload = json.loads(response.read().decode("utf-8"))
        headers = {key.lower(): value for key, value in response.headers.items()}
    if not isinstance(payload, list):
        raise ValueError(f"Expected list payload from {url}, got {type(payload).__name__}")
    return payload, headers


def build_entity_url(base_url: str, entity: str, page: int, per_page: int, fields: list[str] | None = None) -> str:
    route = f"{base_url.rstrip('/')}/wp-json/wp/v2/{entity}s"
    query = {"page": page, "per_page": per_page}
    if fields:
        query["_fields"] = ",".join(fields)
    return f"{route}?{urlencode(query)}"


def default_fetch_report_paths(output_dir: Path, entity: str) -> tuple[Path, Path]:
    report_root = output_dir.parent.parent / 'reports'
    return report_root / f'{entity}_fetch_summary.json', report_root / f'{entity}_fetch_errors.jsonl'


def write_fetch_summary(path: Path, summary: dict) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(summary, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")


def write_fetch_errors(path: Path, errors: list[dict]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open('w', encoding='utf-8') as handle:
        for error in errors:
            handle.write(json.dumps(error, ensure_ascii=False) + "\n")


def fetch_entity_batches(
    *,
    base_url: str,
    entity: str,
    output_dir: Path,
    per_page: int = 25,
    max_pages: int | None = None,
    fields: list[str] | None = None,
    request_json: Callable[[str], tuple[list[dict], dict[str, str]]] = default_request_json,
) -> FetchResult:
    output_dir.mkdir(parents=True, exist_ok=True)
    page_number = 1
    pages_fetched = 0
    records_fetched = 0
    raw_files: list[str] = []
    errors: list[dict] = []
    stop_reason = 'completed'
    reported_total = None
    reported_total_pages = None

    while True:
        if max_pages is not None and page_number > max_pages:
            stop_reason = 'max_pages_reached'
            break

        url = build_entity_url(base_url, entity, page_number, per_page, fields or DEFAULT_FIELDS)
        try:
            payload, headers = request_json(url)
        except Exception as exc:  # noqa: BLE001
            errors.append(
                {
                    'entity': entity,
                    'page': page_number,
                    'source_url': url,
                    'error_type': type(exc).__name__,
                    'message': str(exc),
                }
            )
            stop_reason = 'request_error'
            break

        if headers.get('x-wp-total') is not None:
            try:
                reported_total = int(headers['x-wp-total'])
            except (TypeError, ValueError):
                reported_total = headers['x-wp-total']
        if headers.get('x-wp-totalpages') is not None:
            try:
                reported_total_pages = int(headers['x-wp-totalpages'])
            except (TypeError, ValueError):
                reported_total_pages = headers['x-wp-totalpages']

        if not payload:
            stop_reason = 'empty_payload'
            break

        destination = output_dir / f"{entity}s-page-{page_number:04d}.json"
        envelope = {
            "entity": entity,
            "page": page_number,
            "per_page": per_page,
            "source_url": url,
            "headers": {
                "x-wp-total": headers.get("x-wp-total"),
                "x-wp-totalpages": headers.get("x-wp-totalpages"),
            },
            "items": payload,
        }
        destination.write_text(json.dumps(envelope, indent=2) + "\n", encoding="utf-8")
        raw_files.append(str(destination))
        pages_fetched += 1
        records_fetched += len(payload)

        total_pages = headers.get("x-wp-totalpages")
        if total_pages is not None and page_number >= int(total_pages):
            stop_reason = 'reported_total_pages_reached'
            break

        if len(payload) < per_page:
            stop_reason = 'short_page'
            break

        page_number += 1

    summary = {
        'entity': entity,
        'base_url': base_url,
        'output_dir': str(output_dir),
        'pages_fetched': pages_fetched,
        'records_fetched': records_fetched,
        'raw_files': raw_files,
        'reported_total': reported_total,
        'reported_total_pages': reported_total_pages,
        'max_pages': max_pages,
        'bounded_warning': bool(max_pages is not None and reported_total_pages and pages_fetched < reported_total_pages),
        'error_count': len(errors),
        'stop_reason': stop_reason,
    }
    return FetchResult(
        entity=entity,
        pages_fetched=pages_fetched,
        records_fetched=records_fetched,
        raw_files=raw_files,
        summary=summary,
        errors=errors,
    )
