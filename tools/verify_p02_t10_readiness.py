"""P02-T10 fail-closed screenshot/Help reference readiness audit.

Candidate screenshots from a native Windows run never imply completion of the
29 required finalized M02/M19 screen+option PNGs or screen-reader approval.
"""
from __future__ import annotations

import argparse
import json
import re
from pathlib import Path

from tools.verify_p02_native_evidence import OPTION_REFERENCE_MATRIX, DIRECT_CONTROL_MATRIX, SCREEN_IDS

_SHA = re.compile(r"^[a-f0-9]{40}$")
EXPECTED = {
    *(f"M02-S{i:02d}" for i in range(1, 8)),
    *(f"M02-OPT-{i:02d}" for i in range(1, 9)),
    *(f"M19-S{i:02d}" for i in range(1, 7)),
    *(f"M19-OPT-{i:02d}" for i in range(1, 9)),
}


class InvalidT10Readiness(ValueError):
    """Missing/mismatched native evidence or deceptive acceptance state."""


def _need(condition: bool, message: str) -> None:
    if not condition:
        raise InvalidT10Readiness(message)


def _load(path: Path) -> dict:
    try:
        payload = json.loads(path.read_text(encoding="utf-8-sig"))
    except (OSError, ValueError, UnicodeError) as exc:
        raise InvalidT10Readiness("missing or invalid proof: " + path.name) from exc
    _need(isinstance(payload, dict), path.name + ": evidence must be an object")
    return payload


def audit(root: Path, source_sha: str) -> dict:
    _need(bool(_SHA.fullmatch(source_sha)), "invalid exact source SHA")
    manifest = _load(root / "docs/screenshots/MANIFEST.json")
    entries = [row for row in manifest.get("required", [])
               if row.get("module") in ("M02", "M19")]
    ids = [row.get("asset_id") for row in entries]
    _need(len(entries) == 29 and set(ids) == EXPECTED and len(set(ids)) == 29,
          "P02 required 29 screenshot IDs absent, duplicated or altered")
    for row in entries:
        asset = row["asset_id"]
        expected_path = f"docs/screenshots/{row['module']}/{asset}.png"
        _need(row.get("path") == expected_path, asset + ": unexpected final screenshot path")
        _need(row.get("status") in ("PENDING", "VERIFIED"),
              asset + ": invalid screenshot status")
        if row["status"] == "VERIFIED":
            _need((root / expected_path).is_file(),
                  asset + ": verified claim has no committed final PNG")
    machine = _load(root / "docs/screenshots/_ci/M02/P02-native-machine-review.json")
    _need(machine.get("source_commit_sha") == source_sha,
          "machine review source SHA differs from exact desktop build")
    _need(machine.get("status") == "MACHINE_METADATA_HASH_VALIDATED_ONLY"
          and machine.get("independent_visual_review") is False
          and machine.get("manifest_completed") is False,
          "machine report may not claim final independent review")
    validated = machine.get("screens", [])
    captured_ids = [x.get("screen_id") for x in validated if isinstance(x, dict)]
    _need(len(validated) == len(SCREEN_IDS) and set(captured_ids) == set(SCREEN_IDS)
          and len(set(captured_ids)) == len(SCREEN_IDS),
          "machine proof must include all expected real native candidate IDs")
    matrix = machine.get("option_reference_matrix", {})
    _need(matrix.get("status") == "MACHINE_REFERENCE_CAPTURE_ONLY"
          and matrix.get("count") == 16
          and matrix.get("ids") == list(OPTION_REFERENCE_MATRIX)
          and matrix.get("final_29_manifest_assets_verified") is False,
          "16-option reference matrix cannot claim actual controls are complete")
    controls = machine.get("actual_screen_control_candidates", {})
    _need(controls.get("status") == "MACHINE_CONTROL_CAPTURE_ONLY"
          and controls.get("count") == len(DIRECT_CONTROL_MATRIX)
          and controls.get("ids") == list(DIRECT_CONTROL_MATRIX)
          and controls.get("final_29_manifest_assets_verified") is False,
          "15-direct-control capture matrix cannot claim final manifest acceptance")
    perf = _load(root / "docs/screenshots/_ci/M02/P02-native-performance.json")
    _need(perf.get("source_commit_sha") == source_sha
          and perf.get("schema_version") == 1
          and perf.get("performance_budget_approved") is False
          and perf.get("no_user_data") is True,
          "performance sample missing provenance or falsely approved")
    for key in ("startup_local_metadata_ready_ms", "native_screenshot_suite_ms"):
        value = perf.get(key)
        _need(type(value) is int and 0 < value < 2700000,
              key + ": invalid native sample duration")
    finalized = sum(row["status"] == "VERIFIED" and
                    (root / row["path"]).is_file() for row in entries)
    missing = [row["asset_id"] for row in entries
               if row["status"] != "VERIFIED" or not (root / row["path"]).is_file()]
    return {
        "schema_version": 1,
        "phase": "P02",
        "source_commit_sha": source_sha,
        "status": "NOT_READY",
        "candidate_total": len(validated),
        "native_option_references_captured": 16,
        "native_direct_control_candidates": len(DIRECT_CONTROL_MATRIX),
        "native_total_candidate_frames": len(validated),
        "final_manifest_expected": 29,
        "final_manifest_verified": finalized,
        "pending_final_assets": missing,
        "independent_full_visual_review": False,
        "screen_reader_approved": False,
        "performance_budget_approved": False,
        "note": "69 source-bound native candidate frames (including 15 direct control captures and 16 separate Help references); final 29 app screenshots, independent visual/a11y and performance budgets not approved.",
    }


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--root", type=Path, default=Path("."))
    parser.add_argument("--source-sha", required=True)
    parser.add_argument("--report", type=Path)
    args = parser.parse_args(argv)
    try:
        result = audit(args.root, args.source_sha)
    except (InvalidT10Readiness, OSError, KeyError, ValueError) as exc:
        parser.exit(1, "ZYN-P02-T10-001: " + str(exc) + "\n")
    if args.report:
        args.report.parent.mkdir(parents=True, exist_ok=True)
        args.report.write_text(json.dumps(result, indent=2, sort_keys=True) + "\n",
                               encoding="utf-8")
    print(json.dumps({"status": result["status"],
                      "candidates": result["candidate_total"],
                      "option_references": result["native_option_references_captured"],
                      "final_verified": result["final_manifest_verified"]}))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
