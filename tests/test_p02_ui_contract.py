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
        self.assertIn('role="tab"', workbench)
        self.assertIn('aria-selected={active === pane.key}', workbench)
        self.assertIn('onKeyDown={event => tabKeys(event, index)}', workbench)
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
        self.assertIn("-Shortcut '{TAB}{TAB}{TAB}{TAB}{TAB}'", native)
        self.assertLess(native.index("-ScreenshotId 'M02-S03'"), native.index("-ScreenshotId 'M02-OPT-07'"))
        self.assertLess(native.index("-ScreenshotId 'M02-OPT-07'"), native.index("-ScreenshotId 'M02-S05'"))
        self.assertIn("candidate_pending_visual_review", native)
        self.assertIn("capture_verified = $false", native)
        self.assertIn("docs/screenshots/_ci/M02/*.png", workflow)
        self.assertIn("tests.test_p02_ui_contract -v", workflow)


    def test_t02_final_native_theme_and_keyboard_guide_capture_contract(self):
        """T02.12: new native themes and keyboard guide remain source-SHA candidates."""
        capture = (ROOT / "scripts/capture_p01_desktop.ps1").read_text(encoding="utf-8")
        for screenshot in ("M02-S07", "P02-T02-12-LIGHT", "P02-T02-12-DARK"):
            self.assertIn("-ScreenshotId '" + screenshot + "'", capture)
        self.assertIn("-Shortcut '+{TAB}{END}{TAB}'", capture)
        self.assertIn("-Shortcut '^{2}{TAB}{TAB}{TAB}{HOME}{DOWN}{DOWN}{TAB}'", capture)
        self.assertIn("-Shortcut '+{TAB}{HOME}{DOWN}{TAB}'", capture)
        self.assertLess(capture.index("-ScreenshotId 'M02-OPT-07'"),
                        capture.index("-ScreenshotId 'M02-S07'"))
        self.assertLess(capture.index("-ScreenshotId 'M02-S07'"),
                        capture.index("-ScreenshotId 'M02-S05'"))
        self.assertLess(capture.index("-ScreenshotId 'P02-T02-07-continued'"),
                        capture.index("-ScreenshotId 'P02-T02-12-LIGHT'"))
        self.assertLess(capture.index("-ScreenshotId 'P02-T02-12-LIGHT'"),
                        capture.index("-ScreenshotId 'P02-T02-12-DARK'"))
        self.assertIn("candidate_pending_visual_review", capture)
        self.assertIn("capture_verified = $false", capture)

    def test_gallery_interaction_states_keep_input_independent(self):
        """T02.06: action selection cannot erase typed sample content."""
        source = (APP / "src/ui/Workbench.tsx").read_text(encoding="utf-8")
        for marker in (
            'const [selectedAction, setSelectedAction]',
            'setSelectedAction("primary")',
            'setSelectedAction("secondary")',
            'aria-pressed={selectedAction === "primary"}',
            'aria-pressed={selectedAction === "secondary"}',
            'role="group" aria-label="Select a gallery action preview"',
            'disabled title="Unavailable in this foundation preview"',
            'role="status"',
            'role="group" aria-label="Illustrative status states, not live service health"',
            'value={sampleInput}',
            'onChange={event => setSampleInput(event.target.value)}',
        ):
            self.assertIn(marker, source)
        self.assertNotIn('setSampleInput("Action preview selected")', source)
        self.assertNotIn('setSampleInput("Secondary action selected")', source)

    def test_gallery_selected_hover_disabled_css_contracts(self):
        """T02.06: active, hovered, disabled and feedback examples are distinct."""
        css = (APP / "src/styles.css").read_text(encoding="utf-8")
        for token in (
            '.shell .gold-action:hover:not(:disabled)',
            '.shell .subtle-action:hover:not(:disabled)',
            '.shell button:disabled { cursor:not-allowed;',
            '.shell .component-row button[aria-pressed="true"]',
            '.shell .component-row button[aria-pressed="true"]::after',
            '.shell .component-row button:disabled { box-shadow:none; }',
            '.shell .component-state-list',
            '.shell .pending-chip', '.shell .warning-chip', '.shell .error-chip',
        ):
            self.assertIn(token, css, token)
        workbench = (APP / "src/ui/Workbench.tsx").read_text(encoding="utf-8")
        self.assertIn("Nothing is saved.", workbench)
        self.assertNotIn("fetch(", workbench)
        self.assertNotIn("localStorage", workbench)

    def test_adaptive_gallery_and_split_panes_at_native_minimum(self):
        """T02.07: responsive rules cover the 900px native width."""
        css = (APP / "src/styles.css").read_text(encoding="utf-8")
        workbench = (APP / "src/ui/Workbench.tsx").read_text(encoding="utf-8")
        native = json.loads((APP / "src-tauri/tauri.conf.json").read_text(encoding="utf-8"))
        window = native["app"]["windows"][0]
        self.assertEqual(900, window["minWidth"])
        self.assertTrue(window["resizable"])
        self.assertIn("@media (max-width:950px)", css)
        self.assertIn("@media (max-width:850px)", css)
        self.assertNotIn(".shell .gallery-metrics { grid-template-columns:repeat(3,minmax(0,1fr)); }", css)
        self.assertIn(".shell .gallery-grid { grid-template-columns:minmax(0,1fr); }", css)
        self.assertIn("repeat(auto-fit,minmax(140px,1fr))", css)
        self.assertIn(".shell .component-state-list>div { flex-wrap:wrap;", css)
        self.assertIn("overflow-wrap:anywhere;", css)
        self.assertIn("minmax(0, ", workbench)
        self.assertIn("100 - split", workbench)
        self.assertIn("aria-valuetext=", workbench)
        self.assertIn("min={25} max={65} step={5}", workbench)

    def test_native_gallery_state_and_narrow_capture_is_fail_closed(self):
        """T02.06/07: native evidence is real and never self-certifying."""
        capture = (ROOT / "scripts/capture_p01_desktop.ps1").read_text(encoding="utf-8")
        for name in ("P02-T02-06", "P02-T02-07", "P02-T02-07-continued"):
            self.assertIn(f"-ScreenshotId '{name}'", capture)
        self.assertIn("-Shortcut '{TAB}{TAB}{TAB}{ENTER}{PGDN}'", capture)
        self.assertIn("[ZynoaScreenWin32]::MoveWindow", capture)
        self.assertIn("DwmGetWindowAttribute", capture)
        self.assertIn("$narrowWidth -gt 920", capture)
        self.assertIn("$narrowWidth -ge $priorWidth", capture)
        self.assertIn("$script:bounds = $narrowVisible", capture)
        for code in ("ZYN-SCREEN-020", "ZYN-SCREEN-021", "ZYN-SCREEN-022"):
            self.assertIn(code, capture)
        self.assertIn("candidate_pending_visual_review", capture)
        self.assertIn("capture_verified = $false", capture)
        self.assertLess(capture.index("-ScreenshotId 'M02-S05'"), capture.index("-ScreenshotId 'P02-T02-06'"))
        self.assertLess(capture.index("-ScreenshotId 'M19-S01'"), capture.index("-ScreenshotId 'P02-T02-07'"))
        wf = (ROOT / ".github/workflows/p01-desktop.yml").read_text(encoding="utf-8")
        self.assertIn("tests.test_p02_ui_contract -v", wf)
        self.assertIn("docs/screenshots/_ci/M02/*.png", wf)


    def test_compact_properties_preview_is_real_and_accessible(self):
        """M02-OPT-03: toggle controls real local property row density, not persistent data."""
        wb = (APP / "src/ui/Workbench.tsx").read_text(encoding="utf-8")
        css = (APP / "src/styles.css").read_text(encoding="utf-8")
        for snippet in (
            'const [compactProperties, setCompactProperties] = useState(false);',
            'aria-pressed={compactProperties}',
            'aria-controls="workbench-properties-preview"',
            'onClick={() => setCompactProperties(current => !current)}',
            'data-properties-density={compactProperties ? "compact" : "comfortable"}',
            'id="workbench-properties-preview"',
            'aria-label="Illustrative properties rows"',
            'Compact property spacing enabled for this preview.',
            'Comfortable property spacing enabled for this preview.',
            'No real project properties are loaded.',
        ):
            self.assertIn(snippet, wb, snippet)
        for rule in (
            '.shell .properties-heading .subtle-action[aria-pressed="true"]',
            '.shell .properties-preview[data-properties-density="compact"] .property-preview-row',
            '@media (max-width:950px)',
        ):
            self.assertIn(rule, css)
        self.assertNotIn("localStorage", wb)
        self.assertNotIn("sessionStorage", wb)
        self.assertNotIn("fetch(", wb)
        native = (ROOT / "scripts/capture_p01_desktop.ps1").read_text(encoding="utf-8")
        self.assertIn("-ScreenshotId 'M02-OPT-03'", native)
        self.assertIn("-Shortcut '+{TAB}{LEFT}{TAB}{TAB}{TAB}{ENTER}{PGDN}'", native)
        verifier = (ROOT / "tools/verify_p02_native_evidence.py").read_text(encoding="utf-8")
        self.assertIn('"M02-OPT-03"', verifier)



if __name__ == "__main__":
    unittest.main()
