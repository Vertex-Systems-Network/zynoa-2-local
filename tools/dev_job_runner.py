"""P00 allowlisted development-job runner (no shell, network, AI or Git writes).

The queue has a future-compatible interface but P00 only executes deterministic,
read-only governance checks. Model-authored code and terminal execution belong
to a later independently authorized sandboxed executor.
"""
from __future__ import annotations

import argparse
import json
import sys
import uuid
from pathlib import Path

from tools.dev_job_queue import JobQueue, QueuePolicyError, ClaimedJob
from tools.phase_controller import validate_snapshot
from scripts.check_design_interop_policy import validate as validate_design_spec

class JobCheckFailed(RuntimeError):
    pass


def run_safe_check(kind: str, state: dict, root: Path) -> dict:
    if kind == "phase-policy":
        errors = validate_snapshot(state)
        if errors:
            raise JobCheckFailed("phase policy failed")
    elif kind == "design-spec":
        errors = validate_design_spec(root)
        if errors:
            raise JobCheckFailed("design contract failed")
    elif kind == "docs-integrity":
        mandatory = [
            "AGENTS.md", "docs/MASTER_PLAN_V3_2.md",
            "docs/state/PHASE.json", "docs/state/STATUS.md",
            "docs/state/HANDOFF.md", "docs/operations/P00_WORKER_RUNBOOK.md",
            "docs/operations/DESIGN_INTEROPERABILITY.md",
            "docs/PLANNING_CHANGELOG.md",
        ]
        if any(not (root / p).is_file() for p in mandatory):
            raise JobCheckFailed("required documentation missing")
    else:
        raise QueuePolicyError("check not in fixed allowlist")
    return {"check": kind, "passed": True}


def run_one(queue: JobQueue, state: dict, root: Path, owner: str) -> dict | None:
    errors = validate_snapshot(state)
    if errors or state.get("phase_status") != "IN_PROGRESS":
        raise QueuePolicyError("active phase not valid for running jobs")
    job = queue.claim(state["phase"], state["active_branch"], owner)
    if job is None:
        return None
    try:
        result = run_safe_check(job.kind, state, root)
        queue.complete(job, owner, result)
        return {"id": job.id, "attempt": job.attempt, "status": "SUCCEEDED"}
    except (JobCheckFailed, QueuePolicyError, OSError, ValueError):
        queue.fail(job, owner, "CheckFailed")
        return {"id": job.id, "attempt": job.attempt, "status": queue.inspect(job.id)["state"]}


def main() -> int:
    parser = argparse.ArgumentParser(description="Zynoa allowlisted read-only job queue smoke")
    parser.add_argument("--state", type=Path, default=Path("docs/state/PHASE.json"))
    parser.add_argument("--repo-root", type=Path, default=Path("."))
    parser.add_argument("--db", type=Path, required=True)
    parser.add_argument("--smoke", action="store_true",
                        help="queue three deterministic checks; no network or mutation")
    args = parser.parse_args()
    root = args.repo_root.resolve()
    try:
        state = json.loads(args.state.read_text(encoding="utf-8"))
        if validate_snapshot(state) or state.get("phase_status") != "IN_PROGRESS":
            raise QueuePolicyError("invalid active phase state")
        queue = JobQueue(args.db)
        if args.smoke:
            for kind in ("phase-policy", "design-spec", "docs-integrity"):
                queue.enqueue(
                    "p00-" + kind, state["phase"], state["active_branch"], kind, max_attempts=2
                )
        owner = "ci-" + uuid.uuid4().hex
        results = []
        for _ in range(10):
            result = run_one(queue, state, root, owner)
            if result is None:
                break
            results.append(result)
        summary = {
            "phase": state["phase"], "branch": state["active_branch"],
            "results": results, "queue": queue.stats(),
            "commands_executed": 0, "github_writes": 0,
            "model_tasks_executed": 0, "worker_deployed": False,
        }
        print(json.dumps(summary, sort_keys=True, indent=2))
        if args.smoke and (
            len(results) != 3 or any(x["status"] != "SUCCEEDED" for x in results)
        ):
            return 1
        return 0
    except (QueuePolicyError, OSError, ValueError, json.JSONDecodeError) as exc:
        print(json.dumps({"status": "BLOCKED", "error_class": type(exc).__name__,
                          "commands_executed": 0, "github_writes": 0}))
        return 2


if __name__ == "__main__":
    raise SystemExit(main())
