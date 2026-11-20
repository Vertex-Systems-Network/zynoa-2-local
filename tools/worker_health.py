#!/usr/bin/env python3
"""Read-only P00 on-host observer heartbeat inspection (not deployment attestation).

A fresh SQLite lease is not proof of successful GitHub observations. Compare
the active owner/lease with the separately updated last-success timestamp.
The caller still needs independent systemd/process and remote API evidence.
No DB creation, token access, GitHub calls or user files are written here.
"""
from __future__ import annotations

import argparse
from contextlib import closing
import json
import re
import sqlite3
import time
from pathlib import Path
from typing import Callable

from tools.host_bootstrap import HostBootstrapError, HostLayout

_SHA = re.compile(r"^[a-f0-9]{40}$")


class WorkerHealthDenied(ValueError):
    """The local read-only observer evidence is absent or inconsistent."""


def probe_local_observer(
    repo_root: Path, host_root: Path, *,
    clock: Callable[[], float] = time.time,
    max_age_seconds: int = 120,
) -> dict:
    """Read known P00 SQLite schema and require owner-matched recent success.

    Recent local database entries are only a hint of activity. They cannot
    attest a systemd process, remote GitHub authentication or 24/7 service.
    """
    if type(max_age_seconds) is not int or not 1 <= max_age_seconds <= 300:
        raise WorkerHealthDenied("invalid heartbeat freshness limit")
    layout = HostLayout(repo_root, host_root)
    layout.verify()
    now = float(clock())
    try:
        with closing(sqlite3.connect(layout.db.as_uri() + "?mode=ro", uri=True, timeout=4)) as db:
            lease = db.execute(
                "SELECT owner, expires_at FROM worker_leases WHERE name=?",
                ("active-phase",),
            ).fetchone()
            proof = db.execute(
                "SELECT owner, observed_at, head_sha, main_sha "
                "FROM worker_observation_health WHERE name=?",
                ("active-phase",),
            ).fetchone()
    except sqlite3.Error:
        raise WorkerHealthDenied("worker heartbeat records unavailable") from None

    valid_lease = bool(
        lease and isinstance(lease[0], str) and lease[0]
        and isinstance(lease[1], (float, int))
        and now < lease[1] <= now + 180.0
    )
    valid_proof = bool(
        valid_lease and proof and proof[0] == lease[0]
        and isinstance(proof[1], (float, int))
        and 0 <= now - proof[1] <= max_age_seconds
        and proof[1] <= lease[1]
        and all(isinstance(s, str) and _SHA.fullmatch(s) for s in proof[2:4])
    )
    return {
        "status": "RECENT_LOCAL_OBSERVER_EVIDENCE" if valid_proof else "OBSERVER_NOT_FRESHLY_VERIFIED",
        "phase": "P00",
        "lease_current": valid_lease,
        "last_successful_remote_observation_recent": valid_proof,
        "local_storage_integrity_checked": True,
        "github_remote_rechecked": False,
        "systemd_service_verified": False,
        "persistent_worker_deployment_verified": False,
        "model_coding_verified": False,
        "os_sandbox_verified": False,
        "github_writes": 0,
        "next_phase_started": False,
    }


def main() -> int:
    parser = argparse.ArgumentParser(description="P00 local observer proof; read only")
    parser.add_argument("--repo-root", required=True, type=Path)
    parser.add_argument("--host-root", required=True, type=Path)
    parser.add_argument("--max-age-seconds", type=int, default=120)
    args = parser.parse_args()
    try:
        result = probe_local_observer(
            args.repo_root, args.host_root, max_age_seconds=args.max_age_seconds,
        )
        print(json.dumps(result, sort_keys=True))
        return 0 if result["last_successful_remote_observation_recent"] else 2
    except (WorkerHealthDenied, HostBootstrapError, OSError, ValueError, TypeError):
        print(json.dumps({
            "status": "BLOCKED",
            "credentials_echoed": False,
            "systemd_service_verified": False,
            "persistent_worker_deployment_verified": False,
            "github_writes": 0,
        }, sort_keys=True))
        return 2


if __name__ == "__main__":
    raise SystemExit(main())
