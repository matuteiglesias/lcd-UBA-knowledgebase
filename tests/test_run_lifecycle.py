import json
import tempfile
import unittest
from pathlib import Path

from lcd_kb.registry.run_lifecycle import build_drift_report, ensure_run_layout


class RunLifecycleTests(unittest.TestCase):
    def test_ensure_run_layout(self) -> None:
        with tempfile.TemporaryDirectory() as tmpdir:
            layout = ensure_run_layout(Path(tmpdir) / "runs" / "run-1")
            self.assertTrue(layout["staging"].exists())
            self.assertTrue(layout["reports"].exists())

    def test_build_drift_report(self) -> None:
        with tempfile.TemporaryDirectory() as tmpdir:
            base = Path(tmpdir)
            current_page = base / "current-page.jsonl"
            current_post = base / "current-post.jsonl"
            previous_page = base / "previous-page.jsonl"
            previous_post = base / "previous-post.jsonl"

            current_page.write_text(
                json.dumps(
                    {
                        "entity_type": "page",
                        "slug": "plan-2026",
                        "source_url": "https://lcd.exactas.uba.ar/plan-2026/",
                        "content_hash": "sha256:new",
                    }
                )
                + "\n",
                encoding="utf-8",
            )
            current_post.write_text("", encoding="utf-8")
            previous_page.write_text(
                json.dumps(
                    {
                        "entity_type": "page",
                        "slug": "plan-2025",
                        "source_url": "https://lcd.exactas.uba.ar/plan-2025/",
                        "content_hash": "sha256:old",
                    }
                )
                + "\n",
                encoding="utf-8",
            )
            previous_post.write_text("", encoding="utf-8")

            report = build_drift_report(
                current_run_id="run-current",
                current_page_path=current_page,
                current_post_path=current_post,
                previous_trusted_manifest={
                    "run_id": "run-previous",
                    "artifacts": [
                        {"kind": "normalized_page_jsonl", "path": str(previous_page)},
                        {"kind": "normalized_post_jsonl", "path": str(previous_post)},
                    ],
                },
            )

            self.assertEqual(report["previous_trusted_run_id"], "run-previous")
            self.assertEqual(report["page_count_delta"], 0)
            self.assertEqual(report["added_urls"], ["https://lcd.exactas.uba.ar/plan-2026/"])
            self.assertEqual(report["removed_urls"], ["https://lcd.exactas.uba.ar/plan-2025/"])
            self.assertIn("removed_urls_detected", report["suspicious_thresholds_triggered"])


if __name__ == "__main__":
    unittest.main()
