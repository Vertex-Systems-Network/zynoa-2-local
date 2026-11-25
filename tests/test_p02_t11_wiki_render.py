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
    def test_m26_requires_all_twenty_rendered_options_and_exact_documentation_links(self):
        ids=" ".join(f"M26-OPT-{i:02d}" for i in range(1,21))
        links="".join(f'<a href="/{REPO}/blob/{SHA}/{path}">Source</a>' for path in
                      ("docs/help/articles/M26.md","docs/wiki/pages/M26.md","docs/modules/M26.md"))
        html=f'<div id="wiki-body"><h1>Unshipped preview</h1><p>{ids}</p>{links}</div>'
        self.assertEqual(audit_dom("M26",html,SHA)["rendered_option_ids"],20)
        for bad in (html.replace("M26-OPT-20","missing"),html.replace("docs/help/articles/M26.md","docs/help/articles/M19.md"),
                    html.replace(SHA,"main"),html.replace("Unshipped preview","Released")):
            with self.assertRaises(WikiProofError):audit_dom("M26",bad,SHA)

if __name__=="__main__":
    unittest.main()
