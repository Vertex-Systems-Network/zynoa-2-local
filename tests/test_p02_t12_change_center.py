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
        self.assertIn('<button type="button" disabled>{label}</button>',view)
        self.assertIn("onClick={onHelp}",view)
        self.assertNotIn('aria-disabled="false"', view)

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

if __name__ == "__main__":
    unittest.main()
