"""Fail-closed P02 review-asset ZIP tests. Fake PNGs are ONLY test fixtures."""
from __future__ import annotations

import hashlib
import json
from pathlib import Path
import struct
import tempfile
import unittest
import zlib
import zipfile

from tools.stage_p02_native_assets import StagingError, stage, staged_archive
from tools.build_p02_visual_review_pack import _EXISTING_DIRECT
from tools.verify_p02_native_evidence import SCREEN_IDS
from tools.verify_p02_t10_readiness import EXPECTED

SOURCE = "a" * 40


def chunk(tag: bytes, data: bytes) -> bytes:
    return struct.pack(">I", len(data)) + tag + data + struct.pack(">I", zlib.crc32(tag + data) & 0xffffffff)


def png(seed: int) -> bytes:
    # Actual valid PNG bytes at a native-like dimension; deliberately a test-only fixture.
    row = b"\x00" + bytes([seed, 20, 40]) * 880
    raw = row * 600
    header = struct.pack(">IIBBBBB", 880, 600, 8, 2, 0, 0, 0)
    return (b"\x89PNG\r\n\x1a\n" + chunk(b"IHDR", header) +
            chunk(b"IDAT", zlib.compress(raw, 8)) + chunk(b"IEND", b""))


def create_fixture(root: Path) -> None:
    source = root / "docs/screenshots/_ci"
    records = []
    frame_rows = []
    for code in SCREEN_IDS:
        records.append({"screen_id": code, "source_commit_sha": SOURCE,
                        "sha256": "0" * 64})
    by_id = {x["screen_id"]: x for x in records}
    for index, asset in enumerate(sorted(EXPECTED), 1):
        module = asset[:3]
        name = asset if asset in _EXISTING_DIRECT else "P02-T10-CTRL-" + asset
        image = png(index)
        digest = hashlib.sha256(image).hexdigest()
        by_id[name]["sha256"] = digest
        folder = source / module
        folder.mkdir(parents=True, exist_ok=True)
        (folder / (name + ".png")).write_bytes(image)
        receipt = {
            "source_commit_sha": SOURCE, "built_commit_sha": SOURCE,
            "sha256": digest, "source": "GitHub Windows Actions actual Tauri process",
            "screenshot_id": name, "capture_status": "candidate_pending_visual_review",
            "capture_verified": False, "window_fully_visible": True,
            "window_width": 880, "window_height": 600,
        }
        if name.startswith("P02-T10-CTRL-"):
            receipt.update(candidate_final_asset_id=asset,
                           interaction="actual-native-screen-or-control:keyboard",
                           evidence_limit="NOT a final manifest screenshot or independent visual approval")
        (folder / (name + ".capture.json")).write_text(json.dumps(receipt), encoding="utf-8")
        frame_rows.append({
            "asset_id": asset, "module": module, "native_candidate_id": name,
            "native_path": f"docs/screenshots/_ci/{module}/{name}.png",
            "sha256": digest, "status": "CANDIDATE_PENDING_INDEPENDENT_FINAL_REVIEW",
            "final_manifest_verified": False,
        })
    index = {
        "source_commit_sha": SOURCE, "status": "REVIEW_PACK_ONLY_NOT_FINAL",
        "final_manifest_completed": False, "independent_full_visual_review": False,
        "screen_reader_approved": False, "final_asset_targets": 29,
        "mapped_real_native_targets": 29, "additional_direct": 15,
        "existing_direct": 14, "separate_option_help_references": 16,
        "frames": frame_rows,
    }
    machine = {
        "source_commit_sha": SOURCE, "status": "MACHINE_METADATA_HASH_VALIDATED_ONLY",
        "independent_visual_review": False, "manifest_completed": False,
        "screens": records,
    }
    (source / "M02").mkdir(parents=True, exist_ok=True)
    (source / "M02" / "P02-T10-29-review-index.json").write_text(json.dumps(index), encoding="utf-8")
    (source / "M02" / "P02-native-machine-review.json").write_text(json.dumps(machine), encoding="utf-8")


