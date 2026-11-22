#!/usr/bin/env python3
"""Resumable read-only active-phase controller worker (not deployed).

It observes authenticated remote phase/PR/CI/issue facts and checkpoints
sanitized results in a SQLite journal. It has no GitHub write capability.
No AI coding model or autonomous merge executor is implied.
"""
from __future__ import annotations

import argparse
from contextlib import closing
import hashlib
import json
import re
import signal
import sqlite3
import threading
import time
import uuid
from pathlib import Path
from typing import Callable, Mapping

from tools.github_gateway import GitHubEvidenceError, GitHubGateway
from tools.phase_controller import EventJournal, PhasePolicyError, PHASE_ORDER, validate_snapshot
from tools.systemd_watchdog import SystemdWatchdog, SystemdWatchdogDenied


class LeaseBusy(RuntimeError):
    pass


class LeaseLost(RuntimeError):
    pass


class WorkerLease:
    """Single-owner renewable lease backed by SQLite BEGIN IMMEDIATE."""

    def __init__(self, db_path: Path, clock: Callable[[], float] = time.time):
        self.db_path = Path(db_path)
        self.db_path.parent.mkdir(parents=True, exist_ok=True)
        self.clock = clock
        with closing(self._connect()) as db, db:
            db.execute("PRAGMA journal_mode=WAL")
            db.execute(
                "CREATE TABLE IF NOT EXISTS worker_leases "
                "(name TEXT PRIMARY KEY, owner TEXT NOT NULL, expires_at REAL NOT NULL)"
            )
            # Separate from the deduplicated event journal. A successful
            # observation must advance its timestamp every polling cycle;
            # a renewed lease without GitHub success is insufficient.
            db.execute(
                "CREATE TABLE IF NOT EXISTS worker_observation_health "
                "(name TEXT PRIMARY KEY, owner TEXT NOT NULL, observed_at REAL NOT NULL, "
                "head_sha TEXT NOT NULL, main_sha TEXT NOT NULL)"
            )
        try:
            self.db_path.chmod(0o600)
        except OSError:
            pass

    def _connect(self):
        return sqlite3.connect(self.db_path, timeout=15)

    def acquire(self, name: str, owner: str, ttl_seconds: float = 180.0) -> None:
        if not name or not owner or ttl_seconds <= 0:
            raise ValueError("invalid lease arguments")
        now = self.clock()
        with closing(self._connect()) as db, db:
            db.execute("BEGIN IMMEDIATE")
            row = db.execute(
                "SELECT owner, expires_at FROM worker_leases WHERE name=?", (name,)
            ).fetchone()
            if row and row[0] != owner and row[1] > now:
                raise LeaseBusy("another controller owns the lease")
            db.execute(
                "INSERT INTO worker_leases(name, owner, expires_at) VALUES(?, ?, ?) "
                "ON CONFLICT(name) DO UPDATE SET owner=excluded.owner, expires_at=excluded.expires_at",
                (name, owner, now + ttl_seconds),
            )

    def heartbeat(self, name: str, owner: str, ttl_seconds: float = 180.0) -> None:
        now = self.clock()
        with closing(self._connect()) as db, db:
            row = db.execute(
                "UPDATE worker_leases SET expires_at=? "
                "WHERE name=? AND owner=? AND expires_at>?",
                (now + ttl_seconds, name, owner, now),
            )
            if row.rowcount != 1:
                raise LeaseLost("lease expired or ownership changed")

    def record_observation(self, name: str, owner: str, head_sha: str, main_sha: str) -> None:
        """Persist only successfully observed remote SHAs for the live lease owner.

        Never records raw GitHub responses, credentials, error messages or
        model/user content. Old workers cannot update a stolen/expired lease.
        """
        if not name or not owner or not all(
            isinstance(s, str) and re.fullmatch(r"[a-f0-9]{40}", s)
            for s in (head_sha, main_sha)
        ):
            raise ValueError("remote observation SHA invalid")
        now = self.clock()
        with closing(self._connect()) as db, db:
            db.execute("BEGIN IMMEDIATE")
            lease = db.execute(
                "SELECT owner, expires_at FROM worker_leases WHERE name=?", (name,)
            ).fetchone()
            if lease is None or lease[0] != owner or lease[1] <= now:
                raise LeaseLost("cannot record observation without live lease")
            db.execute(
                "INSERT INTO worker_observation_health "
                "(name,owner,observed_at,head_sha,main_sha) VALUES (?,?,?,?,?) "
                "ON CONFLICT(name) DO UPDATE SET owner=excluded.owner, "
                "observed_at=excluded.observed_at, head_sha=excluded.head_sha, "
                "main_sha=excluded.main_sha",
                (name, owner, now, head_sha, main_sha),
            )

    def release(self, name: str, owner: str) -> None:
        with closing(self._connect()) as db, db:
            db.execute("DELETE FROM worker_leases WHERE name=? AND owner=?", (name, owner))


