SHELL := /usr/bin/env bash
.DEFAULT_GOAL := help

PYTHON ?= python3
PACKAGE := lcd_kb

PROJECT_ROOT := $(CURDIR)
DATA_ROOT := data/lcd
RUN_ROOT := $(DATA_ROOT)/runs
REGISTRY_DIR := $(DATA_ROOT)/registry
RAW_DIR := $(DATA_ROOT)/raw
REPORTS_DIR := $(DATA_ROOT)/reports
NORMALIZED_DIR := $(DATA_ROOT)/normalized
CHUNKS_DIR := $(DATA_ROOT)/chunks
INDEXES_DIR := $(DATA_ROOT)/indexes
FRONT_BUNDLE_DIR := $(DATA_ROOT)/front_bundle
FRONTEND_BUNDLE_DIR := frontend/data/lcd_bundle

PAGE_RAW := $(RAW_DIR)/pages
POST_RAW := $(RAW_DIR)/posts

PAGE_DOC := $(NORMALIZED_DIR)/page_doc.v1.jsonl
POST_DOC := $(NORMALIZED_DIR)/post_doc.v1.jsonl

PAGE_CHUNKS := $(CHUNKS_DIR)/page_chunk_doc.v1.jsonl
POST_CHUNKS := $(CHUNKS_DIR)/post_chunk_doc.v1.jsonl

TITLE_SLUG_INDEX := $(INDEXES_DIR)/title_slug_index.json
MANIFEST := $(DATA_ROOT)/manifests/run_manifest.json
VALIDATION_REPORT := $(REPORTS_DIR)/validation_report.json

LATEST_TRUSTED := $(REGISTRY_DIR)/latest_trusted.json

PER_PAGE ?= 25
MAX_PAGES ?=
MAX_CHARS ?= 400
RUN_ID ?=

ifdef MAX_PAGES
MAX_PAGES_ARG := --max-pages $(MAX_PAGES)
else
MAX_PAGES_ARG :=
endif

ifdef RUN_ID
RUN_ID_ARG := --run-id $(RUN_ID)
else
RUN_ID_ARG :=
endif

PYTHONPATH := $(PROJECT_ROOT)/src
export PYTHONPATH

.PHONY: help
help:
	@echo ""
	@echo "LCD KB operational Makefile"
	@echo ""
	@echo "Common targets:"
	@echo "  make doctor              Check repo/data-root hygiene"
	@echo "  make test                Run tests"
	@echo "  make fetch               Fetch page and post raw batches"
	@echo "  make normalize           Normalize raw batches into page_doc.v1"
	@echo "  make chunk               Chunk normalized docs"
	@echo "  make check               Validate corpus"
	@echo "  make index               Build title/slug index"
	@echo "  make manifest            Write manifest from current artifacts"
	@echo "  make build               Run staged build and promote only if validation passes"
	@echo "  make latest              Show latest successful/trusted run pointer"
	@echo "  make latest-artifacts    List artifacts for latest successful run"
	@echo "  make front-bundle        Export frontend bundle from latest trusted run"
	@echo "  make front-bundle-run RUN_ID=<id>"
	@echo "  make clean-drift         Fail if src/data/lcd exists"
	@echo ""

.PHONY: doctor
doctor:
	@echo "PROJECT_ROOT=$(PROJECT_ROOT)"
	@echo "PYTHONPATH=$(PYTHONPATH)"
	@echo "DATA_ROOT=$(DATA_ROOT)"
	@echo "RUN_ROOT=$(RUN_ROOT)"
	@echo "FRONT_BUNDLE_DIR=$(FRONT_BUNDLE_DIR)"
	@echo ""
	@$(PYTHON) -c "import lcd_kb, sys; print('lcd_kb import OK:', lcd_kb.__file__)"
	@$(MAKE) clean-drift

.PHONY: clean-drift
clean-drift:
	@if [ -d "src/data/lcd" ]; then \
		echo "ERROR: drifted data root exists at src/data/lcd"; \
		echo "Move it to _archive/drifted_data_roots/ before continuing."; \
		exit 1; \
	fi
	@echo "OK: no src/data/lcd drift root detected."

.PHONY: dirs
dirs:
	@mkdir -p \
		$(PAGE_RAW) \
		$(POST_RAW) \
		$(REPORTS_DIR) \
		$(NORMALIZED_DIR) \
		$(CHUNKS_DIR) \
		$(INDEXES_DIR) \
		$(REGISTRY_DIR) \
		$(FRONT_BUNDLE_DIR)

.PHONY: test
test:
	PYTHONPATH=$(PYTHONPATH) pytest -q

.PHONY: fetch fetch-page fetch-post
fetch: fetch-page fetch-post

