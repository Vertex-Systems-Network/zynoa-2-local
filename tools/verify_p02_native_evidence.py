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
    "M02-S03", "M02-OPT-07", "M02-S05", "P02-T02-06",
    "M02-S06", "M02-S04", "M19-S01", "P02-T02-07",
    "P02-T02-07-continued",
)
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
    return {"schema_version": 1,
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
