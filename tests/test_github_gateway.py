"""Authenticated GitHub readback tests — no network, no credentials."""
import unittest
from urllib.parse import urlparse, parse_qs
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
        self.open_issues = [{"number": 3, "state": "open", "labels": []}]
        self.run_id = 1234
        self.job_id = 5678
        self.suite_id = 99
        self.run_overrides = {}
        self.job_overrides = {}
        self.checks = [{
            "name": "governance-lint", "head_sha": SHA,
            "status": "completed", "conclusion": "success", "app": {"id": 15368},
            "check_suite": {"id": self.suite_id},
            "details_url": f"https://github.com/{REPO}/actions/runs/{self.run_id}/job/{self.job_id}",
        }]
        self.ruleset_active = True
        self.ruleset_include = ["refs/heads/main"]
        self.ruleset_bypass = []
        self.ruleset_user_bypass = "never"
        self.ruleset_source = REPO
        self.ruleset_count = 1
        self.workflow_blob_main = "1" * 40
        self.workflow_blob_pr = "1" * 40
        self.workflow_content_missing = False
        self.rules = [
            {"type": "pull_request", "parameters": {"required_review_thread_resolution": True}},
            {"type": "required_status_checks", "parameters": {
                "strict_required_status_checks_policy": True,
                "required_status_checks": [
                    {"context": "governance-lint", "integration_id": 15368}
                ]
            }},
        ]
        self.head = SHA
        self.head_ref = BRANCH
        self.pr_number = 1
        self.request_count = 0

    def __call__(self, method, url, headers, body, timeout):
        self.request_count += 1
        assert method == "GET"
        assert body is None
        assert url.startswith("https://api.github.com/repos/" + REPO)
        assert headers["Authorization"] == "Bearer fake-token"
        path = urlparse(url).path
        if path.endswith(f"/pulls/{self.pr_number}"):
            return {
                "number": self.pr_number, "head": {"ref": self.head_ref, "sha": self.head},
                "base": {"ref": "main"}, "merged": self.pr_merged,
                "merged_at": "2026-11-18T00:00:00Z" if self.pr_merged else None,
                "merge_commit_sha": MERGE, "draft": self.pr_draft,
            }
        if path.endswith(f"/actions/runs/{self.run_id}"):
            data = {
                "id": self.run_id, "check_suite_id": self.suite_id,
                "name": "Governance v3.2", "path": ".github/workflows/governance.yml",
                "event": "pull_request", "status": "completed", "conclusion": "success",
                "head_sha": SHA, "head_branch": self.head_ref,
                "repository": {"full_name": REPO},
                "head_repository": {"full_name": REPO},
                "pull_requests": [{"number": self.pr_number}],
            }
            return {**data, **self.run_overrides}
        if path.endswith(f"/actions/jobs/{self.job_id}"):
            data = {
                "id": self.job_id, "run_id": self.run_id, "name": "governance-lint",
                "head_sha": SHA, "status": "completed", "conclusion": "success",
            }
            return {**data, **self.job_overrides}
        if "/actions/jobs/" in path:
            # Real GitHub returns a missing-job API error, not a test fixture
            # AssertionError; missing or forged job IDs must fail closed.
            raise GitHubEvidenceError("workflow job not found")
        if path.endswith("/contents/.github/workflows/governance.yml"):
            query = parse_qs(urlparse(url).query)
            ref = query.get("ref", [None])[0]
            assert ref in (self.main_sha, self.head)
            if self.workflow_content_missing:
                raise GitHubEvidenceError("workflow contents readback missing")
            return {
                "type": "file", "path": ".github/workflows/governance.yml",
                "name": "governance.yml", "size": 8700,
                "sha": self.workflow_blob_main if ref == self.main_sha else self.workflow_blob_pr,
            }
        if path.endswith("/rulesets"):
            return [
                {"id": 27593065, "target": "branch",
                 "enforcement": "active" if self.ruleset_active else "disabled",
                 "source_type": "Repository", "source": self.ruleset_source}
                for _ in range(self.ruleset_count)
            ]
        if path.endswith("/rulesets/27593065"):
            return {
                "id": 27593065, "target": "branch",
                "enforcement": "active" if self.ruleset_active else "disabled",
                "source_type": "Repository", "source": self.ruleset_source,
                "conditions": {"ref_name": {"include": self.ruleset_include, "exclude": []}},
                "bypass_actors": self.ruleset_bypass,
                "current_user_can_bypass": self.ruleset_user_bypass,
                "rules": self.rules,
            }
        if path.endswith("/rules/branches/main"):
            return self.rules
        if path.endswith("/branches/main"):
            return {"name": "main", "protected": self.main_protected, "commit": {"sha": self.main_sha}}
        if path.endswith("/commits/" + SHA + "/check-runs"):
            return {"total_count": len(self.checks), "check_runs": self.checks}
        if path.endswith("/issues/3"):
            return {"number": 3, "state": "open" if self.issue_open else "closed"}
        if path.endswith("/issues"):
            query = parse_qs(urlparse(url).query)
            assert query.get("state") == ["open"]
            assert query.get("per_page") == ["100"]
            page = int(query["page"][0])
            return self.open_issues[(page - 1) * 100:page * 100]
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
        self.assertTrue(snapshot["workflow_provenance_verified"])
        self.assertEqual(MERGE, snapshot["merge_sha"])
        self.assertGreaterEqual(fake.request_count, 5)

    def test_lookalike_actions_workflow_cannot_grant_merge_readiness(self):
        for key, forged in (
            ("name", "Untrusted Tests"),
            ("path", ".github/workflows/other.yml"),
            ("event", "workflow_dispatch"),
            ("head_sha", "e" * 40),
            ("head_branch", "phase/01-unauthorized"),
            ("check_suite_id", 100),
            ("repository", {"full_name": "other/fork"}),
            ("head_repository", {"full_name": "other/fork"}),
            ("pull_requests", [{"number": 2}]),
            ("conclusion", "failure"),
        ):
            client, fake = self.build()
            fake.run_overrides[key] = forged
            with self.subTest(key=key):
                result = client.observe(STATE)
                self.assertFalse(result["workflow_provenance_verified"])
                self.assertFalse(result["checks_passed"])
                self.assertFalse(result["transition_ready"])

    def test_forged_job_or_check_url_cannot_grant_merge_readiness(self):
        for key, forged in (
            ("name", "other-job"), ("run_id", 77),
            ("head_sha", "f" * 40), ("conclusion", "failure"),
            ("id", 999),
        ):
            client, fake = self.build()
            fake.job_overrides[key] = forged
            with self.subTest(key=key):
                result = client.observe(STATE)
                self.assertFalse(result["workflow_provenance_verified"])
        for bad_url in (
            "https://evil.example/actions/runs/1234/job/5678",
            f"https://github.com/{REPO}/actions/runs/1234/job/5678?x=1",
            f"https://github.com/{REPO}/actions/runs/1234/job/999",
            None,
        ):
            client, fake = self.build()
            fake.checks[0]["details_url"] = bad_url
            with self.subTest(url=bad_url):
                result = client.observe(STATE)
                self.assertFalse(result["workflow_provenance_verified"])
                self.assertFalse(result["transition_ready"])

    def test_workflow_run_api_inaccessible_blocks_without_faking_success(self):
        client, fake = self.build()
        old = fake.__call__
        def unavailable(method, url, headers, body, timeout):
            if "/actions/runs/" in url:
                raise GitHubEvidenceError("permission unavailable")
            return old(method, url, headers, body, timeout)
        client.transport = unavailable
        result = client.observe(STATE)
        self.assertFalse(result["workflow_provenance_verified"])
        self.assertFalse(result["transition_ready"])

    def test_p01_observer_does_not_inherit_p00_issue_or_fake_readiness(self):
        client, fake = self.build()
        fake.pr_number = 10
        fake.head_ref = "phase/01-foundation"
        fake.issue_open = True
        state = {"phase": "P01", "active_branch": "phase/01-foundation", "primary_pr": 10}
        snapshot = client.observe(state)
        self.assertEqual("P01", snapshot["phase"])
        self.assertEqual(10, snapshot["pr_number"])
        self.assertEqual([], snapshot["blocker_issue_numbers"])
        self.assertFalse(snapshot["blocker_policy_complete"])
        self.assertIsNone(snapshot["open_critical_blockers"])
        self.assertEqual([3], snapshot["unclassified_issue_numbers"])
        self.assertFalse(snapshot["transition_ready"])
        # Caller-supplied tuples must never become an independent phase policy.
        for override in ((), (3,), (2, 3)):
            with self.subTest(override=override), self.assertRaises(GitHubEvidenceError):
                client.observe(state, blocker_numbers=override)

    @staticmethod
    def labelled_issue(number, scope, disposition):
        return {"number": number, "state": "open", "labels": [
            {"name": "phase:" + scope}, {"name": "merge:" + disposition},
        ]}

    def test_p01_exhaustive_owner_labelled_inventory_excludes_other_phases(self):
        client, fake = self.build()
        fake.pr_number = 10
        fake.head_ref = "phase/01-foundation"
        fake.open_issues = [
            self.labelled_issue(2, "P08I", "nonblocker"),
            self.labelled_issue(3, "P00", "blocker"),
            self.labelled_issue(7, "P00", "blocker"),
            self.labelled_issue(8, "P01", "nonblocker"),
            {"number": 10, "state": "open", "pull_request": {}, "labels": []},
        ]
        state = {"phase": "P01", "active_branch": "phase/01-foundation", "primary_pr": 10}
        result = client.observe(state)
        self.assertTrue(result["blocker_policy_complete"])
        self.assertEqual("authenticated_github_open_issue_labels", result["issue_scope_source"])
        self.assertEqual([], result["unclassified_issue_numbers"])
        self.assertEqual([], result["blocker_issue_numbers"])
        self.assertEqual(0, result["open_critical_blockers"])

    def test_phase_issue_inventory_fingerprint_is_stable_but_sensitive_to_labels(self):
        client, fake = self.build()
        fake.pr_number = 10
        fake.head_ref = "phase/01-foundation"
        state = {"phase": "P01", "active_branch": "phase/01-foundation", "primary_pr": 10}
        fake.open_issues = [
            self.labelled_issue(2, "P00", "blocker"),
            self.labelled_issue(3, "P01", "nonblocker"),
        ]
        first = client.observe(state)
        self.assertTrue(first["blocker_policy_complete"])
        self.assertRegex(first["issue_inventory_fingerprint"], r"^[0-9a-f]{64}$")
        fake.open_issues.reverse()
        second = client.observe(state)
        self.assertEqual(first["issue_inventory_fingerprint"],
                         second["issue_inventory_fingerprint"])
        fake.open_issues[0] = self.labelled_issue(3, "P01", "blocker")
        third = client.observe(state)
        self.assertNotEqual(first["issue_inventory_fingerprint"],
                            third["issue_inventory_fingerprint"])
        self.assertEqual(1, third["open_critical_blockers"])

    def test_unclassified_issue_has_no_trusted_fingerprint(self):
        client, fake = self.build()
        fake.pr_number = 10
        fake.head_ref = "phase/01-foundation"
        fake.open_issues = [{"number": 7, "state": "open", "labels": []}]
        state = {"phase": "P01", "active_branch": "phase/01-foundation", "primary_pr": 10}
        result = client.observe(state)
        self.assertFalse(result["blocker_policy_complete"])
        self.assertIsNone(result["issue_inventory_fingerprint"])

    def test_p01_and_global_labelled_blockers_are_not_excluded(self):
        client, fake = self.build()
        fake.pr_number = 10
        fake.head_ref = "phase/01-foundation"
        fake.open_issues = [
            self.labelled_issue(11, "P01", "blocker"),
            self.labelled_issue(12, "global", "blocker"),
            self.labelled_issue(13, "P00", "blocker"),
        ]
        state = {"phase": "P01", "active_branch": "phase/01-foundation", "primary_pr": 10}
        result = client.observe(state)
        self.assertTrue(result["blocker_policy_complete"])
        self.assertEqual([11, 12], result["blocker_issue_numbers"])
        self.assertEqual(2, result["open_critical_blockers"])
        self.assertFalse(result["transition_ready"])

    def test_p01_unlabelled_ambiguous_and_fake_scope_remain_incomplete(self):
        state = {"phase": "P01", "active_branch": "phase/01-foundation", "primary_pr": 10}
        for labels in ([], [{"name": "phase:P00"}],
                       [{"name": "merge:nonblocker"}],
                       [{"name": "phase:P00"}, {"name": "merge:ignore"}],
                       [{"name": "phase:garbage"}, {"name": "merge:nonblocker"}],
                       [{"name": "phase:P01"}, {"name": "merge:blocker"},
                        {"name": "merge:nonblocker"}]):
            client, fake = self.build()
            fake.pr_number = 10
            fake.head_ref = "phase/01-foundation"
            fake.open_issues = [{"number": 11, "state": "open", "labels": labels}]
            with self.subTest(labels=labels):
                result = client.observe(state)
                self.assertFalse(result["blocker_policy_complete"])
                self.assertIsNone(result["open_critical_blockers"])
                self.assertEqual([11], result["unclassified_issue_numbers"])
                self.assertFalse(result["transition_ready"])

    def test_p01_issue_inventory_paginates_and_rejects_duplicate_or_partial(self):
        client, fake = self.build()
        fake.pr_number = 10
        fake.head_ref = "phase/01-foundation"
        state = {"phase": "P01", "active_branch": "phase/01-foundation", "primary_pr": 10}
        fake.open_issues = [
            self.labelled_issue(i, "P00", "nonblocker") for i in range(1, 102)
        ]
        result = client.observe(state)
        self.assertTrue(result["blocker_policy_complete"])
        self.assertEqual(0, result["open_critical_blockers"])
        fake.open_issues[100] = self.labelled_issue(1, "P00", "nonblocker")
        result = client.observe(state)
        self.assertFalse(result["blocker_policy_complete"])
        self.assertIsNone(result["open_critical_blockers"])
        fake.open_issues = [
            self.labelled_issue(i + 1, "P00", "nonblocker") for i in range(1000)
        ]
        result = client.observe(state)
        self.assertFalse(result["blocker_policy_complete"])
        self.assertFalse(result["transition_ready"])

    def test_p01_issue_inventory_inaccessible_is_fail_closed(self):
        client, fake = self.build()
        fake.pr_number = 10
        fake.head_ref = "phase/01-foundation"
        transport = fake.__call__
        def unavailable(method, url, headers, body, timeout):
            if "/issues?" in url:
                raise GitHubEvidenceError("issues read access denied")
            return transport(method, url, headers, body, timeout)
        client.transport = unavailable
        state = {"phase": "P01", "active_branch": "phase/01-foundation", "primary_pr": 10}
        result = client.observe(state)
        self.assertFalse(result["blocker_policy_complete"])
        self.assertIsNone(result["open_critical_blockers"])
        self.assertFalse(result["transition_ready"])

    def test_invalid_explicit_blocker_scope_fails_closed(self):
        client, fake = self.build()
        for invalid in ((0,), (True,), ("3",), [3]):
            with self.subTest(value=invalid):
                with self.assertRaises(GitHubEvidenceError):
                    client.observe(STATE, blocker_numbers=invalid)

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

    def test_trusted_actions_run_with_modified_pr_workflow_is_rejected(self):
        client, fake = self.build()
        fake.workflow_blob_pr = "2" * 40
        observed = client.observe(STATE)
        self.assertTrue(observed["workflow_provenance_verified"])
        self.assertFalse(observed["workflow_source_verified"])
        self.assertFalse(observed["checks_passed"])
        self.assertFalse(observed["rules_policy_verified"])
        self.assertFalse(observed["transition_ready"])

    def test_governance_workflow_source_missing_fails_closed(self):
        client, fake = self.build()
        fake.workflow_content_missing = True
        observed = client.observe(STATE)
        self.assertFalse(observed["workflow_source_verified"])
        self.assertFalse(observed["checks_passed"])
        self.assertFalse(observed["transition_ready"])

    def test_exact_protected_main_workflow_blob_is_verified(self):
        client, fake = self.build()
        observed = client.observe(STATE)
        self.assertTrue(observed["workflow_source_verified"])
        self.assertTrue(observed["checks_passed"])

    def test_required_check_without_pinned_app_blocks(self):
        client, fake = self.build()
        fake.rules[1]["parameters"]["required_status_checks"][0]["integration_id"] = None
        self.assertFalse(client.observe(STATE)["rules_policy_verified"])

    def test_wrong_check_provider_blocks(self):
        client, fake = self.build()
        fake.checks[0]["app"]["id"] = 999
        snap = client.observe(STATE)
        self.assertFalse(snap["checks_passed"])
        self.assertFalse(snap["rules_policy_verified"])

    def test_matching_but_unapproved_check_provider_is_denied(self):
        client, fake = self.build()
        # Matching a compromised/misconfigured ruleset ID is not sufficient:
        # the provider must also be the project-approved GitHub Actions App.
        fake.rules[1]["parameters"]["required_status_checks"][0]["integration_id"] = 999
        fake.checks[0]["app"]["id"] = 999
        snap = client.observe(STATE)
        self.assertFalse(snap["checks_passed"])
        self.assertFalse(snap["rules_policy_verified"])
        self.assertFalse(snap["transition_ready"])

    def test_non_strict_required_check_rule_is_denied(self):
        client, fake = self.build()
        fake.rules[1]["parameters"]["strict_required_status_checks_policy"] = False
        snap = client.observe(STATE)
        self.assertTrue(snap["checks_passed"])
        self.assertFalse(snap["rules_policy_verified"])
        self.assertFalse(snap["transition_ready"])

    def test_missing_review_thread_resolution_rule_is_denied(self):
        client, fake = self.build()
        fake.rules[0]["parameters"]["required_review_thread_resolution"] = False
        snap = client.observe(STATE)
        self.assertFalse(snap["rules_policy_verified"])
        self.assertFalse(snap["transition_ready"])

    def test_no_required_status_rule_blocks(self):
        client, fake = self.build()
        fake.rules = [fake.rules[0]]
        self.assertFalse(client.observe(STATE)["rules_policy_verified"])

    def test_legacy_rules_api_denial_can_use_exact_enforced_non_bypass_ruleset(self):
        client, fake = self.build()
        old = fake.__call__
        def legacy_forbidden(method, url, headers, body, timeout):
            if "/rules/branches/" in url:
                raise GitHubEvidenceError("legacy endpoint forbidden")
            return old(method, url, headers, body, timeout)
        client.transport = legacy_forbidden
        result = client.observe(STATE)
        self.assertTrue(result["rules_policy_verified"])
        self.assertTrue(result["checks_passed"])
        self.assertTrue(result["transition_ready"])

    def test_ruleset_fallback_fails_closed_for_bypass_wrong_target_or_missing_rules(self):
        for name, modifications in (
            ("bypass_actor", {"ruleset_bypass": [{"actor_id": 1, "actor_type": "Team"}]}),
            ("user_can_bypass", {"ruleset_user_bypass": "always"}),
            ("wrong_target", {"ruleset_include": ["refs/heads/development"]}),
            ("unknown_pattern", {"ruleset_include": ["~DEFAULT_BRANCH"]}),
            ("inherited_policy", {"ruleset_source": "different-org"}),
            ("no_active_policy", {"ruleset_active": False}),
            ("no_rulesets", {"ruleset_count": 0}),
            ("incomplete_page", {"ruleset_count": 100}),
        ):
            client, fake = self.build()
            for key, value in modifications.items():
                setattr(fake, key, value)
            old = fake.__call__
            def legacy_forbidden(method, url, headers, body, timeout):
                if "/rules/branches/" in url:
                    raise GitHubEvidenceError("legacy endpoint forbidden")
                return old(method, url, headers, body, timeout)
            client.transport = legacy_forbidden
            with self.subTest(name=name):
                snap = client.observe(STATE)
                self.assertFalse(snap["rules_policy_verified"])
                self.assertFalse(snap["transition_ready"])

    def test_ruleset_fallback_never_waives_pinned_trusted_check(self):
        client, fake = self.build()
        fake.rules[1]["parameters"]["required_status_checks"][0]["integration_id"] = 1111
        old = fake.__call__
        def legacy_forbidden(method, url, headers, body, timeout):
            if "/rules/branches/" in url:
                raise GitHubEvidenceError("legacy endpoint forbidden")
            return old(method, url, headers, body, timeout)
        client.transport = legacy_forbidden
        snap = client.observe(STATE)
        self.assertFalse(snap["rules_policy_verified"])
        self.assertFalse(snap["transition_ready"])

    def test_rules_readback_unavailable_blocks_without_api_write(self):
        client, fake = self.build()
        old = fake.__call__
        def unavailable(method, url, headers, body, timeout):
            if "/rules/branches/" in url or "/rulesets" in url:
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
