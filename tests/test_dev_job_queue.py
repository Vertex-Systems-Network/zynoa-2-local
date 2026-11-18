"""P00 durable development queue and allowlisted runner regressions."""
import json
import tempfile
import unittest
from pathlib import Path

from tools.dev_job_queue import JobQueue, QueuePolicyError
from tools.dev_job_runner import run_one, run_safe_check, JobCheckFailed
from tools.phase_controller import PHASE_ORDER

BRANCH = "phase/00-governance"
PHASE = "P00"
STATE = {
    "phase": "P00", "phase_status": "IN_PROGRESS",
    "active_branch": BRANCH, "primary_pr": 1,
    "worker_running": False, "last_verified_remote_sha": "a" * 40,
}
ROOT = Path(__file__).resolve().parents[1]


class JobQueueTests(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory()
        self.addCleanup(self.temp.cleanup)
        self.now = [1000.0]
        self.file = Path(self.temp.name) / "queue.db"
        self.queue = JobQueue(self.file, clock=lambda: self.now[0])

    def job(self, id="task-1", kind="phase-policy", max_attempts=3, priority=50):
        self.queue.enqueue(id, PHASE, BRANCH, kind, max_attempts, priority)

    def test_duplicate_idempotent_but_conflicting_spec_rejected(self):
        self.assertTrue(self.queue.enqueue("task-1", PHASE, BRANCH, "phase-policy"))
        self.assertFalse(self.queue.enqueue("task-1", PHASE, BRANCH, "phase-policy"))
        with self.assertRaises(QueuePolicyError):
            self.queue.enqueue("task-1", PHASE, BRANCH, "design-spec")

    def test_only_read_only_job_kinds(self):
        for kind in ("git-push", "shell", "merge", "model-call", "delete-files"):
            with self.subTest(kind=kind), self.assertRaises(QueuePolicyError):
                self.queue.enqueue("task-" + kind, PHASE, BRANCH, kind)

    def test_path_and_invalid_id_rejected(self):
        for id in ("../bad", "task/123", "", "bad space"):
            with self.subTest(id=id), self.assertRaises(QueuePolicyError):
                self.queue.enqueue(id, PHASE, BRANCH, "phase-policy")
        with self.assertRaises(QueuePolicyError):
            self.queue.enqueue("good", PHASE, "main", "phase-policy")

    def test_phase_interop_requires_specific_branch(self):
        with self.assertRaises(QueuePolicyError):
            self.queue.enqueue("task", "P08I", BRANCH, "design-spec")

    def test_single_claim_no_duplicate_while_lease_valid(self):
        self.job()
        claimed = self.queue.claim(PHASE, BRANCH, "agent-a")
        self.assertIsNotNone(claimed)
        self.assertIsNone(JobQueue(self.file, clock=lambda: self.now[0]).claim(PHASE, BRANCH, "agent-b"))
        self.assertEqual("RUNNING", self.queue.inspect("task-1")["state"])

    def test_priority_and_phase_isolation(self):
        self.job("low", priority=90)
        self.job("high", priority=1)
        self.queue.enqueue("other", "P01", "phase/01-foundation", "phase-policy")
        self.assertEqual("high", self.queue.claim(PHASE, BRANCH, "agent-a").id)
        self.assertEqual("low", self.queue.claim(PHASE, BRANCH, "agent-a").id)
        self.assertIsNone(self.queue.claim(PHASE, BRANCH, "agent-a"))

    def test_success_and_restart_are_durable(self):
        self.job()
        claimed = self.queue.claim(PHASE, BRANCH, "agent-a")
        self.queue.complete(claimed, "agent-a", {"check": "phase-policy", "passed": True})
        other = JobQueue(self.file, clock=lambda: self.now[0])
        self.assertEqual("SUCCEEDED", other.inspect("task-1")["state"])
        self.assertIsNone(other.claim(PHASE, BRANCH, "agent-b"))
        self.assertEqual(64, len(other.inspect("task-1")["result_sha256"]))

    def test_stale_owner_cannot_complete(self):
        self.job()
        claim = self.queue.claim(PHASE, BRANCH, "agent-a", lease_seconds=5)
        with self.assertRaises(QueuePolicyError):
            self.queue.complete(claim, "agent-b", {"check": "phase-policy", "passed": True})
        self.now[0] += 6
        with self.assertRaises(QueuePolicyError):
            self.queue.complete(claim, "agent-a", {"check": "phase-policy", "passed": True})
        restored = self.queue.claim(PHASE, BRANCH, "agent-b", lease_seconds=5)
        self.assertEqual(2, restored.attempt)
        with self.assertRaises(QueuePolicyError):
            self.queue.heartbeat(claim, "agent-a")
        self.queue.complete(restored, "agent-b", {"check": "phase-policy", "passed": True})

    def test_lease_heartbeat_extends_live_claim(self):
        self.job()
        claim = self.queue.claim(PHASE, BRANCH, "agent-a", lease_seconds=5)
        self.now[0] += 4
        self.queue.heartbeat(claim, "agent-a", lease_seconds=10)
        self.now[0] += 5
        self.assertIsNone(self.queue.claim(PHASE, BRANCH, "agent-b"))
        self.queue.complete(claim, "agent-a", {"check": "phase-policy", "passed": True})

    def test_bounded_backoff_then_terminal_block(self):
        self.job(max_attempts=2)
        first = self.queue.claim(PHASE, BRANCH, "agent-a")
        self.queue.fail(first, "agent-a", "CheckFailed", initial_delay=4)
        self.assertEqual("RETRY_WAIT", self.queue.inspect("task-1")["state"])
        self.assertIsNone(self.queue.claim(PHASE, BRANCH, "agent-a"))
        self.now[0] += 4
        second = self.queue.claim(PHASE, BRANCH, "agent-a")
        self.queue.fail(second, "agent-a", "CheckFailed")
        self.assertEqual("BLOCKED", self.queue.inspect("task-1")["state"])

    def test_exhausted_expired_lease_blocks(self):
        self.job(max_attempts=1)
        first = self.queue.claim(PHASE, BRANCH, "agent-a", lease_seconds=5)
        self.now[0] += 6
        self.assertIsNone(self.queue.claim(PHASE, BRANCH, "agent-b"))
        self.assertEqual("BLOCKED", self.queue.inspect("task-1")["state"])

    def test_no_raw_error_content_in_log(self):
        self.job()
        claimed = self.queue.claim(PHASE, BRANCH, "agent-a")
        with self.assertRaises(QueuePolicyError):
            self.queue.fail(claimed, "agent-a", "password=secret-and-chat-content")

    def test_invalid_result_rejected(self):
        self.job()
        claimed = self.queue.claim(PHASE, BRANCH, "agent-a")
        with self.assertRaises(QueuePolicyError):
            self.queue.complete(claimed, "agent-a", {"check": "phase-policy", "passed": True, "raw_stack": "secret"})


class AllowlistedRunnerTests(unittest.TestCase):
    def test_real_repository_check_handlers(self):
        for kind in ("phase-policy", "design-spec", "docs-integrity"):
            self.assertEqual({"check": kind, "passed": True}, run_safe_check(kind, STATE, ROOT))

    def test_arbitrary_command_handler_denied(self):
        with self.assertRaises(QueuePolicyError):
            run_safe_check("run-shell", STATE, ROOT)

    def test_missing_docs_failure_not_faked(self):
        with tempfile.TemporaryDirectory() as temp:
            with self.assertRaises(JobCheckFailed):
                run_safe_check("docs-integrity", STATE, Path(temp))

    def test_runner_marks_bad_docs_as_retryable(self):
        with tempfile.TemporaryDirectory() as temp:
            q = JobQueue(Path(temp) / "queue.db")
            q.enqueue("doc-run", PHASE, BRANCH, "docs-integrity")
            result = run_one(q, STATE, Path(temp), "agent-a")
            self.assertEqual("RETRY_WAIT", result["status"])
            self.assertEqual("CheckFailed", q.inspect("doc-run")["error_class"])

    def test_runner_rejects_wrong_phase(self):
        with tempfile.TemporaryDirectory() as temp:
            q = JobQueue(Path(temp) / "queue.db")
            q.enqueue("policy-run", PHASE, BRANCH, "phase-policy")
            with self.assertRaises(QueuePolicyError):
                run_one(q, {**STATE, "phase_status": "MERGED_VERIFIED"}, ROOT, "agent-a")
            self.assertEqual("PENDING", q.inspect("policy-run")["state"])


if __name__ == "__main__":
    unittest.main()
