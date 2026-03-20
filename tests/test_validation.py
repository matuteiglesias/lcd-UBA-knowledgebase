import unittest
from pathlib import Path
import tempfile
import json

from lcd_kb.checks.validation import validate_corpus, write_validation_report


class ValidationTests(unittest.TestCase):
    def test_validate_corpus_pass(self) -> None:
        with tempfile.TemporaryDirectory() as tmpdir:
            base = Path(tmpdir)
            page = base / "page.jsonl"
            post = base / "post.jsonl"
            page_chunk = base / "page_chunk.jsonl"
            post_chunk = base / "post_chunk.jsonl"
            raw_pages = base / "raw-pages"
            raw_posts = base / "raw-posts"
            raw_pages.mkdir()
            raw_posts.mkdir()
            page.write_text(json.dumps({
                "entity_type": "page",
                "source_id": 1,
                "source_url": "https://lcd.exactas.uba.ar/uno/",
                "html": "<p>Uno</p>",
                "text": "Uno",
            }) + "\n", encoding="utf-8")
            post.write_text("", encoding="utf-8")
            page_chunk.write_text(json.dumps({"page_id": "page:1", "chunk_id": "page:1#chunk:0001", "text": "Uno"}) + "\n", encoding="utf-8")
            post_chunk.write_text("", encoding="utf-8")
            (raw_pages / "pages-page-0001.json").write_text(json.dumps({
                "headers": {"x-wp-total": "1", "x-wp-totalpages": "1"},
                "items": [{"link": "https://lcd.exactas.uba.ar/uno/"}],
            }), encoding="utf-8")
            report = validate_corpus(
                page_path=page,
                post_path=post,
                page_chunk_path=page_chunk,
                post_chunk_path=post_chunk,
                raw_page_dir=raw_pages,
                raw_post_dir=raw_posts,
            )
            self.assertTrue(report["ok"])
            self.assertEqual(report["anomaly_counts"]["duplicate_source_urls"], 0)

    def test_validate_corpus_failures(self) -> None:
        with tempfile.TemporaryDirectory() as tmpdir:
            base = Path(tmpdir)
            page = base / "page.jsonl"
            post = base / "post.jsonl"
            page_chunk = base / "page_chunk.jsonl"
            post_chunk = base / "post_chunk.jsonl"
            raw_pages = base / "raw-pages"
            raw_posts = base / "raw-posts"
            raw_pages.mkdir()
            raw_posts.mkdir()
            page.write_text(
                json.dumps({"entity_type": "page", "source_id": 1, "source_url": "https://lcd.exactas.uba.ar/dup/", "html": "<p>Uno</p>", "text": "Uno"}) + "\n"
                + json.dumps({"entity_type": "page", "source_id": 2, "source_url": "https://lcd.exactas.uba.ar/dup/", "html": "<p>Dos</p>", "text": ""}) + "\n",
                encoding="utf-8",
            )
            post.write_text("", encoding="utf-8")
            page_chunk.write_text(json.dumps({"page_id": "page:999", "chunk_id": "page:999#chunk:0001", "text": ""}) + "\n", encoding="utf-8")
            post_chunk.write_text("", encoding="utf-8")
            (raw_pages / "pages-page-0001.json").write_text(json.dumps({
                "headers": {"x-wp-total": "3", "x-wp-totalpages": "1"},
                "items": [
                    {"link": "https://lcd.exactas.uba.ar/dup/"},
                    {"link": "https://lcd.exactas.uba.ar/missing/"},
                ],
            }), encoding="utf-8")
            report = validate_corpus(
                page_path=page,
                post_path=post,
                page_chunk_path=page_chunk,
                post_chunk_path=post_chunk,
                raw_page_dir=raw_pages,
                raw_post_dir=raw_posts,
            )
            self.assertFalse(report["ok"])
            self.assertEqual(report["checks"]["duplicate_source_urls"], ["https://lcd.exactas.uba.ar/dup/"])
            self.assertEqual(report["checks"]["missing_chunk_parents"], ["page:999"])
            self.assertEqual(report["checks"]["empty_chunks"], ["page:999#chunk:0001"])
            self.assertEqual(report["checks"]["empty_text_with_html"], ["https://lcd.exactas.uba.ar/dup/"])
            self.assertEqual(len(report["anomaly_records"]["duplicate_source_urls"]), 2)
            self.assertEqual(len(report["anomaly_records"]["empty_text_docs"]), 1)
            self.assertEqual(len(report["anomaly_records"]["orphan_chunks"]), 1)
            self.assertEqual(len(report["anomaly_records"]["empty_chunks"]), 1)


if __name__ == "__main__":
    unittest.main()
