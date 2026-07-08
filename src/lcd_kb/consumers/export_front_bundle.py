from __future__ import annotations

import argparse
import json
import re
from html import unescape
from pathlib import Path
from typing import Any


DEFAULT_RUN_ROOT = Path("data/lcd/runs")
DEFAULT_OUTPUT_DIR = Path("data/lcd/front_bundle")
BUNDLE_CONTRACT = "lcd_front_bundle.v1"


# -----------------------------
# Basic IO
# -----------------------------


def load_json(path: Path) -> dict[str, Any]:
    return json.loads(path.read_text(encoding="utf-8"))


def load_jsonl(path: Path) -> list[dict[str, Any]]:
    with path.open("r", encoding="utf-8") as handle:
        return [json.loads(line) for line in handle if line.strip()]


def write_json(path: Path, payload: Any) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(payload, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")


# -----------------------------
# Run source resolution
# -----------------------------


def resolve_run_source_paths(run_root: Path, run_id: str) -> dict[str, Any]:
    run_dir = run_root / run_id
    if not run_dir.exists():
        raise FileNotFoundError(f"Run directory not found: {run_dir}")

    status_path = run_dir / "registry" / "run_status.json"
    manifest_path = run_dir / "registry" / "run_manifest.json"

    if not status_path.exists():
        raise FileNotFoundError(f"Missing run_status.json: {status_path}")
    if not manifest_path.exists():
        raise FileNotFoundError(f"Missing run_manifest.json: {manifest_path}")

    finalized_page = run_dir / "normalized" / "page_doc.v1.jsonl"
    finalized_post = run_dir / "normalized" / "post_doc.v1.jsonl"
    finalized_index = run_dir / "indexes" / "title_slug_index.json"

    staging_page = run_dir / "staging" / "page_doc.v1.jsonl"
    staging_post = run_dir / "staging" / "post_doc.v1.jsonl"
    staging_index = run_dir / "staging" / "title_slug_index.json"

    finalized_exists = finalized_page.exists() and finalized_post.exists()
    staging_exists = staging_page.exists() and staging_post.exists()

    if finalized_exists:
        source_kind = "finalized"
        page_path = finalized_page
        post_path = finalized_post
        index_path = finalized_index if finalized_index.exists() else None
    elif staging_exists:
        source_kind = "staging"
        page_path = staging_page
        post_path = staging_post
        index_path = staging_index if staging_index.exists() else None
    else:
        raise FileNotFoundError(
            f"Neither finalized nor staging normalized artifacts found in run {run_id}"
        )

    return {
        "run_dir": run_dir,
        "status_path": status_path,
        "manifest_path": manifest_path,
        "page_path": page_path,
        "post_path": post_path,
        "index_path": index_path,
        "source_kind": source_kind,
    }


# -----------------------------
# Field shaping helpers
# -----------------------------


def strip_html(html: str | None) -> str:
    if not html:
        return ""
    text = unescape(html)
    text = re.sub(r"<br\s*/?>", "\n", text, flags=re.IGNORECASE)
    text = re.sub(r"</p\s*>", "\n\n", text, flags=re.IGNORECASE)
    text = re.sub(r"<[^>]+>", " ", text)
    text = re.sub(r"\s+", " ", text)
    return text.strip()


def normalize_space(text: str | None) -> str:
    if not text:
        return ""
    return re.sub(r"\s+", " ", text).strip()


def slugify_for_route(value: str) -> str:
    text = normalize_space(value).lower()
    text = re.sub(r"[^a-z0-9]+", "-", text)
    text = re.sub(r"-+", "-", text).strip("-")
    return text or "item"


def build_item_id(record: dict[str, Any]) -> str:
    return f"{record.get('entity_type')}:{record.get('source_id')}"


def build_route_slug(record: dict[str, Any]) -> str:
    entity = record.get("entity_type") or "item"
    source_id = str(record.get("source_id") or "0")
    slug = record.get("slug") or record.get("title") or source_id
    return f"{entity}--{source_id}--{slugify_for_route(slug)}"


def choose_excerpt(record: dict[str, Any], max_chars: int) -> str:
    excerpt = strip_html(record.get("metadata", {}).get("excerpt", ""))
    if not excerpt:
        excerpt = strip_html(record.get("excerpt", ""))
    if not excerpt:
        excerpt = normalize_space(record.get("text", ""))
    excerpt = normalize_space(excerpt)
    if len(excerpt) <= max_chars:
        return excerpt
    clipped = excerpt[:max_chars].rsplit(" ", 1)[0].strip()
    return (clipped or excerpt[:max_chars]).strip() + "…"


def classify_builder_heavy(record: dict[str, Any]) -> tuple[bool, str | None]:
    html = (record.get("html") or "").lower()
    if not html:
        return False, None

    builder_markers = [
        "fusion-",
        "avada-",
        "fusion_builder_column",
        "fusion-fullwidth",
        "fusion-recent-posts",
    ]
    if not any(marker in html for marker in builder_markers):
        return False, None

    if "fusion-recent-posts" in html or "entry-title" in html:
        return True, "embedded_post_grid"
    return True, "builder_heavy_page"


def choose_render_mode(record: dict[str, Any], is_index_like: bool) -> str:
    entity_type = record.get("entity_type")
    html = normalize_space(record.get("html", ""))
    if not html:
        return "text_only"
    if entity_type == "page" and is_index_like:
        return "text_only"
    if entity_type == "page" and "fusion-" in html.lower():
        return "text_only"
    return "html_clean"


def clean_html_for_front(record: dict[str, Any], render_mode: str) -> str:
    html = record.get("html") or ""
    if not html:
        return ""
    if render_mode == "text_only":
        return ""

    cleaned = html
    cleaned = re.sub(r"\sclass=\"[^\"]*fusion[^\"]*\"", "", cleaned, flags=re.IGNORECASE)
    cleaned = re.sub(r"\sstyle=\"[^\"]*\"", "", cleaned, flags=re.IGNORECASE)
    cleaned = re.sub(r"\sdata-[a-zA-Z0-9_-]+=\"[^\"]*\"", "", cleaned)
    cleaned = re.sub(r"<(div|section)([^>]*)>", "<div>", cleaned, flags=re.IGNORECASE)
    cleaned = re.sub(r"</section>", "</div>", cleaned, flags=re.IGNORECASE)
    return cleaned.strip()


def normalize_attachment(att: dict[str, Any]) -> dict[str, Any]:
    url = att.get("url")
    label = att.get("label") or "Attachment"
    lower_url = (url or "").lower()
    kind = "attachment"
    if ".pdf" in lower_url or "/download/" in lower_url:
        kind = "pdf"
        if label == "Attachment":
            label = "Descargar PDF"
    return {
        "url": url,
        "label": label,
        "kind": kind,
        "is_download_like": kind == "pdf",
    }


def derive_attachments(record: dict[str, Any]) -> list[dict[str, Any]]:
    attachments = []
    seen = set()
    for att in record.get("attachments", []) or []:
        url = att.get("url")
        if not url or url in seen:
            continue
        seen.add(url)
        attachments.append(normalize_attachment(att))

    html = record.get("html") or ""
    if "Descargar PDF" in html:
        matches = re.findall(r'href="([^"]+)"', html)
        for url in matches:
            if "/download/" in url and url not in seen:
                seen.add(url)
                attachments.append(
                    {
                        "url": url,
                        "label": "Descargar PDF",
                        "kind": "pdf",
                        "is_download_like": True,
                    }
                )
    return attachments


def build_search_text(record: dict[str, Any], excerpt_plain: str) -> str:
    parts = [
        record.get("title", ""),
        record.get("slug", ""),
        excerpt_plain,
        normalize_space(record.get("text", "")),
    ]
    text = " ".join(part for part in parts if part)
    text = normalize_space(text)
    return text[:8000]


# -----------------------------
# Item transforms
# -----------------------------


def make_detail_item(record: dict[str, Any], *, max_excerpt_chars: int) -> dict[str, Any]:
    item_id = build_item_id(record)
    route_slug = build_route_slug(record)
    is_index_like, index_like_reason = classify_builder_heavy(record)
    render_mode = choose_render_mode(record, is_index_like)
    excerpt_plain = choose_excerpt(record, max_excerpt_chars)
    attachments = derive_attachments(record)
    search_text = build_search_text(record, excerpt_plain)
    html_clean = clean_html_for_front(record, render_mode)

    return {
        "id": item_id,
        "entity_type": record.get("entity_type"),
        "source_id": record.get("source_id"),
        "slug": record.get("slug"),
        "route_slug": route_slug,
        "title": record.get("title"),
        "source_url": record.get("source_url"),
        "created_at": record.get("created_at"),
        "modified_at": record.get("modified_at"),
        "sort_date": record.get("modified_at") or record.get("created_at"),
        "status": record.get("status"),
        "excerpt_plain": excerpt_plain,
        "text": normalize_space(record.get("text", "")),
        "html_clean": html_clean,
        "html_raw": record.get("html", ""),
        "render_mode": render_mode,
        "attachments": attachments,
        "has_attachments": bool(attachments),
        "attachment_count": len(attachments),
        "outlinks": record.get("outlinks", []),
        "is_index_like": is_index_like,
        "index_like_reason": index_like_reason,
        "content_hash": record.get("content_hash"),
        "search_text": search_text,
    }


    # In make_detail_item, keep both names explicit:

    # "source_url": record.get("source_url"),
    # "wp_slug": record.get("slug"),
    # "route_slug": route_slug,

    # Right now you already export "slug" and "route_slug", but I would rename/add wp_slug for clarity:

    # "wp_slug": record.get("slug"),
    # "slug": record.get("slug"),
    # "route_slug": route_slug,

def make_listing_item(detail_item: dict[str, Any]) -> dict[str, Any]:
    return {
        "id": detail_item["id"],
        "entity_type": detail_item["entity_type"],
        "source_id": detail_item["source_id"],
        "slug": detail_item["slug"],
        "route_slug": detail_item["route_slug"],
        "title": detail_item["title"],
        "source_url": detail_item["source_url"],
        "created_at": detail_item["created_at"],
        "modified_at": detail_item["modified_at"],
        "sort_date": detail_item["sort_date"],
        "excerpt_plain": detail_item["excerpt_plain"],
        "has_attachments": detail_item["has_attachments"],
        "attachment_count": detail_item["attachment_count"],
        "is_index_like": detail_item["is_index_like"],
        "index_like_reason": detail_item["index_like_reason"],
        "render_mode": detail_item["render_mode"],
    }


def make_search_item(detail_item: dict[str, Any]) -> dict[str, Any]:
    return {
        "id": detail_item["id"],
        "route_slug": detail_item["route_slug"],
        "title": detail_item["title"],
        "entity_type": detail_item["entity_type"],
        "excerpt_plain": detail_item["excerpt_plain"],
        "search_text": detail_item["search_text"],
        "is_index_like": detail_item["is_index_like"],
    }


# -----------------------------
# Export
# -----------------------------


def export_front_bundle(
    *,
    run_root: Path,
    run_id: str,
    output_dir: Path,
    max_excerpt_chars: int = 280,
    include_html_raw: bool = False,
) -> dict[str, Any]:
    resolved = resolve_run_source_paths(run_root, run_id)
    run_status = load_json(resolved["status_path"])
    run_manifest = load_json(resolved["manifest_path"])

    page_records = load_jsonl(resolved["page_path"])
    post_records = load_jsonl(resolved["post_path"])
    all_records = page_records + post_records

    detail_items = []
    listing_items = []
    search_items = []

    output_items_dir = output_dir / "items"
    output_items_dir.mkdir(parents=True, exist_ok=True)

    for record in all_records:
        detail = make_detail_item(record, max_excerpt_chars=max_excerpt_chars)
        if not include_html_raw:
            detail.pop("html_raw", None)

        listing = make_listing_item(detail)
        search = make_search_item(detail)

        detail_items.append(detail)
        listing_items.append(listing)
        search_items.append(search)

        write_json(output_items_dir / f"{detail['route_slug']}.json", detail)

    listing_items.sort(
        key=lambda item: (item.get("sort_date") or "", item.get("title") or ""),
        reverse=True,
    )
    search_items.sort(key=lambda item: (item.get("title") or "").casefold())

    posts = [item for item in listing_items if item.get("entity_type") == "post"]
    pages = [item for item in listing_items if item.get("entity_type") == "page"]

    write_json(
        output_dir / "listing.json",
        {
            "generated_from_run_id": run_id,
            "sort": "sort_date_desc",
            "items": listing_items,
        },
    )

    write_json(
        output_dir / "posts.json",
        {
            "generated_from_run_id": run_id,
            "sort": "sort_date_desc",
            "items": posts,
        },
    )

    write_json(
        output_dir / "pages.json",
        {
            "generated_from_run_id": run_id,
            "sort": "sort_date_desc",
            "items": pages,
        },
    )

    write_json(output_dir / "search.json", search_items)

    counts = {
        "items_total": len(detail_items),
        "pages": len(page_records),
        "posts": len(post_records),
        "index_like": sum(1 for item in detail_items if item["is_index_like"]),
        "with_attachments": sum(1 for item in detail_items if item["has_attachments"]),
    }

    bundle_manifest = {
        "bundle_contract": BUNDLE_CONTRACT,
        "generated_from": {
            "run_id": run_id,
            "run_status": run_status.get("status"),
            "run_result": run_status.get("result"),
            "trusted": run_status.get("trusted"),
            "validation_ok": run_status.get("validation_ok"),
            "source_kind": resolved["source_kind"],
            "source_page_path": str(resolved["page_path"]),
            "source_post_path": str(resolved["post_path"]),
            "run_manifest_path": str(resolved["manifest_path"]),
            "run_status_path": str(resolved["status_path"]),
        },
        "source_counts": run_manifest.get("entity_counts", {}),
        "export_counts": counts,
        "artifacts": {
            "listing": "listing.json",
            "posts": "posts.json",
            "pages": "pages.json",
            "search": "search.json",
            "items_dir": "items",
        },
        "notes": [
            "Frontend bundle exported from an explicit ingest run.",
            "This bundle is designed for a dumb frontend: listing, search, and item detail are pre-shaped.",
            "posts.json and pages.json are convenience splits over listing.json for frontend routing.",
        ],
    }
    write_json(output_dir / "manifest.json", bundle_manifest)

    return {
        "result": "pass",
        "run_id": run_id,
        "source_kind": resolved["source_kind"],
        "source_run_status": run_status.get("status"),
        "items_total": len(detail_items),
        "pages": len(page_records),
        "posts": len(post_records),
        "index_like": counts["index_like"],
        "with_attachments": counts["with_attachments"],
        "output_dir": str(output_dir),
        "artifacts": bundle_manifest["artifacts"],
    }



# -----------------------------
# CLI
# -----------------------------


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        prog="lcd-export-front-bundle",
        description="Export a dumb-frontend bundle from an explicit LCD ingest run",
    )
    parser.add_argument("--run-id", required=True, help="Run identifier to export from")
    parser.add_argument("--run-root", default=str(DEFAULT_RUN_ROOT), help="Root directory containing per-run artifacts")
    parser.add_argument("--output-dir", default=str(DEFAULT_OUTPUT_DIR), help="Output directory for front bundle")
    parser.add_argument("--max-excerpt-chars", type=int, default=280, help="Maximum chars for listing excerpt")
    parser.add_argument(
        "--include-html-raw",
        action="store_true",
        help="Include html_raw in detail payloads",
    )
    return parser


def main() -> int:
    parser = build_parser()
    args = parser.parse_args()

    result = export_front_bundle(
        run_root=Path(args.run_root),
        run_id=args.run_id,
        output_dir=Path(args.output_dir),
        max_excerpt_chars=args.max_excerpt_chars,
        include_html_raw=args.include_html_raw,
    )
    print(json.dumps(result, indent=2, ensure_ascii=False))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
