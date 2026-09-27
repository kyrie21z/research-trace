"""Regression tests for event attribution, classification and correction context."""
import importlib.util
import json
from datetime import date
from pathlib import Path
import subprocess
import sys
import tempfile
import unittest

SCRIPT = Path(__file__).resolve().parents[1] / 'scripts/extract_weekly_facts.py'
spec = importlib.util.spec_from_file_location('weekly_extract', SCRIPT)
module = importlib.util.module_from_spec(spec)
spec.loader.exec_module(module)


class ExtractionTests(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory()
        self.addCleanup(self.temp.cleanup)
        self.root = Path(self.temp.name)

    def record(self, ident, occurred=None, **extra):
        data = dict(id=ident, title=ident, summary='summary', scope='scope', topics=[],
                    occurred_at=occurred, recorded_at='2026-09-20T00:00:00Z')
        data.update(extra)
        (self.root / f'{ident}.md').write_text('<!-- research-record\n' + json.dumps(data) + '\n-->\n')

    def extract(self):
        return module.extract(self.root, date(2026, 9, 19), date(2026, 9, 25))

    def test_unknown_is_not_migration_week(self):
        self.record('R-OLD')
        result = self.extract()
        self.assertEqual(result['records'], [])
        self.assertEqual(result['unknown_dates'][0]['id'], 'R-OLD')

    def test_intervals_overlap_and_legacy_prefix_is_not_excluded(self):
        self.record('R-HISTORY-X', '2026-09-18 / 2026-09-20')
        self.record('R-END', '2026-09-25T23:59:00-03:00')
        self.record('R-OUT', '2026-09-26')
        self.assertEqual({r['id'] for r in self.extract()['records']}, {'R-HISTORY-X', 'R-END'})

    def test_invalid_dates_and_reverse_windows_are_visible(self):
        self.record('R-BAD', '2026-02-30')
        result = self.extract()
        self.assertTrue(result['issues'])
        self.assertEqual(result['records'], [])
        with self.assertRaises(ValueError):
            module.extract(self.root, date(2026, 9, 25), date(2026, 9, 19))
        with self.assertRaises(ValueError):
            module.event_interval('2026-09-25/2026-09-19')

    def test_character_is_not_ar_and_conflicts_need_review(self):
        self.record('R-SLPID-CHARACTER-CODEBOOK', '2026-09-20')
        self.record('R-CANDIDATE-AR-SEMOFF', '2026-09-20')
        patterns = module.load_routes(SCRIPT.parents[1] / 'references/routes.example.json')
        result = module.extract(self.root, date(2026, 9, 19), date(2026, 9, 25), patterns)
        rows = {r['id']: r for r in result['records']}
        self.assertEqual(rows['R-SLPID-CHARACTER-CODEBOOK']['_route'], 'str')
        self.assertEqual(rows['R-CANDIDATE-AR-SEMOFF']['_route'], 'review')

    def test_default_has_no_domain_assumptions(self):
        self.record('R-CHARACTER-CODEBOOK', '2026-09-20', topics=['materials'])
        row = self.extract()['records'][0]
        self.assertEqual(row['_route'], 'unclassified')
        self.assertEqual(row['topics'], ['materials'])

    def test_custom_domain_routes_and_invalid_config(self):
        self.record('R-LAB', '2026-09-20', topics=['materials'])
        config = self.root / 'routes.json'
        config.write_text(json.dumps({'materials': r'\bMATERIALS\b'}))
        result = module.extract(self.root, date(2026, 9, 19), date(2026, 9, 25), module.load_routes(config))
        self.assertEqual(result['records'][0]['_route'], 'materials')
        for invalid in [{'bad': '['}, {'review': 'X'}, ['X']]:
            config.write_text(json.dumps(invalid))
            with self.assertRaises(ValueError):
                module.load_routes(config)

    def test_bidirectional_transitive_correction_context(self):
        self.record('R-OLD', '2026-09-01')
        self.record('R-WEEK', '2026-09-20', corrects=['R-OLD'], related=['R-BACKGROUND'])
        self.record('R-LATER', '2026-10-01', corrects=['R-WEEK'])
        self.record('R-LATEST', '2026-10-02', supersedes=['R-LATER'])
        self.record('R-BACKGROUND', '2026-01-01')
        result = self.extract()
        self.assertEqual([r['id'] for r in result['records']], ['R-WEEK'])
        self.assertEqual({r['id'] for r in result['correction_context']}, {'R-OLD', 'R-LATER', 'R-LATEST'})
        self.assertEqual(result['issues'], [])

    def test_cycles_terminate_without_discarding_records(self):
        self.record('R-A', '2026-09-20', corrects=['R-B'])
        self.record('R-B', None, corrects=['R-A'])
        self.assertEqual(len(self.extract()['correction_context']), 1)

    def test_malformed_and_dangling_references_fail_cli(self):
        self.record('R-X', '2026-09-20', corrects=['R-MISSING'])
        (self.root / 'malformed.md').write_text('not a record')
        run = subprocess.run([sys.executable, str(SCRIPT), '--since', '2026-09-19', '--until',
                              '2026-09-25', '--records-dir', str(self.root), '--json'], capture_output=True, text=True)
        self.assertEqual(run.returncode, 2)
        result = json.loads(run.stdout)
        self.assertEqual(len(result['issues']), 2)
        self.assertIn('not verified', result['verification'])

    def test_json_and_markdown_expose_same_context(self):
        self.record('R-WEEK', '2026-09-20', corrects=['R-OLD'])
        self.record('R-OLD')
        result = self.extract()
        rendered = module.markdown(result)
        self.assertIn('R-OLD', rendered)
        self.assertIn('corrects: R-OLD', rendered)
        self.assertIn('未核验', rendered)


if __name__ == '__main__':
    unittest.main()
