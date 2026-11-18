"""Trusted-main PR task updater: no PR code executed and no real GitHub writes."""
import copy
import unittest
from pathlib import Path

from tools.pr_task_board import TaskBoardError, load_manifest
from tools.pr_task_trusted_sync import run_trusted_sync

REPO = "Vertex-Systems-Network/zynoa-2-local"
SHA = "a" * 40
ROOT = Path(__file__).resolve().parents[1]
MANIFEST = ROOT / "docs/state/pr-tasks/P00.json"
STATE = {
    "phase": "P00", "phase_status": "IN_PROGRESS",
    "active_branch": "phase/00-governance", "primary_pr": 1,
}


def event():
    return {
        "workflow_run": {
            "event": "pull_request",
            "conclusion": "success",
            "head_sha": SHA,
            "head_repository": {"full_name": REPO},
            "pull_requests": [{"number": 1}],
        }
    }


class FakeSources:
    def __init__(self):
        self.event = event()
        self.state = copy.deepcopy(STATE)
        self.manifest = load_manifest(MANIFEST)
        self.body = "Human-authored PR body."
        self.current_sha = SHA
        self.current_repo = REPO
        self.current_pr = 1
        self.requests = []
        self.files_read = []
        self.write_calls = []

    def file_loader(self, token, sha, path):
        self.files_read.append((sha, path))
        if sha != SHA:
            raise AssertionError("unexpected commit")
        if path == "docs/state/PHASE.json":
            return self.state
        if path == "docs/state/pr-tasks/P00.json":
            return self.manifest
        raise TaskBoardError("unavailable manifest for requested phase")

    def transport(self, method, url, payload):
        self.requests.append(method)
        if method == "PATCH":
            self.body = payload["body"]
        return {
            "number": self.current_pr,
            "state": "open",
            "head": {
                "ref": "phase/00-governance", "sha": self.current_sha,
                "repo": {"full_name": self.current_repo},
            },
            "base": {"ref": "main"},
            "body": self.body,
        }

    def writer(self, manifest, sha, token, **kwargs):
        self.write_calls.append((manifest["phase"], sha, token))
        return {"status": "SYNCED_VERIFIED", "pr_number": 1, "github_writes": 1}

    def run(self, **kwargs):
        return run_trusted_sync(
            kwargs.get("event", self.event), kwargs.get("token", "fake-test-token"),
            enabled=kwargs.get("enabled", True),
            file_loader=self.file_loader,
            pr_transport=self.transport,
            writer=self.writer,
        )


class TrustedSyncTests(unittest.TestCase):
    def test_real_success_event_reconciles_and_updates(self):
        f = FakeSources()
        result = f.run()
        self.assertEqual("SYNCED_VERIFIED", result["status"])
        self.assertEqual(["GET"], f.requests)
        self.assertEqual([
            (SHA, "docs/state/PHASE.json"),
            (SHA, "docs/state/pr-tasks/P00.json"),
        ], f.files_read)
        self.assertEqual(1, len(f.write_calls))

    def test_disabled_writer_never_reads_or_writes(self):
        f = FakeSources()
        with self.assertRaises(TaskBoardError):
            f.run(enabled=False)
        self.assertEqual([], f.requests)

    def test_failed_ci_event_cannot_claim_done_or_modify_pr(self):
        f = FakeSources()
        f.event["workflow_run"]["conclusion"] = "failure"
        self.assertEqual("SKIPPED_NON_SUCCESS_PR_RUN", f.run()["status"])
        self.assertEqual([], f.requests)

    def test_push_event_not_processed(self):
        f = FakeSources()
        f.event["workflow_run"]["event"] = "push"
        self.assertEqual("SKIPPED_NON_SUCCESS_PR_RUN", f.run()["status"])
        self.assertEqual([], f.requests)

    def test_fork_or_foreign_repo_refused(self):
        f = FakeSources()
        f.event["workflow_run"]["head_repository"]["full_name"] = "someone/else"
        self.assertEqual("SKIPPED_UNTRUSTED_REPOSITORY", f.run()["status"])
        self.assertEqual([], f.requests)

    def test_ambiguous_or_missing_pull_request_no_write(self):
        for prs in ([], [{"number": 1}, {"number": 2}], None):
            f = FakeSources()
            f.event["workflow_run"]["pull_requests"] = prs
            with self.subTest(prs=prs):
                self.assertEqual("SKIPPED_AMBIGUOUS_PR", f.run()["status"])
                self.assertEqual([], f.requests)

    def test_stale_head_sha_skips_before_loading_pr_code_data(self):
        f = FakeSources()
        f.current_sha = "b" * 40
        self.assertEqual("SKIPPED_STALE_OR_FOREIGN_PR", f.run()["status"])
        self.assertFalse(f.files_read)
        self.assertFalse(f.write_calls)

    def test_wrong_current_repository_prevents_data_load(self):
        f = FakeSources()
        f.current_repo = "malicious/fork"
        self.assertEqual("SKIPPED_STALE_OR_FOREIGN_PR", f.run()["status"])
        self.assertFalse(f.files_read)

    def test_phase_state_mismatch_blocks_sync(self):
        for key, value in (
            ("phase", "P01"), ("primary_pr", 7),
            ("active_branch", "main"), ("phase_status", "MERGED_VERIFIED"),
        ):
            f = FakeSources()
            f.state[key] = value
            with self.subTest(key=key), self.assertRaises(TaskBoardError):
                f.run()
            self.assertFalse(f.write_calls)

    def test_manifest_cross_pr_and_malicious_title_refused(self):
        for key, value in (("pr_number", 7), ("branch", "phase/01-foundation")):
            f = FakeSources()
            f.manifest[key] = value
            with self.subTest(key=key), self.assertRaises(TaskBoardError):
                f.run()
            self.assertFalse(f.write_calls)
        f = FakeSources()
        f.manifest["tasks"][0]["title"] = "Task | malicious table row"
        with self.assertRaises(TaskBoardError):
            f.run()

    def test_unexpected_event_sha_rejected(self):
        f = FakeSources()
        f.event["workflow_run"]["head_sha"] = "HEAD"
        with self.assertRaises(TaskBoardError):
            f.run()
        self.assertFalse(f.requests)

    def test_missing_read_token_refused(self):
        f = FakeSources()
        with self.assertRaises(TaskBoardError):
            f.run(token="")

    def test_missing_workflow_run_rejected(self):
        f = FakeSources()
        with self.assertRaises(TaskBoardError):
            f.run(event={"event": "push"})


if __name__ == "__main__":
    unittest.main()
