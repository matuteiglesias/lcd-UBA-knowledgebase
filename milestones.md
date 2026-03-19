Yes. I would frame it as a **small product team project**, not as a “crawl everything” effort.

The key premise stays the same: LCD is the first narrow corpus, REST is primary, normalized JSONL documents are the core artifact, and raw pages should land in a document-oriented corpus rather than being pushed straight into Summary Bus.  

## Project name

**LCD Corpus Monorepo**

## Mission

Turn the current LCD WordPress surface into a governed, re-runnable, KB-native document corpus that can be searched, chunked, validated, and later fed into downstream context systems. The intended end state is a single stable JSONL corpus, manifests with counts and hashes, a schema, a runbook, and a small consumer path. 

## Team shape

Keep it lean. Five roles are enough:

**1. Product / Architecture Lead**
Owns scope, bus placement, contracts, and acceptance criteria.

**2. Ingestion Engineer**
Builds the WordPress REST fetcher, pagination, raw preservation, and normalization pipeline.

**3. Contracts / Data Quality Engineer**
Owns `page_doc.v1`, `chunk_doc.v1`, schema validation, drift checks, and manifests.

**4. Search / Consumer Engineer**
Builds the first reader or search surface over the normalized corpus.

**5. Ops / QA Engineer**
Owns smoke runs, reproducibility, runbooks, exit codes, and failure evidence.

One person can wear several hats. The point is to separate concerns, not to inflate headcount.

---

# Phase plan

## Phase 0. Framing and freeze

**Goal**
Prevent scope drift before code starts.

**Questions settled here**

* What counts in v1
* What is explicitly excluded
* Where the corpus lands
* What “done” means

**Likely decision**

* Include: `page`, `post`
* Defer custom types until coverage proves value
* Exclude binary downloads, full media ingestion, broad mirroring, screenshots
* Treat LCD as one narrow source corpus first. 

**Deliverables**

* `docs/lcd_ingest_scope_v1.md`
* architecture note with source priority:

  * REST first
  * sitemap second
  * HTML probe only for coverage/debug

**Exit gate**

* Everyone agrees what v1 is
* Nobody is still arguing for “mirror the site”

**Main risk**

* Starting with all custom post types and media
* That is where the project turns messy early

---

## Phase 1. Contract design

**Goal**
Define the stable units before building extractors.

The project should think in **knowledge documents**, not raw WordPress objects. The core recommended contract is `page_doc.v1`, with source identity, normalized content, extracted relationships, ingest metadata, and reproducibility fields. 

I would add `chunk_doc.v1` in the same phase, even if chunking is implemented later.

**Deliverables**

* `docs/contracts/page_doc_v1.md`
* `schemas/page_doc_v1.json`
* `examples/page_doc_v1.example.json`
* `docs/contracts/chunk_doc_v1.md`
* `schemas/chunk_doc_v1.json`

**Data shape**

* `page_doc.v1` for page-level records
* `chunk_doc.v1` for retrieval units
* `run_manifest.v1` for run evidence

**Exit gate**

* Hand-made sample validates against schema
* Required fields frozen
* Parent-child link from chunk to page is defined

**Main risk**

* Trying to perfect metadata before first run
* Freeze v1 and move

---

## Phase 2. Extractor skeleton

**Goal**
Produce a usable CLI with disciplined outputs.

The extractor should fetch REST entities, preserve raw JSON, emit normalized JSONL, support pagination and field reduction, and avoid binary downloads in v1. 

**Deliverables**

* `src/lcd_kb/cli.py`
* `src/lcd_kb/sources/wordpress_rest.py`
* `src/lcd_kb/normalize/page_doc.py`

**CLI shape**

```bash
lcd-kb fetch --entity page
lcd-kb fetch --entity post
lcd-kb normalize
lcd-kb manifest
lcd-kb check
```

**Output shape**

```text
data/lcd/raw/pages/*.json
data/lcd/raw/posts/*.json
data/lcd/normalized/page_doc.v1.jsonl
data/lcd/manifests/run_manifest.json
```

**Exit gate**

* `--help` works
* one smoke run against `page`
* one sample JSONL line written
* exit codes behave predictably

**Main risk**

* Adding five extractors before one smoke run passes
* Do not let that happen

---

## Phase 3. First bounded ingestion run

**Goal**
Run the pipeline end to end on the LCD corpus.

This is the first moment the repo becomes real. “Done” here is not “everything downloaded.” It is: JSONL exists, schema passes, counts are known, manifest exists, and a tiny consumer can read it. 

**Deliverables**

* first full `page_doc.v1.jsonl`
* first `run_manifest.json`
* validation log

**Suggested run evidence**

* counts by entity
* file hashes
* result flag
* observed timestamp

**Exit gate**

* first successful full run
* manifest written
* schema pass rate acceptable
* failure cases recorded, not hidden

**Main risk**

* reopening extractor architecture because text cleaning is imperfect
* that should be deferred into a later contract/cleanup step, exactly as your plan notes. 

---

