"""Authenticated GitHub readback tests — no network, no credentials."""
import unittest
from urllib.parse import urlparse
from tools.github_gateway import GitHubGateway, GitHubEvidenceError

SHA = "c" * 40
MERGE = "d" * 40
BRANCH = "phase/00-governance"
REPO = "Vertex-Systems-Network/zynoa-2-local"


class FakeTransport:
    def __init__(self):
        self.pr_merged = True
        self.pr_draft = False
        self.main_protected = True
        self.main_sha = MERGE
        self.issue_open = False
        self.checks = [{"name": "governance-lint", "head_sha": SHA, "status": "completed", "conclusion": "success", "app": {"id": 42}}]
        self.rules = [
            {"type": "pull_request", "parameters": {}},
            {"type": "required_status_checks", "parameters": {
                "required_status_checks": [
                    {"context": "governance-lint", "integration_id": 42}
                ]
            }},
        ]
        self.head = SHA
        self.head_ref = BRANCH
        self.request_count = 0

    def __call__(self, method, url, headers, body, timeout):
        self.request_count += 1
        assert method == "GET"
        assert body is None
        assert url.startswith("https://api.github.com/repos/" + REPO)
        assert headers["Authorization"] == "Bearer fake-token"
        path = urlparse(url).path
        if path.endswith("/pulls/1"):
            return {
                "number": 1, "head": {"ref": self.head_ref, "sha": self.head},
                "base": {"ref": "main"}, "merged": self.pr_merged,
                "merged_at": "2026-11-18T00:00:00Z" if self.pr_merged else None,
                "merge_commit_sha": MERGE, "draft": self.pr_draft,
            }
        if path.endswith("/rules/branches/main"):
            return self.rules
        if path.endswith("/branches/main"):
            return {"name": "main", "protected": self.main_protected, "commit": {"sha": self.main_sha}}
        if path.endswith("/commits/" + SHA + "/check-runs"):
            return {"total_count": len(self.checks), "check_runs": self.checks}
        if path.endswith("/issues/3"):
            return {"number": 3, "state": "open" if self.issue_open else "closed"}
        if path.endswith("/" + REPO):
            return {"full_name": REPO, "allow_auto_merge": True}
        raise AssertionError("Unexpected route: " + path)


STATE = {"phase": "P00", "active_branch": BRANCH, "primary_pr": 1}


class GitHubEvidenceTests(unittest.TestCase):
    def build(self):
        fake = FakeTransport()
        client = GitHubGateway(REPO, token="fake-token", transport=fake)
        return client, fake

    def test_authenticated_merged_checks_and_closed_blocker(self):
        client, fake = self.build()
        snapshot = client.observe(STATE)
        self.assertTrue(snapshot["authenticated_remote"])
        self.assertTrue(snapshot["transition_ready"])
        self.assertTrue(snapshot["checks_passed"])
        self.assertTrue(snapshot["rules_policy_verified"])
        self.assertEqual(MERGE, snapshot["merge_sha"])
        self.assertGreaterEqual(fake.request_count, 5)

    def test_unmerged_draft_never_advances(self):
        client, fake = self.build()
        fake.pr_merged = False
        fake.pr_draft = True
        snap = client.observe(STATE)
        self.assertFalse(snap["transition_ready"])
        self.assertIsNone(snap["merge_sha"])

    def test_open_blocker_blocks_transition(self):
        client, fake = self.build()
        fake.issue_open = True
        snap = client.observe(STATE)
        self.assertEqual([3], snap["blocker_issue_numbers"])
        self.assertFalse(snap["transition_ready"])

    def test_no_branch_protection_blocks_transition(self):
        client, fake = self.build()
        fake.main_protected = False
        self.assertFalse(client.observe(STATE)["transition_ready"])

    def test_protected_branch_without_required_pr_rule_blocks(self):
        client, fake = self.build()
        fake.rules = [r for r in fake.rules if r["type"] != "pull_request"]
        snapshot = client.observe(STATE)
        self.assertTrue(snapshot["branch_protected"])
        self.assertFalse(snapshot["rules_policy_verified"])
        self.assertFalse(snapshot["transition_ready"])

    def test_required_check_without_pinned_app_blocks(self):
        client, fake = self.build()
        fake.rules[1]["parameters"]["required_status_checks"][0]["integration_id"] = None
        self.assertFalse(client.observe(STATE)["rules_policy_verified"])

    def test_wrong_check_provider_blocks(self):
        client, fake = self.build()
        fake.checks[0]["app"]["id"] = 999
        snap = client.observe(STATE)
        self.assertTrue(snap["checks_passed"])
        self.assertFalse(snap["rules_policy_verified"])

    def test_no_required_status_rule_blocks(self):
        client, fake = self.build()
        fake.rules = [fake.rules[0]]
        self.assertFalse(client.observe(STATE)["rules_policy_verified"])

    def test_rules_readback_unavailable_blocks_without_api_write(self):
        client, fake = self.build()
        old = fake.__call__
        def unavailable(method, url, headers, body, timeout):
            if "/rules/branches/" in url:
                raise GitHubEvidenceError("permissions denied")
            return old(method, url, headers, body, timeout)
        client.transport = unavailable
        self.assertFalse(client.observe(STATE)["rules_policy_verified"])

    def test_stale_main_sha_blocks_transition(self):
        client, fake = self.build()
        fake.main_sha = "e" * 40
        self.assertFalse(client.observe(STATE)["transition_ready"])

    def test_missing_required_check_blocks(self):
        client, fake = self.build()
        fake.checks = []
        self.assertFalse(client.observe(STATE)["checks_passed"])

    def test_failed_other_check_blocks(self):
        client, fake = self.build()
        fake.checks.append({
            "name": "security", "head_sha": SHA,
            "status": "completed", "conclusion": "failure",
        })
        self.assertFalse(client.observe(STATE)["checks_passed"])

    def test_remote_mismatch_is_hard_error(self):
        client, fake = self.build()
        fake.head_ref = "phase/99-unauthorized"
        with self.assertRaises(GitHubEvidenceError):
            client.observe(STATE)

    def test_token_required(self):
        with self.assertRaises(GitHubEvidenceError):
            GitHubGateway(REPO, token="", transport=FakeTransport())

    def test_repository_validation(self):
        with self.assertRaises(ValueError):
            GitHubGateway("../another", token="fake-token", transport=FakeTransport())

    def test_no_dangerous_routes(self):
        client, _ = self.build()
        with self.assertRaises(GitHubEvidenceError):
            client._get("/issues/../secrets")

    def test_incomplete_check_page_fails_closed(self):
        client, fake = self.build()
        old = fake.__call__
        def oversized(method, url, headers, body, timeout):
            r = old(method, url, headers, body, timeout)
            if "/check-runs" in url:
                r["total_count"] = 101
            return r
        client.transport = oversized
        self.assertFalse(client.observe(STATE)["checks_passed"])


if __name__ == "__main__":
    unittest.main()
