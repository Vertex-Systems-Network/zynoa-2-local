"""Fail closed on fabricated, stale or missing actual Narrator speech evidence."""
import unittest
from pathlib import Path
from tools.verify_p02_t11_narrator import verify, InvalidNarratorProof, EXPECTED
SHA = "a"*40
RUN = "45300000001"
def sample():
    return {"schema_version":1,"status":"CAPTURED","source_commit_sha":SHA,"github_run_id":RUN,
        "target":"Real Microsoft Narrator speech copied from native Windows Tauri WebView2",
        "binary_source_commit_sha":SHA,"diagnostic_artifact_reuse":False,
        "app_executable_sha256":"a"*64,"narrator_executable_sha256":"b"*64,
        "narrator_signature_verified":True,"narrator_version":"10.0.26100.1",
        "app_pid":222,"narrator_pid":333,"native_uia_pid_match":True,"actual_keyboard_input_value":"M19-OPT-06",
        "actual_no_match_keyboard_input_value":"zynoa-no-match-7f6c","actual_no_match_result_verified":True,
        "no_user_data":True,"full_narrator_certified":False,"product_release_approved":False,
        "events":[{"stage":stage,"label":label,"clipboard_sequence_before":10+i*3,
                   "clipboard_sequence_after":11+i*3,"actual_speech_clipboard_changed":True}
                  for i,(stage,label) in enumerate(EXPECTED.items())]}
