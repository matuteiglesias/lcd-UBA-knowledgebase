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

The repo has moved beyond initial planning and bootstrap. It now sits in a **late middle-stage hardening phase**: the bounded corpus and local consumer exist, and the next work should focus on making ingestion credible, repeatable, and ready for real live-source runs. See `docs/frozen_context/current_phase_after_bootstrap.md` and `docs/frozen_context/agent_self_placement_and_next_milestone.md` for the frozen guidance used to place follow-on work.

The earlier bounded corpus + local consumer milestones that are already in place are:

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
# writes data/lcd/reports/page_fetch_summary.json and page_fetch_errors.jsonl
python -m lcd_kb.cli normalize --entity page
python -m lcd_kb.cli chunk --entity page
python -m lcd_kb.cli build --run-id lcd_ingest_20260319T200000Z
python -m lcd_kb.cli build-index
python -m lcd_kb.cli search "plan de estudios"
python -m lcd_kb.cli open --slug plan-de-estudios
python -m lcd_kb.cli stats
python -m lcd_kb.cli manifest
python -m lcd_kb.cli check --report-output data/lcd/reports/validation_report.json
python -m lcd_kb.cli latest
python -m lcd_kb.cli latest-artifacts
python -m lcd_kb.cli inspect-run --run-id lcd_ingest_20260319T200000Z
```

`build` now writes derived artifacts into `data/lcd/runs/<run_id>/...` by default, emits `registry/artifact_inventory.json` for that run, and updates `data/lcd/state/latest_success.json` when a run succeeds.

## Output layout

```text
data/lcd/raw/pages/*.json
data/lcd/raw/posts/*.json
data/lcd/reports/page_fetch_summary.json
data/lcd/reports/page_fetch_errors.jsonl
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
