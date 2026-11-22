"""P02 M02/M19 source contract: does not substitute for real Windows UI screenshots."""
from pathlib import Path
import json
import unittest

ROOT = Path(__file__).resolve().parents[1]
APP = ROOT / "apps" / "desktop"


class P02UIContractTests(unittest.TestCase):
    def test_p02_phase_and_manifest_require_current_primary_pr(self):
        phase = json.loads((ROOT/"docs/state/PHASE.json").read_text(encoding="utf-8"))
        manifest = json.loads((ROOT/"docs/state/pr-tasks/P02.json").read_text(encoding="utf-8"))
        self.assertEqual("P02", phase["phase"])
        self.assertEqual("phase/02-shared-ui", phase["active_branch"])
        self.assertEqual(12, phase["primary_pr"])
        self.assertEqual("P02", manifest["phase"])
        self.assertEqual(12, manifest["pr_number"])
        self.assertEqual(11, len(manifest["tasks"]))
        self.assertLess(sum(x["status"] == "DONE" for x in manifest["tasks"]), 11)

    def test_ui_features_keep_native_boundary_unmodified(self):
        app = (APP/"src/App.tsx").read_text(encoding="utf-8")
        for item in ("CommandPalette", "HelpCenter", "ComponentGallery", "Workbench",
                     "effectiveTheme", 'data-density={density}', "session-only",
                     "Native services require verification", "No workspace data stored"):
            self.assertIn(item, app)
        for unsafe in ("fetch(", "localStorage", "sessionStorage", "dangerouslySetInnerHTML",
                       "http://", "https://", "invoke(", "new WebSocket("):
            self.assertNotIn(unsafe, app)
        cfg = json.loads((APP/"src-tauri/tauri.conf.json").read_text(encoding="utf-8"))
        cap = json.loads((APP/"src-tauri/capabilities/main-readonly.json").read_text(encoding="utf-8"))
        self.assertEqual(["main-readonly"], cfg["app"]["security"]["capabilities"])
        self.assertEqual(["allow-workspace-handshake"], cap["permissions"])

    def test_palette_keyboard_focus_and_accessible_dialog(self):
        palette = (APP/"src/ui/CommandPalette.tsx").read_text(encoding="utf-8")
        for item in ('role="dialog"', 'aria-modal="true"', 'returnFocusRef.current?.focus',
                     'inputRef.current?.focus()', 'event.key === "Escape"',
                     'event.key === "Tab"', 'aria-selected={selected === index}',
                     'onNavigate(view)', "Search available commands"):
            self.assertIn(item, palette)
        app = (APP/"src/App.tsx").read_text(encoding="utf-8")
        self.assertIn('event.key.toLowerCase() === "p"', app)
        self.assertIn('event.key === "F1"', app)

    def test_real_help_catalog_bundled_and_does_not_render_raw_html(self):
        catalog = (APP/"src/ui/help-catalog.ts").read_text(encoding="utf-8")
        help_page = (APP/"src/ui/HelpCenter.tsx").read_text(encoding="utf-8")
        for marker in ("export function searchHelp", "findHelpArticle", "quick-start",
                       "native-troubleshooting", "M19-OPT-01", "M19-OPT-08"):
            self.assertIn(marker, catalog)
        self.assertIn('type="search"', help_page)
        self.assertIn('role="status"', help_page)
        self.assertIn('maxLength={120}', help_page)
        for unsafe in ("fetch(", "dangerouslySetInnerHTML", "localStorage", "axios",
                       "<iframe", "eval("):
            self.assertNotIn(unsafe, catalog+help_page)

    def test_workbench_tab_arrows_and_split_are_real_session_controls(self):
        s=(APP/"src/ui/Workbench.tsx").read_text(encoding="utf-8")
        for marker in ('role="tablist"', 'role="tabpanel"', 'ArrowLeft', 'ArrowRight',
                       'aria-selected={active === pane.key}', 'type="range"',
                       'value={split}', 'onChange={event => setSplit'):
            self.assertIn(marker, s)
        self.assertIn('disabled title="No workspace creation service yet"', s)
        self.assertNotIn("localStorage", s)

    def test_p02_desktop_workflow_keeps_p01_real_windows_verification(self):
        wf=(ROOT/".github/workflows/p01-desktop.yml").read_text(encoding="utf-8")
        self.assertIn("phase/01-foundation", wf)
        self.assertIn("phase/02-shared-ui", wf)
        self.assertIn("npm run test:ui", wf)
        self.assertIn("npm run build", wf)
        self.assertIn("windows-latest", wf)
        self.assertNotIn("contents: write", wf)


if __name__ == "__main__":
    unittest.main()