fetch-page: dirs doctor
	$(PYTHON) -m $(PACKAGE).cli fetch \
		--entity page \
		--output-dir $(PAGE_RAW) \
		--per-page $(PER_PAGE) \
		$(MAX_PAGES_ARG)

fetch-post: dirs doctor
	$(PYTHON) -m $(PACKAGE).cli fetch \
		--entity post \
		--output-dir $(POST_RAW) \
		--per-page $(PER_PAGE) \
		$(MAX_PAGES_ARG)

.PHONY: normalize normalize-page normalize-post
normalize: normalize-page normalize-post

normalize-page: dirs doctor
	$(PYTHON) -m $(PACKAGE).cli normalize \
		--entity page \
		--raw-dir $(PAGE_RAW) \
		--output $(PAGE_DOC) \
		$(RUN_ID_ARG)

normalize-post: dirs doctor
	$(PYTHON) -m $(PACKAGE).cli normalize \
		--entity post \
		--raw-dir $(POST_RAW) \
		--output $(POST_DOC) \
		$(RUN_ID_ARG)

.PHONY: chunk chunk-page chunk-post
chunk: chunk-page chunk-post

chunk-page: dirs doctor
	$(PYTHON) -m $(PACKAGE).cli chunk \
		--entity page \
		--input $(PAGE_DOC) \
		--output $(PAGE_CHUNKS) \
		--max-chars $(MAX_CHARS)

chunk-post: dirs doctor
	$(PYTHON) -m $(PACKAGE).cli chunk \
		--entity post \
		--input $(POST_DOC) \
		--output $(POST_CHUNKS) \
		--max-chars $(MAX_CHARS)

.PHONY: index
index: dirs doctor
	$(PYTHON) -m $(PACKAGE).cli build-index \
		--page-input $(PAGE_DOC) \
		--post-input $(POST_DOC) \
		--output $(TITLE_SLUG_INDEX)

.PHONY: check
check: dirs doctor
	$(PYTHON) -m $(PACKAGE).cli check \
		--page-input $(PAGE_DOC) \
		--post-input $(POST_DOC) \
		--page-chunks $(PAGE_CHUNKS) \
		--post-chunks $(POST_CHUNKS) \
		--raw-page-dir $(PAGE_RAW) \
		--raw-post-dir $(POST_RAW) \
		--report-output $(VALIDATION_REPORT)

.PHONY: manifest
manifest: dirs doctor
	$(PYTHON) -m $(PACKAGE).cli manifest \
		--output $(MANIFEST) \
		--page-normalized $(PAGE_DOC) \
		--post-normalized $(POST_DOC) \
		--page-chunks $(PAGE_CHUNKS) \
		--post-chunks $(POST_CHUNKS) \
		--raw-page-dir $(PAGE_RAW) \
		--raw-post-dir $(POST_RAW) \
		$(RUN_ID_ARG)

.PHONY: local-pipeline
local-pipeline: fetch normalize chunk index check manifest
	@echo "Local pipeline completed against canonical data root: $(DATA_ROOT)"

.PHONY: build
build: dirs doctor
	$(PYTHON) -m $(PACKAGE).cli build \
		$(RUN_ID_ARG) \
		--run-root $(RUN_ROOT) \
		--registry-dir $(REGISTRY_DIR) \
		--page-raw $(PAGE_RAW) \
		--post-raw $(POST_RAW) \
		--page-output $(PAGE_DOC) \
		--post-output $(POST_DOC) \
		--page-chunks $(PAGE_CHUNKS) \
		--post-chunks $(POST_CHUNKS) \
		--index-output $(TITLE_SLUG_INDEX) \
		--manifest-output $(MANIFEST) \
		--max-chars $(MAX_CHARS)

.PHONY: latest
latest: doctor
	$(PYTHON) -m $(PACKAGE).cli latest \
		--latest-success $(REGISTRY_DIR)/latest_success.json
	@echo ""
	@echo "Latest trusted pointer:"
	@if [ -f "$(LATEST_TRUSTED)" ]; then cat $(LATEST_TRUSTED); else echo "missing: $(LATEST_TRUSTED)"; fi

.PHONY: latest-artifacts
latest-artifacts: doctor
	$(PYTHON) -m $(PACKAGE).cli latest-artifacts \
		--latest-success $(REGISTRY_DIR)/latest_success.json

.PHONY: inspect-run
inspect-run: doctor
	@if [ -z "$(RUN_ID)" ]; then \
		echo "Usage: make inspect-run RUN_ID=<run_id>"; \
		exit 1; \
	fi
	$(PYTHON) -m $(PACKAGE).cli inspect-run \
		--run-id $(RUN_ID) \
		--run-root $(RUN_ROOT)

	

