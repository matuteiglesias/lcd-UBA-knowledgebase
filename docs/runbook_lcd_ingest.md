# LCD ingest runbook

## Purpose

This runbook describes the bounded v1 LCD ingestion workflow and the minimum evidence expected from each run.

## Expected artifact flow

1. Fetch raw WordPress REST batches for `page` and `post`, plus fetch summary/error artifacts.
2. Normalize those batches into `page_doc.v1` JSONL outputs.
3. Chunk normalized documents into `chunk_doc.v1` JSONL outputs.
4. Run validation checks before treating the run as trustworthy.
5. Write `run_manifest.v1` with counts and artifact hashes.

## Typical command sequence

```bash
python -m lcd_kb.cli fetch --entity page --max-pages 1
python -m lcd_kb.cli fetch --entity post --max-pages 1
# inspect data/lcd/reports/*_fetch_summary.json and *_fetch_errors.jsonl when source behavior looks suspicious
python -m lcd_kb.cli normalize --entity page
python -m lcd_kb.cli normalize --entity post
python -m lcd_kb.cli chunk --entity page
python -m lcd_kb.cli chunk --entity post
python -m lcd_kb.cli check --report-output data/lcd/reports/validation_report.json
python -m lcd_kb.cli manifest
```

`build` now defaults to writing derived artifacts into a per-run directory under `data/lcd/runs/<run_id>/...`, emits `registry/artifact_inventory.json` for that run, and, on success, updates `data/lcd/state/latest_success.json` to point at the latest trusted run. Operators can inspect that state with `lcd-kb latest`, `lcd-kb latest-artifacts`, and `lcd-kb inspect-run --run-id ...`.

## What `check` currently validates

- duplicate `source_url` values across normalized page/post docs
- records with non-empty `html` but empty extracted `text`
- chunk records whose `page_id` does not map back to a normalized parent record
- chunk records with empty `text`
- normalized page/post counts that do not match fetched raw item counts
- fetched source URLs that are missing from normalized outputs, and normalized URLs that were not present in the raw fetch

## Failure handling

If `check` fails:

1. inspect the failing URLs, count mismatches, or chunk ids from the JSON output or `data/lcd/reports/validation_report.json`
2. re-open the raw batch in `data/lcd/raw/...`
3. verify whether the issue came from fetch, normalize, or chunk stages
4. rerun only the affected stage first, then rerun `check`
5. regenerate the manifest once the run passes

## Notes

- v1 remains intentionally narrow: LCD only, REST first, no binary mirroring
- summaries and embeddings remain downstream concerns
- a run should not be considered good merely because files exist; `check` must pass too
