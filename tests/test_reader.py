import json
import tempfile
import unittest
from pathlib import Path

from lcd_kb.consumers.reader import get_record_by_slug, search_records, stats


class ReaderTests(unittest.TestCase):
    def test_search_and_open(self) -> None:
        with tempfile.TemporaryDirectory() as tmpdir:
            path = Path(tmpdir) / "records.jsonl"
            path.write_text(
                json.dumps({"slug": "plan", "title": "Plan", "text": "Plan de estudios"}) + "\n"
                + json.dumps({"slug": "becas", "title": "Becas", "text": "Ayuda económica"}) + "\n",
                encoding="utf-8",
            )
            matches = search_records(path, "plan")
            self.assertEqual(len(matches), 1)
            record = get_record_by_slug(path, "becas")
            self.assertEqual(record["title"], "Becas")

    def test_stats(self) -> None:
        with tempfile.TemporaryDirectory() as tmpdir:
            first = Path(tmpdir) / "one.jsonl"
            second = Path(tmpdir) / "two.jsonl"
            first.write_text(json.dumps({"slug": "uno"}) + "\n", encoding="utf-8")
            second.write_text("", encoding="utf-8")
            report = stats({"one": first, "two": second})
            self.assertEqual(report, {"one": 1, "two": 0})


if __name__ == "__main__":
    unittest.main()
