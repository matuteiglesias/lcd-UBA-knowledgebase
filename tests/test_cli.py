import argparse
import contextlib
import json
import io
import tempfile
import unittest
from pathlib import Path

from lcd_kb.cli import build_parser, cmd_build


class CliTests(unittest.TestCase):
    def test_fetch_parser(self) -> None:
        parser = build_parser()
        args = parser.parse_args(["fetch", "--entity", "page"])
        self.assertEqual(args.command, "fetch")
        self.assertEqual(args.entity, "page")

    def test_build_writes_anomaly_artifacts_without_promoting_failed_run(self) -> None:
        with tempfile.TemporaryDirectory() as tmpdir:
            base = Path(tmpdir)
            raw_pages = base / "raw" / "pages"
            raw_posts = base / "raw" / "posts"
            raw_pages.mkdir(parents=True)
            raw_posts.mkdir(parents=True)
            payload = {
                "entity": "page",
                "items": [
                    {
                        "id": 1,
                        "type": "page",
                        "slug": "uno",
                        "status": "publish",
                        "link": "https://lcd.exactas.uba.ar/dup/",
                        "title": {"rendered": "Uno"},
                        "content": {"rendered": "<p>Uno</p>"},
                        "excerpt": {"rendered": ""},
                        "author": 1,
                        "featured_media": 0,
                        "parent": 0,
                        "menu_order": 0,
                        "categories": [],
                        "tags": [],
                        "date_gmt": "2026-03-20T00:00:00",
                        "modified_gmt": "2026-03-20T00:00:00",
                    },
                    {
                        "id": 2,
                        "type": "page",
                        "slug": "dos",
                        "status": "publish",
                        "link": "https://lcd.exactas.uba.ar/dup/",
                        "title": {"rendered": "Dos"},
                        "content": {"rendered": "<p>Dos</p>"},
                        "excerpt": {"rendered": ""},
                        "author": 1,
                        "featured_media": 0,
                        "parent": 0,
                        "menu_order": 0,
                        "categories": [],
                        "tags": [],
                        "date_gmt": "2026-03-20T00:00:00",
                        "modified_gmt": "2026-03-20T00:00:00",
                    },
                ],
            }
            (raw_pages / "pages-page-0001.json").write_text(json.dumps(payload), encoding="utf-8")
            (raw_posts / "posts-page-0001.json").write_text(json.dumps({"entity": "post", "items": []}), encoding="utf-8")

            with contextlib.redirect_stdout(io.StringIO()):
                result = cmd_build(
                    argparse.Namespace(
                        run_id="failed-run",
                        observed_at="2026-03-20T00:00:00Z",
                        started_at="2026-03-20T00:00:00Z",
                        completed_at="2026-03-20T00:01:00Z",
                        page_raw=str(raw_pages),
                        post_raw=str(raw_posts),
                        page_output=str(base / "canonical" / "page.jsonl"),
                        post_output=str(base / "canonical" / "post.jsonl"),
                        page_chunks=str(base / "canonical" / "page_chunks.jsonl"),
                        post_chunks=str(base / "canonical" / "post_chunks.jsonl"),
                        index_output=str(base / "canonical" / "index.json"),
                        manifest_output=str(base / "canonical" / "manifest.json"),
                        registry_dir=str(base / "registry"),
                        runs_dir=str(base / "runs"),
                        max_chars=400,
                    )
                )

            self.assertEqual(result, 1)
            self.assertFalse((base / "registry" / "latest_success.json").exists())
            self.assertTrue((base / "registry" / "latest_attempted.json").exists())
            self.assertTrue((base / "runs" / "failed-run" / "reports" / "anomalies" / "duplicate_source_urls.jsonl").exists())


if __name__ == "__main__":
    unittest.main()
