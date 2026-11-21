"""P00 GitHub protected-main manifest static contract tests (no remote mutation)."""
import json
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
CONFIG = ROOT / "deploy" / "github" / "main-ruleset.json"


class MainRulesetManifestTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.ruleset = json.loads(CONFIG.read_text(encoding="utf-8"))

    def test_exact_main_scope_and_active_policy(self):
        d = self.ruleset
        self.assertEqual("branch", d["target"])
        self.assertEqual("active", d["enforcement"])
        self.assertEqual(["refs/heads/main"], d["conditions"]["ref_name"]["include"])
        self.assertEqual([], d["conditions"]["ref_name"]["exclude"])

    def test_no_bypass_and_unsafe_history_mutations(self):
        d = self.ruleset
        self.assertEqual([], d["bypass_actors"])
        kinds = {rule["type"] for rule in d["rules"]}
        self.assertTrue({"deletion", "non_fast_forward"}.issubset(kinds))

    def test_pr_required_but_no_redundant_human_approval(self):
        d = self.ruleset
        pr = next(rule for rule in d["rules"] if rule["type"] == "pull_request")
        self.assertEqual(0, pr["parameters"]["required_approving_review_count"])
        self.assertTrue(pr["parameters"]["required_review_thread_resolution"])

    def test_pinned_github_actions_check_required(self):
        d = self.ruleset
        status = next(r for r in d["rules"] if r["type"] == "required_status_checks")
        self.assertTrue(status["parameters"]["strict_required_status_checks_policy"])
        required = status["parameters"]["required_status_checks"]
        self.assertIn({"context": "governance-lint", "integration_id": 15368}, required)

    def test_no_publish_or_auto_merge_in_manifest(self):
        d = self.ruleset
        self.assertNotIn("merge", d)
        self.assertNotIn("auto_merge", d)
        self.assertNotIn("github_token", json.dumps(d).lower())


if __name__ == "__main__":
    unittest.main()
