"""Fail-closed metadata/hash gate for real P02 Tauri screenshot candidates.

This validates the Windows CI capture receipts; it does NOT certify pixel content,
accessibility semantics, or a final M02/M19 documentation screenshot manifest.
"""
from __future__ import annotations

import argparse
import hashlib
import json
from pathlib import Path
import re
import struct

SCREEN_IDS = (
    "M02-S03", "M02-OPT-07", "M02-S07", "M02-OPT-03", "M02-S05", "P02-T02-06",
    "M02-S06", "M02-S04", "M19-S01", "M19-S02", "M19-S03",
    "M19-S04", "M19-S05", "M19-S06", "M19-OPTION-REFERENCE-CI", "M19-FAQ-GLOSSARY-CI", "P02-T02-07",
    "P02-T02-07-continued", "P02-T02-12-LIGHT", "P02-T02-12-DARK",
    "M02-OPT-04", "P02-T02-OPT-04-swapped",
    "P02-T04-NO-MATCH", "P02-T04-ESCAPE", "P02-T04-ENTER-NAV",
    "P02-T03-RAIL-COLLAPSED", "P02-T03-RAIL-EXPANDED", "P02-T03-RAIL-RESTORED",
    "P02-T06-GALLERY-READY", "P02-T06-GALLERY-OFFLINE", "P02-T06-GALLERY-LOADING",
    "P02-T06-GALLERY-EMPTY", "P02-T06-GALLERY-ERROR", "P02-T05-PREFERENCES-LIVE",
    "M19-UNIFIED-OPTION-RESULTS", "M19-UNIFIED-OPTION-DEST",
    "M19-UNIFIED-ARTICLE-RESULTS", "M19-UNIFIED-ARTICLE-DEST",
)
OPTION_REFERENCE_MATRIX = tuple(
    f"{module}-T10-REF-OPT-{i:02d}"
    for module in ("M02", "M19") for i in range(1, 9)
)
SCREEN_IDS += OPTION_REFERENCE_MATRIX
_SHA = re.compile(r"^[0-9a-f]{40}$")
PNG_SIGNATURE = b"\x89PNG\r\n\x1a\n"
ORIGIN = "GitHub Windows Actions actual Tauri process"
STATUS = "candidate_pending_visual_review"


class InvalidNativeEvidence(ValueError):
    """The evidence cannot be trusted for a given source SHA."""


def _require(condition: bool, message: str) -> None:
    if not condition:
        raise InvalidNativeEvidence(message)


def _png_dimensions(png: bytes, screen_id: str) -> tuple[int, int]:
    _require(len(png) >= 33 and png[:8] == PNG_SIGNATURE, f"{screen_id}: invalid PNG signature")
    _require(png[12:16] == b"IHDR" and png[8:12] == b"\x00\x00\x00\x0d",
             f"{screen_id}: missing PNG IHDR")
    width, height = struct.unpack(">II", png[16:24])
    _require(880 <= width <= 2500 and 600 <= height <= 1600,
             f"{screen_id}: not a plausible measured native window size")
    return width, height


