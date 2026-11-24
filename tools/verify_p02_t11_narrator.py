"""Verify actual Microsoft Narrator phrase-copy receipts, not UIA labels."""
import argparse
import json
from pathlib import Path
import re

class InvalidNarratorProof(ValueError):
    pass

EXPECTED = {"preferences": "interface appearance", "palette": "search available commands and offline help", "help": "wiki mapping and link checker"}

def verify(proof, head, run_id):
    def need(ok, why):
        if not ok:
            raise InvalidNarratorProof(why)
    need(isinstance(proof, dict) and proof.get("schema_version") == 1 and proof.get("status") == "CAPTURED", "incomplete speech receipt")
    need(bool(re.fullmatch(r"[a-f0-9]{40}", head)) and proof.get("source_commit_sha") == head, "stale source SHA")
    need(proof.get("binary_source_commit_sha") == head and proof.get("diagnostic_artifact_reuse") is False, "diagnostic or stale binary cannot pass exact-head acceptance")
    need(run_id.isdigit() and proof.get("github_run_id") == run_id, "wrong CI run")
    need(proof.get("target") == "Real Microsoft Narrator speech copied from native Windows Tauri WebView2", "wrong assistive technology")
    for key in ("app_executable_sha256", "narrator_executable_sha256"):
        need(bool(re.fullmatch(r"[a-f0-9]{64}", proof.get(key, ""))), "native executable identity missing")
    need(proof.get("narrator_signature_verified") is True and isinstance(proof.get("narrator_version"), str) and bool(proof["narrator_version"]), "Microsoft signature not verified")
    for key in ("app_pid", "narrator_pid"):
        need(type(proof.get(key)) is int and proof[key] > 0, "live process missing")
    need(proof["app_pid"] != proof["narrator_pid"] and proof.get("native_uia_pid_match") is True, "native app PID mismatch")
    need(proof.get("actual_keyboard_input_value") == "M19-OPT-06", "keyboard journey missing")
    need(proof.get("no_user_data") is True and proof.get("full_narrator_certified") is False and proof.get("product_release_approved") is False, "unsafe data or unsupported product claim")
    events = proof.get("events")
    need(isinstance(events, list) and len(events) == 3, "three actual Narrator speech stages required")
    last_sequence = -1
    for stage, event in zip(EXPECTED, events):
        need(isinstance(event, dict) and event.get("stage") == stage, "missing/replayed stage")
        label = event.get("label")
        need(isinstance(label, str) and 1 <= len(label) <= 150 and EXPECTED[stage] in label.casefold(), "required spoken phrase missing")
        before, after = event.get("clipboard_sequence_before"), event.get("clipboard_sequence_after")
        need(type(before) is int and type(after) is int and last_sequence < before < after and event.get("actual_speech_clipboard_changed") is True, "stale or replayed clipboard")
        last_sequence = after
    return {"schema_version": 1, "status": "SCOPED_LIVE_MICROSOFT_NARRATOR_SPEECH_PASS", "source_commit_sha": head, "github_run_id": run_id, "narrator_live_spoken_journeys": 3, "full_narrator_certified": False, "product_release_approved": False, "protected_merge_verified": False}

def main():
    a = argparse.ArgumentParser()
    a.add_argument("--proof", type=Path, required=True)
    a.add_argument("--source-sha", required=True)
    a.add_argument("--run-id", required=True)
    a.add_argument("--report", type=Path, required=True)
    args = a.parse_args()
    try:
        result = verify(json.loads(args.proof.read_text(encoding="utf-8-sig")), args.source_sha, args.run_id)
    except (OSError, ValueError, TypeError) as exc:
        a.exit(1, "ZYN-NAR-020: " + str(exc) + "\n")
    args.report.parent.mkdir(parents=True, exist_ok=True)
    args.report.write_text(json.dumps(result, indent=2) + "\n", encoding="utf-8")
    print(json.dumps(result, sort_keys=True))

if __name__ == "__main__":
    main()
