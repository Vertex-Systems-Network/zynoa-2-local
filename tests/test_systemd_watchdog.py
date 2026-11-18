"""P00 systemd watchdog policy: no running host/service assumed."""
from __future__ import annotations

import json
import os
import socket
import sys
import tempfile
import unittest
from pathlib import Path

from tools.github_gateway import GitHubEvidenceError
from tools.phase_controller import EventJournal
from tools.phase_worker import LeaseBusy, PhaseObserver, PhaseWorker, WorkerLease
from tools.systemd_watchdog import (
    SystemdWatchdog, SystemdWatchdogDenied, _send_notification,
)

STATE = {
    "phase": "P00",
    "phase_status": "IN_PROGRESS",
    "active_branch": "phase/00-governance",
    "primary_pr": 1,
    "last_verified_remote_sha": "a" * 40,
    "worker_running": False,
}


class FakeRemote:
    def __init__(self, fail_on=(), unauthenticated_on=()):
        self.calls = 0
        self.fail_on = set(fail_on)
        self.unauthenticated_on = set(unauthenticated_on)

    def observe(self, state):
        self.calls += 1
        if self.calls in self.fail_on:
            raise GitHubEvidenceError("remote error may contain user secrets")
        return {
            "authenticated_remote": self.calls not in self.unauthenticated_on,
            "head_branch": "phase/00-governance",
            "pr_number": 1,
            "pr_head_sha": "c" * 40,
            "main_sha": "a" * 40,
            "checks_passed": False,
            "merged": False,
            "main_matches_merge": False,
            "branch_protected": False,
            "draft": True,
            "blocker_issue_numbers": [3],
            "transition_ready": False,
        }


class SystemdWatchdogPolicyTests(unittest.TestCase):
    def config(self, **overrides):
        settings = {
            "NOTIFY_SOCKET": "/run/systemd/notify",
            "WATCHDOG_USEC": "300000000",
            "WATCHDOG_PID": "1234",
        }
        settings.update(overrides)
        sent = []
        notifier = SystemdWatchdog.from_environment(
            settings, platform="linux", pid=1234,
            sender=lambda addr, marker: sent.append((addr, marker)),
        )
        return notifier, sent

    def test_operator_service_environment_required_and_bounded(self):
        for key, value in (
            ("NOTIFY_SOCKET", ""),
            ("NOTIFY_SOCKET", "@"),
            ("NOTIFY_SOCKET", "tcp://127.0.0.1:9000"),
            ("NOTIFY_SOCKET", "/run/notify\\bad"),
            ("NOTIFY_SOCKET", "/run/notify\nBAD=1"),
            ("NOTIFY_SOCKET", " " * 250),
            ("WATCHDOG_USEC", ""),
            ("WATCHDOG_USEC", "-10"),
            ("WATCHDOG_USEC", "0"),
            ("WATCHDOG_USEC", "1000000"),
            ("WATCHDOG_USEC", "700000000"),
            ("WATCHDOG_USEC", "300000000;rm -rf /"),
            ("WATCHDOG_PID", "1235"),
            ("WATCHDOG_PID", ""),
        ):
            settings = {
                "NOTIFY_SOCKET": "/run/systemd/notify",
                "WATCHDOG_USEC": "300000000",
                "WATCHDOG_PID": "1234",
            }
            settings[key] = value
            with self.subTest(field=key, value=value):
                with self.assertRaises(SystemdWatchdogDenied):
                    SystemdWatchdog.from_environment(
                        settings, platform="linux", pid=1234
                    )

    def test_no_systemd_environment_or_windows_is_denied(self):
        with self.assertRaises(SystemdWatchdogDenied):
            SystemdWatchdog.from_environment({}, platform="linux")
        with self.assertRaises(SystemdWatchdogDenied):
            SystemdWatchdog.from_environment(
                {"NOTIFY_SOCKET": "/run/systemd/notify",
                 "WATCHDOG_USEC": "300000000"}, platform="win32",
            )

    def test_only_first_success_emits_ready(self):
        notifier, sent = self.config()
        self.assertFalse(notifier.ready_sent)
        notifier.on_successful_observation()
        notifier.on_successful_observation()
        notifier.on_successful_observation()
        self.assertEqual(
            [b"READY=1\nWATCHDOG=1", b"WATCHDOG=1", b"WATCHDOG=1"],
            [m for _, m in sent],
        )
        self.assertTrue(notifier.ready_sent)
        self.assertTrue(all(addr == "/run/systemd/notify" for addr, _ in sent))

    def test_delivery_failure_aborts_readiness_without_leaking_path(self):
        def fail(_address, _message):
            raise OSError("secret host /home/user/canary")
        notifier = SystemdWatchdog(
            "/run/systemd/notify", 300000000, sender=fail,
        )
        with self.assertRaises(SystemdWatchdogDenied) as ctx:
            notifier.on_successful_observation()
        self.assertFalse(notifier.ready_sent)
        self.assertNotIn("/home/user/canary", str(ctx.exception))

    def test_service_template_is_opt_in_and_has_supervision(self):
        unit = (Path(__file__).resolve().parents[1]
                / "deploy/systemd/zynoa-phase-observer.service").read_text()
        for required in (
            "Type=notify", "NotifyAccess=main", "WatchdogSec=300",
            "TimeoutStartSec=150", "StartLimitBurst=4",
            "--systemd-watchdog", "Restart=on-failure",
            "User=zynoa", "NoNewPrivileges=true",
            "ProtectSystem=strict", "ReadWritePaths=/var/lib/zynoa",
        ):
            with self.subTest(setting=required):
                self.assertIn(required, unit)
        self.assertIn("TEMPLATE ONLY", unit)
        self.assertNotIn("Type=simple", unit)


