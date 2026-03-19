# `chunk_doc.v1`

Retrieval-oriented child contract derived from `page_doc.v1`.

## Purpose

`chunk_doc.v1` turns a page document into stable retrieval units. Each chunk must point back to its parent page document so local search and later downstream systems can reconstruct provenance.

## Required fields

- `contract`
- `parent_contract`
- `site_id`
- `source_url`
- `page_id`
- `chunk_id`
- `title`
- `slug`
- `text`
- `token_count`
- `char_count`
- `content_hash`
- `page_content_hash`
- `observed_at`

## Notes

- `section_path` is optional but recommended when chunking preserves document structure.
- `page_id` should be stable enough to join back to the parent `page_doc.v1` record.
