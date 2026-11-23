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
        for name in ("articles", "troubleshoot", "faq", "wiki"):
            self.assertIn(f'["{name}",', self.center)
        self.assertIn('<HelpWorkflows mode={mode} onOpenArticle={openArticle} />', self.center)
        self.assertIn('<LocalArticleReport articleId={selected.id} />', self.center)
        self.assertNotIn('disabled title="Issue reporting service is not enabled"', self.center)
        self.assertIn('setMode("articles")', self.center)

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

    def test_real_node_tests_verify_negative_cases(self):
        for marker in (
            "validateOfflineHelpCatalog()", "nextWizardStep", "getWizardStep",
            "localBrokenArticleReport", "helpRoute", "resolveHelpRoute",
            '"help://article/../../secrets"', "assert.equal(map.published, false)",
            'assert.equal(localBrokenArticleReport("quick-start", "invalid"), null)',
        ):
            self.assertIn(marker, self.tests)

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
