"""Negative tests for real NVDA Windows Tauri speech gate."""
from tools.verify_p02_nvda_speech import verify, InvalidNvdaProof
import copy
import unittest
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1]
HEAD="a"*40
def sample():
    return {
        "schema_version":1,"source_commit_sha":HEAD,"github_run_id":"45200000000",
        "app_executable_sha256":"a"*64,
        "official_nvda_installer_sha256":"6f80a5b0ca720a7d0d314b5be212f37388bbe81a1107ac3298c1821a1cd3f052",
        "nvda_version":"2026.3.1",
        "target":"Real Windows Tauri WebView2 with live NVDA pre_synthSpeak",
        "app_pid":200,"nvda_pid":201,"native_uia_pid_match":True,
        "actual_keyboard_input_value":"M19-OPT-06","plugin_loaded":True,"no_user_data":True,
        "full_narrator_verified":False,"performance_budget_approved":False,
        "events":[{"kind":"speech","stage":stage,"label":label,"unix_ms":1795000000000+i}
                  for i,(stage,label) in enumerate((("preferences","Preferences"),("palette","Search available commands and offline Help"),("help","Wiki mapping and link checker")))]
    }
class NVDAProofTests(unittest.TestCase):
    def test_scoped_valid_does_not_approve_narrator_or_release(self):
        result=verify(sample(),HEAD)
        self.assertEqual(result["status"],"SCOPED_LIVE_NVDA_SPEECH_PASS")
        self.assertFalse(result["narrator_verified"])
        self.assertFalse(result["full_product_release_approved"])
    def test_every_missing_speech_announcement_fails(self):
        for i in range(3):
            p=sample();p["events"].pop(i)
            with self.subTest(i=i),self.assertRaises(InvalidNvdaProof): verify(p,HEAD)
    def test_stage_replay_is_not_three_real_screen_reader_journeys(self):
        p=sample()
        for item in p["events"]: item["stage"]="help"
        with self.assertRaises(InvalidNvdaProof): verify(p,HEAD)
    def test_untrusted_or_fake_output_rejected(self):
        for key,val in (("source_commit_sha","b"*40),("plugin_loaded",False),
                        ("official_nvda_installer_sha256","b"*64),("native_uia_pid_match",False),
                        ("actual_keyboard_input_value","fake"),("no_user_data",False),
                        ("full_narrator_verified",True),("performance_budget_approved",True)):
            p=sample();p[key]=val
            with self.subTest(key=key),self.assertRaises(InvalidNvdaProof):verify(p,HEAD)
    def test_live_probe_and_no_mock_browser(self):
        ps=(ROOT/"scripts/probe_p02_nvda_speech.ps1").read_text(encoding="utf-8")
        plugin=(ROOT/"scripts/nvda/zynoaAudit.py").read_text(encoding="utf-8")
        for word in ("Get-FileHash","Invoke-WebRequest","SetForegroundWindow","SendKeys","M19-OPT-06","nvda.exe"):
            self.assertIn(word,ps)
        for word in ("pre_synthSpeak.register","pre_synthSpeak.unregister","plugin_loaded"):
            self.assertIn(word,plugin)
        for forbidden in ("selenium","playwright","mock_window","speech.speak("):
            self.assertNotIn(forbidden,plugin+ps)
if __name__=="__main__":unittest.main()
