"""P00-T22 CI incident authoring: independently verified failure and remote dedup.

ALL transport data here is simulated. The trusted workflow_run listener
cannot activate until the reviewed PR merges onto default branch. The test
suite must never claim that a live Actions issue delivery took place.
"""
import json
import unittest

from tools.github_issue_bridge import DeveloperIssueBridge, IncidentPublishError

REPO = "Vertex-Systems-Network/zynoa-2-local"
RUN = 44652995831
SHA = "c8846cf24b9bd440753a3bb9435557ef4f954a0a"
EVENT = {
    "source_type": "developer-ci", "severity": "P2",
    "module": "M22", "error_code": "GOVERNANCE_CI_FAILURE",
    "message_class": "GitHubActionsFailure", "app_version": "0.0.1",
    "token": "PRIVATE-TOKEN", "prompt": "PRIVATE-MODEL-PROMPT",
}


class GitHubSimulator:
    def __init__(self):
        self.events = []
        self.issues = []
        self.bad_update = False
        self.run = {
            "id": RUN, "head_sha": SHA, "status": "completed",
            "conclusion": "failure", "name": "Governance v3.2",
            "event": "pull_request", "head_repository": {"full_name": REPO},
        }

    def __call__(self, method, url, headers, payload, timeout):
        self.events.append((method, url))
        assert headers["Authorization"] == "Bearer test-github-token"
        assert url.startswith("https://api.github.com/repos/" + REPO)
        if method == "GET" and "/actions/runs/" in url:
            return dict(self.run)
        if method == "GET" and "/issues?state=all" in url:
            return list(self.issues)
        if method == "POST" and url.endswith("/issues"):
            item = dict(json.loads(payload))
            item.update(number=71, html_url="https://github.com/" + REPO + "/issues/71")
            item["user"] = {"login": "github-actions[bot]"}
            self.issues.append(item)
            return dict(item)
        if method == "PATCH" and url.endswith("/issues/71"):
            self.issues[0].update(json.loads(payload))
            response = dict(self.issues[0])
            if self.bad_update:
                response["body"] = "tampered"
            return response
        raise AssertionError("unapproved GitHub request")


