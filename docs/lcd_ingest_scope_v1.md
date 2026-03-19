# LCD ingest scope v1

## Goal

Build a narrow, reproducible ingestion path that turns LCD web content into a document corpus.

## In scope for v1

- source site: `lcd.exactas.uba.ar`
- source priority:
  1. WordPress REST
  2. sitemap for coverage checks
  3. HTML probe only for coverage/debug
- content entities:
  - `page`
  - `post`
- normalized outputs:
  - `page_doc.v1`
  - `chunk_doc.v1`
  - `run_manifest.v1`
- local consumer path:
  - basic search/list/open workflow over normalized outputs

## Explicitly out of scope for v1

- binary asset downloads
- full media library mirroring
- screenshots as ingestion artifacts
- broad Exactas ingestion beyond LCD
- direct summary generation during acquisition
- custom WordPress types before coverage evidence justifies them

## Done means

A successful v1 produces:

- raw REST payload preservation
- normalized JSONL documents
- chunk JSONL documents
- a run manifest with counts and hashes
- schema validation checks
- one small local consumer path

## Re-run policy

- each run gets a unique run identifier
- each output artifact is hashable
- manifests record counts, output paths, and result status
- future runs compare counts and URLs against prior runs and coverage sources

## Next pointer

Proceed to contract and schema hardening, then build the WordPress REST fetch/normalize skeleton.
