# Current phase after bootstrap

## Program placement

The LCD corpus monorepo is no longer in early scaffold mode.

It has already crossed these thresholds:

- governance is frozen enough for v1
- core contracts exist
- extractor skeleton exists
- bounded corpus build exists
- chunking exists
- a local consumer exists
- integrity checks exist
- a landed index exists
- there is now an end-to-end local `build` path

That places the repo in a **late middle stage**.

The architecture exists, the local corpus exists, and the next work should focus on making the pipeline **credible, repeatable, and ready for real ingestion**.

## Phase map

The current placement is approximately:

- **Phase 1: Governance freeze** — substantially done
- **Phase 2: Contracts** — substantially done
- **Phase 3: Extractor skeleton** — done enough for bounded work
- **Phase 4: Bounded corpus build** — done
- **Phase 5: Checks / trust layer** — started and materially present
- **Phase 6: Corpus landing / local consumer** — started and materially present
- **Phase 7: Hardening for repeatable real syncs** — not yet done

## What the final vision means now

The final vision is no longer abstract.

> LCD knowledge must become a stable source corpus that can be re-ingested, validated, inspected, indexed, and consumed without relying on the WordPress frontend.

In concrete terms:

- WordPress is the source system.
- This repo is building the backend-like representation.
- Normalized docs are the canonical internal representation.
- Chunks are retrieval units.
- The manifest and index are registry and evidence surfaces.
- The build command should eventually support a real rerunnable sync against live LCD.
- The corpus should become trustworthy enough to feed downstream knowledge systems without manual spelunking.

The unfinished question is no longer "can we model the documents?"

The unfinished question is:

> Can we run this against reality repeatedly and trust the result?

## Current phase, stated sharply

Treat the repo as being in:

## Phase: Hardening the source-system pipeline

The core question for new work is:

> Can this repo behave like a real source ingestion asset, not just a successful sample?

Anything that helps answer "yes" belongs in the current phase.

Anything that mainly adds breadth, novelty, or decoration does not.

## Current priority

Agents should assume the next major phase is **hardening and live-source credibility**.

Prefer work that improves:

- live-source robustness
- coverage confidence
- rerun stability
- artifact discipline
- canonical naming and identity stability
- real-run diagnostics
- incremental sync behavior
- coverage comparison between source surfaces

Do not default to inventing another subsystem when trust in the source-system path is still incomplete.

## Missing pieces relative to the final vision

### 1. Real live-sync robustness

The project still needs a clearer strategy for real-source acquisition conditions and environment-dependent failures.

Examples of on-path work:

- document live-source assumptions
- isolate environment-sensitive fetch behavior
- define expected fetch evidence
- handle source failures explicitly

### 2. Coverage confidence

The corpus has internal integrity checks, but it still needs stronger evidence that the landed corpus is complete relative to source signals.

Examples of on-path work:

- compare normalized counts to source-reported totals
- compare REST URLs to sitemap URLs
- produce coverage reports
- emit missing/extra URL diagnostics

### 3. Stable rerun semantics

The build path exists, but rerun policy still needs to be made explicit.

Examples of on-path work:

- stable run IDs or run folders
- latest-success markers
- changed-page detection
- no-duplication guarantees
- clean separation between sample/demo and canonical outputs

### 4. Registry maturity

The manifest and index exist, but the registry layer should become easier to inspect and audit.

Examples of on-path work:

- inventory artifacts
- artifact cataloging
- parent-child traceability from raw to normalized to chunks to index
- a small artifact registry view or file

### 5. Failure debugging ergonomics

Checks exist, but failures should become cheaper to debug.

Examples of on-path work:

- validation report files, not just exit codes
- anomaly packets
- explicit debug artifacts for duplicate URLs, empty text, and orphan chunks
- failure summaries that point directly to offending records

## Milestone framing

The next milestone should be treated as:

## Milestone: Trusted live-ingestion candidate

Definition:

The repo is a trusted live-ingestion candidate when it can perform a bounded real-source run, produce canonical artifacts, compare coverage against source signals, detect anomalies, and leave behind enough evidence to debug failures cheaply.

Reaching that milestone is more important than adding new content types.
