"""Final T02 sign-off must be evidence-gated; partial green checks are not release."""
from __future__ import annotations

import json
from pathlib import Path
import tempfile
import unittest

from tools.verify_p02_t02_acceptance import (
    PrematureT02Closure, SCREEN_IDS, OPTION_IDS, REQUIRED_IDS, audit,
)

ROOT = Path(__file__).resolve().parents[1]


class T02FinalAcceptanceGateTests(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory()
        self.addCleanup(self.temp.cleanup)
        self.root = Path(self.temp.name)
        self.paths = (
            "docs/state/pr-tasks/P02.json",
            "docs/screenshots/MANIFEST.json",
            "docs/help/articles/M02.md",
            "docs/wiki/pages/M02.md",
            "docs/modules/M02.md",
            "docs/screenshots/M02/T02-visual-foundation.review.json",
            "docs/screenshots/M02/T02-final-15-native-visual.review.json",
            "apps/desktop/src/styles.css",
            "apps/desktop/src/ui/Workbench.tsx",
            "apps/desktop/src/App.tsx",
            "tests/test_p02_ui_contract.py",
            "tests/test_p02_m02_controls.py",
            "scripts/probe_p02_native_a11y.ps1",
        )
        for name in self.paths:
            dest = self.root / name
            dest.parent.mkdir(parents=True, exist_ok=True)
            dest.write_bytes((ROOT / name).read_bytes())
        for image_id in REQUIRED_IDS:
            name = f"docs/screenshots/M02/{image_id}.png"
            dest = self.root / name
            dest.parent.mkdir(parents=True, exist_ok=True)
            dest.write_bytes((ROOT / name).read_bytes())

    def _json(self, path):
        return json.loads((self.root / path).read_text(encoding="utf-8"))

    def _save(self, path, payload):
        (self.root / path).write_text(json.dumps(payload), encoding="utf-8")

    def test_done_parent_accepts_committed_scoped_evidence(self):
        result = audit(self.root)
        self.assertEqual("P02-T02", result["task_id"])
        self.assertEqual("DONE", result["official_task_status"])
        self.assertEqual("READY_FOR_T02_SCOPED_REMOTE_CI", result["acceptance"])
        self.assertEqual(15, result["expected_final_screenshot_count"])
        self.assertEqual(15, result["verified_manifest_screenshot_count"])
        self.assertEqual([], result["blockers"])
        self.assertNotIn("M02 independent 15-image final visual review absent", result["blockers"])
        self.assertNotIn("M02-OPT-03 functionality explicitly not implemented", result["blockers"])
        self.assertNotIn("M02-OPT-04 functionality explicitly not implemented", result["blockers"])
        self.assertFalse(result["remote_ci_and_merge_verified"])

    def test_premature_done_is_a_failing_gate(self):
        t = self._json("docs/state/pr-tasks/P02.json")
        next(row for row in t["tasks"] if row["id"] == "P02-T02")["status"] = "DONE"
        self._save("docs/state/pr-tasks/P02.json", t)
        (self.root / "docs/screenshots/M02/M02-S01.png").unlink()
        with self.assertRaisesRegex(PrematureT02Closure, "falsely marked DONE"):
            audit(self.root)

    def test_manifest_status_without_real_pngs_is_insufficient(self):
        m = self._json("docs/screenshots/MANIFEST.json")
        for row in m["required"]:
            if row["module"] == "M02":
                row["status"] = "VERIFIED"
        self._save("docs/screenshots/MANIFEST.json", m)
        for image_id in REQUIRED_IDS:
            (self.root / f"docs/screenshots/M02/{image_id}.png").unlink()
        with self.assertRaisesRegex(PrematureT02Closure, "15 M02 final screenshot PNGs not committed"):
            audit(self.root)

    def test_m02_image_status_does_not_equate_to_complete_module(self):
        result = audit(ROOT)
        self.assertEqual(15, result["verified_manifest_screenshot_count"])
        self.assertEqual("READY_FOR_T02_SCOPED_REMOTE_CI", result["acceptance"])
        self.assertTrue(result["t02_scope_only"])
        self.assertFalse(result["m02_module_release_verified"])
        self.assertFalse(result["full_nvda_narrator_verified"])
        self.assertFalse(result["performance_budget_approved"])
        self.assertIn("NOT YET VERIFIED", (ROOT / "docs/modules/M02.md").read_text(encoding="utf-8"))
        self.assertFalse(result["remote_ci_and_merge_verified"])

    def test_manifest_missing_screen_id_is_not_ready(self):
        m = self._json("docs/screenshots/MANIFEST.json")
        m["required"] = [row for row in m["required"] if row["asset_id"] != "M02-S07"]
        self._save("docs/screenshots/MANIFEST.json", m)
        with self.assertRaisesRegex(PrematureT02Closure, "M02 missing required screenshot IDs: M02-S07"):
            audit(self.root)

    def test_m19_pending_is_separate_not_in_m02_count(self):
        self.assertEqual(7, len(SCREEN_IDS))
        self.assertEqual(8, len(OPTION_IDS))
        self.assertEqual(15, len(REQUIRED_IDS))
        m = self._json("docs/screenshots/MANIFEST.json")
        self.assertEqual(14, sum(row["module"] == "M19" for row in m["required"]))

    def test_no_scope_review_is_not_final_visual_proof(self):
        (self.root / "docs/screenshots/M02/T02-visual-foundation.review.json").unlink()
        with self.assertRaisesRegex(PrematureT02Closure, "T02 early native foundation review record absent"):
            audit(self.root)

    def test_windows_gate_runs_and_preserves_candidate_only_visual_proof(self):
        workflow = (ROOT / ".github/workflows/p01-desktop.yml").read_text(encoding="utf-8")
        native = (ROOT / "scripts/capture_p01_desktop.ps1").read_text(encoding="utf-8")
        verifier = (ROOT / "tools/verify_p02_native_evidence.py").read_text(encoding="utf-8")
        self.assertIn("P02-T02 final acceptance guard (no premature DONE)", workflow)
        self.assertIn("python -m unittest tests.test_p02_t02_acceptance -v", workflow)
        self.assertIn("python -m tools.verify_p02_t02_acceptance --report", workflow)
        self.assertIn("docs/screenshots/_ci/M02/P02-T02-12-readiness.json", workflow)
        for image_id in ("M02-S07", "P02-T02-12-LIGHT", "P02-T02-12-DARK"):
            self.assertIn("-ScreenshotId '" + image_id + "'", native)
            self.assertIn('"' + image_id + '"', verifier)
        self.assertIn("capture_verified = $false", native)
        self.assertIn("light/dark capture has identical pixels", verifier)
        self.assertIn("candidate_pending_visual_review", native)

    def test_scoped_t02_done_requires_original_png_bytes_not_just_manifest(self):
        m = self._json("docs/screenshots/MANIFEST.json")
        for row in m["required"]:
            if row["module"] == "M02":
                path = self.root / row["path"]
                path.parent.mkdir(parents=True, exist_ok=True)
                path.write_bytes((ROOT / row["path"]).read_bytes())
        t = self._json("docs/state/pr-tasks/P02.json")
        next(row for row in t["tasks"] if row["id"] == "P02-T02")["status"] = "DONE"
        self._save("docs/state/pr-tasks/P02.json", t)
        complete = audit(self.root)
        self.assertEqual("READY_FOR_T02_SCOPED_REMOTE_CI", complete["acceptance"])
        self.assertEqual("DONE", complete["official_task_status"])
        self.assertEqual(15, complete["verified_manifest_screenshot_count"])
        # Tampering even one byte invalidates scoped DONE despite the review file.
        original = self.root / "docs/screenshots/M02/M02-S01.png"
        original.write_bytes(original.read_bytes() + b"tamper")
        with self.assertRaisesRegex(PrematureT02Closure, "falsely marked DONE"):
            audit(self.root)

    def test_t02_scope_is_not_t10_full_module_or_t11_merge(self):
        result = audit(ROOT)
        self.assertIn(result["official_task_status"], ("IN_PROGRESS", "DONE"))
        self.assertEqual("READY_FOR_T02_SCOPED_REMOTE_CI", result["acceptance"])
        self.assertFalse(result["m02_module_release_verified"])
        self.assertFalse(result["full_nvda_narrator_verified"])
        self.assertFalse(result["remote_ci_and_merge_verified"])


if __name__ == "__main__":
    unittest.main()
