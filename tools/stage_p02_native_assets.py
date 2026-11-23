"""Stage 29 actual native Windows P02 screenshot candidates for independent review.

Source-SHA and PNG receipts must match the previously passed 69-frame native
capture gate. This creates one DOWNLOADABLE review-only ZIP, *never* commits
images or writes final paths, marks a manifest entry VERIFIED, or claims
NVDA/Narrator/approved performance/remote Wiki/merge acceptance.
"""
from __future__ import annotations

import argparse
import hashlib
import io
import json
from pathlib import Path
import re
import struct
import zipfile

_SHA = re.compile(r"[a-f0-9]{40}\Z")
_ID = re.compile(r"M(?:02|19)-(?:S0[1-7]|OPT-0[1-8])\Z")
_PNG = b"\x89PNG\r\n\x1a\n"
_ZIP_NAME = "P02-T10-29-native-review-candidates.zip"
_INDEX = "P02-T10-29-review-index.json"
_MACHINE = "P02-native-machine-review.json"
_RUN_ORIGIN = "GitHub Windows Actions actual Tauri process"


class StagingError(ValueError):
    """Review images must not be emitted when evidence lacks integrity."""


def require(condition: bool, message: str) -> None:
    if not condition:
        raise StagingError(message)


def dimensions(data: bytes) -> tuple[int, int]:
    require(len(data) >= 33 and data[:8] == _PNG and data[12:16] == b"IHDR", "invalid PNG signature/IHDR")
    w, h = struct.unpack(">II", data[16:24])
    require(880 <= w <= 2500 and 600 <= h <= 1600, "invalid real Windows DWM dimensions")
    return w, h


