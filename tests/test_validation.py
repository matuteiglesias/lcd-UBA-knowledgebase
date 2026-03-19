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
            self.assertEqual(report["coverage"]["page"]["fetched_item_count"], 1)
            self.assertEqual(report["checks"]["page_missing_normalized_urls"], [])

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
            self.assertEqual(report["checks"]["page_missing_normalized_urls"], ["https://lcd.exactas.uba.ar/missing/"])
            self.assertEqual(report["checks"]["page_count_mismatch_vs_raw"], [])
            self.assertEqual(report["coverage"]["page"]["warnings"], [
                "raw fetch captured 2 items but source reported total 3; this looks like a bounded or partial fetch"
            ])

    def test_write_validation_report(self) -> None:
        with tempfile.TemporaryDirectory() as tmpdir:
            output = Path(tmpdir) / "reports" / "validation.json"
            write_validation_report(output, {"ok": True})
            self.assertTrue(output.exists())
            self.assertEqual(json.loads(output.read_text(encoding="utf-8"))["ok"], True)


if __name__ == "__main__":
    unittest.main()