class NativeStagingContracts(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        self.addCleanup(self.tmp.cleanup)
        self.root = Path(self.tmp.name)
        create_fixture(self.root)
        self.out = self.root / "review-output"

    def change_index(self, fn):
        p = self.root / "docs/screenshots/_ci/M02/P02-T10-29-review-index.json"
        data = json.loads(p.read_text(encoding="utf-8"));fn(data)
        p.write_text(json.dumps(data), encoding="utf-8")

    def test_stages_all_29_in_exact_target_paths_without_any_approval(self):
        report = stage(self.root, SOURCE, self.out)
        self.assertEqual(29, report["candidate_png_count"])
        self.assertEqual(29, report["unique_png_hashes"])
        self.assertEqual(0, report["final_manifest_verified"])
        self.assertFalse(report["independent_full_visual_review"])
        self.assertFalse(report["full_screen_reader_verified"])
        path = self.out / "P02-T10-29-native-review-candidates.zip"
        self.assertTrue(path.exists())
        with zipfile.ZipFile(path) as z:
            files = z.namelist()
            images = [name for name in files if name.endswith(".png")]
            self.assertEqual(29, len(images))
            self.assertEqual(60, len(files))
            self.assertEqual(15, sum(name.startswith("docs/screenshots/M02/") for name in images))
            self.assertEqual(14, sum(name.startswith("docs/screenshots/M19/") for name in images))
            self.assertTrue(all("-T10-REF-" not in name for name in images))
            receipt = json.loads(z.read("docs/screenshots/M02/M02-OPT-08.review-candidate.json"))
            self.assertEqual("PENDING", receipt["final_manifest_status"])
            self.assertEqual("P02-T10-CTRL-M02-OPT-08", receipt["original_capture_id"])
            self.assertEqual("PENDING_INDEPENDENT_VISUAL_AND_SCREEN_READER_REVIEW", receipt["review_status"])
            self.assertEqual(SOURCE, receipt["source_commit_sha"])
        with self.assertRaisesRegex(StagingError, "overwrite"):
            stage(self.root, SOURCE, self.out)

    def test_wrong_source_sha_rejected(self):
        with self.assertRaisesRegex(StagingError, "source SHA mismatch"):
            staged_archive(self.root, "b" * 40)

    def test_broken_png_hash_fails_before_export(self):
        self.change_index(lambda x: x["frames"][0].update(sha256="b" * 64))
        with self.assertRaisesRegex(StagingError, "hash mismatch"):
            stage(self.root, SOURCE, self.out)
        self.assertFalse(self.out.exists())

    def test_help_reference_can_never_impersonate_a_control(self):
        self.change_index(lambda x: next(f for f in x["frames"] if f["asset_id"] == "M19-OPT-06").update(
            native_candidate_id="M19-T10-REF-OPT-06"))
        with self.assertRaisesRegex(StagingError, "Help reference"):
            staged_archive(self.root, SOURCE)

    def test_false_visual_signoff_is_rejected(self):
        self.change_index(lambda x: x.update(independent_full_visual_review=True))
        with self.assertRaisesRegex(StagingError, "improperly claims acceptance"):
            staged_archive(self.root, SOURCE)

    def test_duplicate_png_frames_fail_closed(self):
        f = self.root / "docs/screenshots/_ci/M02"
        source = f / "P02-T10-CTRL-M02-OPT-01.png"
        other = f / "P02-T10-CTRL-M02-OPT-02.png"
        payload = source.read_bytes();digest=hashlib.sha256(payload).hexdigest()
        other.write_bytes(payload)
        receipt_path = other.with_suffix(".capture.json")
        receipt=json.loads(receipt_path.read_text(encoding="utf-8"))
        receipt["sha256"] = digest
        receipt_path.write_text(json.dumps(receipt), encoding="utf-8")
        self.change_index(lambda x: next(r for r in x["frames"] if r["asset_id"] == "M02-OPT-02").update(sha256=digest))
        machine_path = f / "P02-native-machine-review.json"
        machine=json.loads(machine_path.read_text(encoding="utf-8"))
        next(r for r in machine["screens"] if r["screen_id"] == "P02-T10-CTRL-M02-OPT-02")["sha256"] = digest
        machine_path.write_text(json.dumps(machine), encoding="utf-8")
        with self.assertRaisesRegex(StagingError, "duplicated pixels"):
            staged_archive(self.root, SOURCE)

    def test_fake_actual_control_keyboard_evidence_denied(self):
        receipt = self.root / "docs/screenshots/_ci/M19/P02-T10-CTRL-M19-OPT-07.capture.json"
        data=json.loads(receipt.read_text(encoding="utf-8"))
        data["interaction"]="palette:exact-id:enter:option-detail"
        receipt.write_text(json.dumps(data),encoding="utf-8")
        with self.assertRaisesRegex(StagingError, "keyboard evidence missing"):
            staged_archive(self.root, SOURCE)

    def test_workflow_exports_zip_only_after_strict_hash_and_reviewer_index(self):
        repo_root = Path(__file__).resolve().parents[1]
        workflow = (repo_root / ".github/workflows/p01-desktop.yml").read_text(encoding="utf-8")
        self.assertLess(workflow.index("python -m tools.verify_p02_native_evidence --root"),
                        workflow.index("python -m tools.stage_p02_native_assets --root"))
        self.assertLess(workflow.index("python -m tools.build_p02_visual_review_pack --root"),
                        workflow.index("python -m tools.stage_p02_native_assets --root"))
        for marker in ("tests.test_p02_staged_native_assets -v",
                       "docs/screenshots/_ci/M02/P02-T10-29-native-review-candidates.zip"):
            self.assertIn(marker, workflow)


if __name__ == "__main__":
    unittest.main()