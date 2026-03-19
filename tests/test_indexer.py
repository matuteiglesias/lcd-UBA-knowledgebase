import json
import tempfile
import unittest
from pathlib import Path

from lcd_kb.consumers.indexer import build_title_slug_index


class IndexerTests(unittest.TestCase):
    def test_build_title_slug_index(self) -> None:
        with tempfile.TemporaryDirectory() as tmpdir:
            base = Path(tmpdir)
            page = base / 'page.jsonl'
            post = base / 'post.jsonl'
            page.write_text(json.dumps({
                'slug': 'plan-de-estudios',
                'title': 'Plan de estudios',
                'source_url': 'https://lcd.exactas.uba.ar/plan-de-estudios/',
                'entity_type': 'page',
                'source_id': 395,
                'content_hash': 'sha256:page',
            }) + '\n', encoding='utf-8')
            post.write_text(json.dumps({
                'slug': 'inscripciones-2026',
                'title': 'Inscripciones 2026',
                'source_url': 'https://lcd.exactas.uba.ar/inscripciones-2026/',
                'entity_type': 'post',
                'source_id': 901,
                'content_hash': 'sha256:post',
            }) + '\n', encoding='utf-8')
            index = build_title_slug_index(page_path=page, post_path=post)
            self.assertEqual(len(index), 2)
            self.assertEqual(index[0]['title'], 'Inscripciones 2026')
            self.assertEqual(index[1]['slug'], 'plan-de-estudios')


if __name__ == '__main__':
    unittest.main()
