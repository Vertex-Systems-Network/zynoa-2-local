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
        )
        for name in self.paths:
            dest = self.root / name
            dest.parent.mkdir(parents=True, exist_ok=True)
            dest.write_bytes((ROOT / name).read_bytes())

    def _json(self, path):
        return json.loads((self.root / path).read_text(encoding="utf-8"))

    def _save(self, path, payload):
        (self.root / path).write_text(json.dumps(payload), encoding="utf-8")

    def test_in_progress_parent_reports_real_finalization_blockers(self):
        result = audit(self.root)
        self.assertEqual("P02-T02", result["task_id"])
        self.assertEqual("IN_PROGRESS", result["official_task_status"])
        self.assertEqual("NOT_READY", result["acceptance"])
        self.assertEqual(15, result["expected_final_screenshot_count"])
        self.assertEqual(0, result["verified_manifest_screenshot_count"])
        self.assertIn("15 M02 final screenshot PNGs not committed", result["blockers"])
        self.assertIn("15 M02 screenshot entries not VERIFIED", result["blockers"])
        self.assertIn("M02-OPT-03 functionality explicitly not implemented", result["blockers"])
        self.assertIn("M02-OPT-04 functionality explicitly not implemented", result["blockers"])
        self.assertFalse(result["remote_ci_and_merge_verified"])

    def test_premature_done_is_a_failing_gate(self):
        t = self._json("docs/state/pr-tasks/P02.json")
        next(row for row in t["tasks"] if row["id"] == "P02-T02")["status"] = "DONE"
        self._save("docs/state/pr-tasks/P02.json", t)
        with self.assertRaisesRegex(PrematureT02Closure, "falsely marked DONE"):
            audit(self.root)

    def test_manifest_status_without_real_pngs_is_insufficient(self):
        m = self._json("docs/screenshots/MANIFEST.json")
        for row in m["required"]:
            if row["module"] == "M02":
                row["status"] = "VERIFIED"
        self._save("docs/screenshots/MANIFEST.json", m)
        result = audit(self.root)
        self.assertEqual(0, result["verified_manifest_screenshot_count"])
        self.assertIn("15 M02 final screenshot PNGs not committed", result["blockers"])

    def test_manifest_missing_screen_id_is_not_ready(self):
        m = self._json("docs/screenshots/MANIFEST.json")
        m["required"] = [row for row in m["required"] if row["asset_id"] != "M02-S07"]
        self._save("docs/screenshots/MANIFEST.json", m)
        self.assertIn("M02 missing required screenshot IDs: M02-S07", audit(self.root)["blockers"])

    def test_m19_pending_is_separate_not_in_m02_count(self):
        self.assertEqual(7, len(SCREEN_IDS))
        self.assertEqual(8, len(OPTION_IDS))
        self.assertEqual(15, len(REQUIRED_IDS))
        m = self._json("docs/screenshots/MANIFEST.json")
        self.assertEqual(14, sum(row["module"] == "M19" for row in m["required"]))

    def test_no_scope_review_is_not_final_visual_proof(self):
        (self.root / "docs/screenshots/M02/T02-visual-foundation.review.json").unlink()
        self.assertIn("T02 native visual review record absent", audit(self.root)["blockers"])

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

    def test_current_official_status_cannot_be_auto_closed_by_passing_ci(self):
        result = audit(ROOT)
        self.assertNotEqual("DONE", result["official_task_status"])
        self.assertEqual("NOT_READY", result["acceptance"])


if __name__ == "__main__":
    unittest.main()
