"""PR-comment transition receipt: mocked GitHub write/readback, no live writes."""
import json
import tempfile
import unittest
from pathlib import Path

from tools.github_gateway import GitHubGateway
from tools.phase_controller import EventJournal
from tools.phase_transition_publisher import (
    API, REPO, TransitionPublishDenied, _MARKER, _receipt_body,
    publish_verified_transition,
)

MERGE = "a" * 40
MAIN = "b" * 40
FP = "c" * 64
STATE = {
    "phase": "P01",
    "phase_status": "MERGED_VERIFIED",
    "active_branch": "phase/01-foundation",
    "primary_pr": 10,
    "last_verified_remote_sha": MERGE,
    "worker_running": False,
    "lease_holder": None,
}


class FakeGitHub(GitHubGateway):
    """Strict in-memory authenticated GitHub API fixture, never a real client."""

    def __init__(self):
        self.repo = REPO
        self.token = "fake-scoped-test-token"
        self.calls = []
        self.comments = []
        self.post_count = 0
        self.main_sha = MAIN
        self.merged = True
        self.compare_status = "ahead"
        self.compare_base = MERGE
        self.bad_readback = False
        self.bad_comment_author = False
        self.observation = {
            "authenticated_remote": True,
            "repo": REPO,
            "phase": "P01",
            "pr_number": 10,
            "head_branch": "phase/01-foundation",
            "base_branch": "main",
            "merge_sha": MERGE,
            "main_sha": MAIN,
            "main_matches_merge": False,
            "merged": True,
            "checks_passed": True,
            "branch_protected": True,
            "rules_policy_verified": True,
            "workflow_provenance_verified": True,
            "workflow_source_verified": True,
            "open_critical_blockers": 0,
            "blocker_policy_complete": True,
            "issue_scope_source": "authenticated_github_open_issue_labels",
            "issue_inventory_fingerprint": FP,
            "unclassified_issue_numbers": [],
            "blocker_issue_numbers": [],
        }

    def observe(self, state):
        self.calls.append("observe")
        return dict(self.observation)

    def pull_request(self, number):
        self.calls.append("pull_request")
        return {
            "number": 10, "merged": self.merged, "merge_commit_sha": MERGE,
            "head": {"ref": "phase/01-foundation"}, "base": {"ref": "main"},
        }

    def branch(self, name):
        assert name == "main"
        self.calls.append("branch")
        return {"commit": {"sha": self.main_sha}, "protected": True}

    def _get(self, path, params=None):
        self.calls.append((path, params))
        if path == "/compare/" + MERGE + "..." + MAIN:
            return {
                "status": self.compare_status, "behind_by": 0, "ahead_by": 1,
                "base_commit": {"sha": MERGE},
                "merge_base_commit": {"sha": self.compare_base},
            }
        if path == "/issues/10/comments":
            assert params == {"per_page": "100", "page": "1"}
            return [dict(comment) for comment in self.comments]
        if path.startswith("/issues/comments/"):
            found = [x for x in self.comments if str(x["id"]) == path.rsplit("/", 1)[1]]
            if len(found) != 1:
                raise AssertionError("unexpected missing readback")
            comment = dict(found[0])
            if self.bad_readback:
                comment["body"] = "altered"
            return comment
        raise AssertionError("unexpected API read " + path)

    def post(self, pr, body, token):
        assert pr == 10
        assert token == self.token
        self.post_count += 1
        item = {
            "id": 9001,
            "body": body,
            "user": {"login": "untrusted-user" if self.bad_comment_author else "github-actions[bot]"},
            "issue_url": API + "/issues/10",
        }
        self.comments.append(item)
        return dict(item)


