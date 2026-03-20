import json
import tempfile
import unittest
from pathlib import Path

from lcd_kb.registry.manifest import default_run_id, manifest_for_outputs


class ManifestTests(unittest.TestCase):
    def test_default_run_id(self) -> None:
        self.assertEqual(default_run_id("2026-03-19T20:00:00Z"), "lcd_ingest_20260319T200000Z")

    def test_manifest_for_outputs(self) -> None:
        with tempfile.TemporaryDirectory() as tmpdir:
            base = Path(tmpdir)
            normalized_page = base / "page_doc.v1.jsonl"
            normalized_post = base / "post_doc.v1.jsonl"
            normalized_page.write_text(json.dumps({"slug": "uno"}) + "\n", encoding="utf-8")
            normalized_post.write_text("", encoding="utf-8")
            raw_pages = base / "raw-pages"
            raw_posts = base / "raw-posts"
            raw_pages.mkdir()
            raw_posts.mkdir()
            (raw_pages / "pages-page-0001.json").write_text("{}", encoding="utf-8")

            manifest = manifest_for_outputs(
                run_id="run-1",
                started_at="2026-03-19T20:00:00Z",
                completed_at="2026-03-19T20:01:00Z",
                normalized_paths={"page": normalized_page, "post": normalized_post},
                chunk_paths={"page": base / "page_chunk_doc.v1.jsonl", "post": base / "post_chunk_doc.v1.jsonl"},
                raw_dirs={"page": raw_pages, "post": raw_posts},
            )
            self.assertEqual(manifest["contract"], "run_manifest.v1")
            self.assertEqual(manifest["entity_counts"]["page"], 1)
            self.assertEqual(manifest["entity_counts"]["post"], 0)
            self.assertEqual(manifest["run_status"], "completed_untrusted")
            self.assertEqual(manifest["trust_level"], "untrusted")
            self.assertTrue(manifest["artifacts"][0]["sha256"].startswith("sha256:"))


if __name__ == "__main__":
    unittest.main()
