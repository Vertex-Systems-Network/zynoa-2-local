"""M26 P02 source contract, not a substitute for native screenshots or signed data."""
from pathlib import Path
import unittest

ROOT = Path(__file__).resolve().parents[1]
UI = ROOT / "apps/desktop/src/ui"

class ChangeCenterTests(unittest.TestCase):
    def test_real_navigation_local_filters_and_contextual_help(self):
        app = (ROOT / "apps/desktop/src/App.tsx").read_text(encoding="utf-8")
        view = (UI / "ChangeCenter.tsx").read_text(encoding="utf-8")
        catalog = (UI / "help-catalog.ts").read_text(encoding="utf-8")
        for marker in ('view === "changelog"', 'aria-label="Changelog"', 'changelog: "change-history"'):
            self.assertIn(marker, app)
        for marker in ("What's New", "Known Issues", "Version History", "Module Changes",
                       'role="tablist"', 'role="tab"', 'role="tabpanel"', 'aria-selected=',
                       "ArrowLeft", "ArrowRight", '"Home"', '"End"', "filterChangeNotices(query,module)",
                       "Reset filters", "Changelog help", "No matching notices"):
            self.assertIn(marker, view)
        self.assertIn('id: "change-history"', catalog)

    def test_no_fake_release_or_unapproved_native_privilege(self):
        view = (UI / "ChangeCenter.tsx").read_text(encoding="utf-8")
        core = (UI / "change-center.ts").read_text(encoding="utf-8")
        for marker in ("verifiedReleaseCount:0", "liveIssuesAvailable:false", "releaseFeedAvailable:false",
                       'kind:"capability-limitation"'):
            self.assertIn(marker,core)
        for marker in ("No verified releases", "No verified versions", "Not a released fix or live issue status", 'type="button" disabled'):
            self.assertIn(marker,view)
        for unsafe in ("fetch(", "localStorage", "sessionStorage", "invoke(", "dangerouslySetInnerHTML", "window.open("):
            self.assertNotIn(unsafe,view+core)

    def test_deferred_service_surfaces_are_named_and_non_operational(self):
        view = (UI / "ChangeCenter.tsx").read_text(encoding="utf-8")
        core = (UI / "change-center.ts").read_text(encoding="utf-8")
        for marker in ("Audit Timeline", "Notifications", "Migration Notes", "ServiceBoundary",
                       'tabIndex={active===item.key?0:-1}', "UnavailableAction",
                       "Open linked issue", "Open linked pull request", "Report problem from change",
                       "Filter release channel or version", "Filter change category", "View fixed problems"):
            self.assertIn(marker, view)
        for marker in ("Audit access is not enabled", "Notification settings unavailable",
                       "No verified migration notes", "Export change history", "View rollback guidance"):
            self.assertIn(marker,core)
        self.assertIn('<button type="button" disabled aria-describedby={reasonId}>{label}</button>',view)
        self.assertIn('role="group" aria-label={label+" unavailable"} aria-describedby={reasonId} tabIndex={0}',view)
        self.assertIn('<p id={reasonId}>{reason}</p>',view)
        self.assertIn("onClick={onHelp}",view)
        self.assertNotIn('aria-disabled="false"', view)

    def test_product_keyboard_notice_detail_reset_and_runtime_guidance(self):
        view=(UI/"ChangeCenter.tsx").read_text(encoding="utf-8")
        css=(ROOT/"apps/desktop/src/styles.css").read_text(encoding="utf-8")
        for marker in ('onClick={resetFilters}>No matching notices.', 'searchInput.current?.focus()',
                       'pendingNoticeFocus.current=event.detail===0', 'detailHeading.current?.focus()',
                       'noticeButtons.current.get(selected)?.focus()', 'Back to notice list',
                       'data-runtime-state={availability.runtimeState}', 'availability.guidance'):
            self.assertIn(marker,view)
        self.assertIn('@container (max-width:540px)',css)
        self.assertIn('max-height:none; overflow:visible;',css)

    def test_native_candidate_suite_is_separate_and_fail_closed(self):
        script = (ROOT / "scripts/capture_p01_desktop.ps1").read_text(encoding="utf-8")
        workflow = (ROOT / ".github/workflows/p01-desktop.yml").read_text(encoding="utf-8")
        from tools.verify_p02_m26_candidates import EXPECTED, verify
        import tempfile
        import json
        for key in EXPECTED:
            self.assertIn(key, script)
        for marker in ("GetForegroundWindow", "ValuePattern", "ZYN-M26-005",
                       "screen_reader_verified=$false", "independent_visual_review=$false"):
            self.assertIn(marker,script)
        self.assertIn("-M26Only",workflow)
        self.assertIn("steps.native_build.outcome == 'success'",workflow)
        self.assertIn("!cancelled()",workflow)
        self.assertNotIn("continue-on-error: true",workflow)
        self.assertIn("tools.verify_p02_m26_candidates",workflow)
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            (root / "M26-journey.capture.json").write_text(json.dumps({
                "schema_version": 1, "source_commit_sha": "a"*40, "built_commit_sha": "a"*40,
                "github_run_id": "123", "native_process_id": 1, "no_user_data": True,
                "status": "M26_NATIVE_CANDIDATES_ONLY", "independent_visual_review": True,
                "screen_reader_verified": False, "observations": []}), encoding="utf-8")
            with self.assertRaisesRegex(ValueError, "false acceptance"):
                verify(root,"a"*40,"123")
            with self.assertRaisesRegex(ValueError, "wrong native journey identity"):
                verify(root,"b"*40,"123")

    def test_m26_native_viewport_review_keeps_marker_visibility(self):
        view = (UI / "ChangeCenter.tsx").read_text(encoding="utf-8")
        css = (ROOT / "apps/desktop/src/styles.css").read_text(encoding="utf-8")
        script = (ROOT / "scripts/capture_p01_desktop.ps1").read_text(encoding="utf-8")
        self.assertIn('<h3 tabIndex={-1}>Select a capability notice</h3>', view)
        self.assertIn('matches.length===1?"notice":"notices"', view)
        self.assertIn(".shell .change-center .section-heading", css)
        self.assertIn(".shell .change-center .change-tabs button", css)
        self.assertIn("min-height:44px", css)
        self.assertIn("Wait-M26Name -Name $Heading -Reveal", script)
        self.assertIn("ScrollItemPattern", script)
        self.assertIn("if ($item.Current.IsOffscreen", script)
        self.assertIn("Wait-M26Name -Name $Heading)", script)

    def test_m26_tab_focus_after_commit_and_native_selection_proof(self):
        view = (UI / "ChangeCenter.tsx").read_text(encoding="utf-8")
        script = (ROOT / "scripts/capture_p01_desktop.ps1").read_text(encoding="utf-8")
        self.assertIn("useLayoutEffect",view)
        self.assertIn("pendingTabFocus",view)
        self.assertIn('aria-label="Search bundled notices"',view)
        self.assertIn('aria-label="Module"',view)
        for marker in ("SelectionItemPattern","HasKeyboardFocus","ControlType]::TabItem",
                       "Wait-M26SelectedFocus","previous_tab_deselected=$true","ZYN-M26-013"):
            self.assertIn(marker,script)
        from tools.verify_p02_m26_candidates import verify
        import tempfile
        import json
        with tempfile.TemporaryDirectory() as directory:
            root=Path(directory)
            (root/"M26-journey.capture.json").write_text(json.dumps({
                "schema_version":1,"source_commit_sha":"a"*40,"built_commit_sha":"a"*40,
                "github_run_id":"123","native_process_id":1,"no_user_data":True,
                "status":"M26_NATIVE_CANDIDATES_ONLY","independent_visual_review":False,
                "screen_reader_verified":False,"observations":[],"tab_transitions":[]}),encoding="utf-8")
            with self.assertRaisesRegex(ValueError,"missing native keyboard transitions"):
                verify(root,"a"*40,"123")

    def test_module_filter_requires_real_value_inventory_and_reset(self):
        from tools.verify_p02_m26_candidates import verify_module_filter, MODULE_TITLES
        script = (ROOT / "scripts/capture_p01_desktop.ps1").read_text(encoding="utf-8")
        for marker in ("Read-M26ModuleFilter", "SelectionPattern", "ValuePattern",
                       "Bundled capability notices", "ZYN-M26-016", "ZYN-M26-017"):
            self.assertIn(marker, script)
        valid = {"initial_value":"All modules","initial_titles":MODULE_TITLES,
                 "selected_value":"M23","filtered_titles":MODULE_TITLES[:1],
                 "keyboard_method":"collapsed_keyboard","reset_value":"All modules",
                 "reset_titles":MODULE_TITLES}
        verify_module_filter(valid)
        for key,wrong in (("selected_value","M24"),("filtered_titles",MODULE_TITLES),
                          ("reset_titles",[]),("keyboard_method","fake"),("initial_value","M26")):
            with self.subTest(key=key), self.assertRaises(ValueError):
                verify_module_filter({**valid,key:wrong})
        with self.assertRaises(ValueError):
            verify_module_filter(None)

    def test_native_notice_activation_requires_actual_query_reset_and_keyboard(self):
        from tools.verify_p02_m26_candidates import verify_notice_detail
        script = (ROOT / "scripts/capture_p01_desktop.ps1").read_text(encoding="utf-8")
        for marker in ("HasKeyboardFocus", "ZYN-M26-018", "ZYN-M26-019", "ZYN-M26-020",
                       "query_after_reset", "focused_native_button_enter"):
            self.assertIn(marker, script)
        valid = {"query_before":"zzznomatch","query_after_reset":"",
                 "notice_title":"Backup and restore not available",
                 "activation":"focused_native_button_enter",
                 "detail_marker":"Not a released fix or live issue status."}
        verify_notice_detail(valid)
        for key,wrong in (("query_after_reset","zzznomatch"),("activation","fake"),
                          ("notice_title","Signed updates not available"),("detail_marker","")):
            with self.subTest(key=key), self.assertRaises(ValueError):
                verify_notice_detail({**valid,key:wrong})

    def test_native_popup_and_glossary_keyboard_repair_preserves_checks(self):
        script = (ROOT / "scripts/capture_p01_desktop.ps1").read_text(encoding="utf-8")
        popup = script.split("# A native select popup", 1)[1].split("$filterProof=", 1)[0]
        self.assertIn("SendWait('%{DOWN}{HOME}{DOWN}{ENTER}')", popup)
        self.assertIn("GetForegroundWindow() -eq $hwnd", popup)
        self.assertGreaterEqual(popup.count("Assert-M26Foreground"), 2)
        self.assertIn("Wait-M26ModuleFilter -ExpectedValue 'M23'", popup)
        glossary = script.split("# The aria-pressed mode button", 1)[1].split("P02-T10-CTRL-M19-OPT-04", 1)[0]
        for marker in ("HasKeyboardFocus", "SendWait('{ENTER}')", "Practical answers, no network.",
                       "ZYN-SCREEN-045", "ZYN-SCREEN-046"):
            self.assertIn(marker, glossary)
        self.assertNotIn("$invoke.Invoke()", glossary)

    def test_foreground_recovery_only_at_intentional_focus_boundary(self):
        script = (ROOT / "scripts/capture_p01_desktop.ps1").read_text(encoding="utf-8")
        recovery = script.split("function Restore-M26ForegroundForFocus {", 1)[1].split("function Wait-M26Name", 1)[0]
        for marker in ("MainWindowHandle -ne $hwnd", "SetForegroundWindow($hwnd)",
                       "GetForegroundWindow() -eq $hwnd", "AddSeconds(2)", "Assert-M26Foreground"):
            self.assertIn(marker, recovery)
        focus = script.split("function Focus-M26Control {", 1)[1].split("$observations =", 1)[0]
        for marker in ("$focusAttempt -lt 2", "Restore-M26ForegroundForFocus", "HasKeyboardFocus", "Assert-M26Foreground"):
            self.assertIn(marker, focus)
        for start,end in (("function Send-M26Key {","function Focus-M26Control"),
                          ("function Capture-M26 {","$tabTransitions =")):
            section=script.split(start,1)[1].split(end,1)[0]
            self.assertIn("Assert-M26Foreground",section)
            self.assertNotIn("Restore-M26ForegroundForFocus",section)

    def test_native_capture_precedes_speech_with_independent_fail_closed_gates(self):
        workflow = (ROOT / ".github/workflows/p01-desktop.yml").read_text(encoding="utf-8")
        m26 = workflow.index("name: P02-T12 separate M26 native keyboard")
        nvda = workflow.index("name: P02 live NVDA speech")
        t10 = workflow.index("name: P02-T10 exact-source native preview final acceptance")
        narrator = workflow.index("name: P02-T11 live Microsoft Narrator")
        self.assertLess(m26, nvda)
        self.assertLess(nvda, t10)
        self.assertLess(t10, narrator)
        for marker in ("Get-Process -Name Narrator,nvda", "ZYN-M26-021",
                       "WaitForExit(10000)", "ZYN-M26-022"):
            self.assertIn(marker, workflow[m26:nvda])
        for marker, section in (("steps.p02_performance_budget.outcome == 'success'", workflow[nvda:t10]),
                                ("steps.p02_nvda.outcome == 'success'", workflow[t10:narrator]),
                                ("steps.p02_t10_acceptance.outcome == 'success'", workflow[narrator:])):
            self.assertIn(marker, section)
            self.assertIn("!cancelled()", section)
        script = (ROOT / "scripts/capture_p01_desktop.ps1").read_text(encoding="utf-8")
        for marker in ("GetWindowThreadProcessId", "ZYN-M26-FOREGROUND-LOSS",
                       "search_reset_focus", "search_reset_enter", "search_reset_value",
                       "notice_focus", "notice_enter", "notice_detail"):
            self.assertIn(marker, script)
        self.assertNotIn("MainWindowTitle", script)

    def test_foreground_retry_discards_incomplete_journey_and_never_retries_verifier_failure(self):
        workflow=(ROOT/".github/workflows/p01-desktop.yml").read_text(encoding="utf-8")
        start=workflow.index("name: P02-T12 separate M26 native keyboard")
        end=workflow.index("name: P02 live NVDA speech",start)
        section=workflow[start:end]
        self.assertEqual(section.count("$attempt -le 2"),2)
        self.assertEqual(section.count("$_.Exception.Message -notlike 'ZYN-M26-002:*'"),2)
        self.assertEqual(section.count("Move-Item -LiteralPath $out -Destination $diagnostics"),2)
        self.assertEqual(section.count("if ($LASTEXITCODE -ne 0) { throw 'ZYN-M26-010:"),2)
        self.assertNotIn("continue-on-error",section)
        narrator=(ROOT/"scripts/probe_p02_t11_narrator.ps1").read_text(encoding="utf-8")
        branch=narrator.split("  if ($M26Only) {",1)[1].split("  $prefsNav.SetFocus()",1)[0]
        self.assertIn("NativeChangelogInvoke",branch)
        self.assertIn("TryGetCurrentPattern([System.Windows.Automation.InvokePattern]",branch)
        self.assertIn("Send-M26NarratorPassThrough '{RIGHT}'",branch)
        self.assertIn("actual_previous_tab_deselected",branch)

    def test_all_twenty_m26_option_explanations_are_bundled_and_documented(self):
        catalog=(UI/"help-catalog.ts").read_text(encoding="utf-8")
        help_doc=(ROOT/"docs/help/articles/M26.md").read_text(encoding="utf-8")
        wiki=(ROOT/"docs/wiki/pages/M26.md").read_text(encoding="utf-8")
        for i in range(1,21):
            oid=f"M26-OPT-{i:02d}"
            self.assertIn(oid,catalog)
            self.assertIn("### "+oid+" — ",help_doc)
            self.assertIn(oid,wiki)
        self.assertIn("pending final-module approval",help_doc)

    def test_twenty_option_native_receipt_requires_actual_focus_and_unique_inventory(self):
        from tools.verify_p02_m26_options import EXPECTED, verify_receipt
        from tools.verify_p02_m26_candidates import EXPECTED_TRANSITIONS, MODULE_TITLES
        import copy
        script=(ROOT/"scripts/capture_p01_desktop.ps1").read_text(encoding="utf-8")
        self.assertEqual(len(EXPECTED),20)
        self.assertIn("-M26OptionsOnly",(ROOT/".github/workflows/p01-desktop.yml").read_text(encoding="utf-8"))
        for i in range(1,21):
            self.assertIn(f"Capture-M26Option -Number {i} -Label ",script)
        p={"schema_version":1,"source_commit_sha":"a"*40,"built_commit_sha":"a"*40,"github_run_id":"123","native_process_id":1,
           "status":"M26_P02_OPTION_CANDIDATES_ONLY","no_user_data":True,"independent_visual_review":False,"screen_reader_verified":False,
           "full_module_release_approved":False,"query_before_reset":"zzznomatch","query_after_reset":"",
           "initial_titles":MODULE_TITLES,"selected_module":"M23","filtered_titles":MODULE_TITLES[:1],
           "reset_module":"All modules","reset_titles":MODULE_TITLES,
           "tab_transitions":[{"from":a,"key":b,"to":c,"source_focus_and_selection":True,"destination_focus_and_selection":True,
                               "previous_tab_deselected":True} for a,b,c in EXPECTED_TRANSITIONS],
           "observations":[{"option_id":oid,"screenshot_id":oid.replace("M26-OPT-","M26-P02-OPT-"),"label":label,"state":state,
              "visible_focus_name":focus,"native_focus_verified":True,"foreground_window_verified":True,
              "disabled_control_verified":state=="disabled","additional_visible_marker":
              {"M26-OPT-05":"No matching notices. Reset filters to view all.","M26-OPT-12":"Select a capability notice"}.get(oid,"")}
              for oid,(label,state,focus) in EXPECTED.items()]}
        self.assertEqual(20,len(verify_receipt(p,"a"*40,"123")))
        for key,value in (("disabled_control_verified",False),("native_focus_verified",False),("option_id","M26-OPT-02")):
            bad=copy.deepcopy(p);bad["observations"][0][key]=value
            with self.subTest(key=key), self.assertRaises(ValueError):verify_receipt(bad,"a"*40,"123")
        bad=copy.deepcopy(p);bad["observations"].pop()
        with self.assertRaises(ValueError):verify_receipt(bad,"a"*40,"123")

if __name__ == "__main__":
    unittest.main()