class PhaseWorkerWatchdogTests(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory()
        self.addCleanup(self.temp.cleanup)
        self.path = Path(self.temp.name)
        self.file = self.path / "PHASE.json"
        self.file.write_text(json.dumps(STATE), encoding="utf-8")
        self.db_path = self.path / "phase.db"

    def make_worker(self, remote, notify):
        db = WorkerLease(self.db_path)
        journal = EventJournal(self.db_path)
        return PhaseWorker(
            PhaseObserver(remote, journal), db, self.file,
            sleep_interval=0.001, notify_success=notify,
        )

    def test_one_shot_diagnostic_never_sends_service_readiness(self):
        notifier, sent = SystemdWatchdogPolicyTests().config()
        worker = self.make_worker(FakeRemote(), notifier.on_successful_observation)
        worker.run_once()
        self.assertEqual([], sent)
        self.assertFalse(notifier.ready_sent)

    def test_loop_ready_only_after_observation_and_committed_health(self):
        results = []
        verifier = WorkerLease(self.db_path)
        def notify():
            # Inspect actual SQLite state during notification; durable commit
            # and same-owner lease are preconditions for systemd READY.
            from contextlib import closing
            import sqlite3
            with closing(sqlite3.connect(self.db_path)) as db:
                lease = db.execute(
                    "SELECT owner FROM worker_leases WHERE name='active-phase'"
                ).fetchone()
                row = db.execute(
                    "SELECT owner,head_sha,main_sha FROM worker_observation_health "
                    "WHERE name='active-phase'"
                ).fetchone()
            self.assertIsNotNone(lease)
            self.assertEqual(lease[0], row[0])
            self.assertEqual(("c" * 40, "a" * 40), row[1:])
            results.append(True)
        worker = self.make_worker(FakeRemote(), notify)
        worker.stop_signal.wait = lambda _seconds: False
        self.assertEqual(3, worker.run_loop(max_cycles=3))
        self.assertEqual([True, True, True], results)
        # Released at end of test; cannot be mistaken for deployed service.
        verifier.acquire("active-phase", "another-owner")
        verifier.release("active-phase", "another-owner")

    def test_api_failure_never_sends_watchdog(self):
        notifier, sent = SystemdWatchdogPolicyTests().config()
        remote = FakeRemote(fail_on=(2,))
        worker = self.make_worker(remote, notifier.on_successful_observation)
        worker.stop_signal.wait = lambda _seconds: False
        self.assertEqual(3, worker.run_loop(max_cycles=3))
        self.assertEqual(
            [b"READY=1\nWATCHDOG=1", b"WATCHDOG=1"],
            [msg for _, msg in sent],
        )
        self.assertEqual(3, remote.calls)
        self.assertFalse(worker.last_error_class)

    def test_initial_unreachable_remote_never_sends_ready(self):
        notifier, sent = SystemdWatchdogPolicyTests().config()
        worker = self.make_worker(FakeRemote(fail_on=(1, 2)), notifier.on_successful_observation)
        worker.stop_signal.wait = lambda _seconds: False
        self.assertEqual(2, worker.run_loop(max_cycles=2))
        self.assertEqual([], sent)
        self.assertEqual("GitHubEvidenceError", worker.last_error_class)

    def test_untrusted_response_refused_before_journal_and_ready(self):
        notifier, sent = SystemdWatchdogPolicyTests().config()
        worker = self.make_worker(
            FakeRemote(unauthenticated_on=(1,)), notifier.on_successful_observation,
        )
        worker.stop_signal.wait = lambda _seconds: False
        self.assertEqual(1, worker.run_loop(max_cycles=1))
        self.assertEqual([], sent)
        self.assertEqual("GitHubEvidenceError", worker.last_error_class)
        self.assertEqual(0, EventJournal(self.db_path).count())

    def test_notify_failure_exits_and_releases_lease_for_supervisor(self):
        def fail():
            raise SystemdWatchdogDenied("notification denied")
        worker = self.make_worker(FakeRemote(), fail)
        with self.assertRaises(SystemdWatchdogDenied):
            worker.run_loop(max_cycles=2)
        another = WorkerLease(self.db_path)
        another.acquire("active-phase", "new-owner")
        another.release("active-phase", "new-owner")


@unittest.skipUnless(sys.platform == "linux", "Linux AF_UNIX service socket only")
class LinuxSystemdDatagramTests(unittest.TestCase):
    def test_actual_unix_datagram_and_abstract_path(self):
        with tempfile.TemporaryDirectory() as root:
            dest = str(Path(root) / "notify.sock")
            with socket.socket(socket.AF_UNIX, socket.SOCK_DGRAM) as receiver:
                receiver.bind(dest)
                _send_notification(dest, b"READY=1\nWATCHDOG=1")
                payload, _ = receiver.recvfrom(64)
                self.assertEqual(b"READY=1\nWATCHDOG=1", payload)

    def test_unavailable_systemd_socket_fails_closed(self):
        with tempfile.TemporaryDirectory() as root:
            with self.assertRaises(SystemdWatchdogDenied):
                _send_notification(str(Path(root) / "missing.sock"), b"WATCHDOG=1")


if __name__ == "__main__":
    unittest.main()
