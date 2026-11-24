"""M26 native candidate evidence only; never a visual or screen-reader approval."""
from __future__ import annotations
import argparse
import hashlib
import json
from pathlib import Path
import re

from tools.verify_p02_native_evidence import _png_dimensions, ORIGIN, STATUS

EXPECTED_TRANSITIONS = (
    ("What\x27s New", "{RIGHT}", "Known Issues"),
    ("Known Issues", "{RIGHT}", "Version History"),
    ("Version History", "{RIGHT}", "Module Changes"),
    ("Module Changes", "{RIGHT}", "Audit Timeline"),
    ("Audit Timeline", "{RIGHT}", "Notifications"),
    ("Notifications", "{END}", "Migration Notes"),
    ("Migration Notes", "{HOME}", "What\x27s New"),
)

EXPECTED = {
    "M26-CAND-S01": "No verified releases",
    "M26-CAND-S02": "Select a capability notice",
    "M26-CAND-SEARCH-EMPTY": "No matching notices. Reset filters to view all.",
    "M26-CAND-S04": "Not a released fix or live issue status.",
    "M26-CAND-S03": "No verified versions",
    "M26-CAND-S05": "Select a capability notice",
    "M26-CAND-S06": "Audit access is not enabled",
    "M26-CAND-S07": "Notification settings unavailable",
    "M26-CAND-S08": "No verified migration notes",
    "M26-CAND-HELP": "Changelog and release history",
}


def require(condition, message):
    if not condition:
        raise ValueError(message)


MODULE_TITLES = ["Backup and restore not available", "Data relocation not available",
                 "Signed updates not available", "Live change and release data not available"]


def verify_module_filter(proof) -> None:
    require(isinstance(proof, dict), "missing native module filter evidence")
    require(proof.get("initial_value") == "All modules" and proof.get("initial_titles") == MODULE_TITLES,
            "wrong initial native notice inventory")
    require(proof.get("selected_value") == "M23" and proof.get("filtered_titles") == MODULE_TITLES[:1],
            "wrong actual filtered inventory")
    require(proof.get("keyboard_method") in ("collapsed_keyboard", "expanded_keyboard"),
            "missing real module keyboard selection")
    require(proof.get("reset_value") == "All modules" and proof.get("reset_titles") == MODULE_TITLES,
            "wrong native reset inventory")


def verify(root: Path, source_sha: str, run_id: str) -> None:
    require(bool(re.fullmatch(r"[a-f0-9]{40}", source_sha)), "invalid source SHA")
    require(bool(re.fullmatch(r"[1-9][0-9]*", run_id)), "invalid run ID")
    proof = json.loads((root / "M26-journey.capture.json").read_text(encoding="utf-8-sig"))
    require(proof.get("schema_version") == 1 and proof.get("source_commit_sha") == source_sha
            and proof.get("built_commit_sha") == source_sha
            and proof.get("github_run_id") == run_id, "wrong native journey identity")
    require(type(proof.get("native_process_id")) is int and proof["native_process_id"] > 0
            and proof.get("no_user_data") is True, "missing native process or fixture identity")
    require(proof.get("status") == "M26_NATIVE_CANDIDATES_ONLY"
            and proof.get("independent_visual_review") is False
            and proof.get("screen_reader_verified") is False, "false acceptance claim")
    transitions = proof.get("tab_transitions")
    require(isinstance(transitions, list) and len(transitions) == len(EXPECTED_TRANSITIONS),
            "missing native keyboard transitions")
    for item, expected in zip(transitions, EXPECTED_TRANSITIONS):
        require(isinstance(item, dict) and (item.get("from"), item.get("key"), item.get("to")) == expected,
                "wrong native keyboard transition")
        require(all(item.get(key) is True for key in (
            "source_focus_and_selection", "destination_focus_and_selection", "previous_tab_deselected")),
            "native selected-tab/focus proof absent")
    verify_module_filter(proof.get("module_filter"))
    observations = proof.get("observations")
    require(isinstance(observations, list) and len(observations) == len(EXPECTED),
            "missing native journey observations")
    require([item.get("screenshot_id") for item in observations] == list(EXPECTED),
            "wrong journey order or duplicate candidate")
    hashes = set()
    for item in observations:
        key = item["screenshot_id"]
        require(item.get("actual_visible_uia_name") == EXPECTED[key]
                and item.get("foreground_window_verified") is True, key + ": UIA check absent")
        png = (root / (key + ".png")).read_bytes()
        meta = json.loads((root / (key + ".capture.json")).read_text(encoding="utf-8-sig"))
        require(meta.get("screenshot_id") == key and meta.get("screen") == EXPECTED[key]
                and meta.get("source_commit_sha") == source_sha
                and meta.get("built_commit_sha") == source_sha, key + ": wrong capture identity")
        require(meta.get("source") == ORIGIN and meta.get("capture_status") == STATUS
                and meta.get("capture_verified") is False
                and meta.get("window_fully_visible") is True
                and meta.get("frame_bounds_source") == "DwmGetWindowAttribute DWMWA_EXTENDED_FRAME_BOUNDS (9)"
                and meta.get("privacy") == "Disposable CI fixture with no user content or secrets",
                key + ": invalid native capture provenance")
        require(isinstance(meta.get("alt_text"), str) and len(meta["alt_text"]) >= 25,
                key + ": missing meaningful description")
        require(_png_dimensions(png, key) == (meta.get("window_width"), meta.get("window_height")),
                key + ": wrong geometry")
        digest = hashlib.sha256(png).hexdigest()
        require(meta.get("sha256") == digest and digest not in hashes,
                key + ": mismatched or repeated image")
        hashes.add(digest)


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--root", type=Path, required=True)
    parser.add_argument("--source-sha", required=True)
    parser.add_argument("--run-id", required=True)
    args = parser.parse_args()
    verify(args.root, args.source_sha, args.run_id)
    print("M26: 10 source-bound native candidates; independent visual/speech acceptance pending")


if __name__ == "__main__":
    main()
