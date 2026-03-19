Here is the answer again, rewritten as a **frozen project context** that you can hand to Codex repeatedly.

## Frozen vision for the project

The project’s purpose is to turn the knowledge currently trapped in the LCD WordPress surface into a **governed, queryable, re-runnable knowledge corpus**.

The target is not “a mirror of the website.”
The target is a **stable backend-like representation of the site’s knowledge**: normalized documents, clear schemas, manifests, incremental reruns, and chunked retrieval units that can later feed search, summarization, clustering, or context assembly. The desired end state is a single JSONL corpus of normalized site documents, a manifest with counts and hashes, a stable schema, a small runbook, and enough metadata to support later search and downstream processing. 

The corpus should land in a **document-oriented corpus or bus**, not be dumped directly into Summary Bus. Raw or normalized acquired pages are upstream source artifacts. Summaries are downstream trusted outputs derived later.

The operating principle is narrow and disciplined:

* one source first: LCD
* one extractor path first: WordPress REST
* one normalized document contract first
* one output corpus first
* one consumer path first
* no broad mirroring, no binary asset hoarding, no sprawling “improve everything” phase before the first successful run

## Final vision in one paragraph

We are rebuilding the LCD site as a **KB-native document corpus**. The repo should make the content present on the webpage accessible as structured knowledge records rather than frontend-only pages. That means fetching LCD content from the source system, normalizing it into stable document records, chunking it into retrieval units, storing it with manifests and hashes, validating it with coverage and drift checks, and landing it in a document corpus that can be searched locally and later fed into other knowledge-base systems. The endpoint is not “a crawler worked once,” but “LCD knowledge is present in a durable, inspectable, queryable data structure.”

---

# Codex orientation note

When a Codex agent opens this project and feels lost, it should ask:

**Which layer of the final system is still missing or not yet trustworthy?**

There are only six meaningful layers:

1. **Scope / governance**
2. **Contract / schema**
3. **Extractor / tooling**
4. **Pipeline run / corpus materialization**
5. **Checks / observability**
6. **Corpus landing / consumer access**

If one of those is weak, missing, or noisy, that is the phase the agent should place itself in.

Do not invent new phases unless one of these is clearly complete and stable.

---

# Phase map Codex should use

## Phase 1. Governance freeze

**Question:** do we have a frozen definition of what v1 includes and excludes?

This phase exists to prevent drift. It decides what counts as LCD knowledge in scope, which entities are included in v1, which source has priority, and what is explicitly excluded. The plan calls for a decision note with scope in, scope out, source priority, and rerun policy. 

**Signals that this phase is incomplete**

* no `lcd_ingest_scope_v1.md`
* agents are still debating whether to mirror the whole site
* people are arguing about media, screenshots, binaries, or broad Exactas ingestion
* custom post types are being added with no explicit scope note

**What Codex should do here**

* write or refine the scope note
* list what is in v1 and what is out
* freeze source priority: REST first, sitemap second, HTML only for coverage/debug
* write the next pointer to Contract phase

**What “done” looks like**

* one short governance note exists
* no ambiguity about v1 boundaries
* no one is still treating this as a full-site mirror project

---

## Phase 2. Contract definition

**Question:** do we already have a stable normalized document shape?

This phase defines the unit of knowledge. The important move is to think in **knowledge documents**, not raw WordPress objects. The plan explicitly centers `page_doc.v1` and shows a normalized page-like JSON shape with source identity, content, relationships, metadata, hashes, and ingest metadata. 

**Signals that this phase is incomplete**

* no `page_doc.v1` schema
* no example JSON line
* normalized fields are changing ad hoc across files
* agents are emitting raw JSON with no canonical contract
* chunking work started before parent record shape is stable

**What Codex should do here**

* define or refine `page_doc.v1`
* add `chunk_doc.v1` if missing
* create schema JSON and one example
* freeze required fields and parent-child identity rules

**What “done” looks like**

* one hand-made sample validates
* fields are named and stable
* chunk records can refer cleanly to parent page records

---

## Phase 3. Toolsmith / extractor skeleton

**Question:** do we have a reusable ingestion interface yet?

This phase builds the small CLI that fetches REST entities and writes raw plus normalized outputs. The plan proposes a CLI with fetch, normalize, and manifest steps, plus support for pagination, field reduction, raw preservation, normalized emission, and no binary download.

**Signals that this phase is incomplete**

* only notebooks or one-off scripts exist
* there is no `--help`
* raw acquisition and normalized emission are mixed together in a fragile script
* there is no predictable output layout
* agents are adding custom extractors before the first smoke run passes

**What Codex should do here**

* build or clean the CLI
* ensure fetch, normalize, manifest commands exist
* make outputs deterministic
* preserve raw JSON and emit normalized JSONL
* keep binary download out

**What “done” looks like**

* CLI runs with `--help`
* one smoke run against `page` works
* one sample JSONL line is written
* exit code behavior is predictable 

---

## Phase 4. Bounded corpus build

**Question:** do we already have a real corpus, or only tooling?

This is the phase where the pipeline becomes real. The plan is explicit that “done” here is not “everything downloaded,” but rather: JSONL exists, schema passes, counts are known, a manifest exists, and one consumer can read it. 

