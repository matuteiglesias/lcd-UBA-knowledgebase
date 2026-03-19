import argparse
import json
import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch

from lcd_kb.cli import (
    DEFAULT_LATEST_SUCCESS_PATH,
    DEFAULT_RUN_ROOT,
    build_parser,
    cmd_build,
    cmd_inspect_run,
    cmd_latest,
    cmd_latest_artifacts,
    resolve_run_artifact_paths,
)


class CliTests(unittest.TestCase):
    def test_fetch_parser(self) -> None:
        parser = build_parser()
        args = parser.parse_args(["fetch", "--entity", "page"])
        self.assertEqual(args.command, "fetch")
        self.assertEqual(args.entity, "page")
        self.assertIsNone(args.summary_output)
        self.assertIsNone(args.errors_output)

    def test_check_parser_includes_report_and_raw_dirs(self) -> None:
        parser = build_parser()
        args = parser.parse_args(["check"])
        self.assertEqual(args.command, "check")
        self.assertEqual(args.raw_page_dir, "data/lcd/raw/pages")
        self.assertEqual(args.raw_post_dir, "data/lcd/raw/posts")
        self.assertIsNone(args.report_output)

    def test_build_parser_includes_run_state_defaults(self) -> None:
        parser = build_parser()
        args = parser.parse_args(["build"])
        self.assertEqual(args.command, "build")
        self.assertEqual(args.run_root, str(DEFAULT_RUN_ROOT))
        self.assertEqual(args.latest_success, str(DEFAULT_LATEST_SUCCESS_PATH))
        self.assertIsNone(args.validation_report)

    def test_latest_related_parsers(self) -> None:
        parser = build_parser()
        latest_args = parser.parse_args(["latest"])
        self.assertEqual(latest_args.command, "latest")
        artifacts_args = parser.parse_args(["latest-artifacts"])
        self.assertEqual(artifacts_args.command, "latest-artifacts")
        inspect_args = parser.parse_args(["inspect-run", "--run-id", "run-1"])
        self.assertEqual(inspect_args.command, "inspect-run")
        self.assertEqual(inspect_args.run_root, str(DEFAULT_RUN_ROOT))

    def test_resolve_run_artifact_paths(self) -> None:
        paths = resolve_run_artifact_paths(Path("/tmp/runs"), "run-1")
        self.assertEqual(paths["run_dir"], Path("/tmp/runs/run-1"))
        self.assertEqual(paths["manifest_output"], Path("/tmp/runs/run-1/manifests/run_manifest.json"))
        self.assertEqual(paths["validation_report"], Path("/tmp/runs/run-1/reports/validation_report.json"))
        self.assertEqual(paths["inventory_output"], Path("/tmp/runs/run-1/registry/artifact_inventory.json"))

    def test_cmd_build_writes_run_dir_outputs_and_latest_success(self) -> None:
        with tempfile.TemporaryDirectory() as tmpdir:
            base = Path(tmpdir)
            raw_pages = base / "raw-pages"
            raw_posts = base / "raw-posts"
            raw_pages.mkdir()
            raw_posts.mkdir()
            (raw_pages / "pages-page-0001.json").write_text(
                json.dumps({
                    "items": [{
                        "id": 1,
                        "type": "page",
                        "link": "https://lcd.exactas.uba.ar/plan/",
                        "slug": "plan",
                        "title": {"rendered": "Plan"},
                        "content": {"rendered": "<p>Plan</p>"},
                        "excerpt": {"rendered": ""},
                        "status": "publish",
                        "date_gmt": "2026-03-19T20:00:00",
                        "modified_gmt": "2026-03-19T20:00:00",
                        "author": 1,
                        "featured_media": 0,
                        "parent": 0,
                        "menu_order": 0,
                        "categories": [],
                        "tags": [],
                    }],
                    "headers": {"x-wp-total": "1"},
                }),
                encoding="utf-8",
            )
            (raw_posts / "posts-page-0001.json").write_text(
                json.dumps({
                    "items": [{
                        "id": 2,
                        "type": "post",
                        "link": "https://lcd.exactas.uba.ar/noticia/",
                        "slug": "noticia",
                        "title": {"rendered": "Noticia"},
                        "content": {"rendered": "<p>Noticia</p>"},
                        "excerpt": {"rendered": ""},
                        "status": "publish",
                        "date_gmt": "2026-03-19T20:00:00",
                        "modified_gmt": "2026-03-19T20:00:00",
                        "author": 1,
                        "featured_media": 0,
                        "parent": 0,
                        "menu_order": 0,
                        "categories": [],
                        "tags": [],
                    }],
                    "headers": {"x-wp-total": "1"},
                }),
                encoding="utf-8",
            )
            args = argparse.Namespace(
                run_id="run-1",
                observed_at="2026-03-19T20:00:00Z",
                started_at="2026-03-19T20:00:00Z",
                completed_at="2026-03-19T20:01:00Z",
                run_root=str(base / "runs"),
                latest_success=str(base / "state" / "latest_success.json"),
                page_raw=str(raw_pages),
                post_raw=str(raw_posts),
                page_output=None,
                post_output=None,
                page_chunks=None,
                post_chunks=None,
                index_output=None,
                manifest_output=None,
                validation_report=None,
                max_chars=400,
            )
            with patch("builtins.print"):
                result = cmd_build(args)
            self.assertEqual(result, 0)
            run_dir = base / "runs" / "run-1"
            self.assertTrue((run_dir / "normalized" / "page_doc.v1.jsonl").exists())
            self.assertTrue((run_dir / "chunks" / "page_chunk_doc.v1.jsonl").exists())
            self.assertTrue((run_dir / "reports" / "validation_report.json").exists())
            self.assertTrue((run_dir / "manifests" / "run_manifest.json").exists())
            self.assertTrue((run_dir / "registry" / "artifact_inventory.json").exists())
            latest_success = json.loads((base / "state" / "latest_success.json").read_text(encoding="utf-8"))
            self.assertEqual(latest_success["run_id"], "run-1")
            self.assertEqual(latest_success["run_dir"], str(run_dir))
            self.assertEqual(latest_success["inventory_path"], str(run_dir / "registry" / "artifact_inventory.json"))

    def test_latest_commands_read_latest_success_and_inventory(self) -> None:
        with tempfile.TemporaryDirectory() as tmpdir:
            base = Path(tmpdir)
            latest_success = base / "state" / "latest_success.json"
            inventory_path = base / "runs" / "run-1" / "registry" / "artifact_inventory.json"
            inventory_path.parent.mkdir(parents=True)
            latest_success.parent.mkdir(parents=True)
            inventory_path.write_text(json.dumps({"artifacts": [{"kind": "normalized_page_jsonl"}]}), encoding="utf-8")
            latest_success.write_text(json.dumps({"run_id": "run-1", "inventory_path": str(inventory_path)}), encoding="utf-8")
            with patch("builtins.print") as mock_print:
                self.assertEqual(cmd_latest(argparse.Namespace(latest_success=str(latest_success))), 0)
            self.assertIn('"run_id": "run-1"', mock_print.call_args[0][0])
            with patch("builtins.print") as mock_print:
                self.assertEqual(cmd_latest_artifacts(argparse.Namespace(latest_success=str(latest_success))), 0)
            self.assertIn('normalized_page_jsonl', mock_print.call_args[0][0])

    def test_inspect_run_reports_summary(self) -> None:
        with tempfile.TemporaryDirectory() as tmpdir:
            base = Path(tmpdir)
            run_dir = base / "runs" / "run-1"
            (run_dir / "registry").mkdir(parents=True)
            (run_dir / "manifests").mkdir(parents=True)
            (run_dir / "reports").mkdir(parents=True)
            (run_dir / "registry" / "artifact_inventory.json").write_text(json.dumps({"artifacts": [{"kind": "a"}]}), encoding="utf-8")
            (run_dir / "manifests" / "run_manifest.json").write_text(json.dumps({"result": "success", "entity_counts": {"page": 1}}), encoding="utf-8")
            (run_dir / "reports" / "validation_report.json").write_text(json.dumps({"ok": True, "checks": {"empty_chunks": []}}), encoding="utf-8")
            with patch("builtins.print") as mock_print:
                self.assertEqual(cmd_inspect_run(argparse.Namespace(run_root=str(base / "runs"), run_id="run-1")), 0)
            output = mock_print.call_args[0][0]
            self.assertIn('"artifact_count": 1', output)
            self.assertIn('"validation_ok": true', output)


if __name__ == "__main__":
    unittest.main()
