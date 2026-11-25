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
        for word in ("Get-FileHash","Invoke-WebRequest","SetForegroundWindow","SendKeys","M19-OPT-06","nvda.exe","ZynoaNvdaReportFocus","keybd_event(0x2D","keybd_event(0x09"):
            self.assertIn(word,ps)
        for word in ("pre_synthSpeak.register","pre_synthSpeak.unregister","plugin_loaded"):
            self.assertIn(word,plugin)
        for forbidden in ("selenium","playwright","mock_window","speech.speak("):
            self.assertNotIn(forbidden,plugin+ps)
    def test_native_palette_retry_does_not_bypass_real_speech(self):
        ps=(ROOT/"scripts/probe_p02_nvda_speech.ps1").read_text(encoding="utf-8")
        for marker in ("Get-NvdaNativeRoot", "GetForegroundWindow", "Find-NvdaSearch",
                       "InvokePattern", "native_toolbar_invoke", "Search or run a command",
                       "ZYN-NVDA-010", "ZYN-NVDA-011", "ValuePattern",
                       "actual_keyboard_input_value=$value"):
            self.assertIn(marker,ps)
        self.assertIn("if ($null -eq $input) { throw 'ZYN-NVDA-010",ps)
        self.assertIn("if ($value -cne 'M19-OPT-06') { throw",ps)
        self.assertIn("events=@($events | Where-Object { $_.kind -eq 'speech' })",ps)
    def test_palette_accessible_edit_focus_not_replaced_by_default_result(self):
        view=(ROOT/"apps/desktop/src/ui/CommandPalette.tsx").read_text(encoding="utf-8")
        self.assertIn("useState(false)",view)
        self.assertIn("setResultNavigation(matches.length > 0)",view)
        self.assertIn("aria-activedescendant={resultNavigation && matches.length",view)
        self.assertIn("setQuery(event.target.value); setSelected(0); setResultNavigation(false);",view)
        self.assertIn("execute(matches[Math.min(selected, matches.length - 1)])",view)

    def test_m26_no_match_speech_is_requested_on_real_reset_control(self):
        ps=(ROOT/"scripts/probe_p02_nvda_speech.ps1").read_text(encoding="utf-8")
        branch=ps.split("Set-Content -LiteralPath $stageFile -Value 'm26_empty'",1)[1].split("$app.Refresh();$nvda.Refresh()",1)[0]
        self.assertIn("Focus-M26NvdaControl -Name 'No matching notices. Reset filters to view all.'",branch)
        self.assertIn("Request-M26NvdaFocusSpeech",branch)
        self.assertIn("if ($query -cne 'zzznomatch')",branch)

    def test_palette_typing_retry_is_bounded_and_requires_actual_value(self):
        ps=(ROOT/"scripts/probe_p02_nvda_speech.ps1").read_text(encoding="utf-8")
        for marker in ("$typingAttempt -lt 2","HasKeyboardFocus","ZYN-NVDA-TYPING-RETRY","SendWait('^a')","SendWait('M19-OPT-06')","if ($value -cne 'M19-OPT-06') { throw"):
            self.assertIn(marker,ps)
        self.assertNotIn("SetValue(",ps)
        self.assertIn("TryGetClickablePoint([ref]$point)",ps)
        self.assertIn("BoundingRectangle.Contains($point)",ps)
        self.assertIn("ZYN-NVDA-TYPING-MISMATCH",ps)

    def test_m26_scoped_speech_requires_three_distinct_actual_stages(self):
        from tools.verify_p02_nvda_speech import verify_m26
        p=sample()
        p.update(target="Real Windows Tauri WebView2 M26 with live NVDA pre_synthSpeak",
                 actual_selected_tab="Known Issues", actual_tab_keyboard_focus=True,
                 actual_search_keyboard_focus=True, actual_keyboard_input_value="zzznomatch",
                 actual_no_match_visible=True, full_product_release_approved=False)
        p["events"]=[{"kind":"speech","stage":stage,"label":label,"unix_ms":1795000000000+i}
                     for i,(stage,label) in enumerate((("m26_tab","Known Issues"),("m26_search","Search bundled notices"),("m26_empty","No matching notices. Reset filters to view all.")))]
        self.assertEqual(verify_m26(p,HEAD,p["github_run_id"],"a"*64)["spoken_stages"],3)
        for key,value in (("actual_no_match_visible",False),("actual_tab_keyboard_focus",False),
                          ("actual_keyboard_input_value","fake"),("source_commit_sha","b"*40),
                          ("full_product_release_approved",True)):
            bad=copy.deepcopy(p);bad[key]=value
            with self.subTest(key=key),self.assertRaises(InvalidNvdaProof):
                verify_m26(bad,HEAD,p["github_run_id"],"a"*64)
        for i in range(3):
            bad=copy.deepcopy(p);bad["events"].pop(i)
            with self.subTest(stage=i),self.assertRaises(InvalidNvdaProof):
                verify_m26(bad,HEAD,p["github_run_id"],"a"*64)
        bad=copy.deepcopy(p);bad["events"][2]["unix_ms"]=bad["events"][0]["unix_ms"]
        with self.assertRaises(InvalidNvdaProof):verify_m26(bad,HEAD,p["github_run_id"],"a"*64)
        with self.assertRaises(InvalidNvdaProof):verify_m26(p,HEAD,"123","a"*64)
        with self.assertRaises(InvalidNvdaProof):verify_m26(p,HEAD,p["github_run_id"],"b"*64)
if __name__=="__main__":unittest.main()