class NarratorReceiptTests(unittest.TestCase):
    def test_scoped_receipt_not_release_certification(self):
        r=verify(sample(),SHA,RUN)
        self.assertEqual(r["narrator_live_spoken_journeys"],3)
        self.assertEqual(r["narrator_live_spoken_stages"],4)
        self.assertFalse(r["full_narrator_certified"])
        self.assertFalse(r["protected_merge_verified"])
    def test_bad_label_stale_or_replayed_clipboard_fails(self):
        for key,value in (("label","wrong"),("clipboard_sequence_after",13),("clipboard_sequence_before",10),("stage","help")):
            p=sample();p["events"][1][key]=value
            with self.subTest(key=key),self.assertRaises(InvalidNarratorProof):
                verify(p,SHA,RUN)
    def test_bad_identity_or_product_claim_fails(self):
        for key,value in (("status","INCOMPLETE"),("github_run_id","9"),("narrator_signature_verified",False),("app_pid",333),("full_narrator_certified",True),("diagnostic_artifact_reuse",True),("binary_source_commit_sha","c"*40)):
            p=sample();p[key]=value
            with self.subTest(key=key),self.assertRaises(InvalidNarratorProof):
                verify(p,SHA,RUN)
    def test_probe_uses_both_default_modifier_keys_and_records_failure_diagnostics(self):
        source=(Path(__file__).resolve().parents[1]/"scripts/probe_p02_t11_narrator.ps1").read_text(encoding="utf-8")
        for marker in ("[byte]0x2D,[byte]0x14","ExtendedInsert","MapVirtualKey","GetWindowThreadProcessId",
                       "clipboard_changed","expected_phrase_found","os_build_revision","ZYN-NAR-005"):
            self.assertIn(marker,source)
        self.assertNotIn("Set-Clipboard -Value $ExpectedLabel",source)
        self.assertNotIn("Set-Clipboard -Value $Control",source)
    def test_palette_uses_real_accessible_entry_and_keyboard_input(self):
        source=(Path(__file__).resolve().parents[1]/"scripts/probe_p02_t11_narrator.ps1").read_text(encoding="utf-8")
        for marker in ("@($script:workingNarratorModifier,0x33)", "NarratorPassThroughCtrlShiftP", "Search or run a command",
                       "NativeToolbarInvoke", "InvokePattern", "ZYN-NAR-018", "TryGetClickablePoint", "NativeToolbarPhysicalClick", "Get-PaletteNativeState",
                       "SendWait('M19-OPT-06')", "ValuePattern", "M19-OPT-06 Wiki mapping and link checker"):
            self.assertIn(marker,source)
        self.assertNotIn("SetValue(",source)
    def test_probe_has_single_script_body_and_complete_diagnostic_identity_regex(self):
        source=(Path(__file__).resolve().parents[1]/"scripts/probe_p02_t11_narrator.ps1").read_text(encoding="utf-8")
        for marker in ("Add-Type -AssemblyName System.Windows.Forms", "function Send-NarratorChord",
                       "function Get-CurrentNativeRoot", "function Read-ActualNarratorPhrase",
                       "$proof=[ordered]@{", "Set-Clipboard -Value 'ZYNOA-NARRATOR-DISPOSABLE-CI-COMPLETE'"):
            self.assertEqual(source.count(marker), 1, marker)
        self.assertIn("$DiagnosticBinarySourceSha -cnotmatch '^[a-f0-9]{40}$'",source)
        self.assertIn("$DiagnosticBinarySha256 -cnotmatch '^[a-f0-9]{64}$'",source)
        cleanup = source.rsplit("} finally {", 1)[1]
        marker = "Set-Clipboard -Value 'ZYNOA-NARRATOR-DISPOSABLE-CI-COMPLETE'"
        guard = "if (-not $cleanupOk) { throw 'ZYN-NAR-025: disposable native process cleanup not verified' }"
        self.assertTrue(cleanup.rstrip().endswith(guard + "\n}"))
        self.assertLess(cleanup.index(marker), cleanup.index(guard))
        self.assertIn("$app.WaitForExit(5000)", source)
        self.assertIn("$reader.WaitForExit(5000)", source)
        self.assertIn("if (Get-Process -Name Narrator -ErrorAction SilentlyContinue) { $cleanupOk=$false }", cleanup)
        self.assertEqual(source.count("ZYN-NAR-025"), 1)
    def test_narrator_cursor_is_aligned_with_real_keyboard_focus(self):
        source=(Path(__file__).resolve().parents[1]/"scripts/probe_p02_t11_narrator.ps1").read_text(encoding="utf-8")
        for marker in ("Preferences (Ctrl+2)", "Close command palette", "FocusedElement", "@($modifier,0xDB)",
                       "system_focus_label_matches", "known_spoken_labels", "copied_phrase_sha256"):
            self.assertIn(marker,source)
        self.assertIn("candidate.IndexOf($ExpectedLabel",source)
        self.assertNotIn("SetValue(",source)
        self.assertNotIn("Set-Clipboard -Value $ExpectedLabel",source)
    def test_real_empty_result_input_label_and_selected_result_speech_are_required(self):
        source=(Path(__file__).resolve().parents[1]/"scripts/probe_p02_t11_narrator.ps1").read_text(encoding="utf-8")
        for marker in ("SendWait('zynoa-no-match-7f6c')","No matching commands","ZYN-NAR-023","ZYN-NAR-024",
                       "Read-ActualNarratorPhrase 'palette_result'", "SendWait('^a')"):
            self.assertIn(marker,source)
        self.assertNotIn("SetValue(",source)
        for key,value in (("actual_no_match_keyboard_input_value","wrong"),("actual_no_match_result_verified",False)):
            p=sample();p[key]=value
            with self.subTest(key=key),self.assertRaises(InvalidNarratorProof):
                verify(p,SHA,RUN)
        p=sample();p["events"].pop(2)
        with self.assertRaises(InvalidNarratorProof):
            verify(p,SHA,RUN)
    def test_startup_retry_is_bounded_and_before_actual_speech(self):
        source=(Path(__file__).resolve().parents[1]/"scripts/probe_p02_t11_narrator.ps1").read_text(encoding="utf-8")
        self.assertIn("$launch -lt 2",source)
        self.assertIn("ZYN-NAR-STARTUP-RETRY",source)
        self.assertIn("$app.WaitForExit(5000)",source)
        self.assertLess(source.index("ZYN-NAR-STARTUP-RETRY"),source.index("Read-ActualNarratorPhrase 'preferences'"))
        self.assertIn("if ($null -eq $prefsNav) { throw",source)
if __name__=="__main__":
    unittest.main()
