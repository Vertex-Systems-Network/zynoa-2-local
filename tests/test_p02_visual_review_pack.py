"""Strict review-pack mapping tests. Fixture metadata is not a screenshot."""
from pathlib import Path
import tempfile
import unittest

from tools.build_p02_visual_review_pack import (
    ReviewPackError, candidate_id, plan, _EXISTING_DIRECT,
)
from tools.verify_p02_native_evidence import DIRECT_CONTROL_MATRIX, OPTION_REFERENCE_MATRIX, SCREEN_IDS
from tools.verify_p02_t10_readiness import EXPECTED

SOURCE_SHA = "a" * 40


def fixtures():
    manifest = {"required": [
        {"asset_id": x, "module": x[:3], "kind": "control" if "-OPT-" in x else "screen",
         "path": f"docs/screenshots/{x[:3]}/{x}.png", "status": "PENDING"}
        for x in sorted(EXPECTED)
    ]}
    machine = {
        "source_commit_sha": SOURCE_SHA,
        "status": "MACHINE_METADATA_HASH_VALIDATED_ONLY",
        "independent_visual_review": False, "manifest_completed": False,
        "screens": [
            {"screen_id": x, "source_commit_sha": SOURCE_SHA, "sha256": f"{i+1:064x}"}
            for i, x in enumerate(SCREEN_IDS)
        ],
        "actual_screen_control_candidates": {
            "count": 15, "ids": list(DIRECT_CONTROL_MATRIX),
            "status": "MACHINE_CONTROL_CAPTURE_ONLY",
            "final_29_manifest_assets_verified": False,
        },
        "option_reference_matrix": {
            "count": 16, "ids": list(OPTION_REFERENCE_MATRIX),
            "status": "MACHINE_REFERENCE_CAPTURE_ONLY",
        },
    }
    return manifest, machine


class ReviewPackContracts(unittest.TestCase):
    def test_all_29_true_screen_targets_and_separate_help_refs(self):
        manifest, machine = fixtures()
        report = plan(manifest, machine, SOURCE_SHA)
        self.assertEqual(29, report["mapped_real_native_targets"])
        self.assertEqual(14, report["existing_direct"])
        self.assertEqual(15, report["additional_direct"])
        self.assertEqual(16, report["separate_option_help_references"])
        self.assertFalse(report["final_manifest_completed"])
        self.assertFalse(report["screen_reader_approved"])
        self.assertEqual({x["asset_id"] for x in report["frames"]}, EXPECTED)
        self.assertTrue(all(x["native_candidate_id"] in SCREEN_IDS for x in report["frames"]))
        self.assertTrue(all(not x["final_manifest_verified"] for x in report["frames"]))

    def test_help_reference_is_never_used_as_control_image(self):
        for asset in ("M02-OPT-01", "M19-OPT-06", "M19-OPT-08"):
            self.assertEqual("P02-T10-CTRL-" + asset, candidate_id(asset))
        self.assertNotIn("M19-T10-REF-OPT-06", [candidate_id(x) for x in EXPECTED])
        self.assertNotIn("M02-T10-REF-OPT-01", [candidate_id(x) for x in EXPECTED])
        self.assertEqual(14, len(_EXISTING_DIRECT))

    def test_control_matrix_must_be_source_bound_and_exact(self):
        manifest, machine = fixtures()
        machine["actual_screen_control_candidates"]["ids"].pop()
        with self.assertRaisesRegex(ReviewPackError, "actual control proof"):
            plan(manifest, machine, SOURCE_SHA)

    def test_final_review_must_not_be_fabricated_by_machine(self):
        manifest, machine = fixtures()
        machine["independent_visual_review"] = True
        with self.assertRaisesRegex(ReviewPackError, "machine report invalid"):
            plan(manifest, machine, SOURCE_SHA)

    def test_bad_sha_for_any_mapped_frame_rejected(self):
        manifest, machine = fixtures()
        native_id = candidate_id("M19-OPT-07")
        next(x for x in machine["screens"] if x["screen_id"] == native_id)["sha256"] = "bad"
        with self.assertRaisesRegex(ReviewPackError, "hash missing"):
            plan(manifest, machine, SOURCE_SHA)

    def test_duplicate_manifest_or_wrong_path_rejected(self):
        manifest, machine = fixtures()
        manifest["required"].append(dict(manifest["required"][0]))
        with self.assertRaisesRegex(ReviewPackError, "29 screenshot inventory"):
            plan(manifest, machine, SOURCE_SHA)
        manifest, machine = fixtures()
        manifest["required"][0]["path"] = "docs/screenshots/OTHER.png"
        with self.assertRaisesRegex(ReviewPackError, "asset path mismatch"):
            plan(manifest, machine, SOURCE_SHA)

    def test_missing_native_source_image_id_fails_closed(self):
        manifest, machine = fixtures()
        machine["screens"].pop()
        with self.assertRaisesRegex(ReviewPackError, "inventory missing"):
            plan(manifest, machine, SOURCE_SHA)

    def test_workflow_creates_self_contained_review_pack_after_provenance(self):
        root = Path(__file__).resolve().parents[1]
        wf = (root / ".github/workflows/p01-desktop.yml").read_text(encoding="utf-8")
        self.assertIn("python -m tools.build_p02_visual_review_pack", wf)
        self.assertIn("tests.test_p02_visual_review_pack -v", wf)
        self.assertIn("P02-T10-29-review-index.json", wf)
        self.assertIn("P02-T10-69-native-review.html", wf)
        self.assertIn("docs/screenshots/_ci/M02/*.html", wf)
        src = (root / "tools/build_p02_visual_review_pack.py").read_text(encoding="utf-8")
        self.assertIn("data:image/png;base64,", src)
        self.assertIn("verify_native(root /", src)
        self.assertNotIn("fetch(", src)
        self.assertNotIn("<script", src)
        self.assertNotIn("localStorage", src)


if __name__ == "__main__":
    unittest.main()
