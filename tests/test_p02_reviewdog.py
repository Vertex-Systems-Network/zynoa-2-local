"""Reviewdog static checker: line-specific findings, safe scope and no false success."""
import unittest
from pathlib import Path

from tools.p02_reviewdog import review, review_text

ROOT = Path(__file__).resolve().parents[1]


class P02ReviewdogTests(unittest.TestCase):
    def test_detects_unsafe_html_and_storage_with_source_lines(self):
        code = 'const good = "ok";\nconst value = localStorage.getItem("x");\nconst x = dangerouslySetInnerHTML;\n'
        issues = review_text("apps/desktop/src/App.tsx", code)
        self.assertEqual([2, 3], [issue[1] for issue in issues])
        self.assertIn("P02-RD002", issues[0][2])
        self.assertIn("P02-RD001", issues[1][2])

    def test_reports_missing_img_alt(self):
        self.assertIn("P02-RD007", review_text("apps/desktop/src/ui/Test.tsx",
                                                '<img src="test.png" />')[0][2])
        self.assertEqual([], review_text("apps/desktop/src/ui/Test.tsx",
                                          '<img src="test.png" alt="Test" />'))

    def test_visible_focus_allowed_hidden_interactive_focus_denied(self):
        self.assertEqual([], review_text("apps/desktop/src/styles.css",
                                          ".shell button:focus-visible { outline:2px solid red; }"))
        self.assertEqual([], review_text("apps/desktop/src/styles.css",
                                          "main:focus { outline:none; }"))
        issues = review_text("apps/desktop/src/styles.css",
                             ".shell .workbench-tabpanel:focus { outline:none; }")
        self.assertEqual(1, len(issues))
        self.assertEqual(1, issues[0][1])
        self.assertIn("P02-RD008", issues[0][2])

    def test_non_ui_files_out_of_scope(self):
        self.assertEqual([], review_text("docs/help/articles/M02.md", "localStorage eval("))
        self.assertEqual([], review_text("tests/example.py", "eval("))

    def test_actual_p02_ui_has_no_static_reviewdog_findings(self):
        self.assertEqual([], review(ROOT))


if __name__ == "__main__":
    unittest.main()
