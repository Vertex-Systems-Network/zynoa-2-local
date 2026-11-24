"""The public Wiki browser verifier must fail closed on false rendered pages."""
import unittest
from tools.verify_p02_t11_wiki_render import audit_dom, WikiProofError, REPO
SHA="a"*40
def fixture():
    ids=" ".join(f"M02-OPT-{i:02d}" for i in range(1,9))
    return f'<html><body><div id="wiki-body"><div><h1>Preview</h1><p>{ids}</p><a href="/{REPO}/blob/{SHA}/docs/help/articles/M02.md">Source</a><img src="fake"><br></div></div></body></html>'
class WikiBrowserProofTests(unittest.TestCase):
    def test_real_wiki_container_and_pinned_link_contract(self):
        result=audit_dom("M02",fixture(),SHA)
        self.assertEqual(result["rendered_option_ids"],8)
        self.assertEqual(result["pinned_source_paths"],["docs/help/articles/M02.md"])
    def test_404_or_fake_page_rejected(self):
        for html in ("<html><title>Not found</title></html>",fixture().replace('id="wiki-body"','id="fake"'),fixture().replace("M02-OPT-08","M02-MISSING")):
            with self.subTest(html=html[:60]),self.assertRaises(WikiProofError):
                audit_dom("M02",html,SHA)
    def test_stale_source_or_unsafe_relative_link_rejected(self):
        for html in (fixture().replace(SHA,"main"),fixture().replace("docs/help/articles/M02.md","docs/../secret"),fixture().replace("</p>",'</p><a href="../../help.md">broken</a>')):
            with self.subTest(html=html[:60]),self.assertRaises(WikiProofError):
                audit_dom("M02",html,SHA)
    def test_released_claim_without_preview_rejected(self):
        with self.assertRaises(WikiProofError):
            audit_dom("M02",fixture().replace("Preview","Released"),SHA)
if __name__=="__main__":
    unittest.main()