class PhaseTransitionPublisherTests(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory()
        self.addCleanup(self.temp.cleanup)
        self.db = Path(self.temp.name) / "events.db"
        self.journal = EventJournal(self.db)
        self.reader = FakeGitHub()

    def publish(self, **overrides):
        options = {
            "enabled": True,
            "workflow_ref": "refs/heads/main",
            "workflow_sha": MAIN,
            "transport": self.reader.post,
        }
        options.update(overrides)
        return publish_verified_transition(
            self.reader, self.journal, dict(STATE), **options
        )

    def test_requires_default_denial_and_main_ref_before_network(self):
        for options in ({}, {"enabled": True}, {"workflow_ref": "refs/heads/main"},
                        {"enabled": 1, "workflow_ref": "refs/heads/main"},
                        {"enabled": True, "workflow_ref": "refs/heads/phase/01-foundation"}):
            with self.subTest(options=options), self.assertRaises(TransitionPublishDenied):
                publish_verified_transition(
                    self.reader, self.journal, STATE, transport=self.reader.post,
                    **options,
                )
        self.assertEqual([], self.reader.calls)
        self.assertEqual(0, self.journal.count())

    def test_publishes_real_remote_readback_and_survives_local_restart(self):
        result = self.publish()
        self.assertEqual("REMOTE_PHASE_RECEIPT_VERIFIED", result["status"])
        self.assertEqual(10, result["primary_pr"])
        self.assertEqual(9001, result["comment_id"])
        self.assertTrue(result["comment_created"])
        self.assertTrue(result["external_checkpoint_published"])
        self.assertTrue(result["external_checkpoint_mutable"])
        self.assertTrue(result["local_journal_readback_verified"])
        self.assertFalse(result["next_phase_started"])
        self.assertEqual(1, self.reader.post_count)
        self.assertEqual(1, EventJournal(self.db).count())
        self.assertIn(_MARKER + "P01:P02:" + MERGE, self.reader.comments[0]["body"])
        self.assertNotIn(self.reader.token, json.dumps(result))
        self.assertEqual(
            "https://github.com/" + REPO + "/pull/10#issuecomment-9001",
            result["comment_url"],
        )

    def test_duplicate_retry_reuses_verified_bot_comment_without_new_write(self):
        self.assertTrue(self.publish()["comment_created"])
        second = self.publish()
        self.assertFalse(second["comment_created"])
        self.assertEqual(1, self.reader.post_count)
        self.assertEqual(1, EventJournal(self.db).count())

    def test_rejects_modified_existing_and_fake_author_receipt(self):
        self.publish()
        for mutation in ("altered", "wrong_author"):
            with self.subTest(mutation=mutation):
                original = dict(self.reader.comments[0])
                if mutation == "altered":
                    self.reader.comments[0]["body"] += " MODIFIED"
                else:
                    self.reader.comments[0]["user"] = {"login": "attacker"}
                with self.assertRaises(TransitionPublishDenied):
                    self.publish()
                self.reader.comments[0] = original
        self.assertEqual(1, self.reader.post_count)

    def test_duplicate_matching_markers_fail_closed(self):
        self.publish()
        self.reader.comments.append({**self.reader.comments[0], "id": 9002})
        with self.assertRaises(TransitionPublishDenied):
            self.publish()
        self.assertEqual(1, self.reader.post_count)

    def test_remote_readback_mismatch_cannot_claim_publication(self):
        self.reader.bad_readback = True
        with self.assertRaises(TransitionPublishDenied):
            self.publish()
        self.assertEqual(1, self.journal.count())
        self.assertEqual(1, self.reader.post_count)
        self.reader.bad_readback = False
        result = self.publish()
        self.assertFalse(result["comment_created"])
        self.assertTrue(result["external_checkpoint_published"])
        self.assertEqual(1, self.reader.post_count)

    def test_created_nonbot_comment_is_rejected(self):
        self.reader.bad_comment_author = True
        with self.assertRaises(TransitionPublishDenied):
            self.publish()
        self.assertEqual(1, self.reader.post_count)

    def test_unclassified_issue_or_untrusted_CI_never_writes(self):
        for key, bad in (
            ("unclassified_issue_numbers", [7]),
            ("blocker_policy_complete", False),
            ("open_critical_blockers", False),
            ("workflow_source_verified", False),
            ("rules_policy_verified", False),
        ):
            with self.subTest(key=key):
                self.reader.observation[key] = bad
                with self.assertRaises(TransitionPublishDenied):
                    self.publish()
                self.reader.observation[key] = FakeGitHub().observation[key]
        self.assertEqual(0, self.reader.post_count)
        self.assertEqual(0, self.journal.count())

    def test_stale_workflow_main_or_diverged_ancestry_denied(self):
        with self.assertRaises(TransitionPublishDenied):
            self.publish(workflow_sha="f" * 40)
        self.reader.compare_base = "d" * 40
        with self.assertRaises(TransitionPublishDenied):
            self.publish()
        self.reader.compare_base = MERGE
        self.reader.compare_status = "diverged"
        with self.assertRaises(TransitionPublishDenied):
            self.publish()
        self.assertEqual(0, self.journal.count())

    def test_changed_pr_before_POST_denied(self):
        self.reader.merged = False
        with self.assertRaises(TransitionPublishDenied):
            self.publish()
        self.assertEqual(0, self.reader.post_count)

    def test_p00_history_cannot_be_recreated_by_new_publisher(self):
        state = {
            **STATE, "phase": "P00", "active_branch": "phase/00-governance",
            "primary_pr": 1,
        }
        with self.assertRaises(TransitionPublishDenied):
            publish_verified_transition(
                self.reader, self.journal, state,
                enabled=True, workflow_ref="refs/heads/main",
                workflow_sha=MAIN, transport=self.reader.post,
            )
        self.assertEqual(0, self.journal.count())
        self.assertEqual([], self.reader.calls)

    def test_current_inprogress_phase_never_triggers_comment(self):
        state = {**STATE, "phase_status": "IN_PROGRESS"}
        with self.assertRaises(TransitionPublishDenied):
            publish_verified_transition(
                self.reader, self.journal, state,
                enabled=True, workflow_ref="refs/heads/main",
                workflow_sha=MAIN, transport=self.reader.post,
            )
        self.assertEqual(0, self.journal.count())

    def test_workflow_is_main_only_and_not_PR_privileged(self):
        workflow = (Path(__file__).parents[1]
                    / ".github/workflows/verified-phase-transition.yml").read_text()
        self.assertIn("workflow_dispatch:", workflow)
        self.assertIn("branches: [main]", workflow)
        self.assertIn("github.ref == 'refs/heads/main'", workflow)
        self.assertIn("issues: write", workflow)
        self.assertIn("contents: read", workflow)
        self.assertIn("persist-credentials: false", workflow)
        self.assertIn("tools.phase_transition_publisher --publish", workflow)
        self.assertNotIn("pull_request:", workflow)
        self.assertNotIn("pull_request_target:", workflow)
        self.assertNotIn("schedule:", workflow)


if __name__ == "__main__":
    unittest.main()
