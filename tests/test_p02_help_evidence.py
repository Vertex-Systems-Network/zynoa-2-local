"""P02-T02.11: truthful, source-linked Help/Wiki documentation contracts.

These contracts do not mark unreleased option or screenshot gates complete.
"""
import json
from pathlib import Path
import re
import unittest

ROOT = Path(__file__).resolve().parents[1]
HELP = ROOT / "docs/help/articles/M02.md"
WIKI = ROOT / "docs/wiki/pages/M02.md"
MANIFEST = ROOT / "docs/screenshots/MANIFEST.json"


class M02HelpEvidenceTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.help = HELP.read_text(encoding="utf-8")
        cls.wiki = WIKI.read_text(encoding="utf-8")
        cls.manifest = json.loads(MANIFEST.read_text(encoding="utf-8"))
        cls.app = (ROOT / "apps/desktop/src/App.tsx").read_text(encoding="utf-8")
        cls.theme = (ROOT / "apps/desktop/src/ui/theme.ts").read_text(encoding="utf-8")
        cls.wb = (ROOT / "apps/desktop/src/ui/Workbench.tsx").read_text(encoding="utf-8")

    def test_eight_option_sections_exist_and_match_stable_ids(self):
        ids = [f"M02-OPT-{i:02}" for i in range(1, 9)]
        for option_id in ids:
            self.assertEqual(1, len(re.findall(r"^### " + option_id + r" \u2014", self.help, re.M)))
            self.assertIn(option_id, self.wiki)
            self.assertIn(option_id, self.theme)
            self.assertIn(f"../../screenshots/M02/{option_id}.png", self.help)

    def test_options_preserve_session_only_true_defaults(self):
        self.assertIn('useState<ThemePreference>("system")', self.app)
        self.assertIn('useState<DensityPreference>("comfortable")', self.app)
        self.assertIn('useState(40)', self.wb)
        for snippet in ("Follow system (default)", "Comfortable (default)",
                        "25\u201365%", "40% default", "session-only"):
            self.assertIn(snippet, self.help)
        self.assertIn("No save, sync, or durable preference exists.", self.help)
        for unsafe in ("localStorage", "sessionStorage", "fetch("):
            self.assertNotIn(unsafe, self.wb)

    def test_unimplemented_options_not_advertised_as_working_controls(self):
        for option_id in ("M02-OPT-03", "M02-OPT-04"):
            head = self.help.index("### " + option_id)
            end = self.help.find("### M02-OPT-", head + 5)
            section = self.help[head:] if end == -1 else self.help[head:end]
            self.assertIn("Not implemented", section) if option_id == "M02-OPT-03" else self.assertIn("not implemented", section.lower())
        self.assertIn("No in-app reduce-motion switch", self.help)
        self.assertIn("not persisted", self.wiki)
        self.assertIn("not been synced", self.wiki)
        self.assertIn("not a published/released product manual", self.wiki)

    def test_quick_start_does_not_require_nonexistent_workspace(self):
        self.assertIn("## Quick start", self.help)
        for snippet in ("Ctrl+5", "Ctrl+6", "Ctrl+2", "Ctrl+Shift+P", "F1"):
            self.assertIn(snippet, self.help)
        self.assertNotIn("Select the project/workspace/context", self.help)
        self.assertNotIn("Execute a small real task and review the actual artifact", self.help)
        self.assertNotIn("Report reproducible development errors automatically", self.help)

    def test_screenshot_manifest_remains_explicitly_pending(self):
        m02 = [x for x in self.manifest["required"] if x["module"] == "M02"]
        m19 = [x for x in self.manifest["required"] if x["module"] == "M19"]
        self.assertEqual(15, len(m02))
        self.assertEqual(14, len(m19))
        self.assertTrue(all(x["status"] == "PENDING" for x in m02 + m19))
        self.assertIn("PENDING", self.help)
        self.assertIn("PENDING", self.wiki)
        self.assertIn("CI candidates", self.help)
        self.assertIn("not completed screen/option PNGs", self.help)

    def test_f1_catalog_is_distinct_from_unpublished_wiki_source(self):
        self.assertIn('setView("help")', self.app) if 'setView("help")' in self.app else self.assertIn('return "help"', self.app)
        self.assertIn("bundled offline Help Center", self.help)
        self.assertIn("remote GitHub Wiki repository", self.wiki)
        self.assertIn("not wired", self.help)
        self.assertIn("not a live incident reader", self.help)

    def test_previously_inspected_focus_slice_review_is_not_a_final_manifest_entry(self):
        f = ROOT / "docs/screenshots/M02/M02-OPT-07.review.json"
        self.assertTrue(f.is_file())
        review = json.loads(f.read_text(encoding="utf-8"))
        self.assertEqual("ACCEPTED_NATIVE_FOCUS_SLICE_ONLY", review["review_status"])
        self.assertFalse(review["screenshot_committed_to_manifest_path"])
        self.assertRegex(review["png_sha256"], r"^[0-9a-f]{64}$")

    def test_ci_includes_fail_closed_native_integrity_and_docs_tests(self):
        wf = (ROOT / ".github/workflows/p01-desktop.yml").read_text(encoding="utf-8")
        self.assertIn("python -m unittest tests.test_p02_native_evidence -v", wf)
        self.assertIn("python -m unittest tests.test_p02_help_evidence -v", wf)
        self.assertIn("tools.verify_p02_native_evidence --root docs/screenshots/_ci", wf)
        self.assertIn("docs/screenshots/_ci/M02/P02-native-machine-review.json", wf)
        self.assertIn("tests/test_p02_help_evidence.py", wf)


if __name__ == "__main__":
    unittest.main()
