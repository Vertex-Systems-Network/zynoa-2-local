"""P00 durable remote-success heartbeat tests: local disposable SQLite only."""
from __future__ import annotations

import json
from contextlib import closing
import sqlite3
import tempfile
import time
import unittest
from pathlib import Path

from tools.host_bootstrap import HostLayout
from tools.phase_controller import EventJournal
from tools.phase_worker import LeaseLost, PhaseObserver, PhaseWorker, WorkerLease
from tools.worker_health import WorkerHealthDenied, probe_local_observer

HEAD = "c" * 40
MAIN = "a" * 40
STATE = {
    "phase": "P00", "phase_status": "IN_PROGRESS",
    "active_branch": "phase/00-governance", "primary_pr": 1,
    "last_verified_remote_sha": MAIN, "worker_running": False,
}


class FakeGateway:
    def __init__(self, fail=False):
        self.fail = fail
        self.calls = 0

    def observe(self, state):
        from tools.github_gateway import GitHubEvidenceError
        self.calls += 1
        if self.fail:
            raise GitHubEvidenceError("untrusted api error: never record this")
        return {
            "authenticated_remote": True,
            "head_branch": "phase/00-governance", "pr_number": 1,
            "pr_head_sha": HEAD, "main_sha": MAIN,
            "checks_passed": False, "merged": False,
            "main_matches_merge": False, "branch_protected": False,
            "draft": True, "blocker_issue_numbers": [3],
            "transition_ready": False,
        }


