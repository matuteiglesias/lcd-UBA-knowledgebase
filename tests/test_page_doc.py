import json
import tempfile
import unittest
from pathlib import Path

from lcd_kb.normalize.page_doc import clean_text, normalize_entity_dir, normalize_wordpress_item


class PageDocTests(unittest.TestCase):
    def test_clean_text_removes_html_noise(self) -> None:
        text = clean_text("<p>Hola <strong>mundo</strong></p>")
        self.assertEqual(text, "Hola mundo")

    def test_normalize_wordpress_item(self) -> None:
        item = {
            "id": 10,
            "type": "page",
            "slug": "plan",
            "status": "publish",
            "link": "https://lcd.exactas.uba.ar/plan/",
            "title": {"rendered": "Plan"},
            "content": {"rendered": "<p>Plan <a href='https://example.org/file.pdf'>PDF</a></p>"},
            "excerpt": {"rendered": "Resumen"},
            "author": 5,
            "featured_media": 0,
            "parent": 0,
            "menu_order": 0,
            "categories": [1],
            "tags": [2],
            "date_gmt": "2026-03-19T00:00:00",
            "modified_gmt": "2026-03-19T00:00:00",
        }
        normalized = normalize_wordpress_item(item, entity="page", run_id="run-1", observed_at="2026-03-19T00:00:00Z")
        self.assertEqual(normalized["contract"], "page_doc.v1")
        self.assertEqual(normalized["text"], "Plan PDF")
        self.assertEqual(normalized["attachments"][0]["url"], "https://example.org/file.pdf")

    def test_content_hash_is_stable_across_runs(self) -> None:
        item = {
            "id": 10,
            "type": "page",
            "slug": "plan",
            "status": "publish",
            "link": "https://lcd.exactas.uba.ar/plan/",
            "title": {"rendered": "Plan"},
            "content": {"rendered": "<p>Plan</p>"},
            "excerpt": {"rendered": "Resumen"},
            "author": 5,
            "featured_media": 0,
            "parent": 0,
            "menu_order": 0,
            "categories": [1],
            "tags": [2],
            "date_gmt": "2026-03-19T00:00:00",
            "modified_gmt": "2026-03-19T00:00:00",
        }
        first = normalize_wordpress_item(item, entity="page", run_id="run-1", observed_at="2026-03-19T00:00:00Z")
        second = normalize_wordpress_item(item, entity="page", run_id="run-2", observed_at="2026-03-20T00:00:00Z")
        self.assertEqual(first["content_hash"], second["content_hash"])

    def test_normalize_entity_dir_writes_jsonl(self) -> None:
        raw_payload = {
            "entity": "page",
            "items": [
                {
                    "id": 1,
                    "type": "page",
                    "slug": "uno",
                    "status": "publish",
                    "link": "https://lcd.exactas.uba.ar/uno/",
                    "title": {"rendered": "Uno"},
                    "content": {"rendered": "<p>Uno</p>"},
                    "excerpt": {"rendered": ""},
                    "author": 1,
                    "featured_media": 0,
                    "parent": 0,
                    "menu_order": 0,
                    "categories": [],
                    "tags": [],
                    "date_gmt": "2026-03-19T00:00:00",
                    "modified_gmt": "2026-03-19T00:00:00"
                }
            ]
        }
        with tempfile.TemporaryDirectory() as tmpdir:
            raw_dir = Path(tmpdir) / "raw"
            raw_dir.mkdir()
            (raw_dir / "pages-page-0001.json").write_text(json.dumps(raw_payload), encoding="utf-8")
            output = Path(tmpdir) / "page_doc.v1.jsonl"
            count = normalize_entity_dir(raw_dir, output, entity="page", run_id="run-1", observed_at="2026-03-19T00:00:00Z")
            self.assertEqual(count, 1)
            lines = output.read_text(encoding="utf-8").strip().splitlines()
            self.assertEqual(len(lines), 1)
            record = json.loads(lines[0])
            self.assertEqual(record["slug"], "uno")


if __name__ == "__main__":
    unittest.main()
