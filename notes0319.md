Yes. The right shape is not “clone the WordPress site.” It is “define a small, low-noise acquisition path that turns the current LCD frontend into a governed document corpus.” Your own draft already points in that direction: one narrow corpus first, normalized page-like documents in JSONL, REST as primary source, and a document-oriented bus rather than dumping raw web pages into summary artifacts. 

The main design move is this:

**treat LCD as a source system, not as a website to mirror.**

That means the monorepo should capture four things cleanly:

1. source acquisition
2. normalization into KB-native records
3. registry/manifests/run evidence
4. one small consumer surface for search, chunking, and later context injection

A good v1 monorepo would look like this:

```text
lcd-kb/
  README.md
  pyproject.toml
  Makefile

  docs/
    lcd_ingest_scope_v1.md
    runbook_lcd_ingest.md
    contracts/
      page_doc_v1.md
      chunk_doc_v1.md

  schemas/
    page_doc_v1.json
    chunk_doc_v1.json
    run_manifest_v1.json

  configs/
    lcd.yaml

  src/lcd_kb/
    cli.py
    sources/
      wordpress_rest.py
      sitemap.py
      html_probe.py
    normalize/
      page_doc.py
      html_to_text.py
      outlinks.py
      attachments.py
      chunking.py
    registry/
      manifest.py
      hashes.py
      inventory.py
    checks/
      schema_checks.py
      coverage_checks.py
      drift_checks.py
    consumers/
      search_index.py
      grep_reader.py

  data/
    lcd/
      raw/
      normalized/
      chunks/
      manifests/
      indexes/

  tests/
    test_page_doc.py
    test_chunking.py
    test_manifest.py
    test_coverage.py
```

The core contract should be `page_doc.v1`, exactly as your plan suggests: source identity, normalized content, extracted relationships, and ingest metadata. That gives you a stable unit that can survive frontend changes better than ad hoc HTML snapshots. 

I would then add a second contract immediately after:

```json
{
  "contract": "chunk_doc.v1",
  "parent_contract": "page_doc.v1",
  "site_id": "lcd.exactas.uba.ar",
  "source_url": "...",
  "page_id": "...",
  "chunk_id": "...",
  "title": "...",
  "slug": "...",
  "section_path": ["Plan de estudios", "Ciclo básico"],
  "text": "...",
  "token_count": 312,
  "char_count": 1844,
  "content_hash": "sha256:...",
  "page_content_hash": "sha256:...",
  "observed_at": "..."
}
```

Why add chunks early?

Because “at my fingertips” usually means retrieval, not storage. If you stop at `page_doc.v1`, you have a registry. If you also emit `chunk_doc.v1`, you have something queryable, embeddable, and ready for downstream context assembly.

The bus placement matters. Your own note is right to reject putting raw normalized pages straight into Summary Bus. These should live in a document corpus or document bus first, with summaries derived later.

So I would use:

```text
data/lcd/normalized/page_doc.v1.jsonl
data/lcd/chunks/chunk_doc.v1.jsonl
data/lcd/manifests/run_manifest.json
data/lcd/indexes/title_slug_index.json
```

and conceptually map them to:

```text
corpora/web/lcd/page_doc.v1.jsonl
corpora/web/lcd/chunk_doc.v1.jsonl
```

not to `summary_bus`.

The registry should be first-class, not an afterthought. I would keep three registry artifacts:

```text
inventory.jsonl
run_manifest.json
latest.json
```

Where:

* `inventory.jsonl` is one row per source object/page
* `run_manifest.json` is one row per ingestion run with counts, hashes, result
* `latest.json` is a convenience pointer to the most recent successful run

That gives you reproducibility, cheap drift detection, and a stable handle for downstream consumers.

The extraction path should stay narrow:

* primary: WordPress REST
* secondary: sitemap for coverage checks
* tertiary: HTML probe only when REST misses something

And keep these out of v1:

* binary asset download
* media mirroring
* screenshots
* full-site recursive crawl

That constraint is not cosmetic. It is what prevents the repo from turning into another storage swamp. Your plan explicitly warns against broad mirroring and asset hoarding, and that is the right call. 

The minimal CLI should be boring:

```bash
lcd-kb fetch --entity page
lcd-kb fetch --entity post
lcd-kb normalize
lcd-kb chunk
lcd-kb manifest
lcd-kb check
lcd-kb build-index
```

And the acceptance bar for v1 should be equally boring:

* JSONL exists
* schema passes
* counts known
* duplicate URLs flagged
* empty-text anomalies flagged
* one local search surface works

Your draft already proposes the right quality gates: compare REST counts with prior runs, compare REST URLs with sitemap URLs, flag schema violations, duplicate `source_url`, and suspicious empty text. Those guards are worth more than another extractor feature. 

If I were sharpening the design further, I would make one change to your proposed scope:

Do **not** start with every custom type on day 1.

Start with:

* `page`
* `post`

Then add custom types only if the coverage report proves they matter. Otherwise you risk building endpoint-specific glue before you know the information value. Your plan lists `dlm_download`, `avada_portfolio`, and `avada_faq` as candidates, which is fine as staged scope, but not all need to be first-pass mandatory. 

So the clean v1 sequence is:

**Phase A**

* governance note
* `page_doc.v1`
* fetch `page` and `post`
* normalize
* chunk
* manifest
* local reader

**Phase B**

* coverage diff versus sitemap
* decide whether custom types are worth adding
* add only the ones with actual content value

The local reader can be very small. Even this is enough:

```bash
lcd-kb search "plan de estudios"
lcd-kb open --slug plan-de-estudios
lcd-kb grep --field text "tesis"
lcd-kb stats
```

That gives you the “fingertips” feeling fast, without prematurely building a vector stack.

If you want the repo to feel aligned with KB contracts, the repo should expose these invariants explicitly:

* every run has a manifest
* every normalized record has a contract name
* every chunk links to a parent page record
* every output file is hashable and reproducible
* every drift check fails loudly
* every downstream consumer reads normalized artifacts, never raw HTML directly

That is the backbone.

My recommendation, stated plainly:

**Build a document-corpus monorepo, not a site mirror.**
Use WordPress REST to regenerate a stable backend-like registry from the frontend surface.
Emit `page_doc.v1` and `chunk_doc.v1`.
Store them in a document corpus path with manifests and checks.
Keep summaries and embeddings downstream.

That is the viable path.

I can turn this into a concrete starter pack next: repo tree, `page_doc.v1` schema, `chunk_doc.v1` schema, and a first-pass `pyproject.toml` plus CLI skeleton.

