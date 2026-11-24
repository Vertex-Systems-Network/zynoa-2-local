"""P02 T10 strict CI preview latency guards; no universal SLA approval."""
import copy,unittest
from tools.verify_p02_t10_performance_budget import verify,InvalidP02PerformanceBudget
from pathlib import Path
import json
ROOT=Path(__file__).resolve().parents[1]
SHA="a"*40
def cases():
    budget=json.loads((ROOT/"docs/quality/P02_T10_PERFORMANCE_BUDGET.json").read_text())
    cold={"schema_version":1,"source_commit_sha":SHA,"target":"GitHub-hosted Windows Tauri native executable","startup_local_metadata_ready_ms":7000,"native_screenshot_suite_ms":92000,"no_user_data":True,"performance_budget_approved":False}
    warm={"schema_version":1,"source_commit_sha":SHA,"status":"THREE_WARM_NATIVE_WINDOW_OBSERVATIONS_ONLY","github_run_id":"45298990995","sample_count":3,"window_first_visible_ms":[210,140,145],"native_handshake_ready_ms":[920,850,1100],"native_handshake_median_ms":920,"approved_performance_budget":False,"cold_start_budget_verified":False,"no_user_data":True}
    return budget,cold,warm
class P02BudgetTests(unittest.TestCase):
    def test_valid_preview_budget_retains_product_limitations(self):
        r=verify(*cases(),SHA)
        self.assertEqual(r["status"],"P02_CI_PREVIEW_PERFORMANCE_GUARDRAIL_PASS")
        self.assertFalse(r["product_performance_sla_approved"])
        self.assertTrue(r["historical_outlier_not_waived"])
    def test_bad_timings_fail_closed(self):
        for field,value in (("startup_local_metadata_ready_ms",45001),("native_screenshot_suite_ms",120001)):
            b,c,w=copy.deepcopy(cases());c[field]=value
            with self.subTest(field=field),self.assertRaises(InvalidP02PerformanceBudget):verify(b,c,w,SHA)
        b,c,w=copy.deepcopy(cases());w["native_handshake_ready_ms"][0]=3100
        with self.assertRaises(InvalidP02PerformanceBudget):verify(b,c,w,SHA)
        b,c,w=copy.deepcopy(cases());w["window_first_visible_ms"][0]=1001
        with self.assertRaises(InvalidP02PerformanceBudget):verify(b,c,w,SHA)
    def test_forged_sha_or_waived_outlier_rejected(self):
        for field,value in (("historical_cold_metadata_outlier_ms",0),("product_cold_start_sla_approved",True),("minimum_warm_samples",1)):
            b,c,w=copy.deepcopy(cases());b[field]=value
            with self.subTest(field=field),self.assertRaises(InvalidP02PerformanceBudget):verify(b,c,w,SHA)
        b,c,w=cases();w["source_commit_sha"]="b"*40
        with self.assertRaises(InvalidP02PerformanceBudget):verify(b,c,w,SHA)
    def test_real_windows_job_cannot_skip_budget(self):
        y=(ROOT/".github/workflows/p01-desktop.yml").read_text()
        self.assertIn("P02 enforce preview-only native performance budget",y)
        self.assertIn("tools.verify_p02_t10_performance_budget",y)
if __name__=="__main__":unittest.main()
