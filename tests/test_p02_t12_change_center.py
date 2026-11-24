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

if __name__ == "__main__":
    unittest.main()
