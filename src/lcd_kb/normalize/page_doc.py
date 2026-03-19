from __future__ import annotations

import hashlib
import json
import re
from html import unescape
from html.parser import HTMLParser
from pathlib import Path
from typing import Iterable


class _HTMLTextExtractor(HTMLParser):
    def __init__(self) -> None:
        super().__init__()
        self.parts: list[str] = []

    def handle_data(self, data: str) -> None:
        if data.strip():
            self.parts.append(data.strip())

    def text(self) -> str:
        return " ".join(self.parts)


class _LinkExtractor(HTMLParser):
    def __init__(self) -> None:
        super().__init__()
        self.links: list[dict[str, str]] = []
        self.attachments: list[dict[str, str]] = []

    def handle_starttag(self, tag: str, attrs: list[tuple[str, str | None]]) -> None:
        attributes = dict(attrs)
        if tag != "a" or not attributes.get("href"):
            return
        href = attributes["href"]
        kind = "internal" if "lcd.exactas.uba.ar" in href else "external"
        self.links.append({"url": href, "kind": kind})
        if re.search(r"\.(pdf|docx?|xlsx?|pptx?|zip)$", href, re.IGNORECASE):
            self.attachments.append({"url": href, "mime_type": "application/octet-stream"})


def clean_text(html: str) -> str:
    parser = _HTMLTextExtractor()
    parser.feed(unescape(html))
    return re.sub(r"\s+", " ", parser.text()).strip()


def extract_links_and_attachments(html: str) -> tuple[list[dict[str, str]], list[dict[str, str]]]:
    parser = _LinkExtractor()
    parser.feed(unescape(html))
    return parser.links, parser.attachments


def compute_hash(document: dict) -> str:
    encoded = json.dumps(document, ensure_ascii=False, sort_keys=True).encode("utf-8")
    return f"sha256:{hashlib.sha256(encoded).hexdigest()}"


def iter_raw_items(raw_dir: Path) -> Iterable[dict]:
    for path in sorted(raw_dir.glob("*.json")):
        payload = json.loads(path.read_text(encoding="utf-8"))
        yield from payload.get("items", [])


def normalize_wordpress_item(item: dict, *, entity: str, run_id: str, observed_at: str) -> dict:
    title = unescape(item.get("title", {}).get("rendered", "")).strip()
    html = item.get("content", {}).get("rendered", "") or ""
    text = clean_text(html)
    outlinks, attachments = extract_links_and_attachments(html)
    normalized = {
        "contract": "page_doc.v1",
        "source_system": "wordpress_rest",
        "site_id": "lcd.exactas.uba.ar",
        "entity_type": entity,
        "entity_subtype": item.get("type"),
        "source_id": item.get("id"),
        "source_url": item.get("link"),
        "api_url": None,
        "slug": item.get("slug", ""),
        "title": title,
        "status": item.get("status", ""),
        "language": "es",
        "created_at": item.get("date_gmt"),
        "modified_at": item.get("modified_gmt"),
        "parent_source_id": item.get("parent") or None,
        "taxonomy": {
            "categories": item.get("categories", []),
            "tags": item.get("tags", []),
            "custom": {},
        },
        "html": html,
        "text": text,
        "outlinks": outlinks,
        "attachments": attachments,
        "metadata": {
            "author": item.get("author"),
            "menu_order": item.get("menu_order", 0),
            "featured_media": item.get("featured_media", 0),
            "excerpt": item.get("excerpt", {}).get("rendered", ""),
        },
        "ingest_run_id": run_id,
        "observed_at": observed_at,
    }
    normalized["content_hash"] = compute_hash(normalized)
    return normalized


def normalize_entity_dir(raw_dir: Path, output_path: Path, *, entity: str, run_id: str, observed_at: str) -> int:
    output_path.parent.mkdir(parents=True, exist_ok=True)
    count = 0
    with output_path.open("w", encoding="utf-8") as handle:
        for item in iter_raw_items(raw_dir):
            normalized = normalize_wordpress_item(item, entity=entity, run_id=run_id, observed_at=observed_at)
            handle.write(json.dumps(normalized, ensure_ascii=False) + "\n")
            count += 1
    return count
