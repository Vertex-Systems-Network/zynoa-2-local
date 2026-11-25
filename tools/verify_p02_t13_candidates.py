"""Exact-source real native system-center PNG candidates; never final approval."""
import argparse
import hashlib
import json
import re
import struct
from pathlib import Path

INVENTORY=Path(__file__).resolve().parents[1]/"docs/evidence/P02_T13_UI_INVENTORY.json"

def need(ok,message):
    if not ok: raise ValueError(message)

def read(path):
    return json.loads(path.read_text(encoding="utf-8-sig"))

def verify(root,module,sha,run_id):
    need(bool(re.fullmatch(r"[a-f0-9]{40}",sha)) and bool(re.fullmatch(r"[1-9][0-9]*",run_id)),"invalid source identity")
    center=next(x for x in read(INVENTORY)["centers"] if x["module"]==module)
    proof=read(root/"T13-journey.capture.json")
    need(proof["schema_version"]==1 and proof["module"]==module and proof["source_commit_sha"]==proof["built_commit_sha"]==sha
         and proof["github_run_id"]==run_id and type(proof["native_pid"]) is int and proof["native_pid"]>0 and proof["no_user_data"] is True,"invalid journey identity")
    options={x["id"]:x for x in center["options"]}
    expected=[]
    for screen in center["screens"]:
        expected.append((screen["id"],screen["id"]+" "+screen["title"],"screen"))
        expected.extend((key,key+" "+options[key]["title"],options[key]["kind"]) for key in screen["options"])
    observed=proof["observations"]
    need(len(observed)==len(expected),"incomplete native journey")
    hashes=set()
    for row,(asset,name,kind) in zip(observed,expected):
        need(row["asset_id"]==asset and row["actual_name"]==name and row["kind"]==kind and row["focus_verified"] is True and row["foreground_verified"] is True
             and row["control_verified"] is (kind!="screen"),"native focus/control mismatch")
        p=root/(asset+".png"); meta=read(root/(asset+".capture.json")); png=p.read_bytes()
        digest=hashlib.sha256(png).hexdigest()
        need(png[:8]==b"\x89PNG\r\n\x1a\n" and png[12:16]==b"IHDR" and len(png)>1024,"invalid PNG")
        w,h=struct.unpack(">II",png[16:24])
        need(880<=w<=3840 and 600<=h<=2160 and (w,h)==(meta["window_width"],meta["window_height"]),"invalid geometry")
        need(meta["screenshot_id"]==asset and meta["source_commit_sha"]==meta["built_commit_sha"]==sha
             and meta["sha256"]==digest and digest not in hashes and meta["source"]=="GitHub Windows Actions actual Tauri process"
             and meta["frame_bounds_source"]=="DwmGetWindowAttribute DWMWA_EXTENDED_FRAME_BOUNDS (9)"
             and meta["capture_status"]=="candidate_pending_visual_review" and meta["capture_verified"] is False
             and meta["window_fully_visible"] is True and meta["privacy"]=="Disposable CI fixture with no user content or secrets","invalid original frame")
        hashes.add(digest)
    return {"schema_version":1,"status":"P02_T13_NATIVE_CANDIDATES_PASS","module":module,"source_commit_sha":sha,"github_run_id":run_id,"screens":len(center["screens"]),"options":len(options),"unique_images":len(hashes),"independent_visual_review":False,"full_module_release_approved":False}

def main():
    p=argparse.ArgumentParser()
    p.add_argument("--root",type=Path,required=True);p.add_argument("--module",choices=("M23","M24","M25"),required=True)
    p.add_argument("--source-sha",required=True);p.add_argument("--run-id",required=True);p.add_argument("--report",type=Path,required=True)
    a=p.parse_args()
    try:
        result=verify(a.root,a.module,a.source_sha,a.run_id)
        a.report.write_text(json.dumps(result,indent=2)+"\n",encoding="utf-8")
        print(json.dumps(result,sort_keys=True));return 0
    except (ValueError,KeyError,TypeError,OSError,StopIteration,struct.error) as exc:
        print("ZYN-T13-VERIFY: candidate proof refused:",type(exc).__name__);return 1
if __name__=="__main__":raise SystemExit(main())