**Signals that this phase is incomplete**

* there is no full `page_doc.v1.jsonl`
* no manifest with counts/hashes exists
* agents keep discussing architecture instead of running the pipeline
* the extractor exists but nobody has produced a bounded successful run

**What Codex should do here**

* run the extractor on the full bounded LCD corpus
* write normalized JSONL
* write a manifest
* record counts and result state
* leave HTML cleaning imperfections for later unless they block the run

**What “done” looks like**

* normalized corpus exists
* manifest exists
* validation log exists
* the project has crossed from design to evidence

---

## Phase 5. Checks / drift / observability

**Question:** can the system fail silently right now?

This phase hardens the pipeline. The plan already names the guard set: compare REST counts to prior runs, compare REST URLs to sitemap URLs, flag sudden drops, schema violations, duplicate `source_url`, and empty `text` where `html` is non-empty. 

**Signals that this phase is incomplete**

* a run can succeed while missing many pages
* there are no failing tests for bad cases
* no runbook exists
* no drift signal exists between runs
* duplicate source URLs or empty extracted text can sneak through unnoticed

**What Codex should do here**

* add explicit checks
* add tests for fail/pass cases
* write `runbook_lcd_ingest.md`
* emit debug packets only when a bounded anomaly investigation is needed

**What “done” looks like**

* intentional failing case demonstrated
* same case fixed and passing
* future syncs have guardrails, not hope 

---

## Phase 6. Corpus landing and consumer path

**Question:** is the knowledge actually accessible “at your fingertips,” or just stored somewhere?

This is the phase that makes the project useful. The corpus should land in a document stream such as `document_bus/page_doc.v1.jsonl` or `corpora/web/lcd/page_doc.v1.jsonl`, and one tiny reader should be able to list titles, search by slug/title/text, and open source URLs.

**Signals that this phase is incomplete**

* the data exists but no one can query it easily
* agents are trying to wire raw pages directly into Summary Bus
* there is no single canonical landing path
* downstream use requires manual file spelunking

**What Codex should do here**

* choose and document the bus placement
* materialize the corpus in its canonical location
* add a small local consumer
* keep summary generation downstream, not mixed into acquisition

**What “done” looks like**

* LCD docs live in a document corpus
* there is one obvious place to read them from
* a small reader can search/open them
* the knowledge is genuinely usable, not just archived

---

# Fast self-placement rule for Codex

When picking up work, Codex should classify the repo into one of four states:

### State A. We do not know what we are building

Then the correct phase is **Governance**.

### State B. We know what we want, but the data shape is unstable

Then the correct phase is **Contract**.

### State C. The shape is known, but acquisition is not reliably producing artifacts

Then the correct phase is **Toolsmith** or **Bounded corpus build**.

### State D. Artifacts exist, but they are not yet trustworthy or usable

Then the correct phase is **Checks** or **Corpus landing**.

That rule alone should resolve most agent confusion.

---

# Anti-drift rules Codex should always obey

These should be treated as frozen constraints:

* LCD only for v1
* REST is primary
* sitemap and HTML are only secondary/coverage mechanisms
* no binary asset download in v1
* no full Exactas ingestion in the same phase
* one normalized document contract first
* one output corpus first
* one consumer path first
* raw/normalized pages do **not** go straight into Summary Bus
* if extraction works but cleaning is messy, do not reopen the whole extractor; record a next pointer and move on

These rules exist because otherwise the project turns into storage drift and endless extractor churn.

---

# A compact frozen brief you can paste to Codex

Use this if you want a short handoff block:

```md
## LCD Corpus Monorepo: Frozen Context

Goal: convert the current LCD WordPress surface into a KB-native document corpus. The target is not a site mirror. The target is a stable, re-runnable, queryable corpus of normalized documents and chunks, with manifests, hashes, checks, and one small reader.

End state:
- normalized JSONL corpus of LCD documents
- stable `page_doc.v1` and `chunk_doc.v1`
- run manifest with counts and hashes
- rerunnable acquisition path
- drift/coverage checks
- canonical corpus landing path
- minimal reader/search path

Phase order:
1. Governance: freeze v1 scope and exclusions
2. Contract: define stable normalized record shapes
3. Toolsmith: build CLI extractor skeleton
4. Pipeline: produce first successful bounded corpus
5. Checks: add coverage, drift, schema, duplicate, and empty-text guards
6. Corpus landing: place docs in document corpus and expose tiny reader

Always prefer:
- REST first
- sitemap second
- HTML only for coverage/debug

Always avoid in v1:
- full site mirroring
- binary/media ingestion
- broad Exactas ingestion
- dumping raw pages into Summary Bus
- reopening the extractor because cleaning is imperfect

Self-placement rule:
- unclear scope -> Governance
- unstable schema -> Contract
- no reliable run -> Toolsmith/Pipeline
- artifacts exist but are noisy/unusable -> Checks/Landing
```

---

# My recommendation for your repo

Put this into a file like:

`docs/frozen_context/lcd_corpus_project_vision.md`

and add a shorter companion:

`docs/frozen_context/codex_self_placement_rule.md`

The first explains the vision.
The second tells agents how to detect the current phase without asking you again.

If you want, I can now turn this into the exact Markdown file content for those two docs.