class CIIncidentWriteContractTests(unittest.TestCase):
    def setUp(self):
        self.mock = GitHubSimulator()
        self.bridge = DeveloperIssueBridge(
            REPO, token="test-github-token", publish_enabled=True,
            transport=self.mock,
        )

    def test_retrieve_actual_failed_run_identity_before_post(self):
        report = self.bridge.publish(EVENT, run_id=RUN, commit_sha=SHA)
        self.assertEqual("CREATED", report["status"])
        self.assertTrue(report["ci_run_verified"])
        self.assertEqual(["GET", "GET", "POST"], [x[0] for x in self.mock.events])
        body = self.mock.issues[0]["body"]
        self.assertIn("/actions/runs/44652995831", body)
        self.assertIn(SHA, body)
        self.assertIn("zynoa-ci-run:", body)
        self.assertIn("zynoa-incident:", body)
        self.assertIn("\n## Verified GitHub CI failure run(s)", body)
        self.assertNotIn("PRIVATE-MODEL-PROMPT", body)
        self.assertNotIn("PRIVATE-TOKEN", body)

    def test_same_run_does_not_repost_or_patch(self):
        self.bridge.publish(EVENT, run_id=RUN, commit_sha=SHA)
        self.mock.events.clear()
        result = self.bridge.publish(EVENT, run_id=RUN, commit_sha=SHA)
        self.assertEqual("EXISTING", result["status"])
        self.assertEqual(["GET", "GET"], [x[0] for x in self.mock.events])

    def test_distinct_failure_updates_existing_sanitized_issue(self):
        self.bridge.publish(EVENT, run_id=RUN, commit_sha=SHA)
        self.mock.issues[0]["body"] += "\nUNTRUSTED-EXTRA-TEXT"
        self.mock.run.update(id=RUN+1, head_sha="a"*40)
        result = self.bridge.publish(EVENT, run_id=RUN+1, commit_sha="a"*40)
        self.assertEqual("UPDATED", result["status"])
        self.assertEqual("PATCH", self.mock.events[-1][0])
        self.assertEqual(1, len(self.mock.issues))
        body = self.mock.issues[0]["body"]
        self.assertNotIn("UNTRUSTED-EXTRA-TEXT", body)
        self.assertIn("/actions/runs/" + str(RUN+1), body)
        self.assertIn("/actions/runs/" + str(RUN), body)

    def test_bounded_five_run_evidence(self):
        for i in range(7):
            new_id = RUN+i
            sha = "%040x" % new_id
            self.mock.run.update(id=new_id, head_sha=sha)
            self.bridge.publish(EVENT, run_id=new_id, commit_sha=sha)
        body = self.mock.issues[0]["body"]
        self.assertEqual(5, body.count("<!-- zynoa-ci-run:"))
        self.assertNotIn("zynoa-ci-run:"+str(RUN)+":", body)
        self.assertIn("zynoa-ci-run:"+str(RUN+6)+":", body)

    def test_wrong_run_metadata_refuses_to_mutate_issues(self):
        for change in [
            {"conclusion": "success"}, {"status": "in_progress"},
            {"name": "Other"}, {"event": "workflow_dispatch"},
            {"head_sha": "f"*40}, {"id": RUN+123},
            {"head_repository": {"full_name": "other/fork"}},
        ]:
            mock = GitHubSimulator()
            mock.run.update(change)
            bridge = DeveloperIssueBridge(
                REPO, token="test-github-token", publish_enabled=True,
                transport=mock,
            )
            with self.subTest(change=change), self.assertRaises(IncidentPublishError):
                bridge.publish(EVENT, run_id=RUN, commit_sha=SHA)
            self.assertEqual(["GET"], [x[0] for x in mock.events])
            self.assertEqual([], mock.issues)

    def test_invalid_input_refused_before_any_http(self):
        for ident, sha in [(True,SHA), (0,SHA), (-1,SHA),
                           ("44652995831",SHA), (RUN,"main"),
                           (RUN,"a"*39), (RUN,None), (None,SHA),
                           (10**19,SHA)]:
            mock = GitHubSimulator()
            bridge = DeveloperIssueBridge(
                REPO, token="test-github-token", publish_enabled=True,
                transport=mock
            )
            with self.subTest(ident=ident), self.assertRaises(IncidentPublishError):
                bridge.publish(EVENT, run_id=ident, commit_sha=sha)
            self.assertEqual([], mock.events)

    def test_invalid_update_response_never_claims_delivered(self):
        self.bridge.publish(EVENT, run_id=RUN, commit_sha=SHA)
        self.mock.bad_update = True
        self.mock.run.update(id=RUN+1, head_sha="a"*40)
        with self.assertRaises(IncidentPublishError):
            self.bridge.publish(EVENT, run_id=RUN+1, commit_sha="a"*40)

    def test_unsafe_http_routes_denied(self):
        for method, path in [
            ("GET", "/issues/71"), ("POST", "/issues/71"),
            ("PATCH", "/issues"), ("GET", "/actions/runs/0"),
            ("PATCH", "/issues/71/comments"), ("DELETE", "/issues/71"),
        ]:
            with self.subTest(method=method, path=path), self.assertRaises(
                IncidentPublishError
            ):
                self.bridge._request(method, path, {"private": "NO"})
        self.assertEqual([], self.mock.events)

    def test_fake_existing_marker_cannot_redirect_updates(self):
        safe = self.bridge.safe_record(EVENT)
        self.mock.issues = [{
            "number": 71,
            "html_url": "https://github.com/attacker/forgery/issues/71",
            "body": self.bridge.format_issue(safe)["body"],
        }]
        with self.assertRaises(IncidentPublishError):
            self.bridge.publish(EVENT, run_id=RUN, commit_sha=SHA)
        self.assertEqual(["GET", "GET"], [x[0] for x in self.mock.events])


if __name__ == "__main__":
    unittest.main()