def staged_archive(root: Path, source_sha: str) -> tuple[bytes, dict]:
    """Return validated candidate ZIP bytes and non-approval report, without writes."""
    require(bool(_SHA.fullmatch(source_sha)), "invalid source SHA")
    ci_root = root / "docs/screenshots/_ci"
    index = json.loads((ci_root / "M02" / _INDEX).read_text(encoding="utf-8-sig"))
    machine = json.loads((ci_root / "M02" / _MACHINE).read_text(encoding="utf-8-sig"))
    require(index.get("source_commit_sha") == source_sha and
            machine.get("source_commit_sha") == source_sha, "native source SHA mismatch")
    require(index.get("status") == "REVIEW_PACK_ONLY_NOT_FINAL" and
            index.get("final_manifest_completed") is False and
            index.get("independent_full_visual_review") is False and
            index.get("screen_reader_approved") is False, "review pack improperly claims acceptance")
    require(machine.get("status") == "MACHINE_METADATA_HASH_VALIDATED_ONLY" and
            machine.get("independent_visual_review") is False and
            machine.get("manifest_completed") is False, "machine evidence claims independent visual acceptance")
    require(index.get("final_asset_targets") == 29 and
            index.get("mapped_real_native_targets") == 29 and
            index.get("additional_direct") == 15 and
            index.get("existing_direct") == 14 and
            index.get("separate_option_help_references") == 16, "29 native target matrix mismatch")
    frames = index.get("frames")
    require(isinstance(frames, list) and len(frames) == 29, "29 required screenshot frames missing")
    machine_ids = machine.get("screens")
    require(isinstance(machine_ids, list) and len(machine_ids) == 69, "69 source screenshots missing")
    lookup = {x.get("screen_id"): x for x in machine_ids if isinstance(x, dict)}
    require(len(lookup) == 69, "duplicate original native machine IDs")
    output = io.BytesIO()
    rows: list[dict] = []
    seen_ids: set[str] = set()
    seen_hashes: set[str] = set()
    with zipfile.ZipFile(output, "w", compression=zipfile.ZIP_DEFLATED, compresslevel=8) as archive:
        for frame in sorted(frames, key=lambda f: f.get("asset_id", "")):
            asset = frame.get("asset_id", "")
            require(isinstance(asset, str) and _ID.fullmatch(asset) is not None,
                    "unknown or invalid screenshot asset")
            require(asset not in seen_ids, "duplicate final target ID")
            seen_ids.add(asset)
            module = asset[:3]
            require(frame.get("module") == module and
                    frame.get("status") == "CANDIDATE_PENDING_INDEPENDENT_FINAL_REVIEW" and
                    frame.get("final_manifest_verified") is False, "frame prematurely approved")
            native_id = frame.get("native_candidate_id", "")
            expected_id = asset if asset in {
                "M02-S03", "M02-S04", "M02-S05", "M02-S06", "M02-S07",
                "M02-OPT-03", "M02-OPT-04", "M02-OPT-07",
                *(f"M19-S{i:02d}" for i in range(1, 7)),
            } else "P02-T10-CTRL-" + asset
            require(native_id == expected_id, "Help reference or incorrect live control used")
            native_png = f"docs/screenshots/_ci/{module}/{expected_id}.png"
            require(frame.get("native_path") == native_png, "unsafe native screenshot path")
            p = ci_root / module / (expected_id + ".png")
            image = p.read_bytes()
            digest = hashlib.sha256(image).hexdigest()
            require(frame.get("sha256") == digest and digest not in seen_hashes,
                    "native target hash mismatch or duplicated pixels")
            seen_hashes.add(digest)
            w, h = dimensions(image)
            original = lookup.get(expected_id)
            require(original is not None and original.get("sha256") == digest and
                    original.get("source_commit_sha") == source_sha,
                    "original native machine receipt hash/SHA mismatch")
            receipt_path = p.with_suffix(".capture.json")
            capture = json.loads(receipt_path.read_text(encoding="utf-8-sig"))
            require(capture.get("source_commit_sha") == source_sha and
                    capture.get("built_commit_sha") == source_sha and
                    capture.get("sha256") == digest and
                    capture.get("source") == _RUN_ORIGIN and
                    capture.get("screenshot_id") == expected_id and
                    capture.get("capture_status") == "candidate_pending_visual_review" and
                    capture.get("capture_verified") is False and
                    capture.get("window_fully_visible") is True and
                    (capture.get("window_width"), capture.get("window_height")) == (w, h),
                    "native receipt does not prove running Tauri screenshot")
            if expected_id.startswith("P02-T10-CTRL-"):
                require(capture.get("candidate_final_asset_id") == asset and
                        capture.get("interaction") == "actual-native-screen-or-control:keyboard" and
                        capture.get("evidence_limit") ==
                        "NOT a final manifest screenshot or independent visual approval",
                        "direct control identity/keyboard evidence missing")
            staged_png = f"docs/screenshots/{module}/{asset}.png"
            record = {
                "asset_id": asset,
                "staged_path": staged_png,
                "source_native_path": native_png,
                "source_commit_sha": source_sha,
                "original_capture_id": expected_id,
                "sha256": digest,
                "width": w, "height": h,
                "native_machine_hash_and_receipt_verified": True,
                "review_status": "PENDING_INDEPENDENT_VISUAL_AND_SCREEN_READER_REVIEW",
                "final_manifest_status": "PENDING",
                "full_screen_reader_verified": False,
                "performance_budget_approved": False,
                "hosted_wiki_verified": False,
                "protected_merge_approved": False,
            }
            archive.writestr(staged_png, image)
            archive.writestr(staged_png[:-4] + ".review-candidate.json",
                             json.dumps(record, indent=2) + "\n")
            rows.append(record)
        require(len(seen_ids) == 29 and
                sum(x["asset_id"].startswith("M02-") for x in rows) == 15 and
                sum(x["asset_id"].startswith("M19-") for x in rows) == 14,
                "module screenshot quota mismatch")
        report = {
            "schema_version": 1, "phase": "P02", "source_commit_sha": source_sha,
            "status": "STAGED_REAL_NATIVE_REVIEW_CANDIDATES_NOT_FINAL",
            "candidate_png_count": 29, "unique_png_hashes": 29,
            "m02_targets": 15, "m19_targets": 14,
            "help_reference_substitutions": 0,
            "final_manifest_verified": 0,
            "independent_full_visual_review": False,
            "full_screen_reader_verified": False,
            "performance_budget_approved": False,
            "hosted_wiki_verified": False,
            "phase_merge_verified": False,
            "items": rows,
        }
        archive.writestr("P02_NATIVE_REVIEW_INDEX.json", json.dumps(report, indent=2) + "\n")
        archive.writestr("README-P02-NATIVE-REVIEW.md", """# P02 real Windows screenshot review — NOT FINAL

This ZIP stages 29 original native Tauri PNGs at their proposed repository
screenshot paths, byte-for-byte with SHA-256 proof. These are review candidates
only: the branch manifest remains PENDING and no images are committed to Git.

Review each full-size image for correct UI/control state, clipping, labels,
contrast and focus. Verify actual app keyboard behavior and screen reader
announcements using NVDA/Narrator, Windows motion/theme states and other OS
settings; 9 UI Automation checks alone are not a full reader certification.
Record independent reviewer/source SHA and performance budget approval. The
Wiki must be published and the draft PR must satisfy protected merge gates.
Never turn machine candidate status into automatic final acceptance.
""")
    return output.getvalue(), report


def stage(root: Path, source_sha: str, output_dir: Path) -> dict:
    """Write one atomic no-overwrite ZIP only after all 29 frames have passed."""
    data, report = staged_archive(root, source_sha)
    target = output_dir / _ZIP_NAME
    output_dir.mkdir(parents=True, exist_ok=True)
    try:
        with target.open("xb") as out:
            out.write(data)
    except FileExistsError as exc:
        raise StagingError("refuse to overwrite previous native review archive") from exc
    return report


def main() -> int:
    p = argparse.ArgumentParser(description=__doc__)
    p.add_argument("--root", type=Path, default=Path("."))
    p.add_argument("--source-sha", required=True)
    p.add_argument("--out", type=Path, required=True)
    args = p.parse_args()
    try:
        report = stage(args.root, args.source_sha, args.out)
    except (StagingError, OSError, ValueError, KeyError) as exc:
        p.exit(1, "ZYN-P02-REVIEW-ZIP: " + str(exc) + "\n")
    print(json.dumps({"status": report["status"], "native_images_staged": report["candidate_png_count"],
                      "source_commit_sha": report["source_commit_sha"],
                      "final_manifest_verified": report["final_manifest_verified"]}))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())