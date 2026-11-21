import json
from pathlib import Path
import tempfile
import unittest

from scholarship_intelligence import crawl_views
from scholarship_intelligence.workflow_service import classify_failure


class CrawlViewTests(unittest.TestCase):
    def test_original_saved_values_are_not_redated(self):
        records = crawl_views.load()
        self.assertEqual(len(records), 296)
        self.assertTrue(any(row.get('confidence_score') is not None for row in records))
        self.assertEqual(sum(row['verification_status'] == 'VERIFIED' for row in records), 4)

    def test_saved_crawl_is_selectable_and_preserves_baseline(self):
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            name = crawl_views.save([{'name': 'New record'}], project_root=root)
            self.assertIn(name, dict(crawl_views.available(root)))
            self.assertEqual(crawl_views.load(name, project_root=root), [{'name': 'New record'}])
            with self.assertRaises(ValueError):
                crawl_views.load('../secret.json.gz', project_root=root)

    def test_error_categories(self):
        self.assertEqual(classify_failure(RuntimeError('HTTP 503'))[0], 'SOURCE_UNAVAILABLE')
        self.assertEqual(classify_failure(RuntimeError('HTTP 429'))[0], 'RATE_LIMIT')
        self.assertEqual(classify_failure(RuntimeError('database disk full'))[0], 'STORAGE')


if __name__ == '__main__':
    unittest.main()
