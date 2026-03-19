import json
import tempfile
import unittest
from pathlib import Path

from lcd_kb.registry.manifest import (
    build_artifact_inventory,
    build_latest_success_record,
    default_run_id,
    manifest_for_outputs,
    write_inventory,
    write_latest_success,
)


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
            self.assertTrue(manifest["artifacts"][0]["sha256"].startswith("sha256:"))

    def test_write_latest_success(self) -> None:
        with tempfile.TemporaryDirectory() as tmpdir:
            base = Path(tmpdir)
            latest = base / "state" / "latest_success.json"
            record = build_latest_success_record(
                run_id="run-1",
                completed_at="2026-03-19T20:01:00Z",
                run_dir=base / "runs" / "run-1",
                manifest_path=base / "runs" / "run-1" / "manifests" / "run_manifest.json",
                index_path=base / "runs" / "run-1" / "indexes" / "title_slug_index.json",
                validation_report_path=base / "runs" / "run-1" / "reports" / "validation_report.json",
                inventory_path=base / "runs" / "run-1" / "registry" / "artifact_inventory.json",
            )
            write_latest_success(latest, record)
            self.assertTrue(latest.exists())
            loaded = json.loads(latest.read_text(encoding="utf-8"))
            self.assertEqual(loaded["run_id"], "run-1")
            self.assertEqual(loaded["run_dir"], str(base / "runs" / "run-1"))
            self.assertEqual(loaded["inventory_path"], str(base / "runs" / "run-1" / "registry" / "artifact_inventory.json"))

    def test_write_inventory(self) -> None:
        with tempfile.TemporaryDirectory() as tmpdir:
            base = Path(tmpdir)
            output = base / "registry" / "artifact_inventory.json"
            manifest = {"result": "success", "entity_counts": {"page": 1}, "artifacts": [{"kind": "normalized_page_jsonl"}]}
            inventory = build_artifact_inventory(
                run_id="run-1",
                run_dir=base / "runs" / "run-1",
                manifest_path=base / "runs" / "run-1" / "manifests" / "run_manifest.json",
                manifest=manifest,
                index_path=base / "runs" / "run-1" / "indexes" / "title_slug_index.json",
                validation_report_path=base / "runs" / "run-1" / "reports" / "validation_report.json",
                latest_success_path=base / "state" / "latest_success.json",
            )
            write_inventory(output, inventory)
            loaded = json.loads(output.read_text(encoding="utf-8"))
            self.assertEqual(loaded["contract"], "artifact_inventory.v1")
            self.assertEqual(loaded["run_id"], "run-1")
            self.assertEqual(loaded["latest_success_path"], str(base / "state" / "latest_success.json"))
            self.assertTrue(any(item["relationship"] == "chunked_into" for item in loaded["relationships"]))


if __name__ == "__main__":
    unittest.main()
