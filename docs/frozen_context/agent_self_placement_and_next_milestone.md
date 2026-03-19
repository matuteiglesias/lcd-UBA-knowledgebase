# Agent self-placement and next milestone

## Operating rule

Act like this repo already has enough structure.

**Add trust, not more scaffolding.**

This repo is past bootstrap. Do not spend time re-laying foundations that already exist.

## Agent guidance after initial buildout

This repo already contains:

- frozen v1 ingestion scope
- contract docs and schemas for normalized pages, chunks, and manifests
- Python package scaffold and CLI
- bounded fetch, normalize, and manifest flow
- normalization and chunk generation
- local reader, search, open, and stats commands
- integrity checks
- runbook
- canonical title/slug index
- end-to-end local build command

The repo is currently transitioning from a **bounded local corpus prototype** to a **trustable, rerunnable LCD source-ingestion tool**.

## Final target

The final target is a repo that can:

- ingest LCD from its live source system in a bounded, reproducible way
- preserve raw evidence
- normalize content into stable KB-native documents
- chunk those documents into retrieval units
- validate corpus integrity and detect suspicious drift
- land the corpus into canonical artifacts with manifest and index
- support downstream search and context use without depending on the frontend site structure

The final target is not:

- full site mirroring
- media hoarding
- broad crawling of unrelated Exactas surfaces
- premature embeddings or RAG complexity
- UI ornamentation disconnected from ingestion quality

## Self-placement buckets

When picking up a task, place it into one of these buckets.

### Bucket A. Live-source hardening

Work that makes real LCD ingestion succeed more reliably.

Examples:

- better handling of REST pagination, headers, and errors
- retries, timeouts, and partial-failure behavior
- better metadata around fetch provenance
- separation of sample/demo artifacts from real-run artifacts
- clearer source envelope preservation

This is strongly on-path.

### Bucket B. Trust and validation

Work that improves confidence in the corpus.

Examples:

- compare normalized counts to source-reported totals
- compare REST URLs against sitemap URLs
- detect suspicious drops between runs
- identify slug collisions or unstable identities
- richer validation reports
- better failing exit behavior and debug evidence

This is strongly on-path.

### Bucket C. Repeatable corpus operations

Work that makes builds and reruns stable.

Examples:

- incremental sync logic
- changed-page detection by hash
- latest-success pointers
- inventory files
- canonical run directories
- consistent artifact naming
- separation between staging and canonical outputs

This is strongly on-path.

### Bucket D. Consumer usefulness

Work that improves access to already-landed corpus artifacts without distorting the pipeline.

Examples:

- better local search
- better open, list, stats, and index helpers
- small registry browsing utilities
- export helpers for downstream systems

This is on-path, but lower priority than Buckets A through C unless the core ingestion path is already stable.

### Bucket E. New extraction scope

Work that expands coverage beyond current v1.

Examples:

- adding custom post types
- adding sitemap-based gap recovery
- adding HTML fallback for specific missing content classes

This is only on-path after Buckets A through C are in decent shape.

### Bucket F. Side quests

Work that feels productive but weakens focus.

Examples:

- building a fancy UI
- adding embeddings first
- broadening to more sites
- media download systems
- redesigning contracts without strong evidence
- replacing the pipeline structure because of minor text-cleaning imperfections

This is off-path unless explicitly requested.

## Highest-priority next work

1. strengthen live REST fetch behavior and source envelopes
2. add source-versus-corpus coverage checks
3. define incremental rerun semantics
4. add inventory and registry artifacts
5. emit machine-readable validation and debug reports
6. separate sample artifacts from canonical run outputs if that split is not already clean

## Medium-priority next work

1. improve local reader and index usability
2. tighten normalization edge cases
3. extend checks around identity drift and slug collisions
4. add carefully chosen custom post types only if justified by coverage gaps

## Low-priority work

1. vector search
2. UI layer
3. broader site expansion
4. media handling
5. cross-site generalization

## Practical self-placement rule

- If live runs are weak or environment-sensitive, place yourself in live-source hardening.
- If corpus trust is weak, place yourself in validation and coverage.
- If reruns are noisy or duplicate-prone, place yourself in incremental-sync hardening.
- If artifacts exist but are hard to inspect, place yourself in registry and consumer ergonomics.
- Only expand scope after those areas are reasonably solid.

## Next milestone

### Milestone: Trusted live-ingestion candidate

Definition:

The repo is a trusted live-ingestion candidate when it can perform a bounded real-source run, produce canonical artifacts, compare coverage against source signals, detect anomalies, and leave behind enough evidence to debug failures cheaply.

That milestone matters more than adding new content types.
