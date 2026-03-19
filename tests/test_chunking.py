import json
import tempfile
import unittest
from pathlib import Path

from lcd_kb.normalize.chunking import chunk_jsonl, chunk_page_record, split_text_into_chunks


class ChunkingTests(unittest.TestCase):
    def test_split_text_into_chunks(self) -> None:
        chunks = split_text_into_chunks("Uno. Dos. Tres.", max_chars=8)
        self.assertGreaterEqual(len(chunks), 2)

    def test_chunk_page_record(self) -> None:
        record = {
            "contract": "page_doc.v1",
            "site_id": "lcd.exactas.uba.ar",
            "source_url": "https://lcd.exactas.uba.ar/plan/",
            "entity_type": "page",
            "source_id": 10,
            "title": "Plan",
            "slug": "plan",
            "text": "Uno. Dos. Tres.",
            "content_hash": "sha256:page",
            "observed_at": "2026-03-19T00:00:00Z",
        }
        chunks = chunk_page_record(record, max_chars=8)
        self.assertEqual(chunks[0]["contract"], "chunk_doc.v1")
        self.assertTrue(chunks[0]["chunk_id"].startswith("page:10#chunk:"))

    def test_chunk_jsonl(self) -> None:
        with tempfile.TemporaryDirectory() as tmpdir:
            input_path = Path(tmpdir) / "page_doc.v1.jsonl"
            output_path = Path(tmpdir) / "page_chunk_doc.v1.jsonl"
            input_path.write_text(json.dumps({
                "contract": "page_doc.v1",
                "site_id": "lcd.exactas.uba.ar",
                "source_url": "https://lcd.exactas.uba.ar/plan/",
                "entity_type": "page",
                "source_id": 10,
                "title": "Plan",
                "slug": "plan",
                "text": "Uno. Dos. Tres.",
                "content_hash": "sha256:page",
                "observed_at": "2026-03-19T00:00:00Z",
            }) + "\n", encoding="utf-8")
            count = chunk_jsonl(input_path, output_path, max_chars=8)
            self.assertGreaterEqual(count, 2)
            self.assertTrue(output_path.exists())


if __name__ == "__main__":
    unittest.main()
