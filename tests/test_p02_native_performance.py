"""Negative acceptance tests: 3 native Windows performance samples, never budget approval."""
import copy
from pathlib import Path
import unittest
from tools.verify_p02_native_performance import verify, InvalidRepeatedNativePerformance

ROOT = Path(__file__).resolve().parents[1]
SHA = "a"*40


def sample():
    return {
        "schema_version":1,"source_commit_sha":SHA,"github_run_id":"45284349359",
        "target":"Real GitHub Actions Windows Tauri native main-window UIA",
        "executable_sha256":"a"*64,
        "measurement":"three sequential warm process launches, same executable, visible same-PID UIA HWND",
        "samples":[{"sample_index":i,"native_process_id":9000+i,"window_first_visible_ms":ms,
                    "real_native_visible_hwnd":True,"native_uia_window_pid_matches":True,
                    "process_alive_when_sampled":True} for i,ms in enumerate((1250,900,1800),1)],
        "sample_count":3,"native_test_environment":"GitHub-hosted Windows runner",
        "full_screen_reader_verified":False,"performance_budget_approved":False,"no_user_data":True,
    }


class NativePerformanceTests(unittest.TestCase):
    def test_three_warm_observations_not_full_release_budget(self):
        r = verify(sample(), SHA)
        self.assertEqual(r["median_ms"],1250)
        self.assertEqual(r["observed_max_ms"],1800)
        self.assertEqual(r["sample_count"],3)
        self.assertFalse(r["approved_performance_budget"])
        self.assertFalse(r["cold_start_budget_verified"])
        self.assertFalse(r["screen_reader_verified"])

    def test_fake_source_or_approval_fails_closed(self):
        for key,value in (("source_commit_sha","b"*40),("github_run_id","invalid"),
                          ("target","web browser"),("executable_sha256","missing"),
                          ("native_test_environment","mock machine"),
                          ("measurement","invented"),("sample_count",2),
                          ("performance_budget_approved",True),
                          ("full_screen_reader_verified",True),("no_user_data",False)):
            with self.subTest(key=key):
                v=sample(); v[key]=value
                with self.assertRaises(InvalidRepeatedNativePerformance): verify(v,SHA)

    def test_missing_duplicate_and_non_native_measurements_fail(self):
        mutations=[lambda p:p["samples"].pop(),
                   lambda p:p["samples"][1].update(sample_index=1),
                   lambda p:p["samples"][1].update(native_process_id=p["samples"][0]["native_process_id"]),
                   lambda p:p["samples"][0].update(window_first_visible_ms=-1),
                   lambda p:p["samples"][0].update(window_first_visible_ms=60001),
                   lambda p:p["samples"][0].update(real_native_visible_hwnd=False),
                   lambda p:p["samples"][0].update(native_uia_window_pid_matches=False),
                   lambda p:p["samples"][0].update(process_alive_when_sampled=False)]
        for fn in mutations:
            v=copy.deepcopy(sample());fn(v)
            with self.assertRaises(InvalidRepeatedNativePerformance):verify(v,SHA)

    def test_powershell_and_ci_use_real_win32_window(self):
        ps=(ROOT/"scripts/probe_p02_native_performance.ps1").read_text(encoding="utf-8")
        for word in ("Start-Process","IsWindowVisible","MainWindowHandle","AutomationElement",
                     "ProcessId","Get-FileHash","GITHUB_RUN_ID","Stop-Process",
                     "full_screen_reader_verified = $false","performance_budget_approved = $false"):
            self.assertIn(word,ps)
        for forbidden in ("Invoke-WebRequest","Get-Clipboard","Remove-Item"):self.assertNotIn(forbidden,ps)
        yml=(ROOT/".github/workflows/p01-desktop.yml").read_text(encoding="utf-8")
        for word in ("tests.test_p02_native_performance","scripts\\probe_p02_native_performance.ps1",
                     "tools.verify_p02_native_performance","P02-native-startup-repeat.capture.json"):
            self.assertIn(word,yml)


if __name__=="__main__":
    unittest.main()
