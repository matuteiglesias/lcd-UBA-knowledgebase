import json
import tempfile
import unittest
from pathlib import Path

from lcd_kb.sources.wordpress_rest import build_entity_url, fetch_entity_batches


class WordpressRestTests(unittest.TestCase):
    def test_build_entity_url(self) -> None:
        url = build_entity_url("https://lcd.exactas.uba.ar", "page", 2, 10, ["id", "slug"])
        self.assertIn("/wp-json/wp/v2/pages", url)
        self.assertIn("page=2", url)
        self.assertIn("per_page=10", url)
        self.assertIn("_fields=id%2Cslug", url)

    def test_fetch_entity_batches_writes_raw_pages(self) -> None:
        responses = {
            "https://lcd.exactas.uba.ar/wp-json/wp/v2/pages?page=1&per_page=2&_fields=id%2Cdate_gmt%2Cmodified_gmt%2Cslug%2Cstatus%2Ctype%2Clink%2Ctitle%2Ccontent%2Cexcerpt%2Cauthor%2Cfeatured_media%2Cparent%2Cmenu_order%2Ccategories%2Ctags": (
                [{"id": 1, "slug": "uno"}, {"id": 2, "slug": "dos"}],
                {"x-wp-totalpages": "2", "x-wp-total": "3"},
            ),
            "https://lcd.exactas.uba.ar/wp-json/wp/v2/pages?page=2&per_page=2&_fields=id%2Cdate_gmt%2Cmodified_gmt%2Cslug%2Cstatus%2Ctype%2Clink%2Ctitle%2Ccontent%2Cexcerpt%2Cauthor%2Cfeatured_media%2Cparent%2Cmenu_order%2Ccategories%2Ctags": (
                [{"id": 3, "slug": "tres"}],
                {"x-wp-totalpages": "2", "x-wp-total": "3"},
            ),
        }

        def fake_request(url: str):
            return responses[url]

        with tempfile.TemporaryDirectory() as tmpdir:
            result = fetch_entity_batches(
                base_url="https://lcd.exactas.uba.ar",
                entity="page",
                output_dir=Path(tmpdir),
                per_page=2,
                request_json=fake_request,
            )
            self.assertEqual(result.pages_fetched, 2)
            self.assertEqual(result.records_fetched, 3)
            raw_files = sorted(Path(tmpdir).glob("*.json"))
            self.assertEqual(len(raw_files), 2)
            payload = json.loads(raw_files[0].read_text(encoding="utf-8"))
            self.assertEqual(payload["entity"], "page")
            self.assertEqual(len(payload["items"]), 2)


if __name__ == "__main__":
    unittest.main()
