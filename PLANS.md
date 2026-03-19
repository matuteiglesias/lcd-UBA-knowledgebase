Yes. The clean closure here is not “we learned some things about WordPress,” but “we now have enough evidence to define a low-noise ingestion path.”

Your docs already give the right frame for this. The KB contracts site is built around explicit interfaces, invariants, manifests, run records, and observability, with named buses such as Event Bus, Sessions Bus, Summary Bus, and Manifests. It also emphasizes trusted outputs and failure containment rather than ad hoc glue. ([KB Contracts][1]) Your execution model then gives the runtime discipline: one mode per block, bounded operators, acceptance checks, evidence patterns, OpRuns with next pointers, and DebugPackets when exploration starts to sprawl. ([My Site][2])

So I would close this block with a plan that treats “LCD pages at your fingertips” as a small, staged PIPELINE plus a small TOOLSMITH layer, not as an open-ended crawling project.

## Closure statement for this block

We have already established enough to move from exploration to controlled acquisition:

* LCD is small enough to ingest quietly first.
* The target artifact should be **normalized page-like documents in JSONL**, not a pile of raw HTML dumps.
* REST should be the primary source, with sitemap and HTML only as coverage checks.
* The first successful outcome is not “mirror the site,” but “have LCD content queryable as stable KB documents with manifests and next pointers.”

That matches your contract-first architecture and the execution model’s requirement that every block end with evidence and a next pointer. ([KB Contracts][1])

## The operating principle

Use **one narrow corpus first**: LCD pages/posts/custom types only.

Do **not** start with Exactas media, full binary downloads, screenshots, or whole-site mirroring. That is how this turns from knowledge ingestion into storage drift.

The working unit should be:

* one source
* one extractor
* one normalized document contract
* one manifest
* one small consumer path

That is exactly in line with your execution model: one block, one mode, bounded operator, evidence that actually changes future behavior. ([My Site][2])

# Proposed future sessions

I would design six sessions. Each one should end with a concrete artifact, a minimal manifest, and a next pointer.

---

## Session 1: GOVERNANCE

**Title:** Freeze the LCD ingestion target

**Purpose**
Decide exactly what “available to me as knowledge base” means for LCD.

**Questions to settle**

* Which LCD entities count in v1:

  * `page`
  * `post`
  * `dlm_download`
  * `avada_portfolio`
  * `avada_faq`
* What fields make a “page document”
* What must be excluded in v1:

  * binary assets
  * thumbnails
  * full media library download
  * comments
  * admin-only endpoints

**Artifact**
A one-page decision note, for example:

* scope in
* scope out
* document contract name
* source priority: REST first, sitemap second, HTML third
* re-run policy

**Mode reason**
Your execution model says GOVERNANCE work must produce a decision artifact that changes future behavior, with an explicit next pointer. ([My Site][2])

**Evidence**

* `docs/lcd_ingest_scope_v1.md`
* one-paragraph next pointer

**Stop rule**
If the session starts drifting into implementation, stop and move to Session 2.

---

## Session 2: CONTRACT

**Title:** Define `page_doc.v1` for KB buses

**Purpose**
Create the normalized JSONL line contract for site pages/documents.

**This is the key move.**
Do not think “WordPress object.” Think “knowledge document.”

### Suggested `page_doc.v1`

```json
{
  "contract": "page_doc.v1",
  "source_system": "wordpress_rest",
  "site_id": "lcd.exactas.uba.ar",
  "entity_type": "page",
  "entity_subtype": null,
  "source_id": 395,
  "source_url": "https://lcd.exactas.uba.ar/...",
  "api_url": "https://lcd.exactas.uba.ar/wp-json/wp/v2/pages/395",
  "slug": "plan-de-estudios",
  "title": "Plan de estudios",
  "status": "publish",
  "language": "es",
  "created_at": "2025-01-10T12:34:56-03:00",
  "modified_at": "2026-03-01T09:10:11-03:00",
  "parent_source_id": 12,
  "taxonomy": {
    "categories": [],
    "tags": [],
    "custom": {}
  },
  "html": "<p>...</p>",
  "text": "clean extracted text...",
  "outlinks": [
    {"url": "https://...", "kind": "external"}
  ],
  "attachments": [
    {"url": "https://...", "mime_type": "application/pdf"}
  ],
  "metadata": {
    "template": "",
    "author": 3,
    "menu_order": 0,
    "featured_media": 17
  },
  "content_hash": "sha256:...",
  "ingest_run_id": "lcd_ingest_2026-03-12T...",
  "observed_at": "2026-03-12T..."
}
```

