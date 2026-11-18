import json, tempfile, unittest
from pathlib import Path
from tools.incident_router import sanitize,upsert,scrub

class IncidentRouterTests(unittest.TestCase):
    def setUp(self):
        self.event=dict(module='M03',error_code='MODEL_RUNTIME_CRASH',severity='P1',source_type='developer-ci',app_version='1.2.3',platform='Windows',message_class='RuntimeError',token='private-token',prompt='secret prompt',stack='C:/Users/Alice/file.txt')
    def test_redacts_disallowed_fields(self):
        rec=sanitize(self.event)
        self.assertNotIn('token',rec)
        self.assertNotIn('prompt',rec)
        self.assertNotIn('stack',rec)
        self.assertNotIn('private',json.dumps(rec))
    def test_fingerprint_stable_and_version_banded(self):
        a=sanitize(self.event)
        self.event['app_version']='1.2.9'
        self.assertEqual(a['fingerprint'],sanitize(self.event)['fingerprint'])
    def test_dedup_local(self):
        with tempfile.TemporaryDirectory() as d:
            p=Path(d)/'events.db'
            x=sanitize(self.event)
            self.assertEqual(upsert(p,x)['occurrence_count'],1)
            self.assertEqual(upsert(p,x)['occurrence_count'],2)
    def test_rejects_unknown_severity(self):
        self.event['severity']='PERMIT_ALL'
        with self.assertRaises(ValueError): sanitize(self.event)
    def test_redact_sensitive_strings(self):
        self.assertNotIn('foo@example.org',scrub('email foo@example.org'))
        self.assertNotIn('192.168.1.20',scrub('192.168.1.20'))
        self.assertNotIn('ABCD1234',scrub('token=ABCD1234'))

if __name__=='__main__': unittest.main()