class WorkerHeartbeatTests(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        self.addCleanup(self.tmp.cleanup)
        root = Path(self.tmp.name)
        self.repo = root / "checkout"
        self.host = root / "worker-data"
        (self.repo / "docs/state").mkdir(parents=True)
        (self.repo / "AGENTS.md").write_text("P00 scope\n", encoding="utf-8")
        (self.repo / "docs/state/PHASE.json").write_text(
            json.dumps(STATE), encoding="utf-8",
        )
        self.layout = HostLayout(self.repo, self.host)
        self.layout.initialize(authorized=True)

    def report(self, now=None, age=120):
        return probe_local_observer(
            self.repo, self.host,
            clock=(lambda: now) if now is not None else time.time,
            max_age_seconds=age,
        )

    def test_new_host_has_no_verified_observer(self):
        report = self.report()
        self.assertEqual("OBSERVER_NOT_FRESHLY_VERIFIED", report["status"])
        self.assertFalse(report["lease_current"])
        self.assertFalse(report["last_successful_remote_observation_recent"])
        self.assertFalse(report["persistent_worker_deployment_verified"])
        self.assertEqual(0, report["github_writes"])

    def test_owner_must_hold_lease_and_valid_remote_shas(self):
        lease = WorkerLease(self.layout.db, clock=lambda: 1000.0)
        with self.assertRaises(LeaseLost):
            lease.record_observation("active-phase", "owner", HEAD, MAIN)
        lease.acquire("active-phase", "owner", ttl_seconds=180)
        for bad in ("invalid", "", True, "z" * 40):
            with self.subTest(bad=bad), self.assertRaises(ValueError):
                lease.record_observation("active-phase", "owner", bad, MAIN)
        with self.assertRaises(LeaseLost):
            lease.record_observation("active-phase", "different-owner", HEAD, MAIN)
        lease.record_observation("active-phase", "owner", HEAD, MAIN)
        report = self.report(now=1000.0)
        self.assertEqual("RECENT_LOCAL_OBSERVER_EVIDENCE", report["status"])
        self.assertTrue(report["lease_current"])
        self.assertTrue(report["last_successful_remote_observation_recent"])
        self.assertFalse(report["github_remote_rechecked"])
        self.assertFalse(report["systemd_service_verified"])
        lease.release("active-phase", "owner")
        self.assertFalse(self.report(now=1000.0)["lease_current"])

    def test_expired_and_stale_success_cannot_report_running(self):
        clock = [1000.0]
        lease = WorkerLease(self.layout.db, clock=lambda: clock[0])
        lease.acquire("active-phase", "owner", 180.0)
        lease.record_observation("active-phase", "owner", HEAD, MAIN)
        clock[0] = 1150.0
        self.assertFalse(self.report(now=clock[0], age=120)["last_successful_remote_observation_recent"])
        clock[0] = 1181.0
        self.assertFalse(self.report(now=clock[0])["lease_current"])
        with self.assertRaises(LeaseLost):
            lease.record_observation("active-phase", "owner", HEAD, MAIN)

    def test_new_owner_cannot_reuse_previous_observation(self):
        clock = [1000.0]
        lease = WorkerLease(self.layout.db, clock=lambda: clock[0])
        lease.acquire("active-phase", "old-owner", 5)
        lease.record_observation("active-phase", "old-owner", HEAD, MAIN)
        clock[0] = 1006.0
        lease.acquire("active-phase", "new-owner", 180)
        report = self.report(now=1006.0)
        self.assertTrue(report["lease_current"])
        self.assertFalse(report["last_successful_remote_observation_recent"])
        lease.record_observation("active-phase", "new-owner", HEAD, MAIN)
        self.assertTrue(self.report(now=1006.0)["last_successful_remote_observation_recent"])

    def test_worker_run_once_records_success_but_cannot_claim_persistence(self):
        gateway = FakeGateway()
        lease = WorkerLease(self.layout.db)
        worker = PhaseWorker(
            PhaseObserver(gateway, EventJournal(self.layout.db)), lease,
            self.repo / "docs/state/PHASE.json",
        )
        view = worker.run_once()
        self.assertEqual(HEAD, view["head_sha"])
        self.assertEqual(1, gateway.calls)
        with closing(sqlite3.connect(self.layout.db)) as db, db:
            row = db.execute(
                "SELECT head_sha,main_sha FROM worker_observation_health "
                "WHERE name='active-phase'"
            ).fetchone()
        self.assertEqual((HEAD, MAIN), row)
        # A one-shot process has already released its lease. Do not imply 24/7.
        self.assertFalse(self.report()["last_successful_remote_observation_recent"])

    def test_success_inside_live_loop_updates_heartbeat(self):
        gateway = FakeGateway()
        worker = PhaseWorker(
            PhaseObserver(gateway, EventJournal(self.layout.db)),
            WorkerLease(self.layout.db),
            self.repo / "docs/state/PHASE.json", sleep_interval=1,
        )
        observed = []
        def inspect_then_stop(_seconds):
            observed.append(self.report())
            worker.stop_signal.set()
        worker.stop_signal.wait = inspect_then_stop
        self.assertEqual(1, worker.run_loop(max_cycles=2))
        self.assertTrue(observed[0]["last_successful_remote_observation_recent"])
        self.assertFalse(observed[0]["persistent_worker_deployment_verified"])
        self.assertFalse(self.report()["lease_current"])

    def test_failed_remote_observation_never_advances_success(self):
        gateway = FakeGateway(fail=True)
        worker = PhaseWorker(
            PhaseObserver(gateway, EventJournal(self.layout.db)),
            WorkerLease(self.layout.db),
            self.repo / "docs/state/PHASE.json", sleep_interval=1,
        )
        seen = []
        def inspect_then_stop(_seconds):
            seen.append(self.report())
            worker.stop_signal.set()
        worker.stop_signal.wait = inspect_then_stop
        self.assertEqual(1, worker.run_loop(max_cycles=2))
        self.assertEqual("GitHubEvidenceError", worker.last_error_class)
        self.assertTrue(seen[0]["lease_current"])
        self.assertFalse(seen[0]["last_successful_remote_observation_recent"])
        with closing(sqlite3.connect(self.layout.db)) as db, db:
            self.assertEqual(0, db.execute(
                "SELECT COUNT(*) FROM worker_observation_health"
            ).fetchone()[0])

    def test_missing_success_table_or_corrupt_data_fails_closed(self):
        with closing(sqlite3.connect(self.layout.db)) as db, db:
            db.execute("DROP TABLE worker_observation_health")
        with self.assertRaises(WorkerHealthDenied):
            self.report()

    def test_freshness_parameters_and_absent_host_are_denied(self):
        for value in (0, 301, True, -1, "120"):
            with self.subTest(value=value), self.assertRaises(WorkerHealthDenied):
                self.report(age=value)
        with self.assertRaises(Exception):
            probe_local_observer(self.repo, self.host / "does-not-exist")

    def test_probe_preserves_database_records_and_host_manifest(self):
        lease = WorkerLease(self.layout.db)
        lease.acquire("active-phase", "owner")
        lease.record_observation("active-phase", "owner", HEAD, MAIN)
        # A WAL-mode SQLite read-only connection may create -wal/-shm protocol
        # sidecars; immutable=1 would miss uncheckpointed live transactions.
        # Verify no application/host data records change instead.
        def rows():
            with closing(sqlite3.connect(
                self.layout.db.as_uri() + "?mode=ro", uri=True
            )) as db:
                return (
                    db.execute("SELECT * FROM worker_leases").fetchall(),
                    db.execute("SELECT * FROM worker_observation_health").fetchall(),
                    db.execute("SELECT * FROM phase_events").fetchall(),
                )
        marker_before = self.layout.marker.read_bytes()
        before = rows()
        report = self.report()
        after = rows()
        self.assertEqual(marker_before, self.layout.marker.read_bytes())
        self.assertEqual(before, after)
        self.assertTrue(report["last_successful_remote_observation_recent"])
        self.assertFalse(report["model_coding_verified"])
        self.assertFalse(report["os_sandbox_verified"])
        lease.release("active-phase", "owner")


if __name__ == "__main__":
    unittest.main()
