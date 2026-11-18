"""P00 workspace capability policy: validation only, no file mutation.

The policy is created by a trusted host controller, NEVER from model text.
It is NOT an OS sandbox; untrusted code still needs separate process, mount,
network and credential isolation before any execution.
"""
from __future__ import annotations

import ntpath
import re
import unicodedata
from dataclasses import dataclass
from pathlib import Path
from typing import Literal

from tools.phase_controller import PHASE_ORDER

Operation = Literal["read", "write"]

# Never permit the model-facing code worker to rewrite its own guardrails.
_ALWAYS_PROTECTED = (
    ".git", ".github", ".env", ".ssh", ".aws", ".npmrc", ".pypirc",
    ".venv", "venv", "node_modules", "__pycache__", ".secrets",
    ".gitattributes", ".gitmodules", ".gitconfig",
)
_PROTECTED_PATHS = (
    "AGENTS.md", "docs/state", "docs/quality", "docs/adr",
    "deploy/github", "tools/workspace_policy.py", "tools/worktree_plan.py",
    "tools/github_gateway.py", "tools/phase_merge_guard.py",
    "tools/phase_controller.py", "tools/dev_job_queue.py",
    "tools/dev_task_graph.py", "tools/phase_worker.py",
    "tools/github_issue_bridge.py",
)
_WINDOWS_RESERVED = frozenset({
    "con", "prn", "aux", "nul", *(f"com{i}" for i in range(1, 10)),
    *(f"lpt{i}" for i in range(1, 10)),
})
_RELATIVE = re.compile(r"^[^\\\x00\r\n:]+$")
_ALLOWED_DEFAULT_WRITES = (
    "docs/help", "docs/wiki", "docs/research", "tests/fixtures",
)


class WorkspaceDenied(ValueError):
    """Path or operation escapes the operator-managed capability envelope."""


def _inside(path: Path, root: Path) -> bool:
    try:
        path.relative_to(root)
        return True
    except ValueError:
        return False


def _has_symlink_component(path: Path) -> bool:
    """Lexically walk existing components to catch links before resolve()."""
    current = path
    while current != current.parent:
        if current.is_symlink() or (hasattr(current, 'is_junction') and current.is_junction()):
            return True
        current = current.parent
    return current.is_symlink()


def _relative_parts(raw: str) -> tuple[str, ...]:
    if not isinstance(raw, str) or not raw or len(raw) > 4096:
        raise WorkspaceDenied("path missing or too long")
    if (not _RELATIVE.fullmatch(raw) or unicodedata.normalize("NFC", raw) != raw
            or any(unicodedata.category(ch) in ("Cc", "Cf", "Cs") for ch in raw)):
        raise WorkspaceDenied("path contains unsafe separators or control characters")
    if raw.startswith("/") or ntpath.isabs(raw) or ntpath.splitdrive(raw)[0]:
        raise WorkspaceDenied("absolute or drive-relative path forbidden")
    parts = tuple(raw.split("/"))
    if len(parts) > 64:
        raise WorkspaceDenied("path too deep")
    if any(
        not part or part in (".", "..") or part.rstrip(" .") != part
        or part.split(".")[0].casefold() in _WINDOWS_RESERVED
        or part.casefold() in _ALWAYS_PROTECTED
        or part.casefold().startswith((".env.", ".ssh.", ".aws."))
        for part in parts
    ):
        raise WorkspaceDenied("unsafe or reserved path component")
    return parts


def _path_is(path: str, prefix: str) -> bool:
    return path == prefix or path.startswith(prefix + "/")


@dataclass(frozen=True)
class WorkspaceScope:
    """Host-provisioned file-scoping proof for an existing isolated worktree.

    Construct only on the trusted side of a process boundary. A language model
    must never choose the root, change the write prefixes or grant itself
    permission. A checked path alone is not a safe open (TOCTOU remains).
    """

    root: Path
    phase: str
    branch: str
    writable_prefixes: tuple[str, ...] = _ALLOWED_DEFAULT_WRITES

    def __post_init__(self):
        root = Path(self.root)
        if not root.is_dir() or _has_symlink_component(root):
            raise WorkspaceDenied("worktree root missing or traverses symlinks")
        if self.phase not in PHASE_ORDER or self.phase != "P00" or self.branch != "phase/00-governance":
            raise WorkspaceDenied("phase/branch not constrained")
        normalized = []
        for prefix in self.writable_prefixes:
            if not isinstance(prefix, str):
                raise WorkspaceDenied("write scope must be a literal path prefix")
            parts = _relative_parts(prefix)
            text = "/".join(parts)
            if any(_path_is(text, p) or _path_is(p, text) for p in _PROTECTED_PATHS):
                raise WorkspaceDenied("write scope overlaps protected governance path")
            if any(part.casefold() in _ALWAYS_PROTECTED for part in parts):
                raise WorkspaceDenied("write scope includes privileged directory")
            normalized.append(text)
        object.__setattr__(self, "root", root.resolve(strict=True))
        object.__setattr__(self, "writable_prefixes", tuple(normalized))

    def check(self, relative_path: str, operation: Operation = "read") -> Path:
        if operation not in ("read", "write"):
            raise WorkspaceDenied("unapproved file operation")
        parts = _relative_parts(relative_path)
        logical = "/".join(parts)
        if any(_path_is(logical.casefold(), blocked.casefold())
               for blocked in _PROTECTED_PATHS):
            raise WorkspaceDenied("file is security/phase-governance protected")
        if operation == "write" and not any(
            logical == prefix or logical.startswith(prefix + "/")
            for prefix in self.writable_prefixes
        ):
            raise WorkspaceDenied("path outside approved write prefixes")
        lexical = self.root.joinpath(*parts)
        if _has_symlink_component(lexical):
            raise WorkspaceDenied("symlinks and junction-like paths are not permitted")
        resolved = lexical.resolve(strict=False)
        if not _inside(resolved, self.root):
            raise WorkspaceDenied("resolved path exits worktree")
        if operation == "read" and not resolved.is_file():
            raise WorkspaceDenied("read target missing or not a regular file")
        if operation == "write" and resolved.exists() and not resolved.is_file():
            raise WorkspaceDenied("writing non-file target forbidden")
        return resolved

    def evaluate(self, relative_path: str, operation: Operation = "read") -> dict:
        """Sanitized decision: no resolved absolute host paths in the output."""
        try:
            self.check(relative_path, operation)
            return {"allowed": True, "operation": operation, "reason": "APPROVED_SCOPE"}
        except WorkspaceDenied:
            return {"allowed": False, "operation": operation, "reason": "WORKSPACE_SCOPE_DENIED"}
