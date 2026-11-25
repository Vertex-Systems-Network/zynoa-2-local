"""P02-T02.11: truthful, source-linked Help/Wiki documentation contracts.

These contracts do not mark unreleased option or screenshot gates complete.
"""
import json
import hashlib
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
        start = self.help.index("### M02-OPT-03")
        end = self.help.index("### M02-OPT-04", start)
        properties = self.help[start:end]
        self.assertIn("Implemented as a session-only foundation preview", properties)
        self.assertIn("Compact on", properties)
        self.assertIn("A real project editor is unavailable", properties)
        start = self.help.index("### M02-OPT-04")
        end = self.help.index("### M02-OPT-05", start)
        shortcuts = self.help[start:end]
        self.assertIn("Implemented for session-only navigation controls", shortcuts)
        self.assertIn("swaps both destinations", shortcuts)
        self.assertIn("Restore default shortcuts", shortcuts)
        self.assertIn("reserved", shortcuts)
        self.assertIn("no independent Reduce motion switch", self.help)
        self.assertIn("not persisted", self.wiki)
        self.assertIn("This source file is newer than that snapshot", self.wiki)
        proof = json.loads((ROOT / "docs/evidence/P02_T10_WIKI_PREVIEW_PUBLISHED_20261124.json").read_text(encoding="utf-8"))
        self.assertTrue(proof["published_preview_not_final_release"])
        self.assertTrue(proof["fresh_unauthenticated_git_clone_readback"])
        self.assertFalse(proof["protected_pr_merged"])
        self.assertIn("**not** a published/released product manual", self.wiki)

    def test_quick_start_does_not_require_nonexistent_workspace(self):
        self.assertIn("## Quick start", self.help)
        for snippet in ("Ctrl+5", "Ctrl+6", "Ctrl+2", "Ctrl+Shift+P", "F1"):
            self.assertIn(snippet, self.help)
        self.assertNotIn("Select the project/workspace/context", self.help)
        self.assertNotIn("Execute a small real task and review the actual artifact", self.help)
        self.assertNotIn("Report reproducible development errors automatically", self.help)

    def test_m02_final_native_png_visuals_verified_m19_and_release_pending(self):
        m02 = [x for x in self.manifest["required"] if x["module"] == "M02"]
        m19 = [x for x in self.manifest["required"] if x["module"] == "M19"]
        self.assertEqual(15, len(m02))
        self.assertEqual(14, len(m19))
        self.assertTrue(all(x["status"] == "VERIFIED" for x in m02))
        self.assertEqual([], sorted(x["asset_id"] for x in m19 if x["status"] == "PENDING"))
        self.assertEqual(14, sum(x["status"] == "VERIFIED" for x in m19))
        m19_review = json.loads((ROOT / "docs/screenshots/M19/T10-final-14-native-visual.review.json").read_text(encoding="utf-8"))
        self.assertEqual("ACCEPTED_M19_14_OF_14_NATIVE_VISUAL_ONLY", m19_review["review_status"])
        self.assertEqual(14, len(m19_review["images"]))
        corrected = next(x for x in m19 if x["asset_id"] == "M19-OPT-01")
        self.assertEqual("e4b8b013ab2d0d10a6ff4d44717fb153e2f99f07f2d5390bb517c252a9a20bcb", corrected["source_capture_sha256"])
        self.assertEqual("8cda88f7d67f4c3d90d301dd80dcca51f78651fa", corrected["source_git_blob_sha"])
        self.assertFalse(m19_review["full_nvda_narrator_approved"])
        self.assertFalse(m19_review["full_module_release_approved"])
        m19_by_id = {entry["asset_id"]: entry for entry in m19_review["images"]}
        self.assertEqual({row["asset_id"] for row in m19 if row["status"] == "VERIFIED"}, set(m19_by_id))
        for entry in m19:
            if entry["status"] != "VERIFIED":
                continue
            original = (ROOT / entry["path"]).read_bytes()
            self.assertEqual(entry["source_capture_sha256"], hashlib.sha256(original).hexdigest())
            self.assertEqual(entry["source_capture_sha256"], m19_by_id[entry["asset_id"]]["sha256"])
            self.assertEqual("PASS_FOR_M19_SCREEN_OPTION_FRAME_ONLY", m19_by_id[entry["asset_id"]]["visual_result"])
        report = json.loads((ROOT / "docs/screenshots/M02/T02-final-15-native-visual.review.json").read_text(encoding="utf-8"))
        self.assertEqual("ACCEPTED_M02_15_NATIVE_VISUAL_ONLY", report["review_status"])
        self.assertEqual(15, len(report["images"]))
        self.assertFalse(report["full_nvda_narrator_approved"])
        self.assertFalse(report["full_m02_module_release_approved"])
        reviewed = {row["asset_id"]: row for row in report["images"]}
        self.assertEqual({row["asset_id"] for row in m02}, set(reviewed))
        for row in m02:
            file = ROOT / row["path"]
            self.assertTrue(file.is_file(), row["asset_id"])
            data = file.read_bytes()
            self.assertEqual(row["source_capture_sha256"], hashlib.sha256(data).hexdigest())
            self.assertEqual(row["source_capture_sha256"], reviewed[row["asset_id"]]["sha256"])
            self.assertEqual("PASS_FOR_M02_SCREEN_OPTION_FRAME_ONLY", reviewed[row["asset_id"]]["visual_result"])
        self.assertIn("15/15", self.help)
        self.assertIn("14/14", (ROOT / "docs/help/articles/M19.md").read_text(encoding="utf-8"))
        self.assertIn("All eight M02 final option PNGs are VERIFIED", self.wiki)
        self.assertIn("full NVDA/Narrator", self.wiki)
        self.assertNotIn("15 M02 and 14 M19 final screen/option PNGs as PENDING", self.wiki)
        self.assertIn("unshipped P02 preview", self.help)

    def test_final_option_screenshot_docs_match_29_verified_native_pngs(self):
        help_m19 = (ROOT / "docs/help/articles/M19.md").read_text(encoding="utf-8")
        for module, article in (("M02", self.help), ("M19", help_m19)):
            for i in range(1, 9):
                code = f"{module}-OPT-{i:02d}"
                start = article.index("### " + code + " ")
                after = article.find("\n### ", start + 6)
                section = article[start:after if after >= 0 else None]
                self.assertIn(f"../../screenshots/{module}/{code}.png", section)
                self.assertIn("VERIFIED", section)
                self.assertNotIn("— **PENDING", section)
        assert (ROOT / "docs/evidence/P02_T10_FINAL_29_NATIVE_SCREENSHOTS_20261124.json").is_file()
        proof = json.loads((ROOT / "docs/evidence/P02_T10_FINAL_29_NATIVE_SCREENSHOTS_20261124.json").read_text(encoding="utf-8"))
        self.assertEqual(29, proof["total"])
        self.assertTrue(proof["image_caption_alt_metadata_complete"])
        reviewed = {x["asset_id"]: x for x in proof["assets"]}
        self.assertEqual(29, len(reviewed))
        for row in self.manifest["required"]:
            if row["module"] not in ("M02", "M19"):
                continue
            self.assertGreater(len(row["alt_text"]), 38, row["asset_id"])
            self.assertTrue(row["caption"].startswith(row["asset_id"] + " — "))
            self.assertEqual(row["native_capture_id"], reviewed[row["asset_id"]]["native_capture_id"])
            self.assertEqual(row["capture_window_width"], reviewed[row["asset_id"]]["window_width"])
            self.assertEqual(row["capture_window_height"], reviewed[row["asset_id"]]["window_height"])
            self.assertEqual("NOT_RECORDED", row["device_pixel_ratio"])
            self.assertEqual("VERIFIED_NATIVE_PNG_IMAGE_ONLY_NOT_MODULE_RELEASE", row["review_scope"])
            self.assertIn("no user content or secrets", row["sensitive_data_check"])
        self.assertFalse(proof["full_screen_reader_nvda_narrator_approved"])
        self.assertFalse(proof["protected_main_merged"])

    def test_f1_catalog_is_distinct_from_hosted_preview_snapshot(self):
        self.assertIn('setView("help")', self.app) if 'setView("help")' in self.app else self.assertIn('return "help"', self.app)
        self.assertIn("bundled offline Help Center", self.help)
        self.assertIn("https://github.com/Vertex-Systems-Network/zynoa-2-local/wiki/M02", self.wiki)
        self.assertIn("source-pinned", self.wiki)
        self.assertIn("not yet wired", self.help)
        self.assertIn("not** a live incident reader", self.help)

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
