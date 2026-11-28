"""Durable, phase-scoped dependency graph for replay-safe P00 development jobs.

Dependency edits are atomic, cycle-checked and forbidden after the child starts.
The graph coordinates only JobQueue's fixed read-only job kinds; it cannot
execute models, shell commands, Git mutations, or release operations.
"""
from __future__ import annotations

from contextlib import closing
from typing import Sequence

from tools.dev_job_queue import JobQueue, QueuePolicyError


class JobGraph:
    def __init__(self, queue: JobQueue):
        self.queue = queue

    def add_dependencies(self, job_id: str, prerequisites: Sequence[str]) -> int:
        """Atomically link prerequisites; repeats are idempotent. Returns new edges."""
        if isinstance(prerequisites, (str, bytes)) or not isinstance(prerequisites, (list, tuple)):
            raise QueuePolicyError("prerequisites must be a list of job IDs")
        if any(not isinstance(parent, str) for parent in prerequisites):
            raise QueuePolicyError("prerequisite IDs must be strings")
        if len(prerequisites) > 32 or len(set(prerequisites)) != len(prerequisites):
            raise QueuePolicyError("too many or repeated prerequisites")
        if not prerequisites:
            return 0
        if any(not isinstance(parent, str) or not parent or parent == job_id
               for parent in prerequisites):
            raise QueuePolicyError("invalid/self dependency")
        with closing(self.queue._connect()) as db, db:
            db.execute("BEGIN IMMEDIATE")
            target = db.execute(
                "SELECT phase,branch,state,attempts FROM development_jobs WHERE id=?",
                (job_id,),
            ).fetchone()
            if target is None:
                raise QueuePolicyError("dependent job not found")
            phase, branch, state, attempts = target
            if state != "PENDING" or attempts:
                raise QueuePolicyError("cannot change dependencies of started job")
            existing = db.execute(
                "SELECT depends_on_job_id FROM job_dependencies WHERE job_id=?",
                (job_id,),
            ).fetchall()
            if len(existing) + len(prerequisites) > 64:
                raise QueuePolicyError("dependency fan-in cap exceeded")
            inserted = 0
            for parent_id in prerequisites:
                parent = db.execute(
                    "SELECT phase,branch FROM development_jobs WHERE id=?",
                    (parent_id,),
                ).fetchone()
                if parent is None:
                    raise QueuePolicyError("missing prerequisite: " + parent_id)
                if parent != (phase, branch):
                    raise QueuePolicyError("cross-phase or cross-branch dependency prohibited")
                # Adding edge job_id -> parent_id cycles iff the parent's
                # existing ancestry already reaches job_id.
                cyclic = db.execute(
                    """
                    WITH RECURSIVE ancestors(node) AS (
                        SELECT depends_on_job_id
                        FROM job_dependencies WHERE job_id=?
                        UNION
                        SELECT d.depends_on_job_id FROM job_dependencies d
                        JOIN ancestors a ON d.job_id=a.node
                    )
                    SELECT 1 FROM ancestors WHERE node=? LIMIT 1
                    """,
                    (parent_id, job_id),
                ).fetchone()
                if cyclic:
                    raise QueuePolicyError("dependency cycle")
                result = db.execute(
                    "INSERT OR IGNORE INTO job_dependencies(job_id,depends_on_job_id) "
                    "VALUES (?,?)",
                    (job_id, parent_id),
                )
                inserted += result.rowcount
            return inserted

    def prerequisites(self, job_id: str) -> list[str]:
        with closing(self.queue._connect()) as db, db:
            return [
                row[0] for row in db.execute(
                    "SELECT depends_on_job_id FROM job_dependencies "
                    "WHERE job_id=? ORDER BY depends_on_job_id",
                    (job_id,),
                ).fetchall()
            ]

    def dependency_status(self, job_id: str) -> dict:
        """Return no raw payload; only dependency IDs and durable status."""
        with closing(self.queue._connect()) as db, db:
            rows = db.execute(
                """
                SELECT d.depends_on_job_id,p.state FROM job_dependencies d
                LEFT JOIN development_jobs p ON p.id=d.depends_on_job_id
                WHERE d.job_id=? ORDER BY p.id
                """,
                (job_id,),
            ).fetchall()
            return {
                "job_id": job_id,
                "prerequisites": [
                    {"id": parent_id, "status": state or "MISSING"} for parent_id, state in rows
                ],
                "ready": all(state == "SUCCEEDED" for _, state in rows),
                "blocked": any(state in ("BLOCKED", None) for _, state in rows),
            }
