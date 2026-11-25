"""Exact real native P02 option candidates, not full-module approval."""
from __future__ import annotations
import argparse
import hashlib
import json
from pathlib import Path
import re
from tools.verify_p02_native_evidence import _png_dimensions, ORIGIN, STATUS
from tools.verify_p02_m26_candidates import EXPECTED_TRANSITIONS, MODULE_TITLES, verify as verify_screens

EXPECTED = {
    "M26-OPT-01": ("Filter release channel or version", "disabled", "Filter release channel or version unavailable"),
    "M26-OPT-02": ("Module", "active", "Module"),
    "M26-OPT-03": ("Filter change category", "disabled", "Filter change category unavailable"),
    "M26-OPT-04": ("View technical details", "disabled", "View technical details unavailable"),
    "M26-OPT-05": ("Search bundled notices", "active", "Search bundled notices"),
    "M26-OPT-06": ("Open linked issue", "disabled", "Open linked issue unavailable"),
    "M26-OPT-07": ("Open linked pull request", "disabled", "Open linked pull request unavailable"),
    "M26-OPT-08": ("M26-OPT-08 — View documentation changes", "active", "M26-OPT-08 — View documentation changes"),
    "M26-OPT-09": ("No verified releases", "boundary", "No verified releases"),
    "M26-OPT-10": ("Live change and release data not available", "active", "Live change and release data not available"),
    "M26-OPT-11": ("View fixed problems", "disabled", "View fixed problems unavailable"),
    "M26-OPT-12": ("Module Changes", "active", "Module Changes"),
    "M26-OPT-13": ("Enable What's New notifications", "disabled", "Enable What's New notifications unavailable"),
    "M26-OPT-14": ("View migration notes", "disabled", "View migration notes unavailable"),
    "M26-OPT-15": ("Audit access is not enabled", "boundary", "Audit access is not enabled"),
    "M26-OPT-16": ("Export change history", "disabled", "Export change history unavailable"),
    "M26-OPT-17": ("Compare versions", "disabled", "Compare versions unavailable"),
    "M26-OPT-18": ("View rollback guidance", "disabled", "View rollback guidance unavailable"),
    "M26-OPT-19": ("Configure unread marker", "disabled", "Configure unread marker unavailable"),
    "M26-OPT-20": ("Report problem from change", "disabled", "Report problem from change unavailable"),
}

def need(condition, message):
    if not condition:
        raise ValueError(message)

def verify_receipt(proof, source_sha, run_id):
    need(bool(re.fullmatch(r"[a-f0-9]{40}", source_sha)) and bool(re.fullmatch(r"[1-9][0-9]*", run_id)), "invalid identity")
    need(isinstance(proof, dict) and proof.get("schema_version") == 1 and proof.get("source_commit_sha") == source_sha
         and proof.get("built_commit_sha") == source_sha and proof.get("github_run_id") == run_id, "wrong option journey identity")
    need(type(proof.get("native_process_id")) is int and proof["native_process_id"] > 0 and proof.get("no_user_data") is True, "native option process absent")
    need(proof.get("status") == "M26_P02_OPTION_CANDIDATES_ONLY" and all(proof.get(k) is False for k in
         ("independent_visual_review", "screen_reader_verified", "full_module_release_approved")), "false acceptance claim")
    need(proof.get("query_before_reset") == "zzznomatch" and proof.get("query_after_reset") == "", "actual search and reset absent")
    need(proof.get("initial_titles") == MODULE_TITLES and proof.get("selected_module") == "M23"
         and proof.get("filtered_titles") == MODULE_TITLES[:1] and proof.get("reset_module") == "All modules"
         and proof.get("reset_titles") == MODULE_TITLES, "actual filter inventory absent")
    transitions=proof.get("tab_transitions")
    need(isinstance(transitions,list) and len(transitions)==len(EXPECTED_TRANSITIONS), "missing option journey tab transitions")
    for item, expected in zip(transitions,EXPECTED_TRANSITIONS):
        need(isinstance(item,dict) and (item.get("from"),item.get("key"),item.get("to")) == expected
             and all(item.get(k) is True for k in ("source_focus_and_selection","destination_focus_and_selection","previous_tab_deselected")), "invalid option tab transition")
    observations=proof.get("observations")
    need(isinstance(observations,list) and len(observations)==len(EXPECTED), "missing option observations")
    seen=set()
    for item in observations:
        need(isinstance(item,dict), "invalid observation")
        oid=item.get("option_id")
        need(oid in EXPECTED and oid not in seen, "unknown or repeated option")
        seen.add(oid)
        label,state,focus=EXPECTED[oid]
        need(item.get("screenshot_id")==oid.replace("M26-OPT-","M26-P02-OPT-") and item.get("label")==label
             and item.get("state")==state and item.get("visible_focus_name")==focus, oid+": option identity mismatch")
        need(item.get("native_focus_verified") is True and item.get("foreground_window_verified") is True, oid+": native focus/foreground absent")
        need(item.get("disabled_control_verified") is (state=="disabled"), oid+": wrong disabled semantics")
        marker={"M26-OPT-05":"No matching notices. Reset filters to view all.","M26-OPT-12":"Select a capability notice"}.get(oid,"")
        need(item.get("additional_visible_marker")==marker, oid+": additional state marker absent")
    return observations

