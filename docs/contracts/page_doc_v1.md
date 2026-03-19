# `page_doc.v1`

Normalized page-level knowledge record for LCD content.

## Purpose

`page_doc.v1` is the canonical parent document contract for content fetched from LCD. It captures source identity, normalized content, extracted relationships, and ingest metadata in a stable shape that downstream chunking and search can depend on.

## Required fields

- `contract`
- `source_system`
- `site_id`
- `entity_type`
- `source_id`
- `source_url`
- `slug`
- `title`
- `status`
- `language`
- `html`
- `text`
- `content_hash`
- `ingest_run_id`
- `observed_at`

## Notes

- `html` preserves normalized source markup for reproducibility.
- `text` is the cleaned extraction used by chunking and search.
- `taxonomy`, `metadata`, `outlinks`, and `attachments` are structured but optional extensions.
- `content_hash` should be computed from the normalized content payload, not from raw transport bytes.
