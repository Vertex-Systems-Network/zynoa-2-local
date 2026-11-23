"""P02-T10 final screenshot readiness tests. Synthetic metadata is NEVER visual proof."""
import hashlib
import json
from pathlib import Path
import tempfile
import unittest

from tools.verify_p02_native_evidence import SCREEN_IDS, OPTION_REFERENCE_MATRIX, DIRECT_CONTROL_MATRIX
from tools.verify_p02_t10_readiness import audit, InvalidT10Readiness, EXPECTED

SHA = "a" * 40


class P02T10ReadinessTests(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        self.addCleanup(self.tmp.cleanup)
        self.root = Path(self.tmp.name)
        self.manifest = self.root / "docs/screenshots/MANIFEST.json"
        self.machine = self.root / "docs/screenshots/_ci/M02/P02-native-machine-review.json"
        self.performance = self.root / "docs/screenshots/_ci/M02/P02-native-performance.json"
        self.manifest.parent.mkdir(parents=True, exist_ok=True)
        self.machine.parent.mkdir(parents=True, exist_ok=True)
        rows = [
            dict(asset_id=asset, module=asset[:3],
                 path=f"docs/screenshots/{asset[:3]}/{asset}.png",
                 status="PENDING", source="REAL_APP_CAPTURE_REQUIRED",
                 kind="control" if "-OPT-" in asset else "screen")
            for asset in sorted(EXPECTED)
        ]
        self._write(self.manifest, dict(status="IN_PROGRESS", required=rows))
        self._write(self.machine, dict(
            schema_version=1, source_commit_sha=SHA,
            status="MACHINE_METADATA_HASH_VALIDATED_ONLY",
            independent_visual_review=False, manifest_completed=False,
            actual_screen_control_candidates=dict(count=15, ids=list(DIRECT_CONTROL_MATRIX),
                status="MACHINE_CONTROL_CAPTURE_ONLY", final_29_manifest_assets_verified=False),
            option_reference_matrix=dict(count=16, ids=list(OPTION_REFERENCE_MATRIX),
                status="MACHINE_REFERENCE_CAPTURE_ONLY",
                final_29_manifest_assets_verified=False),
            screens=[{"screen_id":name} for name in SCREEN_IDS]))
        self._write(self.performance, dict(
            schema_version=1, source_commit_sha=SHA,
            target="GitHub-hosted Windows Tauri native executable",
            startup_local_metadata_ready_ms=1700,
            native_screenshot_suite_ms=52000,
            performance_budget_approved=False, no_user_data=True))

    @staticmethod
    def _write(path: Path, payload: dict):
        path.write_text(json.dumps(payload), encoding="utf-8")

    def _mutate(self, path: Path, fn):
        payload = json.loads(path.read_text(encoding="utf-8"))
        fn(payload)
        self._write(path, payload)

    def _attach_committed_native_fixture(self):
        data = b"\x89PNG\r\n\x1a\n" + b"synthetic-test-bytes-not-visual-proof"
        path = self.root / "docs/screenshots/M02/M02-S01.png"
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_bytes(data)
        git_blob = f"blob {len(data)}\0".encode("ascii") + data
        def attach(payload):
            row = next(x for x in payload["required"] if x["asset_id"] == "M02-S01")
            row["source_capture_sha256"] = hashlib.sha256(data).hexdigest()
            row["source_git_blob_sha"] = hashlib.sha1(git_blob).hexdigest()
            row["source"] = "WINDOWS_TAURI_CI_RUN_fixture"
        self._mutate(self.manifest, attach)
        return path

    def test_committed_native_bytes_validated_without_forged_approval(self):
        self._attach_committed_native_fixture()
        result = audit(self.root, SHA)
        self.assertEqual("NOT_READY", result["status"])
        self.assertEqual(0, result["final_manifest_verified"])

    def test_committed_native_bytes_tampering_fails_closed(self):
        path = self._attach_committed_native_fixture()
        path.write_bytes(path.read_bytes() + b"tampered")
        with self.assertRaisesRegex(InvalidT10Readiness, "committed PNG SHA-256 mismatch"):
            audit(self.root, SHA)

    def test_committed_native_origin_metadata_required(self):
        path = self.root / "docs/screenshots/M02/M02-S01.png"
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_bytes(b"\x89PNG\r\n\x1a\n" + b"unproven")
        with self.assertRaisesRegex(InvalidT10Readiness, "committed source SHA-256 absent"):
            audit(self.root, SHA)

    def test_committed_native_git_blob_identity_required(self):
        self._attach_committed_native_fixture()
        self._mutate(self.manifest, lambda x: next(row for row in x["required"]
            if row["asset_id"] == "M02-S01").update(source_git_blob_sha="a" * 40))
        with self.assertRaisesRegex(InvalidT10Readiness, "committed Git blob SHA mismatch"):
            audit(self.root, SHA)

    def test_all_candidates_are_present_but_never_final_approved(self):
        result = audit(self.root, SHA)
        self.assertEqual("NOT_READY", result["status"])
        self.assertEqual(69, result["candidate_total"])
        self.assertEqual(15, result["native_direct_control_candidates"])
        self.assertEqual(16, result["native_option_references_captured"])
        self.assertEqual(29, result["final_manifest_expected"])
        self.assertEqual(0, result["final_manifest_verified"])
        self.assertEqual(set(EXPECTED), set(result["pending_final_assets"]))
        self.assertFalse(result["independent_full_visual_review"])
        self.assertFalse(result["screen_reader_approved"])

    def test_native_direct_controls_cannot_be_disguised_as_final_acceptance(self):
        self._mutate(self.machine, lambda x: x["actual_screen_control_candidates"].update(
            status="FINAL_VERIFIED"))
        with self.assertRaisesRegex(InvalidT10Readiness, "15-direct-control"):
            audit(self.root, SHA)

    def test_omitted_direct_control_candidate_is_rejected(self):
        self._mutate(self.machine, lambda x: x["actual_screen_control_candidates"]["ids"].pop())
        with self.assertRaisesRegex(InvalidT10Readiness, "15-direct-control"):
            audit(self.root, SHA)

    def test_missing_or_wrong_source_metadata_cannot_pass(self):
        self._mutate(self.machine, lambda x: x.update(source_commit_sha="b" * 40))
        with self.assertRaisesRegex(InvalidT10Readiness, "source SHA"):
            audit(self.root, SHA)

    def test_missing_exact_option_reference_rejected(self):
        self._mutate(self.machine, lambda x: x["option_reference_matrix"].update(count=15))
        with self.assertRaisesRegex(InvalidT10Readiness, "16-option"):
            audit(self.root, SHA)

    def test_truncated_candidate_screen_list_rejected(self):
        self._mutate(self.machine, lambda x: x["screens"].pop())
        with self.assertRaisesRegex(InvalidT10Readiness, "expected real native candidate IDs"):
            audit(self.root, SHA)

    def test_machine_cannot_self_certify_independent_visual_review(self):
        self._mutate(self.machine, lambda x: x.update(independent_visual_review=True))
        with self.assertRaisesRegex(InvalidT10Readiness, "may not claim"):
            audit(self.root, SHA)

    def test_final_screenshot_verification_without_png_fails(self):
        self._mutate(self.manifest, lambda x: x["required"][0].update(status="VERIFIED"))
        with self.assertRaisesRegex(InvalidT10Readiness, "no committed final PNG"):
            audit(self.root, SHA)

    def test_manifest_missing_or_duplicate_ids_rejected(self):
        self._mutate(self.manifest, lambda x: x["required"].pop())
        with self.assertRaisesRegex(InvalidT10Readiness, "29 screenshot IDs"):
            audit(self.root, SHA)

    def test_performance_approval_cannot_be_invented(self):
        self._mutate(self.performance, lambda x: x.update(performance_budget_approved=True))
        with self.assertRaisesRegex(InvalidT10Readiness, "falsely approved"):
            audit(self.root, SHA)

    def test_performance_sample_must_be_positive_and_bounded(self):
        self._mutate(self.performance, lambda x: x.update(native_screenshot_suite_ms=-1))
        with self.assertRaisesRegex(InvalidT10Readiness, "invalid native sample duration"):
            audit(self.root, SHA)

    def test_invalid_build_identity_rejected(self):
        with self.assertRaisesRegex(InvalidT10Readiness, "invalid exact source SHA"):
            audit(self.root, "garbage")


if __name__ == "__main__":
    unittest.main()
