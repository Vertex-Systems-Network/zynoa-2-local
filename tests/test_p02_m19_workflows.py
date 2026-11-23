"""P02 M19 real offline article + recovery + Wiki/report workflow source acceptance."""
from pathlib import Path
import re
import unittest

ROOT = Path(__file__).resolve().parents[1]
UI = ROOT / "apps/desktop/src/ui"


class M19OfflineWorkflowTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.catalog = (UI / "help-catalog.ts").read_text(encoding="utf-8")
        cls.domain = (UI / "help-workflows.ts").read_text(encoding="utf-8")
        cls.widget = (UI / "HelpWorkflows.tsx").read_text(encoding="utf-8")
        cls.center = (UI / "HelpCenter.tsx").read_text(encoding="utf-8")
        cls.css = (ROOT / "apps/desktop/src/styles.css").read_text(encoding="utf-8")
        cls.package = (ROOT / "apps/desktop/package.json").read_text(encoding="utf-8")
        cls.tests = (ROOT / "apps/desktop/tests/ui-logic.test.mjs").read_text(encoding="utf-8")

    def test_real_workflows_are_in_main_help_navigation_not_disabled_previews(self):
        for name in ("articles", "options", "tour", "troubleshoot", "faq", "wiki"):
            self.assertIn(f'["{name}",', self.center)
        self.assertIn('<HelpWorkflows mode={mode} onOpenArticle={openArticle}', self.center)
        self.assertIn('initialOptionId={destination?.kind', self.center)
        self.assertIn('findHelpOption(initialOptionId)', self.widget)
        self.assertIn('<LocalArticleReport articleId={selected.id} />', self.center)
        self.assertNotIn('disabled title="Issue reporting service is not enabled"', self.center)
        self.assertIn('setMode("articles")', self.center)

    def test_all_option_guides_have_offline_routes_and_working_reader(self):
        option_source = (UI / "help-options.ts").read_text(encoding="utf-8")
        for token in ("helpOptionReferences", "resolveOptionHelpRoute",
                      "searchHelpOptions", "validateHelpOptionReferences",
                      "help://option/", "Missing or duplicate option reference"):
            self.assertIn(token, option_source)
        for token in ('mode === "options"', 'Open verified local option',
                      'Read full bundled guide', 'No matching options',
                      'help-option-route', 'aria-pressed={selectedOption?.id === option.id}'):
            self.assertIn(token, self.widget)
        self.assertIn('["options", "Option reference"]', self.center)
        self.assertIn("src/ui/help-options.ts", self.package)
        self.assertIn('test("M02/M19 all sixteen option guides', self.tests)

    def test_guided_tour_has_real_bounded_navigation(self):
        for marker in ('getGuidedTourStep', 'guidedTourSteps', 'Number.isInteger'):
            self.assertIn(marker, self.domain)
        for marker in ('mode === "tour"', 'Previous lesson', 'Next lesson',
                       'Finish guided tour', 'Restart tour', 'Read related offline guide',
                       'role="status" aria-live="polite"'):
            self.assertIn(marker, self.widget)
        self.assertIn('["tour", "Guided tour"]', self.center)
        self.assertIn('test("M19 guided onboarding', self.tests)

    def test_wizard_has_actual_choice_and_transition_controls(self):
        for control in ("help-issue-picker", "This fixed it", "Still stuck — next step",
                        "Previous step", "Start over", "getWizardStep", "nextWizardStep",
                        "Read this offline article"):
            self.assertIn(control, self.widget)
        self.assertIn("setIndex(next);", self.widget)
        self.assertIn("setResolved(true)", self.widget)
        self.assertIn("setExhausted(true)", self.widget)
        self.assertIn("wizardIssues", self.domain)
        self.assertIn("Number.isInteger", self.domain)

    def test_faq_glossary_have_real_anchored_content_and_article_routes(self):
        for label in ("Frequently asked questions", "<details", "<summary>",
                      "helpGlossary.map", "helpFaq.map", "Read related guide"):
            self.assertIn(label, self.widget)
        self.assertIn("helpFaq = [", self.domain)
        self.assertIn("helpGlossary = [", self.domain)

    def test_wiki_checker_is_local_fail_closed_and_does_not_publish(self):
        for label in ("resolveHelpRoute", "validateOfflineHelpCatalog",
                      "Open verified offline reference", "Unrecognized or broken",
                      "Check bundled article and Wiki mappings"):
            self.assertIn(label, self.widget)
        self.assertIn('publication: "source-preview-not-published"', self.domain)
        self.assertIn("if (wiki.published)", self.domain)
        self.assertIn('^help:\\/\\/article\\/', self.domain)
        self.assertIn("transmitted: false", self.domain)
        for source in ("docs/wiki/pages/M02.md", "docs/wiki/pages/M19.md"):
            self.assertTrue((ROOT / source).is_file(), source)

    def test_local_report_is_selectable_and_never_transmits_private_content(self):
        for marker in ('<textarea id="m19-report-payload" readOnly',
                       "navigator.clipboard?.writeText", "Copy report locally",
                       "localBrokenArticleReport", "Not sent", "transmitted: false"):
            self.assertIn(marker, self.widget + self.domain)
        for forbidden in ("fetch(", "localStorage", "sessionStorage", "XMLHttpRequest",
                          "sendBeacon(", "dangerouslySetInnerHTML", "eval("):
            self.assertNotIn(forbidden, self.widget + self.domain)

    def test_versioned_bundle_has_broad_real_article_content(self):
        for label in ("wizard-guide", "wiki-mapping", "faq-glossary",
                      "navigation", "report-guide", "M19-OPT-06", "M19-OPT-07"):
            self.assertIn(label, self.catalog)
        self.assertIn('catalog_version: "2026.11-p02"', self.domain)
        self.assertIn('offline_only: true', self.domain)
        self.assertIn("catalog " + "{offlineHelpContract.catalog_version}", self.center)
        self.assertIn("src/ui/help-workflows.ts", self.package)
        self.assertIn("requestOfflineHelp", self.domain)
        self.assertIn('code: "M19-CATALOG-409"', self.domain)
        self.assertIn('code: "M19-QUERY-400"', self.domain)
        self.assertIn("requestOfflineHelp({", self.center)
        self.assertIn('query, category, limit: 50', self.center)
        self.assertIn('role="alert" className="help-search-error"', self.center)


    def test_real_node_tests_verify_negative_cases(self):
        for marker in (
            "validateOfflineHelpCatalog()", "nextWizardStep", "getWizardStep",
            "localBrokenArticleReport", "helpRoute", "resolveHelpRoute",
            '"help://article/../../secrets"', "assert.equal(map.published, false)",
            'assert.equal(localBrokenArticleReport("quick-start", "invalid"), null)',
        ):
            self.assertIn(marker, self.tests)

    def test_six_mode_real_native_capture_includes_option_reference(self):
        capture=(ROOT/"scripts/capture_p01_desktop.ps1").read_text(encoding="utf-8")
        verifier=(ROOT/"tools/verify_p02_native_evidence.py").read_text(encoding="utf-8")
        self.assertIn("M19-OPTION-REFERENCE-CI",capture)
        self.assertIn("M19-OPTION-REFERENCE-CI",verifier)
        self.assertIn("M19-FAQ-GLOSSARY-CI",capture)
        self.assertIn("M19 FAQ must visually differ",verifier)
        self.assertIn("'M19-S04' -Shortcut '{TAB}{TAB}{TAB}{TAB}{TAB}{ENTER}",capture)
        self.assertIn("+{TAB}+{TAB}+{TAB}+{TAB}+{TAB}{ENTER}",capture)
        self.assertIn("M19 option reference must differ",verifier)

    def test_windows_ci_cannot_skip_m19_from_docs_only_final_commit(self):
        workflow = (ROOT / ".github/workflows/p01-desktop.yml").read_text(encoding="utf-8")
        self.assertIn("git diff --name-only FETCH_HEAD HEAD", workflow)
        self.assertNotIn("git diff --name-only HEAD^ HEAD", workflow)
        self.assertIn("tests.test_p02_m19_workflows -v", workflow)
        self.assertIn("docs/help/articles/M19.md", workflow)
        self.assertIn("docs/wiki/pages/M19.md", workflow)
        self.assertIn("apps/desktop/", workflow)

    def test_responsive_workflow_ui_has_keyboard_focus_and_semantic_status(self):
        for marker in ("help-workflow-switch", "help-tool-panel", "help-faq-grid",
                       "help-report-body", "help-tool-field", "focus-visible"):
            self.assertIn(marker, self.css)
        self.assertIn('aria-pressed={mode === key}', self.center)
        self.assertIn('aria-expanded={visible}', self.widget)
        self.assertIn('aria-labelledby="help-troubleshoot-title"', self.widget)
        self.assertIn('role="status"', self.widget)


if __name__ == "__main__":
    unittest.main()
