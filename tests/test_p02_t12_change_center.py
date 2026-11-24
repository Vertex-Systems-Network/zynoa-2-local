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

if __name__ == "__main__":
    unittest.main()
