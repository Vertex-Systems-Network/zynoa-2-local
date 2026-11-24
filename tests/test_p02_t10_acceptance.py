"""T10 final preview acceptance must fail closed on real bytes and native speech."""
import copy
import json
from pathlib import Path
import tempfile
import unittest
from unittest.mock import patch

import tools.verify_p02_t10_acceptance as gate
from tests.test_p02_native_uia import good as sample_uia
from tests.test_p02_nvda_speech import sample as sample_nvda
from tests.test_p02_native_performance import sample as sample_warm

ROOT = Path(__file__).resolve().parents[1]
SHA = "a" * 40
RUN = "45301683751"
SUB = "docs/screenshots/_ci/M02/"


class T10PreviewAcceptanceTests(unittest.TestCase):
    def test_all_29_committed_images_reviews_and_wiki_are_source_bound(self):
        s = gate.audit_visual_evidence(ROOT)
        self.assertEqual(29, s["native_images_verified"])
        self.assertEqual(29, s["independent_image_reviews"])
        self.assertEqual(16, s["help_wiki_options"])
        self.assertTrue(s["remote_wiki_preview_readback"])

    def test_image_byte_tampering_is_rejected_even_if_manifest_says_verified(self):
        original = Path.read_bytes
        def changed(path):
            data = original(path)
            return data + b"tampered" if str(path).endswith("M02-S01.png") else data
        with patch.object(Path, "read_bytes", changed):
            with self.assertRaisesRegex(gate.InvalidT10Acceptance, "original PNG or review hash mismatch"):
                gate.audit_visual_evidence(ROOT)

    def test_false_remote_wiki_claim_is_rejected(self):
        original = gate.load
        def corrupt(root, path):
            data = original(root, path)
            if path.endswith("P02_T10_WIKI_PREVIEW_PUBLISHED_20261124.json"):
                data = copy.deepcopy(data)
                data["fresh_unauthenticated_git_clone_readback"] = False
            return data
        with patch.object(gate, "load", corrupt):
            with self.assertRaisesRegex(gate.InvalidT10Acceptance, "remote readback"):
                gate.audit_visual_evidence(ROOT)

    def test_premerge_lifecycle_remains_fail_closed(self):
        board = {"tasks": [{"id": "P02-T10", "status": "DONE"},
                           {"id": "P02-T11", "status": "IN_PROGRESS"}]}
        gate.verify_premerge_state({"phase": "P02", "phase_status": "IN_PROGRESS"}, board)
        for state in ({"phase": "P02", "phase_status": "MERGED_VERIFIED"},
                      {"phase": "P03", "phase_status": "IN_PROGRESS"}):
            with self.assertRaises(gate.InvalidT10Acceptance):
                gate.verify_premerge_state(state, board)
        board["tasks"][1]["status"] = "DONE"
        with self.assertRaises(gate.InvalidT10Acceptance):
            gate.verify_premerge_state({"phase": "P02", "phase_status": "IN_PROGRESS"}, board)

    def _audit_runtime_fixture(self, runtime):
        # Exercise real evidence verification with explicit premerge lifecycle
        # fixtures, independent of the checkout's later phase state.
        original = gate.load
        def fixture(root, path):
            if path == "docs/state/PHASE.json":
                return {"phase": "P02", "phase_status": "IN_PROGRESS"}
            if path == "docs/state/pr-tasks/P02.json":
                return {"tasks": [{"id": "P02-T10", "status": "DONE"},
                                  {"id": "P02-T11", "status": "IN_PROGRESS"}]}
            return original(root, path)
        with patch.object(gate, "load", fixture):
            return gate.audit(ROOT, Path(runtime), SHA, RUN)

    def _runtime(self, work):
        root = Path(work)
        folder = root / SUB
        folder.mkdir(parents=True, exist_ok=True)
        raw_uia = sample_uia()
        raw_nvda = sample_nvda()
        raw_nvda["github_run_id"] = RUN
        raw_warm = sample_warm()
        raw_warm["github_run_id"] = RUN
        for i, row in enumerate(raw_warm["samples"]):
            row["window_first_visible_ms"] = (200, 150, 160)[i]
            row["native_handshake_ready_ms"] = (900, 760, 810)[i]
        cold = {
            "schema_version": 1, "source_commit_sha": SHA,
            "target": "GitHub-hosted Windows Tauri native executable",
            "startup_local_metadata_ready_ms": 7000,
            "native_screenshot_suite_ms": 93000,
            "performance_budget_approved": False, "no_user_data": True
        }
        for name, obj in {
            "P02-native-uia.capture.json": raw_uia,
            "P02-nvda-speech.capture.json": raw_nvda,
            "P02-native-startup-repeat.capture.json": raw_warm,
            "P02-native-performance.json": cold,
        }.items():
            (folder / name).write_text(json.dumps(obj), encoding="utf-8")
        return folder

    def test_scoped_preview_passes_without_claiming_product_release(self):
        with tempfile.TemporaryDirectory() as d:
            self._runtime(d)
            proof = self._audit_runtime_fixture(d)
            self.assertEqual("READY_FOR_T10_SCOPED_WINDOWS_PREVIEW_ACCEPTANCE", proof["status"])
            self.assertFalse(proof["full_narrator_certified"])
            self.assertFalse(proof["full_product_a11y_certified"])
            self.assertFalse(proof["product_performance_sla_approved"])
            self.assertTrue(proof["t11_pending"])

    def test_missing_spoken_help_and_bad_performance_fail(self):
        for category in ("speech", "slow", "wrong_run"):
            with self.subTest(category=category), tempfile.TemporaryDirectory() as d:
                folder = self._runtime(d)
                if category == "speech":
                    path = folder / "P02-nvda-speech.capture.json"
                    obj = json.loads(path.read_text())
                    obj["events"] = obj["events"][:2]
                elif category == "slow":
                    path = folder / "P02-native-performance.json"
                    obj = json.loads(path.read_text())
                    obj["startup_local_metadata_ready_ms"] = 45001
                else:
                    path = folder / "P02-nvda-speech.capture.json"
                    obj = json.loads(path.read_text())
                    obj["github_run_id"] = "99"
                path.write_text(json.dumps(obj), encoding="utf-8")
                with self.assertRaises(gate.InvalidT10Acceptance):
                    self._audit_runtime_fixture(d)

    def test_windows_native_job_executes_final_audit_after_real_nvda(self):
        wf = (ROOT / ".github/workflows/p01-desktop.yml").read_text(encoding="utf-8")
        self.assertIn("P02-T10 exact-source native preview final acceptance", wf)
        self.assertIn("python -m tools.verify_p02_t10_acceptance", wf)
        self.assertLess(wf.index("P02 live NVDA speech plus real Windows keyboard journey"),
                        wf.index("P02-T10 exact-source native preview final acceptance"))
        self.assertIn("P02-T10-scoped-acceptance.verify.json", wf)


if __name__ == "__main__":
    unittest.main()
