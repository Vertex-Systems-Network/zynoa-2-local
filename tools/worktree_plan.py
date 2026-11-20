"""P00 trusted-host Git worktree plan builder (NO execution in this module).

Plans one detached, no-checkout, fixed-commit worktree in a dedicated root.
Git worktrees are NOT security sandboxes: untrusted repository config, hooks,
filters, executables and dependencies still require OS-level isolation.
"""
from __future__ import annotations

import re
from dataclasses import dataclass
from pathlib import Path
from typing import Mapping

from tools.workspace_policy import WorkspaceDenied, _has_symlink_component, _inside

_SHA = re.compile(r"^[a-f0-9]{40}$")
_JOB = re.compile(r"^[a-z0-9][a-z0-9-]{0,55}$")


class WorktreePlanDenied(ValueError):
    pass


@dataclass(frozen=True)
class WorktreePlan:
    job_id: str
    phase: str
    branch: str
    commit_sha: str
    target: Path
    argv: tuple[str, ...]
    shell: bool = False
    executed: bool = False

    def summary(self) -> dict:
        """Expose no host-specific paths to a model or public issue reporter."""
        return {
            "job_id": self.job_id,
            "phase": self.phase,
            "branch": self.branch,
            "source_commit": self.commit_sha,
            "command_class": "GIT_DETACHED_NO_CHECKOUT",
            "shell": False,
            "executed": False,
            "github_writes": 0,
            "host_sandbox_provided": False,
        }


def plan_detached_worktree(
    trusted_repo: Path, controlled_root: Path, empty_hooks_dir: Path,
    job_id: str, commit_sha: str, state: Mapping
) -> WorktreePlan:
    """Plans only: a trusted OS broker MUST separately authorize execution.

    The inputs must be provisioned by the host controller, not accepted from
    an AI agent. Read-only PR/CI observation alone cannot authorize execution.
    """
    if not isinstance(job_id, str) or not _JOB.fullmatch(job_id):
        raise WorktreePlanDenied("invalid worktree job ID")
    if not isinstance(commit_sha, str) or not _SHA.fullmatch(commit_sha):
        raise WorktreePlanDenied("expected immutable 40-character Git SHA")
    if not isinstance(state, Mapping):
        raise WorktreePlanDenied("missing phase authority")
    phase = state.get("phase")
    branch = state.get("active_branch")
    if phase != "P00" or branch != "phase/00-governance":
        raise WorktreePlanDenied("P00 branch authority required for this slice")
    if state.get("phase_status") != "IN_PROGRESS" or type(state.get("primary_pr")) is not int:
        raise WorktreePlanDenied("active phase and primary PR not verified")
    paths = tuple(Path(x) for x in (trusted_repo, controlled_root, empty_hooks_dir))
    if any(not p.is_dir() or _has_symlink_component(p) for p in paths):
        raise WorktreePlanDenied("root missing or traverses symlink")
    repo, root, hooks = tuple(p.resolve(strict=True) for p in paths)
    if repo == root or _inside(repo, root) or _inside(root, repo):
        raise WorktreePlanDenied("source checkout and job root overlap")
    if hooks == repo or hooks == root or _inside(hooks, repo) or _inside(hooks, root):
        raise WorktreePlanDenied("hooks location must be independent")
    git_dir = repo / ".git"
    if not git_dir.is_dir() or _has_symlink_component(git_dir):
        raise WorktreePlanDenied("not a trusted ordinary Git source checkout")
    if any(hooks.iterdir()):
        raise WorktreePlanDenied("Git hooks directory must be empty")
    target = root / ("p00-" + job_id + "-" + commit_sha[:12])
    if target.exists() or target.is_symlink():
        raise WorktreePlanDenied("target exists; reconcile before retry")
    if _has_symlink_component(target):
        raise WorktreePlanDenied("target traverses symlink")
    # Exact argv only. No shell, no checkout, no user-supplied Git flags, no
    # remote/fetch/push; explicitly suppress repository hooks using an empty
    # host-owned directory. This does not prevent untrusted .git/config from
    # being dangerous: only an already trusted repo may reach this planner.
    command = (
        "git", "-c", "core.hooksPath=" + str(hooks),
        "-C", str(repo), "worktree", "add", "--detach", "--no-checkout",
        "--", str(target), commit_sha,
    )
    return WorktreePlan(
        job_id=job_id, phase=phase, branch=branch, commit_sha=commit_sha,
        target=target, argv=command,
    )
