"""Verify actual Microsoft Narrator phrase-copy receipts, not UIA labels."""
import argparse
import json
from pathlib import Path
import re

class InvalidNarratorProof(ValueError):
    pass

EXPECTED = {"preferences": "interface appearance", "palette": "search available commands and offline help", "palette_result": "wiki mapping and link checker", "help": "wiki mapping and link checker"}

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
    need(proof.get("actual_no_match_keyboard_input_value") == "zynoa-no-match-7f6c" and proof.get("actual_no_match_result_verified") is True, "real empty-result keyboard journey missing")
    need(proof.get("no_user_data") is True and proof.get("full_narrator_certified") is False and proof.get("product_release_approved") is False, "unsafe data or unsupported product claim")
    events = proof.get("events")
    need(isinstance(events, list) and len(events) == 4, "four actual Narrator speech stages required")
    last_sequence = -1
    for stage, event in zip(EXPECTED, events):
        need(isinstance(event, dict) and event.get("stage") == stage, "missing/replayed stage")
        label = event.get("label")
        need(isinstance(label, str) and 1 <= len(label) <= 150 and EXPECTED[stage] in label.casefold(), "required spoken phrase missing")
        before, after = event.get("clipboard_sequence_before"), event.get("clipboard_sequence_after")
        need(type(before) is int and type(after) is int and last_sequence < before < after and event.get("actual_speech_clipboard_changed") is True, "stale or replayed clipboard")
        last_sequence = after
    return {"schema_version": 1, "status": "SCOPED_LIVE_MICROSOFT_NARRATOR_SPEECH_PASS", "source_commit_sha": head, "github_run_id": run_id, "narrator_live_spoken_journeys": 3, "narrator_live_spoken_stages": 4, "full_narrator_certified": False, "product_release_approved": False, "protected_merge_verified": False}

M26_EXPECTED = {"m26_entry":"changelog","m26_tab":"known issues","m26_search":"search bundled notices",
                "m26_empty":"no matching notices","m26_help":"changelog and release history"}

def verify_m26(proof, head, run_id, executable_sha256):
    def need(ok, why):
        if not ok:
            raise InvalidNarratorProof(why)
    need(isinstance(proof,dict) and proof.get("schema_version")==1 and proof.get("status")=="CAPTURED", "incomplete M26 speech receipt")
    need(bool(re.fullmatch(r"[a-f0-9]{40}",head)) and proof.get("source_commit_sha")==head
         and proof.get("binary_source_commit_sha")==head and proof.get("diagnostic_artifact_reuse") is False, "wrong M26 source/binary identity")
    need(bool(re.fullmatch(r"[1-9][0-9]*",run_id)) and proof.get("github_run_id")==run_id, "wrong M26 run")
    need(bool(re.fullmatch(r"[a-f0-9]{64}",executable_sha256)) and proof.get("app_executable_sha256")==executable_sha256
         and bool(re.fullmatch(r"[a-f0-9]{64}",proof.get("narrator_executable_sha256",""))), "wrong M26 executable")
    need(proof.get("target")=="Real Microsoft Narrator speech copied from native Windows Tauri WebView2 M26"
         and proof.get("narrator_signature_verified") is True and isinstance(proof.get("narrator_version"),str)
         and bool(proof["narrator_version"]), "untrusted Microsoft Narrator")
    need(all(type(proof.get(k)) is int and proof[k]>0 for k in ("app_pid","narrator_pid"))
         and proof["app_pid"]!=proof["narrator_pid"], "missing real native processes")
    need(all(proof.get(k) is True for k in ("native_uia_pid_match","actual_tab_keyboard_focus","actual_previous_tab_deselected",
         "actual_search_keyboard_focus","actual_no_match_result_verified","actual_contextual_help_verified","no_user_data")), "M26 native keyboard evidence absent")
    need(proof.get("actual_selected_tab")=="Known Issues" and proof.get("actual_keyboard_input_value")=="zzznomatch"
         and proof.get("actual_no_match_keyboard_input_value")=="zzznomatch", "wrong actual native tab/query")
    need(proof.get("full_narrator_certified") is False and proof.get("product_release_approved") is False, "false release claim")
    events=proof.get("events")
    need(isinstance(events,list) and len(events)==len(M26_EXPECTED), "five actual M26 speech stages required")
    previous=-1
    for stage,event in zip(M26_EXPECTED,events):
        need(isinstance(event,dict) and event.get("stage")==stage, "replayed or missing M26 stage")
        label=event.get("label")
        need(isinstance(label,str) and 1<=len(label)<=150 and M26_EXPECTED[stage] in label.casefold(), "actual M26 spoken phrase absent")
        before,after=event.get("clipboard_sequence_before"),event.get("clipboard_sequence_after")
        need(type(before) is int and type(after) is int and previous<before<after
             and event.get("actual_speech_clipboard_changed") is True, "stale M26 clipboard")
        previous=after
    return {"schema_version":1,"status":"SCOPED_M26_LIVE_NARRATOR_PASS","source_commit_sha":head,"github_run_id":run_id,
            "app_executable_sha256":executable_sha256,"spoken_stages":len(events),"full_narrator_certified":False,
            "product_release_approved":False}

def main():
    a = argparse.ArgumentParser()
    a.add_argument("--proof", type=Path, required=True)
    a.add_argument("--source-sha", required=True)
    a.add_argument("--run-id", required=True)
    a.add_argument("--report", type=Path, required=True)
    a.add_argument("--m26", action="store_true")
    a.add_argument("--executable-sha256")
    args = a.parse_args()
    try:
        proof=json.loads(args.proof.read_text(encoding="utf-8-sig"))
        if args.m26:
            if not args.executable_sha256: raise InvalidNarratorProof("M26 exact executable required")
            result=verify_m26(proof,args.source_sha,args.run_id,args.executable_sha256)
        else:
            result=verify(proof,args.source_sha,args.run_id)
    except (OSError, ValueError, TypeError) as exc:
        a.exit(1, "ZYN-NAR-020: " + str(exc) + "\n")
    args.report.parent.mkdir(parents=True, exist_ok=True)
    args.report.write_text(json.dumps(result, indent=2) + "\n", encoding="utf-8")
    print(json.dumps(result, sort_keys=True))

if __name__ == "__main__":
    main()