def validate_candidate(root: Path, screen_id: str, source_sha: str) -> dict:
    """Validate a SHA-bound machine candidate; do not infer independent visual approval."""
    _require(screen_id in SCREEN_IDS, f"Unexpected screen id: {screen_id}")
    category = "M19" if screen_id.startswith("M19-") else "M02"
    directory = root / category
    image = directory / f"{screen_id}.png"
    receipt = directory / f"{screen_id}.capture.json"
    _require(image.is_file() and receipt.is_file(), f"{screen_id}: missing PNG/capture pair")
    try:
        meta = json.loads(receipt.read_text(encoding="utf-8-sig"))
        png = image.read_bytes()
    except (OSError, UnicodeError, json.JSONDecodeError) as exc:
        raise InvalidNativeEvidence(f"{screen_id}: unreadable PNG/capture receipt") from exc
    _require(isinstance(meta, dict), f"{screen_id}: malformed metadata object")
    _require(meta.get("screenshot_id") == screen_id, f"{screen_id}: screenshot ID mismatch")
    if screen_id in OPTION_REFERENCE_MATRIX:
        expected_option = screen_id.replace("-T10-REF-OPT-", "-OPT-")
        _require(meta.get("option_id") == expected_option,
                 f"{screen_id}: captured option identity does not match expected reference")
        _require(meta.get("interaction") == "palette:exact-id:enter:option-detail",
                 f"{screen_id}: missing exact-option keyboard journey receipt")
    _require(meta.get("source_commit_sha") == source_sha, f"{screen_id}: wrong source SHA")
    _require(meta.get("built_commit_sha") == source_sha, f"{screen_id}: wrong build SHA")
    _require(meta.get("source") == ORIGIN, f"{screen_id}: wrong native capture origin")
    _require(meta.get("capture_status") == STATUS and meta.get("capture_verified") is False,
             f"{screen_id}: machine capture cannot self-approve visual review")
    _require(meta.get("window_fully_visible") is True,
             f"{screen_id}: native window not fully in desktop")
    _require(meta.get("frame_bounds_source") ==
             "DwmGetWindowAttribute DWMWA_EXTENDED_FRAME_BOUNDS (9)",
             f"{screen_id}: cannot trust window bounds")
    _require(isinstance(meta.get("alt_text"), str) and len(meta["alt_text"]) >= 25,
             f"{screen_id}: meaningful alt text missing")
    _require(meta.get("privacy") == "Disposable CI fixture with no user content or secrets",
             f"{screen_id}: native fixture privacy assertion missing")
    width, height = _png_dimensions(png, screen_id)
    _require(width == meta.get("window_width") and height == meta.get("window_height"),
             f"{screen_id}: PNG geometry does not match capture receipt")
    digest = hashlib.sha256(png).hexdigest()
    _require(digest == meta.get("sha256"), f"{screen_id}: PNG hash mismatch")
    return {"screen_id": screen_id, "width": width, "height": height,
            "sha256": digest, "metadata_sha256": hashlib.sha256(receipt.read_bytes()).hexdigest(),
            "source_commit_sha": source_sha}


