import copy
import json
from pathlib import Path
import unittest
from tools.changelog import validate_records, render_preview

ROOT=Path(__file__).resolve().parents[1]
FIXTURES=json.loads((ROOT/'tests/fixtures/change_records.json').read_text(encoding='utf-8'))

class ChangelogTests(unittest.TestCase):
    def test_fixture_valid_and_docs_exist(self):
        self.assertEqual([],validate_records(FIXTURES,ROOT,check_docs=True))
    def test_release_includes_only_published_public_entry(self):
        output=render_preview(FIXTURES,'0.1.0','2026-11-18','stable')
        self.assertIn('CHG-EXAMPLE-0001',output)
        for bad in ['CHG-EXAMPLE-0002','CHG-EXAMPLE-0003','CHG-EXAMPLE-0004','vulnerability description']:
            self.assertNotIn(bad,output)
    def test_released_requires_test_and_merge_proof(self):
        altered=copy.deepcopy(FIXTURES);altered[0]['verification']['merge_verified']=False
        self.assertTrue(any('verification' in e for e in validate_records(altered)))
    def test_issues_cannot_claim_release(self):
        altered=copy.deepcopy(FIXTURES);altered[2]['release']={'version':'0.1.0','channel':'stable','date':'2026-11-18'}
        self.assertTrue(any('non-released' in e for e in validate_records(altered)))
    def test_duplicate_record_rejected(self):
        self.assertTrue(any('duplicate' in e for e in validate_records(FIXTURES+[copy.deepcopy(FIXTURES[0])])) )
    def test_missing_docs_rejected(self):
        altered=copy.deepcopy(FIXTURES);altered[0]['docs_paths']=['docs/missing_file.md']
        self.assertTrue(any('missing linked documentation' in e for e in validate_records(altered,ROOT,check_docs=True)))
    def test_wrong_release_not_rendered(self):
        with self.assertRaises(ValueError):render_preview(FIXTURES,'0.2.0','2026-11-18','stable')
    def test_wrong_channel_not_rendered(self):
        with self.assertRaises(ValueError):render_preview(FIXTURES,'0.1.0','2026-11-18','beta')
    def test_breaking_requires_migration_guide(self):
        altered=copy.deepcopy(FIXTURES);altered[0]['breaking_change']=True
        self.assertTrue(any('migration' in e for e in validate_records(altered)))
    def test_no_path_escape(self):
        altered=copy.deepcopy(FIXTURES);altered[0]['docs_paths']=['docs/../../user-home/private.txt']
        self.assertTrue(any('unsafe' in e for e in validate_records(altered)))
    def test_deterministic_preview(self):
        a=render_preview(FIXTURES,'0.1.0','2026-11-18');b=render_preview(FIXTURES,'0.1.0','2026-11-18')
        self.assertEqual(a,b)

if __name__=='__main__': unittest.main()