## Phase 4. Coverage and drift guards

**Goal**
Make the pipeline trustworthy over time.

Your own notes already identify the correct guard set:

* compare REST counts against previous run
* compare REST URLs against sitemap URLs
* flag sudden drops
* flag schema violations
* flag duplicate `source_url`
* flag empty `text` when `html` is non-empty. 

**Deliverables**

* `checks/lcd_ingest_checks.py`
* `docs/runbook_lcd_ingest.md`
* tests for intentional fail/pass cases

**Exit gate**

* one failing test demonstrated
* same test corrected and passing
* runbook explains how to debug basic breakages

**Main risk**

* letting “works once” masquerade as a stable system
* this phase is what separates toy pipeline from asset

---

## Phase 5. Chunking and retrieval surface

**Goal**
Make the corpus actually useful at your fingertips.

A page corpus without retrieval units is still awkward. This phase emits chunks and gives you one minimal consumer path.

**Deliverables**

* `src/lcd_kb/normalize/chunking.py`
* `data/lcd/chunks/chunk_doc.v1.jsonl`
* tiny local reader:

  * list titles
  * search by slug/title/text
  * open source URL

**Example commands**

```bash
lcd-kb search "plan de estudios"
lcd-kb open --slug plan-de-estudios
lcd-kb stats
```

**Exit gate**

* chunk file exists
* parent links validated
* one search command returns useful results

**Main risk**

* jumping straight to embeddings, clustering, or RAG infra
* the first search surface should be boring and reliable

---

## Phase 6. Bus landing and integration

**Goal**
Place the corpus into the KB ecosystem without polluting downstream buses.

This is a crucial design point: raw or normalized LCD pages should live in a document-oriented corpus or document bus, not directly in Summary Bus. Summary artifacts should remain downstream derived outputs. 

**Deliverables**

* one bus placement decision
* one materialization path, for example:

  * `corpora/web/lcd/page_doc.v1.jsonl`
  * `corpora/web/lcd/chunk_doc.v1.jsonl`
* one downstream consumer example

**Exit gate**

* corpus is readable from its canonical location
* integration path is documented
* no ambiguity about upstream vs downstream responsibilities

**Main risk**

* collapsing acquisition, normalization, and summary into one blob
* that weakens observability and contract boundaries

---

## Phase 7. Hardening and incremental sync

**Goal**
Convert the pipeline from a one-time build into a maintainable source system.

**Deliverables**

* incremental re-run policy
* content hash comparison
* “latest successful run” pointer
* inventory index
* idempotent behavior for repeated runs

**Suggested registry artifacts**

* `inventory.jsonl`
* `run_manifest.json`
* `latest.json`

**Exit gate**

* repeated run without duplication
* changed page detection works
* unchanged pages do not create noise

**Main risk**

* writing new artifacts every run without stable identity rules

---

# Recommended timeline

## Sprint 1

Phases 0 to 2
Outcome: scope frozen, contracts frozen, extractor skeleton working

## Sprint 2

Phase 3
Outcome: first successful bounded ingestion run

## Sprint 3

Phases 4 and 5
Outcome: validation guards plus usable search surface

## Sprint 4

Phases 6 and 7
Outcome: corpus lands cleanly in KB ecosystem and can be re-run incrementally

---

# Workstreams in parallel

## Stream A. Architecture and contracts

* scope
* schemas
* naming
* registry conventions

## Stream B. Source ingestion

* REST adapter
* pagination
* raw persistence
* normalization

## Stream C. Quality and observability

* schema checks
* coverage checks
* drift checks
* manifests

## Stream D. Consumer utility

* chunking
* local reader
* small index/search utility

This lets the team move in parallel without stepping on the same file all week.

---

# Definition of done for the project

The project is done when all of this is true:

* LCD content exists as a stable normalized JSONL corpus
* the corpus has a frozen schema
* each run writes a manifest with counts and hashes
* a minimal chunk layer exists
* a local search/reader exists
* coverage and drift checks exist
* the corpus lands in a document-oriented KB location, not Summary Bus
* reruns are predictable and low-noise.

---

# What I would explicitly not do in this project

* full WordPress mirroring
* binary asset ingestion in v1
* media-library capture
* “support every custom type first”
* embeddings before basic retrieval works
* broad Exactas ingestion in the same sprint

Those exclusions are not caution for its own sake. They protect the one thing that matters here: getting a clean first corpus instead of a sprawling half-backend. 

---

# Recommended repo milestone map

**M1. Scope + contract freeze**
Decision note, page schema, sample record

**M2. Extractor skeleton**
CLI, raw fetch, normalized emit

**M3. First corpus build**
`page_doc.v1.jsonl`, manifest, validation log

**M4. Trust layer**
coverage checks, drift checks, runbook

**M5. Retrieval layer**
`chunk_doc.v1`, local reader

**M6. KB integration**
document corpus landing path and downstream example

If you want, I can turn this next into a stricter project packet with:
a RACI table, milestone checklist, repo tree, and issue-by-issue task breakdown for the team.

