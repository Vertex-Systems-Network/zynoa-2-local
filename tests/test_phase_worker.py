"""Crash/restart/concurrency tests for read-only P00 worker; no GitHub calls."""
import json
import tempfile
import unittest
from pathlib import Path

from tools.phase_worker import LeaseBusy, LeaseLost, WorkerLease, PhaseObserver, PhaseWorker
from tools.phase_controller import EventJournal
from tools.github_gateway import GitHubEvidenceError


STATE = {
    "phase": "P00",
    "phase_status": "IN_PROGRESS",
    "active_branch": "phase/00-governance",
    "primary_pr": 1,
    "last_verified_remote_sha": "a" * 40,
    "worker_running": False,
}


class StubGateway:
    def __init__(self):
        self.calls = 0
        self.should_fail = False

    def observe(self, state):
        self.calls += 1
        if self.should_fail:
            raise GitHubEvidenceError("unavailable")
        return {
            "head_branch": "phase/00-governance",
            "pr_number": 1,
            "pr_head_sha": "c" * 40,
            "main_sha": "a" * 40,
            "checks_passed": True,
            "merged": False,
            "main_matches_merge": False,
            "branch_protected": False,
            "draft": True,
            "blocker_issue_numbers": [3],
            "transition_ready": False,
        }


class LeaseTests(unittest.TestCase):
    def test_second_worker_cannot_steal_active_lease(self):
        with tempfile.TemporaryDirectory() as d:
            db = Path(d) / "worker.db"
            clock = [1000.0]
            a = WorkerLease(db, clock=lambda: clock[0])
            b = WorkerLease(db, clock=lambda: clock[0])
            a.acquire("phase", "owner-a", 90)
            with self.assertRaises(LeaseBusy):
                b.acquire("phase", "owner-b", 90)
            a.release("phase", "owner-a")
            b.acquire("phase", "owner-b", 90)

    def test_crash_restart_after_expiration(self):
        with tempfile.TemporaryDirectory() as d:
            db = Path(d) / "worker.db"
            clock = [1000.0]
            a = WorkerLease(db, clock=lambda: clock[0])
            a.acquire("phase", "owner-a", 30)
            clock[0] = 1031.0
            b = WorkerLease(db, clock=lambda: clock[0])
            b.acquire("phase", "owner-b", 60)
            with self.assertRaises(LeaseLost):
                a.heartbeat("phase", "owner-a")

    def test_nonowner_release_does_not_unlock(self):
        with tempfile.TemporaryDirectory() as d:
            lease = WorkerLease(Path(d) / "state.db")
            lease.acquire("phase", "owner-a")
            lease.release("phase", "wrong-owner")
            with self.assertRaises(LeaseBusy):
                lease.acquire("phase", "owner-b")


class ObserverTests(unittest.TestCase):
    def make_worker(self, path: Path, gateway: StubGateway):
        path.mkdir(parents=True, exist_ok=True)
        state = path / "PHASE.json"
        state.write_text(json.dumps(STATE), encoding="utf-8")
        db = path / "events.db"
        journal = EventJournal(db)
        lease = WorkerLease(db)
        observer = PhaseObserver(gateway, journal)
        worker = PhaseWorker(observer, lease, state, sleep_interval=0.001)
        return worker, journal

    def test_observe_replay_deduplicated(self):
        with tempfile.TemporaryDirectory() as d:
            gateway = StubGateway()
            worker, events = self.make_worker(Path(d), gateway)
            first = worker.run_once()
            again = worker.run_once()
            self.assertEqual(first, again)
            self.assertEqual(1, events.count())
            self.assertEqual("OBSERVE_ONLY", first["action"])
            self.assertFalse(first["transition_ready"])
            self.assertEqual(2, gateway.calls)

    def test_restart_reuses_event_journal(self):
        with tempfile.TemporaryDirectory() as d:
            directory = Path(d)
            gateway = StubGateway()
            worker, events = self.make_worker(directory, gateway)
            worker.run_once()
            new_worker, new_events = self.make_worker(directory, gateway)
            new_worker.run_once()
            self.assertEqual(1, new_events.count())

    def test_no_pr_merge_even_with_observer_success(self):
        with tempfile.TemporaryDirectory() as d:
            worker, _ = self.make_worker(Path(d), StubGateway())
            result = worker.run_once()
            self.assertFalse(result["merge_performed"])
            self.assertFalse(result["next_phase_created"])

    def test_bounded_failure_loop_reports_blocked(self):
        with tempfile.TemporaryDirectory() as d:
            gateway = StubGateway()
            gateway.should_fail = True
            worker, _ = self.make_worker(Path(d), gateway)
            self.assertEqual(2, worker.run_loop(max_cycles=2))
            self.assertEqual("GitHubEvidenceError", worker.last_error_class)
            self.assertEqual(2, gateway.calls)

    def test_unexpected_corrupt_local_state_rejected(self):
        with tempfile.TemporaryDirectory() as d:
            worker, _ = self.make_worker(Path(d), StubGateway())
            worker.state_file.write_text('{"phase":"P99"}', encoding="utf-8")
            self.assertEqual(1, worker.run_loop(max_cycles=1))
            self.assertEqual("PhasePolicyError", worker.last_error_class)


if __name__ == "__main__":
    unittest.main()
