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
        from tools.phase_controller import PHASE_ORDER
        self.assertEqual("P02", manifest["phase"])
        self.assertEqual(12, manifest["pr_number"])
        self.assertEqual(11, len(manifest["tasks"]))
        self.assertTrue(all(x["status"] in ("DONE", "IN_PROGRESS", "TODO", "BLOCKED")
                            for x in manifest["tasks"]))
        if phase["phase"] == "P02":
            self.assertEqual("phase/02-shared-ui", phase["active_branch"])
            self.assertEqual(12, phase["primary_pr"])
        else:
            # Retain regression coverage after a verified P02 closeout.
            self.assertIn(phase["phase"], PHASE_ORDER[PHASE_ORDER.index("P02") + 1:])

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
        self.assertIn('if (paletteOpen) {', app)
        self.assertIn('}, [paletteOpen]);', app)
        self.assertIn('inert={paletteOpen}', app)
        self.assertIn('paletteOpenerRef.current = event.currentTarget', app)
        self.assertIn('returnFocusTarget={paletteOpenerRef.current}', app)
        self.assertIn('navigationRef.current = true', palette)
        self.assertIn('returnFocusTarget?.isConnected', palette)

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

    def test_help_reader_stays_inside_filtered_results(self):
        catalog = (APP/"src/ui/help-catalog.ts").read_text(encoding="utf-8")
        help_page = (APP/"src/ui/HelpCenter.tsx").read_text(encoding="utf-8")
        self.assertIn("export function resolveVisibleHelpArticle", catalog)
        self.assertIn("resolveVisibleHelpArticle(results, articleId)", help_page)
        self.assertIn('article.id === selected?.id', help_page)
        self.assertIn('No matching help article', help_page)
        self.assertIn('openArticle(id)', help_page)
        self.assertIn('setQuery("");', help_page)
        self.assertIn('setCategory("All");', help_page)

    def test_workbench_tab_arrows_and_split_are_real_session_controls(self):
        s=(APP/"src/ui/Workbench.tsx").read_text(encoding="utf-8")
        for marker in ('role="tablist"', 'role="tabpanel"', 'ArrowLeft', 'ArrowRight',
                       'aria-selected={active === pane.key}', 'type="range"',
                       'value={split}', 'onChange={event => setSplit'):
            self.assertIn(marker, s)
        self.assertIn('disabled title="No workspace creation service yet"', s)
        self.assertNotIn("localStorage", s)

    def test_new_native_proof_never_overwrites_existing_p01_screenshots(self):
        wf = (ROOT / ".github/workflows/p01-desktop.yml").read_text(
            encoding="utf-8")
        self.assertIn("docs\\screenshots\\_ci\\M01", wf)
        for path in ("docs/screenshots/_ci/M01/*.png",
                     "docs/screenshots/_ci/M02/*.png",
                     "docs/screenshots/_ci/M19/*.png",
                     "docs/screenshots/_ci/M02/*.capture.json"):
            self.assertIn(path, wf)
        self.assertIn("ZYNOA_CAPTURE_P02", wf)
        native = (ROOT / "scripts/capture_p01_desktop.ps1").read_text(
            encoding="utf-8")
        self.assertIn("ZYN-SCREEN-008: refuse replacing existing image", native)
        self.assertIn("ZYN-SCREEN-018: refuse replacing native evidence", native)

    def test_p02_desktop_workflow_keeps_p01_real_windows_verification(self):
        wf=(ROOT/".github/workflows/p01-desktop.yml").read_text(encoding="utf-8")
        self.assertIn("phase/01-foundation", wf)
        self.assertIn("phase/02-shared-ui", wf)
        self.assertIn("npm run test:ui", wf)
        self.assertIn("npm run build", wf)
        self.assertIn("windows-latest", wf)
        self.assertNotIn("contents: write", wf)


    def test_p02_windows_pipeline_does_not_mask_ui_test_failures(self):
        wf = (ROOT / ".github/workflows/p01-desktop.yml").read_text(encoding="utf-8")
        for name, command in (
            ("Frontend TypeScript check", "npm run check"),
            ("Frontend UI algorithm tests", "npm run test:ui"),
            ("Frontend offline production bundle", "npm run build"),
        ):
            self.assertIn(
                f"- name: {name}\n        working-directory: apps/desktop\n        run: {command}",
                wf,
            )
        self.assertNotIn("npm run check\n          npm run test:ui", wf)
        self.assertNotIn("npm run test:ui\n          npm run build", wf)

    def test_small_theme_labels_meet_wcag_normal_text_contrast(self):
        import re
        css = (APP / "src/styles.css").read_text(encoding="utf-8")
        def linear(channel):
            value = int(channel, 16) / 255
            return value / 12.92 if value <= 0.04045 else ((value + 0.055) / 1.055) ** 2.4
        def luminance(rgb):
            return sum(weight * linear(rgb[i:i+2]) for i, weight in ((0, .2126), (2, .7152), (4, .0722)))
        # Independent primaries catch accidental off-by-one RGB channel parsing.
        self.assertAlmostEqual(luminance("000000"), 0.0)
        self.assertAlmostEqual(luminance("ffffff"), 1.0)
        self.assertAlmostEqual(luminance("ff0000"), 0.2126)
        self.assertAlmostEqual(luminance("00ff00"), 0.7152)
        self.assertAlmostEqual(luminance("0000ff"), 0.0722)
        for theme in ("light", "dark"):
            block = re.search(r'\.shell\[data-theme="' + theme + r'"\]\s*\{([^}]+)\}', css)
            self.assertIsNotNone(block, theme)
            colors = dict(re.findall(r'--([a-z-]+):\s*(#[0-9a-fA-F]{6})', block.group(1)))
            foreground = luminance(colors["text-tertiary"][1:])
            for name in ("canvas", "rail", "surface", "surface-raised", "surface-hover"):
                background = luminance(colors[name][1:])
                ratio = (max(foreground, background) + 0.05) / (min(foreground, background) + 0.05)
                self.assertGreaterEqual(ratio, 4.5, f"{theme} tertiary text on {name}: {ratio:.2f}:1")


    def test_workbench_keyboard_focus_visible_on_real_tabpanels(self):
        """M02-OPT-07: native Workbench tabpanels show keyboard focus."""
        css = (APP / "src/styles.css").read_text(encoding="utf-8")
        workbench = (APP / "src/ui/Workbench.tsx").read_text(encoding="utf-8")
        self.assertNotIn(".shell .workbench-tabpanel:focus { outline:none; }", css)
        self.assertIn(
            ".shell .workbench-tabpanel:focus-visible { outline: 2px solid var(--outline); outline-offset: 3px; }",
            css,
        )
        self.assertEqual(3, workbench.count('role="tabpanel" tabIndex={0}'))
        for panel in ("status", "layout", "keyboard"):
            self.assertIn(f'hidden={{active !== "{panel}"}}', workbench)
        self.assertIn("@media (prefers-reduced-motion:reduce)", css)

    def test_workbench_focus_ring_contrast_both_themes(self):
        """M02-OPT-07: focus outline has >=3:1 contrast on all semantic surfaces."""
        import re
        css = (APP / "src/styles.css").read_text(encoding="utf-8")
        def luminance(value):
            channels = [int(value[i:i+2], 16) / 255 for i in (1, 3, 5)]
            linear = [c / 12.92 if c <= .04045 else ((c + .055) / 1.055) ** 2.4
                      for c in channels]
            return sum(c * w for c, w in zip(linear, (.2126, .7152, .0722)))
        for theme in ("light", "dark"):
            block = re.search(r'\.shell\[data-theme="' + theme + r'"\]\s*\{([^}]+)\}', css)
            self.assertIsNotNone(block, theme)
            tokens = dict(re.findall(r'--([a-z-]+):\s*(#[0-9a-fA-F]{6})', block.group(1)))
            foreground = luminance(tokens["outline"])
            for background_key in ("canvas", "rail", "surface", "surface-raised", "surface-hover"):
                background = luminance(tokens[background_key])
                ratio = (max(foreground, background) + .05) / (min(foreground, background) + .05)
                self.assertGreaterEqual(ratio, 3, f"{theme} focus on {background_key}: {ratio:.2f}:1")

    def test_native_focus_capture_requires_review(self):
        native = (ROOT / "scripts/capture_p01_desktop.ps1").read_text(encoding="utf-8")
        workflow = (ROOT / ".github/workflows/p01-desktop.yml").read_text(encoding="utf-8")
        self.assertIn("-ScreenshotId 'M02-OPT-07'", native)
        self.assertIn("candidate_pending_visual_review", native)
        self.assertIn("capture_verified = $false", native)
        self.assertIn("docs/screenshots/_ci/M02/*.png", workflow)
        self.assertIn("tests.test_p02_ui_contract -v", workflow)


if __name__ == "__main__":
    unittest.main()
