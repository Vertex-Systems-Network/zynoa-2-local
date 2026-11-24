"""P02 CI-only latency budget for actual Windows Tauri, never a product SLA."""
from __future__ import annotations
import argparse, json, re
from pathlib import Path

class InvalidP02PerformanceBudget(ValueError): pass
def need(ok,reason):
    if not ok: raise InvalidP02PerformanceBudget(reason)

def verify(budget,cold,warm,head):
    need(bool(re.fullmatch(r"[a-f0-9]{40}",head)), "invalid head SHA")
    need(isinstance(budget,dict) and budget.get("schema_version")==1 and budget.get("phase")=="P02", "invalid budget")
    need(budget.get("target")=="GitHub-hosted Windows 2025 Tauri preview build (CI budget only)", "wrong host target")
    need(budget.get("status")=="P02_CI_PREVIEW_BUDGET_GUARDRAIL_NOT_PRODUCT_RELEASE_SLA", "false budget scope")
    need(budget.get("product_cold_start_sla_approved") is False and budget.get("product_real_hardware_performance_approved") is False, "false product performance acceptance")
    need(budget.get("outlier_not_discarded") is True and budget.get("historical_cold_metadata_outlier_ms")==42582, "historical startup outlier hidden")
    required={"cold_native_metadata_ready_ms_max":45000,"native_69_image_suite_ms_max":120000,"warm_native_visible_window_ms_max":1000,"warm_connected_ui_ipc_ms_max":3000,"warm_ipc_median_ms_max":2000}
    need(budget.get("limits")==required and budget.get("minimum_warm_samples")==3, "budget modified without independent approval")
    need(isinstance(cold,dict) and cold.get("source_commit_sha")==head and cold.get("schema_version")==1 and cold.get("target")=="GitHub-hosted Windows Tauri native executable", "native cold receipt is not exact head")
    need(cold.get("no_user_data") is True and cold.get("performance_budget_approved") is False, "cold proof falsely approved or unsafe")
    need(isinstance(warm,dict) and warm.get("source_commit_sha")==head and warm.get("schema_version")==1 and warm.get("status")=="THREE_WARM_NATIVE_WINDOW_OBSERVATIONS_ONLY", "warm native proof missing or mismatched head")
    need(warm.get("no_user_data") is True and warm.get("approved_performance_budget") is False and warm.get("cold_start_budget_verified") is False, "warm proof falsely approved")
    need(warm.get("sample_count")==3 and str(warm.get("github_run_id","")).isdigit(), "warm process provenance missing")
    cold_ms=cold.get("startup_local_metadata_ready_ms")
    suite_ms=cold.get("native_screenshot_suite_ms")
    need(type(cold_ms) is int and 0<cold_ms<=required["cold_native_metadata_ready_ms_max"], "cold native metadata ready budget exceeded")
    need(type(suite_ms) is int and 0<suite_ms<=required["native_69_image_suite_ms_max"], "69-image native capture budget exceeded")
    windows=warm.get("window_first_visible_ms")
    ipcs=warm.get("native_handshake_ready_ms")
    need(isinstance(windows,list) and isinstance(ipcs,list) and len(windows)==len(ipcs)==3, "three real warm process samples needed")
    for visible,ready in zip(windows,ipcs):
        need(type(visible) is int and 0<visible<=required["warm_native_visible_window_ms_max"], "warm visible-window budget exceeded")
        need(type(ready) is int and visible<=ready<=required["warm_connected_ui_ipc_ms_max"], "warm connected IPC budget exceeded")
    ready_median=sorted(ipcs)[1]
    need(ready_median<=required["warm_ipc_median_ms_max"] and warm.get("native_handshake_median_ms")==ready_median, "warm median budget exceeded or mismatched")
    return {"schema_version":1,"phase":"P02","status":"P02_CI_PREVIEW_PERFORMANCE_GUARDRAIL_PASS","source_commit_sha":head,"github_run_id":warm["github_run_id"],"native_cold_metadata_ready_ms":cold_ms,"native_screenshot_suite_ms":suite_ms,"native_warm_ipc_ms":ipcs,"native_warm_ipc_median_ms":ready_median,"historical_cold_outlier_ms":42582,"historical_outlier_not_waived":True,"product_performance_sla_approved":False,"full_accessibility_approved":False,"no_user_data":True}

def main():
    p=argparse.ArgumentParser()
    for item in ("budget","cold","warm","report"):p.add_argument("--"+item,type=Path,required=True)
    p.add_argument("--source-sha",required=True)
    a=p.parse_args()
    try:
        result=verify(*[json.loads(getattr(a,item).read_text(encoding="utf-8-sig")) for item in ("budget","cold","warm")],a.source_sha)
    except (OSError,ValueError,InvalidP02PerformanceBudget) as exc:p.exit(1,"ZYN-PERF-020: "+str(exc)+"\n")
    a.report.parent.mkdir(parents=True,exist_ok=True)
    a.report.write_text(json.dumps(result,indent=2)+"\n",encoding="utf-8")
    print(json.dumps(result,sort_keys=True))
if __name__=="__main__": main()