class PhaseObserver:
    """One bounded remote reconciliation per call; stores no private raw content."""

    def __init__(self, gateway: GitHubGateway, journal: EventJournal):
        self.gateway = gateway
        self.journal = journal

    def run_once(self, state: Mapping) -> dict:
        errors = validate_snapshot(state)
        if errors:
            raise PhasePolicyError("; ".join(errors))
        observation = self.gateway.observe(state)
        if observation.get("authenticated_remote") is not True:
            raise GitHubEvidenceError("GitHub observer response is not authenticated")
        if (observation.get("head_branch") != state.get("active_branch")
                or observation.get("pr_number") != state.get("primary_pr")):
            raise GitHubEvidenceError("remote phase PR identity mismatch")
        # An observed merge is NOT a transition: remote SHA, phase state and
        # required gates still require separate independent verification.
        view = {
            "phase": state.get("phase"),
            "branch": observation["head_branch"],
            "primary_pr": observation["pr_number"],
            "head_sha": observation["pr_head_sha"],
            "main_sha": observation["main_sha"],
            "checks_passed": observation["checks_passed"],
            "merged": observation["merged"],
            "main_matches_merge": observation["main_matches_merge"],
            "branch_protected": observation["branch_protected"],
            "draft": observation["draft"],
            "blocking_issue_numbers": observation["blocker_issue_numbers"],
            "blocker_policy_complete": observation.get("blocker_policy_complete") is True,
            "transition_ready": observation["transition_ready"] and state.get("phase_status") == "MERGED_VERIFIED",
            "action": "OBSERVE_ONLY",
            "next_phase_created": False,
            "merge_performed": False,
        }
        # Stable payload hash avoids duplicate journal entries on replay.
        encoded = json.dumps(view, sort_keys=True, separators=(",", ":"))
        event_id = "observation:" + hashlib.sha256(encoded.encode()).hexdigest()[:40]
        self.journal.append(event_id, str(view["phase"]), "remote_observed", view)
        return view


