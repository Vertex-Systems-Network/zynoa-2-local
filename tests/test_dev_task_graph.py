"""P00 dependency DAG tests, all local SQLite; no network/process execution."""
import tempfile
import unittest
from pathlib import Path

from tools.dev_job_queue import JobQueue, QueuePolicyError
from tools.dev_task_graph import JobGraph

PHASE = "P00"
BRANCH = "phase/00-governance"


class JobGraphTests(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        self.addCleanup(self.tmp.cleanup)
        self.now = [100.0]
        self.path = Path(self.tmp.name) / "tasks.db"
        self.queue = JobQueue(self.path, clock=lambda: self.now[0])
        self.graph = JobGraph(self.queue)

    def task(self, id, phase=PHASE, branch=BRANCH, priority=50):
        self.queue.enqueue(id, phase, branch, "phase-policy", max_attempts=2, priority=priority)

    def finish(self, id, owner="worker"):
        job = self.queue.claim(PHASE, BRANCH, owner, lease_seconds=20)
        self.assertEqual(id, job.id)
        self.queue.complete(job, owner, {"check": job.kind, "passed": True})

    def test_dependency_blocks_higher_priority_job_until_success(self):
        self.task("dependency", priority=90)
        self.task("dependent", priority=1)
        self.assertEqual(1, self.graph.add_dependencies("dependent", ["dependency"]))
        self.assertEqual(["dependency"], self.graph.prerequisites("dependent"))
        self.assertFalse(self.graph.dependency_status("dependent")["ready"])
        self.finish("dependency")
        self.assertTrue(self.graph.dependency_status("dependent")["ready"])
        self.finish("dependent")
        self.assertIsNone(self.queue.claim(PHASE, BRANCH, "worker"))

    def test_exact_duplicate_dependency_is_idempotent(self):
        self.task("base")
        self.task("child")
        self.assertEqual(1, self.graph.add_dependencies("child", ["base"]))
        self.assertEqual(0, self.graph.add_dependencies("child", ["base"]))
        self.assertEqual(["base"], JobGraph(JobQueue(self.path)).prerequisites("child"))

    def test_multi_step_dag_orders_three_jobs(self):
        for id in ("a", "b", "c"):
            self.task(id)
        self.graph.add_dependencies("b", ["a"])
        self.graph.add_dependencies("c", ["b"])
        for id in ("a", "b", "c"):
            self.finish(id)

    def test_direct_cycle_rejected_and_original_edges_preserved(self):
        self.task("a")
        self.task("b")
        self.graph.add_dependencies("b", ["a"])
        with self.assertRaises(QueuePolicyError):
            self.graph.add_dependencies("a", ["b"])
        self.assertEqual([], self.graph.prerequisites("a"))
        self.assertEqual(["a"], self.graph.prerequisites("b"))

    def test_indirect_cycle_rejected(self):
        for id in ("a", "b", "c"):
            self.task(id)
        self.graph.add_dependencies("b", ["a"])
        self.graph.add_dependencies("c", ["b"])
        with self.assertRaises(QueuePolicyError):
            self.graph.add_dependencies("a", ["c"])

    def test_batch_dependency_update_rolls_back_on_error(self):
        self.task("a")
        self.task("b")
        with self.assertRaises(QueuePolicyError):
            self.graph.add_dependencies("b", ["a", "not-existent"])
        self.assertEqual([], self.graph.prerequisites("b"))

    def test_cross_phase_or_branch_dependency_rejected(self):
        self.task("child")
        self.task("other-phase", "P01", "phase/01-desktop")
        self.task("other-branch", PHASE, "phase/00-other")
        for parent in ("other-phase", "other-branch"):
            with self.subTest(parent=parent), self.assertRaises(QueuePolicyError):
                self.graph.add_dependencies("child", [parent])

    def test_invalid_spec_rejected(self):
        self.task("a")
        self.task("b")
        for bad in (["a", "a"], ["b"], "a", [123]):
            with self.subTest(bad=bad), self.assertRaises((QueuePolicyError, TypeError)):
                self.graph.add_dependencies("b", bad)

    def test_cannot_change_dependencies_after_started(self):
        self.task("a")
        self.task("b")
        claimed = self.queue.claim(PHASE, BRANCH, "worker")
        with self.assertRaises(QueuePolicyError):
            self.graph.add_dependencies(claimed.id, ["b" if claimed.id == "a" else "a"])

    def test_blocked_parent_propagates_to_child_and_grandchild(self):
        for id in ("a", "b", "c"):
            self.task(id)
        self.graph.add_dependencies("b", ["a"])
        self.graph.add_dependencies("c", ["b"])
        first = self.queue.claim(PHASE, BRANCH, "worker")
        self.assertEqual("a", first.id)
        self.queue.fail(first, "worker", "CheckFailed", initial_delay=0)
        again = self.queue.claim(PHASE, BRANCH, "worker")
        self.assertEqual("a", again.id)
        self.queue.fail(again, "worker", "CheckFailed")
        self.assertIsNone(self.queue.claim(PHASE, BRANCH, "worker"))
        self.assertEqual("BLOCKED", self.queue.inspect("b")["state"])
        self.assertEqual("DependencyBlocked", self.queue.inspect("c")["error_class"])
        self.assertTrue(self.graph.dependency_status("c")["blocked"])

    def test_orphaned_dependency_cannot_run_after_corrupt_data(self):
        self.task("a")
        self.task("b")
        self.graph.add_dependencies("b", ["a"])
        with self.queue._connect() as db:
            db.execute("DELETE FROM development_jobs WHERE id='a'")
        info = self.graph.dependency_status("b")
        self.assertFalse(info["ready"])
        self.assertTrue(info["blocked"])
        self.assertEqual("MISSING", info["prerequisites"][0]["status"])
        self.assertIsNone(self.queue.claim(PHASE, BRANCH, "worker"))
        self.assertEqual("BLOCKED", self.queue.inspect("b")["state"])

    def test_malformed_nested_id_is_policy_error(self):
        self.task("a")
        self.task("b")
        with self.assertRaises(QueuePolicyError):
            self.graph.add_dependencies("b", [["a"]])

    def test_retrying_parent_prevents_premature_child_execution(self):
        self.task("parent")
        self.task("child", priority=0)
        self.graph.add_dependencies("child", ["parent"])
        first = self.queue.claim(PHASE, BRANCH, "worker")
        self.assertEqual("parent", first.id)
        self.queue.fail(first, "worker", "CheckFailed", initial_delay=5)
        self.assertIsNone(self.queue.claim(PHASE, BRANCH, "worker"))
        self.now[0] += 5
        self.finish("parent")
        self.finish("child")

    def test_prerequisites_persist_after_restart(self):
        self.task("a")
        self.task("b")
        self.graph.add_dependencies("b", ["a"])
        reloaded = JobGraph(JobQueue(self.path))
        self.assertEqual(["a"], reloaded.prerequisites("b"))

    def test_other_independent_work_remains_runnable(self):
        self.task("base", priority=90)
        self.task("blocked", priority=0)
        self.task("independent", priority=10)
        self.graph.add_dependencies("blocked", ["base"])
        self.finish("independent")
        self.finish("base")
        self.finish("blocked")


if __name__ == "__main__":
    unittest.main()