### Why this shape

Because it separates:

* source identity
* normalized content
* extracted relationships
* ingest metadata
* reproducibility

That fits the contracts/manual mindset of stable interfaces, manifests, and trusted outputs. ([KB Contracts][1])

**Artifact**

* `docs/contracts/page_doc_v1.md`
* `schemas/page_doc_v1.json`
* `examples/page_doc_v1.example.json`

**Evidence**
Schema validates one hand-made sample.

**Stop rule**
If you are debating “perfect metadata,” freeze v1 and move on.

---

## Session 3: TOOLSMITH

**Title:** Build the LCD extractor skeleton

**Purpose**
Create one small CLI that pulls REST entities and writes raw JSON plus normalized JSONL.

### CLI shape

```bash
lcd_ingest fetch --site lcd --entity page
lcd_ingest fetch --site lcd --entity post
lcd_ingest fetch --site lcd --entity dlm_download
lcd_ingest normalize --site lcd
lcd_ingest manifest --site lcd
```

### Output layout

```text
data/lcd/raw/pages/*.json
data/lcd/raw/posts/*.json
data/lcd/raw/dlm_download/*.json
data/lcd/raw/avada_portfolio/*.json
data/lcd/raw/avada_faq/*.json

data/lcd/normalized/page_doc.v1.jsonl
data/lcd/manifests/run_manifest.json
```

### Important design choice

The extractor should support:

* pagination
* `_fields=` reduction where possible
* raw preservation
* normalized emission
* no binary download

This is TOOLSMITH because the output is a reusable interface with a clear usage path, not just a one-off notebook. Your execution model explicitly expects a usable interface, predictable smoke run, and one consumer path. ([My Site][2])

**Artifact**
Working CLI with `--help`.

**Evidence**

* one smoke run against `page`
* one sample JSONL line
* exit code discipline

**Stop rule**
If you start adding all custom extractors before the first smoke run passes, stop.

---

## Session 4: PIPELINE

**Title:** Run bounded LCD ingestion v1

**Purpose**
Run the extractor against the full LCD structured corpus.

### Scope

* `page`
* `post`
* `dlm_download`
* `avada_portfolio`
* `avada_faq`
* optional supporting taxonomies

### What “done” means

Not “everything downloaded.”
Done means:

* JSONL exists
* schema passes
* counts are known
* one manifest exists
* one sample consumer can read it

### Manifest proposal

```json
{
  "run_id": "lcd_ingest_2026-03-12T222500Z",
  "site_id": "lcd.exactas.uba.ar",
  "entities": {
    "page": 19,
    "post": 239,
    "media_metadata": 419,
    "dlm_download": 0,
    "avada_portfolio": 0,
    "avada_faq": 0
  },
  "files_written": [
    "data/lcd/normalized/page_doc.v1.jsonl"
  ],
  "hashes": {
    "page_doc.v1.jsonl": "sha256:..."
  },
  "result": "PASS"
}
```

Even if some custom types come back empty, that is still useful evidence.

Your execution model says PIPELINE work should produce non-trivial artifacts plus validation gates and preferably manifests with counts and hashes. That is exactly this session. ([My Site][2])

**Evidence**

* `page_doc.v1.jsonl`
* run manifest
* validation log

**Stop rule**
If extraction works but HTML cleaning is messy, do not reopen the whole extractor. Record a next pointer and move to a small CONTRACT session later.

