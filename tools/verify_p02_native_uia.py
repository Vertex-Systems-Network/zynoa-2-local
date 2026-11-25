"""Fail-closed audit of live Windows Tauri UIA evidence, not screen-reader certification."""
from __future__ import annotations
import argparse
import json
import re
from pathlib import Path

EXPECTED = frozenset({
    "Interface appearance",
    "Navigation density",
    "modal_named",
    "search_input_named",
    "keyboard_focus_enters_modal_search",
    "keyboard_query_filters_to_exact_option",
    "enter_opens_exact_option_help",
    "modal_reopens_after_help_navigation",
    "escape_dismisses_modal",
})
_SHA = re.compile(r"^[0-9a-f]{40}$")


class InvalidUIAEvidence(ValueError):
    pass


def verify(proof: dict, source_sha: str) -> dict:
    if not _SHA.fullmatch(source_sha):
        raise InvalidUIAEvidence("invalid exact source SHA")
    if not isinstance(proof, dict):
        raise InvalidUIAEvidence("UIA evidence must be an object")
    if proof.get("source_commit_sha") != source_sha:
        raise InvalidUIAEvidence("UIA evidence source SHA mismatch")
    if proof.get("schema_version") != 1 or proof.get("module") != "M02":
        raise InvalidUIAEvidence("UIA evidence version/module mismatch")
    if proof.get("target") != "Real Windows Tauri WebView2 UI Automation HWND":
        raise InvalidUIAEvidence("UIA evidence must derive from native Windows Tauri")
    if proof.get("native_pid_matched") is not True or proof.get("no_user_data") is not True:
        raise InvalidUIAEvidence("UIA provider origin or privacy not established")
    if proof.get("status") != "SCOPED_NATIVE_UIA_PASS":
        raise InvalidUIAEvidence("native UIA probe failed or was not run")
    if any(proof.get(flag) is not False for flag in (
        "full_screen_reader_verified", "all_option_controls_verified",
        "final_screenshot_manifest_verified",
    )):
        raise InvalidUIAEvidence("scope boundary falsely claims full accessibility signoff")
    results = proof.get("results")
    if not isinstance(results, dict) or set(results) != EXPECTED or any(
        results.get(key) is not True for key in EXPECTED
    ):
        raise InvalidUIAEvidence("missing native accessible names, functional keyboard search/Enter navigation or Escape")
    # Provider-reported focus may land on the combobox active descendant.
    # The only acceptable substitute is actual typed text in the named
    # input's own native ValuePattern, not a synthetic UIA focus flag.
    diagnostics = proof.get("diagnostics")
    focus = diagnostics.get("search_focus") if isinstance(diagnostics, dict) else None
    if not isinstance(focus, dict) or (
        focus.get("method") != "real_keyboard_text_and_input_ValuePattern"
        or focus.get("exact_local_probe_id") != "M19-OPT-06"
        or focus.get("query_reflected_by_input_provider") is not True
    ):
        raise InvalidUIAEvidence("real keyboard input ValuePattern evidence absent or inconsistent")
    if proof.get("issues") != []:
        raise InvalidUIAEvidence("native accessibility issues remain")
    duration = proof.get("duration_ms")
    if type(duration) is not int or not 0 < duration < 120000:
        raise InvalidUIAEvidence("UIA elapsed duration invalid")
    return {
        "status": "SCOPED_NATIVE_UIA_PASS",
        "source_commit_sha": source_sha,
        "native_aria_checks": len(EXPECTED),
        "native_keyboard_journey_verified": True,
        "full_screen_reader_verified": False,
        "final_screenshot_manifest_verified": False,
    }


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--source-sha", required=True)
    parser.add_argument("--proof", type=Path, required=True)
    parser.add_argument("--report", type=Path, required=True)
    args = parser.parse_args(argv)
    try:
        raw = json.loads(args.proof.read_text(encoding="utf-8-sig"))
        result = verify(raw, args.source_sha)
    except (OSError, ValueError, UnicodeError, InvalidUIAEvidence) as exc:
        parser.exit(1, "ZYN-A11Y-006: " + str(exc) + "\n")
    args.report.parent.mkdir(parents=True, exist_ok=True)
    args.report.write_text(json.dumps(result, sort_keys=True, indent=2) + "\n",
                           encoding="utf-8")
    print(json.dumps(result, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