.PHONY: front-bundle
front-bundle: doctor
	@if [ ! -f "$(LATEST_TRUSTED)" ]; then \
		echo "ERROR: missing latest trusted pointer: $(LATEST_TRUSTED)"; \
		exit 1; \
	fi
	$(eval TRUSTED_RUN_ID := $(shell $(PYTHON) -c "import json; print(json.load(open('$(LATEST_TRUSTED)'))['run_id'])"))
	$(PYTHON) -m $(PACKAGE).consumers.export_front_bundle \
		--run-root $(RUN_ROOT) \
		--run-id $(TRUSTED_RUN_ID) \
		--output-dir $(FRONT_BUNDLE_DIR)

.PHONY: front-bundle-run
front-bundle-run: doctor
	@if [ -z "$(RUN_ID)" ]; then \
		echo "Usage: make front-bundle-run RUN_ID=<run_id>"; \
		exit 1; \
	fi
	$(PYTHON) -m $(PACKAGE).consumers.export_front_bundle \
		--run-root $(RUN_ROOT) \
		--run-id $(RUN_ID) \
		--output-dir $(FRONT_BUNDLE_DIR)



.PHONY: front-bundle-check
front-bundle-check:
	@test -f $(FRONT_BUNDLE_DIR)/manifest.json
	@test -f $(FRONT_BUNDLE_DIR)/listing.json
	@test -f $(FRONT_BUNDLE_DIR)/posts.json
	@test -f $(FRONT_BUNDLE_DIR)/pages.json
	@test -f $(FRONT_BUNDLE_DIR)/search.json
	@test -d $(FRONT_BUNDLE_DIR)/items
	@echo "OK: front bundle has expected v1 files."


.PHONY: copy-front-bundle
copy-front-bundle: front-bundle front-bundle-check
	rm -rf $(FRONTEND_BUNDLE_DIR)
	mkdir -p $(FRONTEND_BUNDLE_DIR)
	cp -R $(FRONT_BUNDLE_DIR)/* $(FRONTEND_BUNDLE_DIR)/
	@echo "OK: copied front bundle to $(FRONTEND_BUNDLE_DIR)"




.PHONY: search
search: doctor
	@if [ -z "$(Q)" ]; then \
		echo "Usage: make search Q='plan de estudios'"; \
		exit 1; \
	fi
	$(PYTHON) -m $(PACKAGE).cli search "$(Q)" \
		--input $(PAGE_CHUNKS) \
		--limit 10

.PHONY: open
open: doctor
	@if [ -z "$(SLUG)" ]; then \
		echo "Usage: make open SLUG=plan-de-estudios"; \
		exit 1; \
	fi
	$(PYTHON) -m $(PACKAGE).cli open \
		--slug $(SLUG) \
		--input $(PAGE_DOC)

.PHONY: stats
stats: doctor
	$(PYTHON) -m $(PACKAGE).cli stats \
		--page-input $(PAGE_DOC) \
		--post-input $(POST_DOC) \
		--page-chunks $(PAGE_CHUNKS) \
		--post-chunks $(POST_CHUNKS)

.PHONY: archive-src-data
archive-src-data:
	@if [ -d "src/data/lcd" ]; then \
		mkdir -p _archive/drifted_data_roots; \
		dest="_archive/drifted_data_roots/src_data_lcd_$$(date -u +%Y%m%dT%H%M%SZ)"; \
		mv src/data/lcd "$$dest"; \
		echo "Archived src/data/lcd to $$dest"; \
	else \
		echo "No src/data/lcd drift root found."; \
	fi

.PHONY: clean-front-bundle
clean-front-bundle:
	rm -rf $(FRONT_BUNDLE_DIR)
	mkdir -p $(FRONT_BUNDLE_DIR)


.PHONY: front-bundle-url-check
front-bundle-url-check:
	@python3 - <<'PY'
	import json
	from pathlib import Path
	bundle = Path("data/lcd/front_bundle")
	bad = []
	for name in ["posts.json", "pages.json"]:
		path = bundle / name
		payload = json.loads(path.read_text())
		for item in payload.get("items", []):
			url = item.get("source_url") or ""
			if not url.startswith("https://lcd.exactas.uba.ar/") and not url.startswith("http://lcd.exactas.uba.ar/"):
				bad.append((name, item.get("id"), item.get("title"), url))
	print(f"checked bundle={bundle}")
	print(f"bad_source_urls={len(bad)}")
	for row in bad[:20]:
		print(row)
	raise SystemExit(1 if bad else 0)
	PY

.PHONY: clean-runtime
clean-runtime:
	@echo "Refusing to delete $(DATA_ROOT) automatically."
	@echo "Use explicit shell commands after inspecting artifacts."