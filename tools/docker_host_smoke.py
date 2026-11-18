"""P00 operator-only live rootless Docker syntax smoke (NOT host attestation).

No AI model input, GitHub write, worktree mutation or arbitrary command.
This can be run by an operator on their separately provisioned Linux host.
GitHub CI only tests its contract with a stub; it cannot qualify the host.
"""
from __future__ import annotations

import argparse
import hashlib
import json
import os
from pathlib import Path
from typing import Callable

from tools.docker_syntax_broker import (
    DEFAULT_IMAGE, DockerSyntaxDenied, run_python_syntax,
)
from tools.workspace_policy import WorkspaceDenied, WorkspaceScope, _has_symlink_component

_TASK = "P00-T20"
_FILE = "tests/fixtures/zynoa-host-smoke.py"
_CASES = (
    ("valid", "answer = 1\n", "PYTHON_SYNTAX_VALID_NO_CODE_EXECUTION"),
    ("invalid", "def broken(\n", "PYTHON_SYNTAX_INVALID_NO_CODE_EXECUTION"),
)
_MAX_PHASE_BYTES = 4096


class HostSmokeDenied(ValueError):
    """An incomplete/unsafe host probe has no acceptance authority."""


def _linux_nonroot() -> bool:
    return os.name == "posix" and hasattr(os, "geteuid") and os.geteuid() != 0


def _trusted_scope(repo_root: Path) -> WorkspaceScope:
    """Validate local context; DOES NOT authenticate current GitHub remote."""
    root = Path(repo_root)
    if not root.is_dir() or _has_symlink_component(root):
        raise HostSmokeDenied("trusted P00 checkout missing or linked")
    if not (root / "AGENTS.md").is_file() or _has_symlink_component(root / "AGENTS.md"):
        raise HostSmokeDenied("AGENTS.md missing or linked")
    phase = root / "docs/state/PHASE.json"
    if not phase.is_file() or _has_symlink_component(phase):
        raise HostSmokeDenied("trusted phase state missing or linked")
    try:
        with phase.open("rb") as stream:
            data = stream.read(_MAX_PHASE_BYTES + 1)
        if len(data) > _MAX_PHASE_BYTES:
            raise HostSmokeDenied("phase document exceeds limit")
        state = json.loads(data)
    except (OSError, UnicodeError, ValueError, TypeError):
        raise HostSmokeDenied("phase document cannot be validated") from None
    if not isinstance(state, dict) or (
        state.get("phase") != "P00" or
        state.get("phase_status") != "IN_PROGRESS" or
        state.get("active_branch") != "phase/00-governance" or
        type(state.get("primary_pr")) is not int or state["primary_pr"] != 1 or
        type(state.get("worker_running")) is not bool
    ):
        raise HostSmokeDenied("checkout does not have expected unfinished P00 state")
    try:
        return WorkspaceScope(
            root=root, phase="P00", branch="phase/00-governance",
            writable_prefixes=("tests/fixtures",),
        )
    except (WorkspaceDenied, OSError, ValueError):
        raise HostSmokeDenied("trusted workspace scope unavailable") from None


def _plan() -> dict:
    return {
        "schema_version": 1, "phase": "P00", "branch": "phase/00-governance",
        "task_id": _TASK, "summary": "Trusted operator rootless syntax smoke",
        "file_proposals": [{
            "path": _FILE, "action": "DRAFT_ONLY",
            "reason": "Fixed harmless host-owned syntax fixture",
        }],
        "checks": ["phase-policy"],
    }


def _check_receipt(receipt: object, source: str, expected: str) -> None:
    """Never accept a malformed/partial/forged Docker adapter receipt."""
    if not isinstance(receipt, dict) or (
        receipt.get("status") != expected or
        receipt.get("phase") != "P00" or
        receipt.get("task_id") != _TASK or
        receipt.get("image_digest") != DEFAULT_IMAGE.split("@", 1)[1] or
        receipt.get("candidate_sha256") != hashlib.sha256(source.encode("utf-8")).hexdigest() or
        receipt.get("rootless_daemon_status_observed") is not True or
        receipt.get("model_source_executed") is not False or
        type(receipt.get("workspace_files_written")) is not int or
        receipt["workspace_files_written"] != 0 or
        type(receipt.get("github_writes")) is not int or
        receipt["github_writes"] != 0 or
        receipt.get("independent_host_sandbox_verified") is not False or
        receipt.get("persistent_worker_deployed") is not False
    ):
        raise HostSmokeDenied("Docker syntax smoke receipt invalid or unverified")


def run_host_syntax_smoke(
    repo_root: Path, *, enabled: bool = False, operator_ack: bool = False,
    docker_binary: str = "/usr/bin/docker",
    socket_url: str | None = None,
    runner: Callable | None = None,
) -> dict:
    """Run fixed valid+invalid fixture in two isolated rootless containers.

    Requires BOTH explicit operator flags, non-root POSIX identity, a trusted
    P00 checkout and the underlying default-disabled Docker security gate.
    The result does not prove hostile-code confinement, delegation or restart.
    """
    if enabled is not True or operator_ack is not True:
        raise HostSmokeDenied("two explicit operator authorizations required")
    if not _linux_nonroot():
        raise HostSmokeDenied("dedicated non-root Linux host required")
    scope = _trusted_scope(repo_root)
    plan = _plan()
    for _, source, expected in _CASES:
        opts = {
            "expected_task_id": _TASK, "enabled": True,
            "docker_binary": docker_binary, "socket_url": socket_url,
        }
        if runner is not None:
            opts["runner"] = runner
        try:
            receipt = run_python_syntax(plan, source, scope, **opts)
        except (DockerSyntaxDenied, WorkspaceDenied, OSError, ValueError):
            raise HostSmokeDenied("rootless Docker smoke unavailable or refused") from None
        _check_receipt(receipt, source, expected)
    return {
        "status": "ROOTLESS_SYNTAX_SMOKE_ONLY",
        "phase": "P00", "primary_pr": 1,
        "cases": ["valid", "invalid"], "case_count": len(_CASES),
        "image_digest": DEFAULT_IMAGE.split("@", 1)[1],
        "model_source_executed": False,
        "github_writes": 0, "workspace_files_written": 0,
        "independent_host_sandbox_verified": False,
        "remote_git_branch_verified": False,
        "persistent_worker_deployed": False,
        "next_phase_started": False,
    }


def main() -> int:
    parser = argparse.ArgumentParser(
        description="P00 operator-only Docker syntax smoke; never proves full sandbox isolation"
    )
    parser.add_argument("--repo-root", type=Path, required=True)
    parser.add_argument("--enable-live-smoke", action="store_true")
    parser.add_argument("--acknowledge-operator-owned-rootless-host", action="store_true")
    parser.add_argument("--docker-binary", default="/usr/bin/docker")
    args = parser.parse_args()
    try:
        result = run_host_syntax_smoke(
            args.repo_root, enabled=args.enable_live_smoke,
            operator_ack=args.acknowledge_operator_owned_rootless_host,
            docker_binary=args.docker_binary,
            socket_url=("unix:///run/user/" + str(os.geteuid()) + "/docker.sock")
            if _linux_nonroot() else None,
        )
        print(json.dumps(result, sort_keys=True))
        return 0
    except (HostSmokeDenied, OSError, ValueError):
        print(json.dumps({
            "status": "BLOCKED", "error_class": "HostSmokeDenied",
            "credentials_echoed": False, "host_sandbox_verified": False,
            "model_code_executed": False, "github_writes": 0,
        }, sort_keys=True))
        return 2


if __name__ == "__main__":
    raise SystemExit(main())