class PhaseWorker:
    """Reusable loop with bounded retry delay and safe issue-free failure log."""

    def __init__(self, observer: PhaseObserver, lease: WorkerLease, state_file: Path,
                 sleep_interval: float = 30.0, owner: str | None = None,
                 notify_success: Callable[[], None] | None = None):
        if sleep_interval <= 0:
            raise ValueError("polling interval must be positive")
        self.observer = observer
        self.lease = lease
        self.state_file = Path(state_file)
        self.sleep_interval = sleep_interval
        self.owner = owner or uuid.uuid4().hex
        self.name = "active-phase"
        self.stop_signal = threading.Event()
        self.last_error_class: str | None = None
        self.notify_success = notify_success

    def run_once(self) -> dict:
        self.lease.acquire(self.name, self.owner)
        try:
            state = json.loads(self.state_file.read_text(encoding="utf-8"))
            result = self.observer.run_once(state)
            self.lease.heartbeat(self.name, self.owner)
            self.lease.record_observation(
                self.name, self.owner, result["head_sha"], result["main_sha"]
            )
            return result
        finally:
            self.lease.release(self.name, self.owner)

    def run_loop(self, max_cycles: int | None = None) -> int:
        """Keep ONE lease for the entire loop, not one lock per observation."""
        cycles, failures = 0, 0
        self.lease.acquire(self.name, self.owner)
        try:
            while not self.stop_signal.is_set() and (max_cycles is None or cycles < max_cycles):
                state = {}
                try:
                    state = json.loads(self.state_file.read_text(encoding="utf-8"))
                    result = self.observer.run_once(state)
                    self.lease.heartbeat(self.name, self.owner)
                    self.lease.record_observation(
                        self.name, self.owner, result["head_sha"], result["main_sha"]
                    )
                    # One and only one authority path: a verified remote
                    # observation and durable owner-fenced success record
                    # before the main service process notifies systemd.
                    if self.notify_success is not None:
                        self.notify_success()
                    failures = 0
                    self.last_error_class = None
                except (GitHubEvidenceError, PhasePolicyError, sqlite3.Error, OSError, ValueError) as exc:
                    failures += 1
                    # Never log exception strings; persist only a safe error class.
                    self.last_error_class = type(exc).__name__
                    # Never invent P00 attribution for invalid/missing phase state.
                    phase = state.get("phase") if isinstance(state, dict) else None
                    if phase in PHASE_ORDER:
                        self.observer.journal.append(
                            "blocked:" + self.last_error_class + ":" + str(min(failures, 3)),
                            phase, "observation_blocked",
                            {"error_class": self.last_error_class, "retry": min(failures, 3)},
                        )
                    # Keep the lease fresh during transient GitHub/API failures.
                    self.lease.heartbeat(self.name, self.owner)
                except LeaseLost:
                    self.last_error_class = "LeaseLost"
                    break
                cycles += 1
                delay = min(300, self.sleep_interval * 2 ** min(max(failures - 1, 0), 3))
                if max_cycles is None or cycles < max_cycles:
                    # Renew lease during long backoff. Otherwise a 300-second
                    # retry could outlive its 180-second lease and permit a
                    # second worker to take over while the first is sleeping.
                    remaining = delay
                    while remaining > 0 and not self.stop_signal.is_set():
                        step = min(30.0, remaining)
                        self.stop_signal.wait(step)
                        if self.stop_signal.is_set():
                            break
                        self.lease.heartbeat(self.name, self.owner)
                        remaining -= step
        finally:
            self.lease.release(self.name, self.owner)
        return cycles


def main() -> int:
    parser = argparse.ArgumentParser(description="Zynoa active-phase read-only observer; no AI/merge actions")
    parser.add_argument("--repo", default="Vertex-Systems-Network/zynoa-2-local")
    parser.add_argument("--state", type=Path, default=Path("docs/state/PHASE.json"))
    parser.add_argument("--db", type=Path, default=Path.home() / ".zynoa" / "controller" / "events.db")
    parser.add_argument("--interval", type=float, default=30.0)
    parser.add_argument("--once", action="store_true")
    parser.add_argument("--cycles", type=int, help="bounded test cycles; omission runs continuously")
    parser.add_argument("--systemd-watchdog", action="store_true",
                        help="operator-only systemd Type=notify readiness after verified GitHub observations")
    args = parser.parse_args()
    if args.interval <= 0 or (args.cycles is not None and args.cycles < 1):
        parser.error("interval and cycles must be positive")
    if args.systemd_watchdog and (args.once or args.cycles is not None):
        parser.error("systemd watchdog requires an unbounded service loop")
    try:
        notifier = SystemdWatchdog.from_environment() if args.systemd_watchdog else None
        client = GitHubGateway(args.repo)
        lease = WorkerLease(args.db)
        worker = PhaseWorker(PhaseObserver(client, EventJournal(args.db)), lease, args.state,
                             sleep_interval=args.interval,
                             notify_success=(notifier.on_successful_observation if notifier else None))
        for sig in (signal.SIGINT, signal.SIGTERM):
            signal.signal(sig, lambda _signum, _frame: worker.stop_signal.set())
        if args.once:
            result = worker.run_once()
            print(json.dumps(result, indent=2))
            return 0
        count = worker.run_loop(args.cycles)
        print(json.dumps({
            "observations_attempted": count, "last_error_class": worker.last_error_class,
            "github_mutations": 0, "worker_deployed_by_this_command": False,
        }))
        return 1 if worker.last_error_class else 0
    except (GitHubEvidenceError, PhasePolicyError, LeaseBusy, LeaseLost, SystemdWatchdogDenied,
            OSError, ValueError) as exc:
        print(json.dumps({"status": "BLOCKED", "error_class": type(exc).__name__,
                          "credentials_echoed": False, "github_mutations": 0}))
        return 2


if __name__ == "__main__":
    raise SystemExit(main())
