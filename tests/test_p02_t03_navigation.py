"""P02-T03 accessible adaptive workspace navigation source and evidence contracts.

These contracts do not replace the real Windows Tauri screenshot or visual review.
"""
import json
from pathlib import Path
import unittest

ROOT = Path(__file__).resolve().parents[1]
APP = ROOT / "apps/desktop"


class P02T03NavigationTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.shell = (APP / "src/App.tsx").read_text(encoding="utf-8")
        cls.css = (APP / "src/styles.css").read_text(encoding="utf-8")
        cls.wb = (APP / "src/ui/Workbench.tsx").read_text(encoding="utf-8")
        cls.capture = (ROOT / "scripts/capture_p01_desktop.ps1").read_text(encoding="utf-8")

    def test_auto_collapse_and_resize_listener_cleanup(self):
        for marker in (
            'window.matchMedia("(max-width: 1000px)")',
            'setNavigationCollapsed(query.matches);',
            'const update = (event: MediaQueryListEvent) => setNavigationCollapsed(event.matches);',
            'query.addEventListener("change", update);',
            'query.removeEventListener("change", update);',
            'data-nav-collapsed={navigationCollapsed}',
        ):
            self.assertIn(marker, self.shell, marker)
        self.assertIn("width:78px; flex:0 0 78px;", self.css)
        self.assertIn('@media (max-width:950px)', self.css)
        for unsafe in ("localStorage", "sessionStorage", "fetch("):
            self.assertNotIn(unsafe, self.shell)

    def test_nav_toggle_is_keyboard_reachable_reversible_and_modal_safe(self):
        for marker in (
            'className="nav-toggle"',
            'aria-controls="application-sections"',
            'aria-expanded={!navigationCollapsed}',
            'aria-keyshortcuts="Alt+N"',
            'onClick={() => setNavigationCollapsed(value => !value)}',
            'event.altKey && !event.ctrlKey && !event.metaKey && !event.shiftKey',
            'event.key.toLowerCase() === "n"',
            'setNavigationCollapsed(current => !current)',
            'event.target.matches("input,textarea,select,[contenteditable=true]")',
        ):
            self.assertIn(marker, self.shell, marker)
        self.assertIn('.shell .nav-toggle:focus-visible { outline:2px solid var(--outline);', self.css)
        self.assertIn('min-height:44px;', self.css)
        self.assertLess(self.shell.index('if (paletteOpen) {'),
                        self.shell.index('event.key.toLowerCase() === "n"'))

    def test_collapsed_icons_keep_accessible_names_sections_and_active_view(self):
        for marker in (
            '<aside className="sidebar" aria-label="Primary navigation"',
            '<nav id="application-sections" aria-label="Application sections">',
            'role="group" aria-label={section + " views"}',
            'aria-current={view === page.key ? "page" : undefined}',
            'aria-label={page.title + " (" +',
            'aria-keyshortcuts={page.key === "help" ? "F1"',
            'className="nav-link-title"',
            'className="offline" aria-label="Local-first interface"',
        ):
            self.assertIn(marker, self.shell, marker)
        for marker in (
            '.shell .sidebar[data-nav-collapsed="true"] .nav-link-title,',
            '.shell .sidebar[data-nav-collapsed="true"] .nav-link kbd,',
            '.shell .sidebar[data-nav-collapsed="true"] .nav-toggle-label,',
            '.shell .sidebar[data-nav-collapsed="true"] .offline',
        ):
            self.assertIn(marker, self.css, marker)

    def test_breadcrumb_and_main_are_semantic_accessible_landmarks(self):
        for marker in (
            '<main id="main-content" tabIndex={-1} inert={paletteOpen}>',
            '<nav className="crumb" aria-label="Breadcrumb">',
            '<strong aria-current="page">',
            'inert={paletteOpen}',
            'surface.scrollTop = 0;',
            'surface.focus({ preventScroll: true });',
        ):
            self.assertIn(marker, self.shell)
        self.assertIn('.shell .topbar .crumb { display:flex;', self.css)
        self.assertIn('.shell .content, .shell main { min-width:0; }', self.css)

    def test_structured_panes_bounded_and_named(self):
        for marker in (
            'role="tablist"',
            'role="tabpanel" tabIndex={0}',
            'role="group" aria-label="Adjustable workspace pane preview"',
            'role="region" aria-label="Preview navigation pane"',
            'role="region" aria-label="Preview content pane"',
            'minmax(0, ',
            '100 - split',
            'aria-valuetext=',
            'min={25} max={65} step={5}',
        ):
            self.assertIn(marker, self.wb, marker)

    def test_narrow_real_tauri_capture_is_fail_closed_and_unreviewed(self):
        names = ("P02-T03-RAIL-COLLAPSED", "P02-T03-RAIL-EXPANDED",
                 "P02-T03-RAIL-RESTORED")
        verifier = (ROOT / "tools/verify_p02_native_evidence.py").read_text(encoding="utf-8")
        for name in names:
            self.assertIn(f"-ScreenshotId '{name}'", self.capture)
            self.assertIn(f'"{name}"', verifier)
        self.assertIn("-Shortcut '{F1}^{5}'", self.capture)
        self.assertGreaterEqual(self.capture.count("-Shortcut '%n'"), 2)
        indices = [self.capture.index(f"-ScreenshotId '{name}'") for name in names]
        self.assertEqual(indices, sorted(indices))
        self.assertIn("T03 rail toggle must visibly change", verifier)
        self.assertIn("T03 navigation rail proof must come from native narrow window", verifier)
        self.assertIn("candidate_pending_visual_review", self.capture)
        self.assertIn("capture_verified = $false", self.capture)
        self.assertIn("for ($attempt = 1; $attempt -le 3; $attempt++)", self.capture)
        self.assertIn("for ($x = 0; $x -lt 24; $x++)", self.capture)
        self.assertIn("for ($y = 0; $y -lt 16; $y++)", self.capture)
        self.assertIn("$width / 24", self.capture)
        self.assertIn("$height / 16", self.capture)
        self.assertIn("if ($colors.Count -ge 6) { break }", self.capture)

        self.assertIn("if ($colors.Count -lt 6) {", self.capture)
        self.assertIn("DEBUG-", self.capture)
        self.assertIn("throw 'ZYN-SCREEN-017: blank native follow-up frame'", self.capture)


    def test_help_wiki_and_acceptance_are_consistent(self):
        help_text = (ROOT / "docs/help/articles/M02.md").read_text(encoding="utf-8")
        wiki_text = (ROOT / "docs/wiki/pages/M02.md").read_text(encoding="utf-8")
        evidence = (ROOT / "docs/evidence/P02_T03_ACCEPTANCE.md").read_text(encoding="utf-8")
        for marker in ("P02-T03", "Alt+N", "900px", "session"):
            self.assertIn(marker, help_text)
        for marker in ("P02-T03", "Alt+N", "78px", "PENDING"):
            self.assertIn(marker, wiki_text + evidence)
        self.assertTrue("NATIVE RUN AND REVIEW PENDING" in evidence or
                        "NATIVE REVIEW ACCEPTED" in evidence)
        self.assertIn("15 final M02 manifest entries", wiki_text + evidence)

    def test_official_task_remains_evidence_gated(self):
        data = json.loads((ROOT / "docs/state/pr-tasks/P02.json").read_text(encoding="utf-8"))
        task = next(x for x in data["tasks"] if x["id"] == "P02-T03")
        self.assertIn(task["status"], ("IN_PROGRESS", "DONE"))
        self.assertEqual(12, data["pr_number"])


if __name__ == "__main__":
    unittest.main()
