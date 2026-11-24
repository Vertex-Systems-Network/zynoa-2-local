"""Verify *real NVDA speech* recorded during Windows Tauri keyboard interaction."""
import argparse
import json
from pathlib import Path
import re
class InvalidNvdaProof(ValueError): pass

def verify(p, head):
    def need(ok, why):
        if not ok: raise InvalidNvdaProof(why)
    need(bool(re.fullmatch(r"[a-f0-9]{40}", head)), "invalid exact source SHA")
    need(isinstance(p, dict) and p.get("schema_version") == 1, "invalid schema")
    need(p.get("source_commit_sha") == head, "different source SHA")
    need(bool(re.fullmatch(r"[a-f0-9]{64}",p.get("app_executable_sha256",""))), "missing executable identity")
    need(p.get("official_nvda_installer_sha256") == "6f80a5b0ca720a7d0d314b5be212f37388bbe81a1107ac3298c1821a1cd3f052", "untrusted NVDA installer")
    need(p.get("nvda_version") == "2026.3.1", "wrong NVDA version")
    need(p.get("target") == "Real Windows Tauri WebView2 with live NVDA pre_synthSpeak", "not a screen reader integration")
    need(str(p.get("github_run_id","")).isdigit(), "CI identity missing")
    need(type(p.get("app_pid")) is int and p["app_pid"] > 0 and type(p.get("nvda_pid")) is int and p["nvda_pid"] > 0 and p["app_pid"] != p["nvda_pid"], "native processes missing")
    need(p.get("native_uia_pid_match") is True and p.get("actual_keyboard_input_value") == "M19-OPT-06", "missing actual native keyboard journey")
    need(p.get("plugin_loaded") is True and p.get("no_user_data") is True, "no NVDA plugin or unsafe data")
    need(p.get("full_narrator_verified") is False and p.get("performance_budget_approved") is False, "false release claim")
    events=p.get("events")
    need(isinstance(events,list) and 3 <= len(events) <= 120, "NVDA speech events missing")
    texts=[]
    for e in events:
        need(isinstance(e,dict) and e.get("kind") == "speech" and type(e.get("unix_ms")) is int and e["unix_ms"] > 0, "speech provenance invalid")
        need(e.get("stage") in ("preferences", "palette", "help"), "unattributed NVDA speech event")
        label=e.get("label")
        need(isinstance(label,str) and 1 <= len(label) <= 280, "missing speech text")
        texts.append(label.lower())
    # Genuine synthesized speech from three separate app journeys, not UIA names.
    need(any(e["stage"] == "preferences" and ("preferences" in e["label"].lower() or "interface appearance" in e["label"].lower()) for e in events), "NVDA did not announce Preferences during actual preferences stage")
    need(any(e["stage"] == "palette" and ("command palette" in e["label"].lower() or "search available commands" in e["label"].lower()) for e in events), "NVDA did not announce the palette during actual keyboard stage")
    need(any(e["stage"] == "help" and "wiki mapping and link checker" in e["label"].lower() for e in events), "NVDA did not announce selected option during Help stage")
    return {"schema_version":1, "status":"SCOPED_LIVE_NVDA_SPEECH_PASS", "source_commit_sha":head, "github_run_id":p["github_run_id"], "screen_reader":"NVDA 2026.3.1", "spoken_evidence_events":len(texts), "native_keyboard_journey_verified":True, "narrator_verified":False, "full_product_release_approved":False}

def main():
    a=argparse.ArgumentParser()
    a.add_argument("--proof",type=Path,required=True)
    a.add_argument("--source-sha",required=True)
    a.add_argument("--report",type=Path,required=True)
    args=a.parse_args()
    try: result=verify(json.loads(args.proof.read_text(encoding="utf-8-sig")), args.source_sha)
    except (OSError,ValueError,InvalidNvdaProof) as exc: a.exit(1,"ZYN-NVDA-020: "+str(exc)+"\n")
    args.report.parent.mkdir(parents=True,exist_ok=True)
    args.report.write_text(json.dumps(result,indent=2)+"\n",encoding="utf-8")
    print(json.dumps(result,sort_keys=True))
if __name__ == "__main__": main()
