"""P00 durable single-phase development job queue.

Only preapproved, replay-safe, read-only jobs are admitted. This is a scheduler
primitive, NOT a model-backed coding agent or a privileged shell executor.
"""
from __future__ import annotations

import hashlib
import json
import re
import sqlite3
import time
import uuid
from dataclasses import dataclass
from pathlib import Path
from typing import Callable

from tools.phase_controller import PHASE_ORDER

SAFE_JOB_KINDS = frozenset(("phase-policy", "design-spec", "docs-integrity"))
_JOB_ID = re.compile(r"^[A-Za-z0-9][A-Za-z0-9._-]{0,99}$")
_BRANCH = re.compile(r"^phase/[a-z0-9][a-z0-9-]{0,90}$")


class QueuePolicyError(ValueError):
    """Invalid work specification or invalid ownership transition."""


@dataclass(frozen=True)
class ClaimedJob:
    id: str
    phase: str
    branch: str
    kind: str
    attempt: int
    lease_token: str
    lease_expires: float


class JobQueue:
    """SQLite BEGIN IMMEDIATE claims, fenced completions and bounded retries."""

    def __init__(self, db_path: Path, clock: Callable[[], float] = time.time):
        self.db_path = Path(db_path)
        self.clock = clock
        self.db_path.parent.mkdir(parents=True, exist_ok=True)
        with self._connect() as db:
            db.execute("PRAGMA journal_mode=WAL")
            db.execute("""
                CREATE TABLE IF NOT EXISTS development_jobs (
                    id TEXT PRIMARY KEY,
                    phase TEXT NOT NULL,
                    branch TEXT NOT NULL,
                    kind TEXT NOT NULL,
                    state TEXT NOT NULL,
                    priority INTEGER NOT NULL,
                    max_attempts INTEGER NOT NULL,
                    attempts INTEGER NOT NULL DEFAULT 0,
                    not_before REAL NOT NULL DEFAULT 0,
                    lease_owner TEXT,
                    lease_token TEXT,
                    lease_expires REAL,
                    error_class TEXT,
                    result_sha256 TEXT,
                    created_at REAL NOT NULL,
                    updated_at REAL NOT NULL
                )
            """)
            db.execute(
                "CREATE INDEX IF NOT EXISTS jobs_claim_idx "
                "ON development_jobs (state, phase, branch, not_before, priority, created_at)"
            )
        try:
            self.db_path.chmod(0o600)
        except OSError:
            pass

    def _connect(self):
        return sqlite3.connect(self.db_path, timeout=15)

    @staticmethod
    def _validate_spec(id: str, phase: str, branch: str, kind: str, max_attempts: int):
        if not isinstance(id, str) or not _JOB_ID.fullmatch(id):
            raise QueuePolicyError("invalid job id")
        if phase not in PHASE_ORDER:
            raise QueuePolicyError("unknown phase")
        if not isinstance(branch, str) or not _BRANCH.fullmatch(branch):
            raise QueuePolicyError("invalid branch")
        if phase == "P08I" and branch != "phase/08i-design-interoperability":
            raise QueuePolicyError("P08I must use designated phase branch")
        if kind not in SAFE_JOB_KINDS:
            raise QueuePolicyError("job kind not in read-only allowlist")
        if type(max_attempts) is not int or not 1 <= max_attempts <= 5:
            raise QueuePolicyError("max_attempts must be 1..5")

    def enqueue(self, id: str, phase: str, branch: str, kind: str,
                max_attempts: int = 3, priority: int = 50) -> bool:
        """True on new insert. Duplicate ID is accepted only for EXACT same spec."""
        self._validate_spec(id, phase, branch, kind, max_attempts)
        if type(priority) is not int or not 0 <= priority <= 100:
            raise QueuePolicyError("priority must be 0..100")
        now = self.clock()
        with self._connect() as db:
            db.execute("BEGIN IMMEDIATE")
            existing = db.execute(
                "SELECT phase, branch, kind, max_attempts, priority "
                "FROM development_jobs WHERE id=?", (id,)
            ).fetchone()
            spec = (phase, branch, kind, max_attempts, priority)
            if existing is not None:
                if existing != spec:
                    raise QueuePolicyError("duplicate job id has conflicting specification")
                return False
            db.execute(
                "INSERT INTO development_jobs "
                "(id,phase,branch,kind,state,priority,max_attempts,created_at,updated_at) "
                "VALUES (?,?,?,?,?,?,?,?,?)",
                (id, phase, branch, kind, "PENDING", priority, max_attempts, now, now),
            )
            return True

    def _recover_expired(self, db: sqlite3.Connection, now: float):
        # Only replay-safe job kinds exist in this queue. Never put network writes,
        # Git merges, shell commands or arbitrary AI tool calls here.
        db.execute(
            "UPDATE development_jobs SET state='BLOCKED', lease_owner=NULL,"
            "lease_token=NULL, lease_expires=NULL, error_class='LeaseExpired',"
            "updated_at=? WHERE state='RUNNING' AND lease_expires<=?"
            "AND attempts>=max_attempts",
            (now, now),
        )
        db.execute(
            "UPDATE development_jobs SET state='RETRY_WAIT', lease_owner=NULL,"
            "lease_token=NULL, lease_expires=NULL, not_before=?,"
            "error_class='LeaseExpired',updated_at=? "
            "WHERE state='RUNNING' AND lease_expires<=? AND attempts<max_attempts",
            (now, now, now),
        )

    def claim(self, phase: str, branch: str, owner: str,
              lease_seconds: float = 120.0) -> ClaimedJob | None:
        if phase not in PHASE_ORDER or not isinstance(branch, str) or not _BRANCH.fullmatch(branch):
            raise QueuePolicyError("invalid active phase or branch")
        if not isinstance(owner, str) or not _JOB_ID.fullmatch(owner):
            raise QueuePolicyError("invalid worker owner")
        if not 5 <= lease_seconds <= 3600:
            raise QueuePolicyError("lease must be 5..3600 seconds")
        now = self.clock()
        with self._connect() as db:
            db.execute("BEGIN IMMEDIATE")
            self._recover_expired(db, now)
            row = db.execute(
                "SELECT id,kind,attempts FROM development_jobs "
                "WHERE phase=? AND branch=? AND state IN ('PENDING','RETRY_WAIT') "
                "AND not_before<=? ORDER BY priority ASC, created_at ASC, id ASC LIMIT 1",
                (phase, branch, now),
            ).fetchone()
            if row is None:
                return None
            id, kind, attempts = row
            token = uuid.uuid4().hex
            until = now + lease_seconds
            updated = db.execute(
                "UPDATE development_jobs SET state='RUNNING', attempts=?, "
                "lease_owner=?,lease_token=?,lease_expires=?,updated_at=? "
                "WHERE id=? AND state IN ('PENDING','RETRY_WAIT')",
                (attempts + 1, owner, token, until, now, id),
            )
            if updated.rowcount != 1:
                raise QueuePolicyError("concurrent claim conflict")
            return ClaimedJob(id, phase, branch, kind, attempts + 1, token, until)

    def _fenced_update(self, job: ClaimedJob, owner: str, fields: str, values: tuple):
        if not isinstance(job, ClaimedJob) or not isinstance(owner, str):
            raise QueuePolicyError("invalid fenced completion")
        now = self.clock()
        with self._connect() as db:
            db.execute("BEGIN IMMEDIATE")
            cur = db.execute(
                "UPDATE development_jobs SET " + fields + ",updated_at=? "
                "WHERE id=? AND state='RUNNING' AND phase=? AND branch=? "
                "AND attempts=? AND lease_owner=? AND lease_token=? AND lease_expires>?",
                (*values, now, job.id, job.phase, job.branch, job.attempt,
                 owner, job.lease_token, now),
            )
            if cur.rowcount != 1:
                raise QueuePolicyError("stale job lease or invalid owner")

    def heartbeat(self, job: ClaimedJob, owner: str, lease_seconds: float = 120.0):
        if not 5 <= lease_seconds <= 3600:
            raise QueuePolicyError("invalid lease")
        self._fenced_update(job, owner, "lease_expires=?", (self.clock() + lease_seconds,))

    def complete(self, job: ClaimedJob, owner: str, result: dict):
        """Only a small validated result marker is stored; no raw task output."""
        if set(result) - {"check", "passed"} or type(result.get("passed")) is not bool:
            raise QueuePolicyError("invalid result schema")
        if result.get("check") != job.kind:
            raise QueuePolicyError("handler result mismatch")
        digest = hashlib.sha256(json.dumps(result, sort_keys=True).encode()).hexdigest()
        self._fenced_update(
            job, owner, "state='SUCCEEDED',result_sha256=?,lease_owner=NULL,"
            "lease_token=NULL,lease_expires=NULL,error_class=NULL",
            (digest,),
        )

    def fail(self, job: ClaimedJob, owner: str, error_class: str,
             initial_delay: float = 2.0):
        if not isinstance(error_class, str) or not re.fullmatch(r"[A-Za-z][A-Za-z0-9_]{0,63}", error_class):
            raise QueuePolicyError("unsafe error class")
        if not 0 <= initial_delay <= 120:
            raise QueuePolicyError("invalid retry delay")
        if job.attempt >= self.max_attempts(job.id):
            state, not_before = "BLOCKED", 0
        else:
            state = "RETRY_WAIT"
            not_before = self.clock() + min(300, initial_delay * (2 ** (job.attempt - 1)))
        self._fenced_update(
            job, owner, "state=?,not_before=?,error_class=?,"
            "lease_owner=NULL,lease_token=NULL,lease_expires=NULL",
            (state, not_before, error_class),
        )

    def max_attempts(self, id: str) -> int:
        with self._connect() as db:
            row = db.execute("SELECT max_attempts FROM development_jobs WHERE id=?", (id,)).fetchone()
            if row is None:
                raise QueuePolicyError("job not found")
            return int(row[0])

    def inspect(self, id: str) -> dict | None:
        with self._connect() as db:
            db.row_factory = sqlite3.Row
            row = db.execute(
                "SELECT id,phase,branch,kind,state,attempts,max_attempts,"
                "error_class,result_sha256 FROM development_jobs WHERE id=?", (id,)
            ).fetchone()
            return dict(row) if row else None

    def stats(self) -> dict:
        with self._connect() as db:
            return {state: n for state, n in db.execute(
                "SELECT state,COUNT(*) FROM development_jobs GROUP BY state"
            ).fetchall()}
