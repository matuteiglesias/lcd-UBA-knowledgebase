# lcd-UBA-knowledgebase

A working monorepo for turning the LCD WordPress site into a governed, queryable, re-runnable knowledge corpus.

## Vision

This repository treats LCD as a source system, not as a website to mirror. The goal is to:

- fetch LCD content from WordPress REST first,
- normalize it into stable document contracts,
- preserve run evidence with manifests and hashes,
- chunk documents into retrieval units, and
- expose a small local consumer path for search and inspection.

## Current implementation phase

The repo has now moved from planning into a **bounded corpus + local consumer** phase:

1. governance scope frozen in `docs/lcd_ingest_scope_v1.md`
2. core contracts defined for `page_doc.v1`, `chunk_doc.v1`, and `run_manifest.v1`
3. a bounded WordPress REST fetcher writes raw JSON page batches
4. a normalizer emits `page_doc.v1` JSONL for `page` and `post`
5. a chunker emits `chunk_doc.v1` JSONL for local retrieval
6. local commands can search, inspect, and summarize the current corpus artifacts
7. integrity checks and a runbook help prevent silent pipeline drift
8. trusted promotion now happens only after validation passes, with run-scoped status, drift reports, and anomaly artifacts

## CLI

```bash
python -m lcd_kb.cli fetch --entity page --max-pages 1
python -m lcd_kb.cli normalize --entity page
python -m lcd_kb.cli chunk --entity page
python -m lcd_kb.cli build
python -m lcd_kb.cli build-index
python -m lcd_kb.cli search "plan de estudios"
python -m lcd_kb.cli open --slug plan-de-estudios
python -m lcd_kb.cli stats
python -m lcd_kb.cli manifest
python -m lcd_kb.cli check
```

## Output layout

```text
data/lcd/raw/pages/*.json
data/lcd/raw/posts/*.json
data/lcd/normalized/page_doc.v1.jsonl
data/lcd/normalized/post_doc.v1.jsonl
data/lcd/chunks/page_chunk_doc.v1.jsonl
data/lcd/chunks/post_chunk_doc.v1.jsonl
data/lcd/indexes/title_slug_index.json
data/lcd/manifests/run_manifest.json
data/lcd/registry/latest_attempted.json
data/lcd/registry/latest_success.json
data/lcd/registry/latest_trusted.json
data/lcd/runs/<run_id>/registry/run_status.json
data/lcd/runs/<run_id>/reports/drift_report.json
data/lcd/runs/<run_id>/reports/anomalies/*.jsonl
```

## Development

Run the lightweight test suite with:

```bash
PYTHONPATH=src python -m unittest discover -s tests
```
