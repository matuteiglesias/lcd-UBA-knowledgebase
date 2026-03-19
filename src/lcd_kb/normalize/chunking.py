from __future__ import annotations

import hashlib
import json
import re
from pathlib import Path


def split_text_into_chunks(text: str, *, max_chars: int = 400) -> list[str]:
    paragraphs = [part.strip() for part in re.split(r"\n\s*\n", text) if part.strip()]
    if not paragraphs:
        paragraphs = [text.strip()] if text.strip() else []

    chunks: list[str] = []
    current = ""
    for paragraph in paragraphs:
        candidate = f"{current}\n\n{paragraph}".strip() if current else paragraph
        if len(candidate) <= max_chars:
            current = candidate
            continue
        if current:
            chunks.append(current)
            current = ""
        if len(paragraph) <= max_chars:
            current = paragraph
            continue
        sentences = [piece.strip() for piece in re.split(r"(?<=[.!?])\s+", paragraph) if piece.strip()]
        sentence_buffer = ""
        for sentence in sentences:
            sentence_candidate = f"{sentence_buffer} {sentence}".strip() if sentence_buffer else sentence
            if len(sentence_candidate) <= max_chars:
                sentence_buffer = sentence_candidate
            else:
                if sentence_buffer:
                    chunks.append(sentence_buffer)
                sentence_buffer = sentence
        if sentence_buffer:
            chunks.append(sentence_buffer)
    if current:
        chunks.append(current)
    return chunks


def token_count(text: str) -> int:
    return len([token for token in re.split(r"\s+", text.strip()) if token])


def compute_hash(payload: dict) -> str:
    encoded = json.dumps(payload, ensure_ascii=False, sort_keys=True).encode("utf-8")
    return f"sha256:{hashlib.sha256(encoded).hexdigest()}"


def chunk_page_record(record: dict, *, max_chars: int = 400) -> list[dict]:
    page_id = f"{record['entity_type']}:{record['source_id']}"
    chunks: list[dict] = []
    for index, text in enumerate(split_text_into_chunks(record.get("text", ""), max_chars=max_chars), start=1):
        chunk = {
            "contract": "chunk_doc.v1",
            "parent_contract": record["contract"],
            "site_id": record["site_id"],
            "source_url": record["source_url"],
            "page_id": page_id,
            "chunk_id": f"{page_id}#chunk:{index:04d}",
            "title": record["title"],
            "slug": record["slug"],
            "section_path": [record["title"]] if record.get("title") else [],
            "text": text,
            "token_count": token_count(text),
            "char_count": len(text),
            "page_content_hash": record["content_hash"],
            "observed_at": record["observed_at"],
        }
        chunk["content_hash"] = compute_hash(chunk)
        chunks.append(chunk)
    return chunks


def chunk_jsonl(normalized_path: Path, output_path: Path, *, max_chars: int = 400) -> int:
    output_path.parent.mkdir(parents=True, exist_ok=True)
    count = 0
    with normalized_path.open("r", encoding="utf-8") as source, output_path.open("w", encoding="utf-8") as target:
        for line in source:
            if not line.strip():
                continue
            record = json.loads(line)
            for chunk in chunk_page_record(record, max_chars=max_chars):
                target.write(json.dumps(chunk, ensure_ascii=False) + "\n")
                count += 1
    return count