def verify(root, source_sha, run_id):
    verify_screens(root.parent,source_sha,run_id)
    proof=json.loads((root/"M26-options.capture.json").read_text(encoding="utf-8-sig"))
    items=verify_receipt(proof,source_sha,run_id)
    hashes=set()
    for item in items:
        key=item["screenshot_id"]
        png=(root/(key+".png")).read_bytes()
        meta=json.loads((root/(key+".capture.json")).read_text(encoding="utf-8-sig"))
        need(meta.get("screenshot_id")==key and meta.get("screen")==item["label"] and meta.get("source_commit_sha")==source_sha
             and meta.get("built_commit_sha")==source_sha, key+": wrong image identity")
        need(meta.get("source")==ORIGIN and meta.get("capture_status")==STATUS and meta.get("capture_verified") is False
             and meta.get("window_fully_visible") is True and meta.get("privacy")=="Disposable CI fixture with no user content or secrets"
             and meta.get("frame_bounds_source")=="DwmGetWindowAttribute DWMWA_EXTENDED_FRAME_BOUNDS (9)", key+": wrong provenance")
        need(isinstance(meta.get("alt_text"),str) and len(meta["alt_text"])>=25,key+": missing alt text")
        need(_png_dimensions(png,key)==(meta.get("window_width"),meta.get("window_height")),key+": wrong geometry")
        digest=hashlib.sha256(png).hexdigest()
        need(digest==meta.get("sha256") and digest not in hashes,key+": mismatched or repeated image")
        hashes.add(digest)
    return {"schema_version":1,"status":"M26_P02_20_OPTION_CANDIDATES_PASS","source_commit_sha":source_sha,
            "github_run_id":run_id,"options":len(items),"unique_native_images":len(hashes),
            "independent_visual_review":False,"screen_reader_verified":False,"full_module_release_approved":False}

def main():
    p=argparse.ArgumentParser(description=__doc__)
    p.add_argument("--root",type=Path,required=True)
    p.add_argument("--source-sha",required=True)
    p.add_argument("--run-id",required=True)
    p.add_argument("--report",type=Path,required=True)
    a=p.parse_args()
    try: result=verify(a.root,a.source_sha,a.run_id)
    except (OSError,ValueError,TypeError,KeyError) as exc: p.exit(1,"ZYN-M26-OPT-010: "+str(exc)+"\n")
    a.report.write_text(json.dumps(result,indent=2)+"\n",encoding="utf-8")
    print(json.dumps(result,sort_keys=True))
if __name__=="__main__":main()