def verify(root: Path, source_sha: str) -> dict:
    _require(bool(_SHA.fullmatch(source_sha)), "invalid PR source SHA")
    screens = [validate_candidate(root, name, source_sha) for name in SCREEN_IDS]
    by_id = {screen["screen_id"]: screen for screen in screens}
    wide = by_id["P02-T02-06"]
    for name in ("P02-T02-07", "P02-T02-07-continued"):
        narrow = by_id[name]
        _require(narrow["width"] < wide["width"] and narrow["width"] <= 920,
                 f"{name}: native viewport did not become narrower")
    _require(by_id["P02-T02-07"]["width"] ==
             by_id["P02-T02-07-continued"]["width"],
             "responsive continuation size changed unexpectedly")
    _require(by_id["P02-T02-07"]["sha256"] !=
             by_id["P02-T02-07-continued"]["sha256"],
             "responsive PageDown did not change view pixels")
    for name in ("P02-T02-12-LIGHT", "P02-T02-12-DARK"):
        _require(by_id[name]["width"] <= 920,
                 f"{name}: theme candidate must be captured in real native narrow frame")
    _require(by_id["P02-T02-12-LIGHT"]["sha256"] !=
             by_id["P02-T02-12-DARK"]["sha256"],
             "light/dark capture has identical pixels (theme change not demonstrated)")
    shortcut_mapping = by_id["M02-OPT-04"]
    shortcut_swapped = by_id["P02-T02-OPT-04-swapped"]
    _require(shortcut_mapping["width"] <= 920 and shortcut_swapped["width"] <= 920,
             "shortcut mapping candidates must be real native narrow window captures")
    _require(shortcut_mapping["sha256"] != shortcut_swapped["sha256"],
             "shortcut remap preview did not visibly change the capture")
    _require(by_id["P02-T04-NO-MATCH"]["sha256"] !=
             by_id["P02-T04-ESCAPE"]["sha256"],
             "Escape failed to visibly dismiss the command palette")
    _require(by_id["P02-T04-ENTER-NAV"]["sha256"] !=
             by_id["M19-S01"]["sha256"],
             "Enter command did not visibly navigate away from Help")
    for result_id, dest_id in (
        ("M19-UNIFIED-OPTION-RESULTS", "M19-UNIFIED-OPTION-DEST"),
        ("M19-UNIFIED-ARTICLE-RESULTS", "M19-UNIFIED-ARTICLE-DEST"),
    ):
        _require(by_id[result_id]["sha256"] != by_id[dest_id]["sha256"],
                 "Unified search Enter failed to change the native frame: " + dest_id)
    _require(by_id["M19-UNIFIED-OPTION-DEST"]["sha256"] !=
             by_id["M19-UNIFIED-ARTICLE-DEST"]["sha256"],
             "Option and article selections must open visually distinct Help destinations")
    gallery_ids = ("P02-T06-GALLERY-READY", "P02-T06-GALLERY-LOADING",
                   "P02-T06-GALLERY-EMPTY", "P02-T06-GALLERY-ERROR",
                   "P02-T06-GALLERY-OFFLINE")
    _require(len({by_id[name]["sha256"] for name in gallery_ids}) == 5,
             "T06 Gallery five states must produce distinct real native frames")
    _require(by_id["P02-T06-GALLERY-OFFLINE"]["sha256"] !=
             by_id["P02-T05-PREFERENCES-LIVE"]["sha256"],
             "T05 Preferences candidate did not navigate away from Gallery")
    _require(by_id["M19-S01"]["sha256"] !=
             by_id["M19-OPTION-REFERENCE-CI"]["sha256"],
             "M19 option reference must differ from the initial Help landing screen")
    _require(by_id["M19-OPTION-REFERENCE-CI"]["sha256"] !=
             by_id["M19-FAQ-GLOSSARY-CI"]["sha256"],
             "M19 FAQ must visually differ from the option directory")
    help_states = ("M19-S01", "M19-S04", "M19-S05", "M19-S06",
                   "M19-S02", "M19-S03")
    _require(all(by_id[a]["sha256"] != by_id[b]["sha256"]
                 for a, b in zip(help_states, help_states[1:])),
             "M19 real Help keyboard transitions did not change native pixels")
    rail_ids = ("P02-T03-RAIL-COLLAPSED", "P02-T03-RAIL-EXPANDED",
                "P02-T03-RAIL-RESTORED")
    rail = [by_id[name] for name in rail_ids]
    _require(all(item["width"] <= 920 for item in rail),
             "T03 navigation rail proof must come from native narrow window")
    _require(len({(item["width"], item["height"]) for item in rail}) == 1,
             "T03 rail frames must share identical measured native geometry")
    _require(rail[0]["sha256"] != rail[1]["sha256"] and
             rail[1]["sha256"] != rail[2]["sha256"],
             "T03 rail toggle must visibly change expanded/collapsed screenshots")
    option_matrix = [by_id[screen_id] for screen_id in OPTION_REFERENCE_MATRIX]
    _require(len({item["sha256"] for item in option_matrix}) == 16,
             "T10 option reference matrix contains duplicate captured pixels")
    _require(all(item["width"] == by_id["M19-UNIFIED-OPTION-DEST"]["width"]
                 and item["height"] == by_id["M19-UNIFIED-OPTION-DEST"]["height"]
                 for item in option_matrix),
             "T10 option reference frames must match measured wide native viewport")
    return {"schema_version": 1,
            "option_reference_matrix": {
                "count": len(option_matrix),
                "ids": list(OPTION_REFERENCE_MATRIX),
                "status": "MACHINE_REFERENCE_CAPTURE_ONLY",
                "final_29_manifest_assets_verified": False,
            },
            "status": "MACHINE_METADATA_HASH_VALIDATED_ONLY",
            "source_commit_sha": source_sha,
            "screens": screens,
            "independent_visual_review": False,
            "manifest_completed": False}


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--root", type=Path, required=True)
    parser.add_argument("--source-sha", required=True)
    parser.add_argument("--report", type=Path, required=True)
    args = parser.parse_args(argv)
    try:
        report = verify(args.root, args.source_sha)
    except InvalidNativeEvidence as exc:
        parser.exit(1, f"ZYN-SCREEN-030: {exc}\n")
    args.report.parent.mkdir(parents=True, exist_ok=True)
    args.report.write_text(json.dumps(report, indent=2, sort_keys=True) + "\n",
                           encoding="utf-8")
    print(json.dumps({"status": report["status"], "screens": len(report["screens"]),
                      "source_sha": report["source_commit_sha"]}))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
