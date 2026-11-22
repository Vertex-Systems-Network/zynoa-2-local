#!/usr/bin/env python3
"""Phase governance primitives for a future persistent development worker.

This module does not deploy a daemon, call GitHub, merge PRs, or verify CI.
Only authenticated caller-provided remote evidence may authorize transitions.
"""
from __future__ import annotations

import argparse
from contextlib import closing
import json
import re
import sqlite3
from pathlib import Path
from typing import Any, Mapping

PHASE_ORDER = (
    "P00", "P01", "P02", "P03", "P04", "P05", "P06",
    "P07", "P08", "P08I", "P09", "P10", "P11", "P12",
)

class PhasePolicyError(ValueError):
    """A proposed phase transition violates the verified governance contract."""


def validate_snapshot(state: Mapping[str, Any]) -> list[str]:
    problems: list[str] = []
    phase = state.get("phase")
    if phase not in PHASE_ORDER:
        problems.append("unknown phase")
    branch = state.get("active_branch")
    if branch is not None and not isinstance(branch, str):
        problems.append("active_branch must be a string or null")
    elif branch is not None:
        if not branch.startswith("phase/"):
            problems.append("active branch must be phase/*")
        if phase == "P08I" and branch != "phase/08i-design-interoperability":
            problems.append("P08I requires the dedicated phase branch")
        elif phase in PHASE_ORDER and phase != "P08I" and not branch.startswith(
            f"phase/{phase[1:].lower()}-"
        ):
            problems.append("active branch does not match active phase")
    pr = state.get("primary_pr")
    if pr is not None and (type(pr) is not int or pr < 1):
        problems.append("primary_pr must be a positive GitHub PR number")
    if pr is not None and not branch:
        problems.append("primary PR requires an active branch")
    if state.get("phase_status") == "MERGED_VERIFIED" and not state.get("last_verified_remote_sha"):
        problems.append("verified merge requires actual remote SHA")
    if state.get("worker_running") is True and not state.get("worker_id"):
        problems.append("worker_running requires actual worker identifier")
    return problems


def next_phase(phase: str) -> str | None:
    if phase not in PHASE_ORDER:
        raise PhasePolicyError("Unknown phase: " + phase)
    i = PHASE_ORDER.index(phase)
    return PHASE_ORDER[i + 1] if i + 1 < len(PHASE_ORDER) else None


def authorize_next_phase(
    state: Mapping[str, Any], target: str, evidence: Mapping[str, Any]
) -> bool:
    """Validate normalized evidence from a trusted authenticated GitHub reader.

    This function is NOT a GitHub verifier: a calling controller must obtain
    the evidence from GitHub with least-privilege credentials, not from AI text.
    """
    errors = validate_snapshot(state)
    if errors:
        raise PhasePolicyError("; ".join(errors))
    source = state["phase"]
    if target != next_phase(source):
        raise PhasePolicyError("next phase must follow the canonical sequence")
    if state.get("phase_status") != "MERGED_VERIFIED":
        raise PhasePolicyError("current phase is not marked MERGED_VERIFIED")
    if not state.get("active_branch") or not state.get("primary_pr"):
        raise PhasePolicyError("cannot advance without a tracked branch and PR")
    if not evidence.get("authenticated_remote") or not evidence.get("merged") or not evidence.get("checks_passed"):
        raise PhasePolicyError("GitHub merge/check evidence not verified")
    if evidence.get("head_branch") != state["active_branch"]:
        raise PhasePolicyError("GitHub branch mismatch")
    if evidence.get("pr_number") != state["primary_pr"]:
        raise PhasePolicyError("GitHub primary PR mismatch")
    if evidence.get("base_branch") != "main":
        raise PhasePolicyError("phase PR must target main")
    verified = state.get("last_verified_remote_sha")
    if evidence.get("merge_sha") != verified or not re.fullmatch(r"[a-f0-9]{40}", str(verified or "")):
        raise PhasePolicyError("verified remote SHA does not match merge commit")
    if evidence.get("open_critical_blockers", 1) != 0:
        raise PhasePolicyError("critical blockers unresolved")
    if target == "P08I" and source != "P08":
        raise PhasePolicyError("interoperability follows completed P08 only")
    return True


class EventJournal:
    """Idempotent local audit event store; no network calls or sensitive payloads."""

    def __init__(self, db_path: Path):
        self.db_path = Path(db_path)
        self.db_path.parent.mkdir(parents=True, exist_ok=True)
        with closing(self._connect()) as db, db:
            db.execute("PRAGMA journal_mode=WAL")
            db.execute(
                "CREATE TABLE IF NOT EXISTS phase_events ("
                "id TEXT PRIMARY KEY, phase TEXT NOT NULL, event_type TEXT NOT NULL, "
                "metadata TEXT NOT NULL, created_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP)"
            )

    def _connect(self):
        return sqlite3.connect(self.db_path, timeout=15)

    def append(self, event_id: str, phase: str, event_type: str, metadata: Mapping[str, Any] | None = None) -> bool:
        if not event_id or phase not in PHASE_ORDER or not event_type:
            raise PhasePolicyError("event ID, valid phase and event_type required")
        payload = json.dumps(metadata or {}, sort_keys=True)
        with closing(self._connect()) as db, db:
            result = db.execute(
                "INSERT OR IGNORE INTO phase_events (id, phase, event_type, metadata) VALUES (?, ?, ?, ?)",
                (event_id, phase, event_type, payload),
            )
            return result.rowcount == 1

    def count(self) -> int:
        with closing(self._connect()) as db, db:
            return int(db.execute("SELECT COUNT(*) FROM phase_events").fetchone()[0])


def main() -> int:
    parser = argparse.ArgumentParser(description="Validate local phase snapshot (not GitHub merge verification)")
    parser.add_argument("--state", type=Path, default=Path("docs/state/PHASE.json"))
    args = parser.parse_args()
    state = json.loads(args.state.read_text(encoding="utf-8"))
    problems = validate_snapshot(state)
    print(json.dumps({
        "local_snapshot": "PASS" if not problems else "FAIL",
        "phase": state.get("phase"),
        "branch": state.get("active_branch"),
        "primary_pr": state.get("primary_pr"),
        "remote_merge_verified_by_this_command": False,
        "persistent_worker_deployed_by_this_command": False,
        "errors": problems,
    }, indent=2))
    return bool(problems)


if __name__ == "__main__":
    raise SystemExit(main())