---

## Session 5: CONTRACT

**Title:** Add coverage and drift guards

**Purpose**
Prevent silent breakage and incomplete future syncs.

### Guards

* compare REST counts against previous run
* compare REST URLs against sitemap URLs
* flag sudden drops
* flag schema violations
* flag duplicate `source_url`
* flag empty `text` when `html` is non-empty

This is straight from your architecture priorities: explicit invariants, observability, and failure containment. ([KB Contracts][1])

**Artifact**

* `checks/lcd_ingest_checks.py`
* `notes/debug_packet_*.md` only if needed
* `docs/runbook_lcd_ingest.md`

**Evidence**
One failing test intentionally demonstrated, then passing.

**Stop rule**
If you exceed the timebox narrowing strange edge cases, write a DebugPacket. Your execution model is explicit about that. ([My Site][2])

---

## Session 6: PIPELINE or SERVICE

**Title:** Land LCD docs into the buses

**Purpose**
Make the normalized pages available as KB-native artifacts.

You mentioned pages as a document type in JSONL lines in the buses. That is the right direction.

### Practical landing options

If you want the least disruption, create a dedicated document stream such as:

* `document_bus/page_doc.v1.jsonl`

or a site-specific corpus path such as:

* `corpora/web/lcd/page_doc.v1.jsonl`

If you want it closer to your existing session/summary ecosystem, treat this as an upstream corpus that later feeds summaries rather than stuffing raw pages directly into `summary_bus`.

My recommendation:

* **raw/normalized pages should not go straight into Summary Bus**
* they should live in a document-oriented corpus/bus
* summaries can be derived later

That is more consistent with contracts and observability. Summary artifacts are downstream trusted outputs, not the place to dump raw acquired web pages. ([KB Contracts][1])

**Artifact**

* one bus placement decision
* one materialization path
* one consumer example that queries or reads the JSONL

**Evidence**
A tiny reader that can:

* list titles
* search slug/title/text
* open source URL

---

# Suggested session sequence

If the goal is “quietly and carefully,” I would do:

1. Session 1, GOVERNANCE, 25 minutes
2. Session 2, CONTRACT, 35 minutes
3. Session 3, TOOLSMITH, 45 minutes
4. Session 4, PIPELINE, 45 minutes
5. Session 5, CONTRACT, 30 minutes
6. Session 6, PIPELINE/SERVICE, 30 minutes

That keeps each block bounded and ensures every block leaves a next pointer, which your execution model requires. ([My Site][2])

# What should be “at your fingertips” after these sessions

For LCD, the end state should be:

* a single JSONL corpus of normalized site documents
* a manifest with counts and hashes
* a stable schema
* a small runbook
* a way to re-run incrementally
* enough metadata to later summarize, cluster, or search

That is a good stopping point because it gives you usable knowledge without dragging you into full mirroring, screenshot capture, or asset hoarding.

# The main anti-drowning constraints

These are the constraints I would enforce from the start:

* LCD only for v1
* no binary asset download in v1
* no Exactas full ingestion in the same phase
* one normalized document contract only
* one output corpus only
* one consumer path only
* no “improve everything” pass before first successful run

That is the difference between a finished small pipeline and another exploratory sprawl.

# Suggested closing note for this block

You can close this session with something like:

> Outcome: stack and extraction surface confirmed.
> Decision: LCD becomes the first controlled web corpus.
> Next: define `page_doc.v1`, build a bounded extractor, write normalized JSONL plus manifest, and land it as a document corpus for the buses.
> Excluded for now: Exactas full media ingestion, binary downloads, and broad mirroring.

If you want, next turn I can turn this into a strict **Session Pack** with six operator cards, each written in your execution-model style: mode, operator, steps, acceptance checks, evidence outputs, failure paths, and next pointer rule.

[1]: https://kb-contracts.matuteiglesias.link/ "KB Manual"
[2]: https://ops.matuteiglesias.link/docs/execution-model "Execution Model | My Site"

