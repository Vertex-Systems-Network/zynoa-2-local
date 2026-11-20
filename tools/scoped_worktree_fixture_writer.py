"""P00 trusted-host, one-file, no-replace draft write to a DETACHED worktree.

This module actually creates ONE new fixture file. Only a trusted operator,
never a model response, chooses the source repo, job root, immutable commit,
phase task and write grant. All user/checkouts and existing files are untouched.
It requires an already-created detached, --no-checkout Git worktree and Linux
non-root dir_fd/O_NOFOLLOW support. The host MUST isolate its write identity
from untrusted processes. An fd-based path guard is NOT a complete OS sandbox.
"""
from __future__ import annotations

import hashlib
import os
import re
import secrets
import stat
from pathlib import Path

from tools.docker_syntax_broker import DockerSyntaxDenied, plan_python_syntax
from tools.workspace_policy import (
    WorkspaceDenied, WorkspaceScope, _has_symlink_component, _inside,
)

_TASK = "P00-T20"
_SHA = re.compile(r"^[a-f0-9]{40}$")
_HASH = re.compile(r"^[a-f0-9]{64}$")
_NAME = re.compile(r"^tests/fixtures/[A-Za-z0-9][A-Za-z0-9_.-]{0,71}\.py$")
_TARGET = re.compile(r"^p00-[a-z0-9][a-z0-9-]{0,55}-[a-f0-9]{12}$")


class ScopedFixtureWriteDenied(ValueError):
    """Failure is sanitized: never emit source contents or private paths."""


def _linux_preflight() -> None:
    if (
        os.name != "posix" or not hasattr(os, "geteuid")
        or not hasattr(os, "O_DIRECTORY") or not hasattr(os, "O_NOFOLLOW")
        or not hasattr(os, "O_CLOEXEC")
        or not {os.open, os.stat, os.link, os.unlink}.issubset(os.supports_dir_fd)
    ):
        raise ScopedFixtureWriteDenied("fd-scoped fixture writer is Linux-only")
    # Nonroot kernel identity mandatory. A CI test fixture exercises the
    # nonroot path; neither GitHub Actions nor this module install a host.
    if os.geteuid() == 0:
        raise ScopedFixtureWriteDenied("root identity forbidden for model fixture writes")


def _directory(path: Path, *, expected_uid: int) -> int:
    """Open a real owned directory with no symlink traversal at final step."""
    fd = os.open(path, os.O_RDONLY | os.O_DIRECTORY | os.O_NOFOLLOW | os.O_CLOEXEC)
    try:
        meta = os.fstat(fd)
        if not stat.S_ISDIR(meta.st_mode) or meta.st_uid != expected_uid:
            raise ScopedFixtureWriteDenied("unowned job directory")
        if meta.st_mode & 0o022:
            raise ScopedFixtureWriteDenied("group/world-writable job directory")
        return fd
    except BaseException:
        os.close(fd)
        raise


def _subdir(parentfd: int, name: str, uid: int) -> int:
    fd = os.open(name, os.O_RDONLY | os.O_DIRECTORY | os.O_NOFOLLOW |
                 os.O_CLOEXEC, dir_fd=parentfd)
    try:
        meta = os.fstat(fd)
        if not stat.S_ISDIR(meta.st_mode) or meta.st_uid != uid or meta.st_mode & 0o022:
            raise ScopedFixtureWriteDenied("unowned or writable fixture parent")
        return fd
    except BaseException:
        os.close(fd)
        raise


def _validate_detached(
    scope: WorkspaceScope, source_repo: Path, controlled_root: Path,
    expected_commit_sha: str,
) -> Path:
    """Require immutable detached HEAD at source repo's linked worktree gitdir.

    This validates existing checkout metadata as a *host-controlled precondition*.
    It does not execute Git commands, read repository source or fetch remote.
    """
    if not isinstance(expected_commit_sha, str) or not _SHA.fullmatch(expected_commit_sha):
        raise ScopedFixtureWriteDenied("expected commit identity invalid")
    paths = [Path(scope.root), Path(source_repo), Path(controlled_root)]
    if any(not x.is_dir() or _has_symlink_component(x) for x in paths):
        raise ScopedFixtureWriteDenied("host-owned worktree directory invalid")
    worktree, repo, root = [x.resolve(strict=True) for x in paths]
    if (
        worktree.parent != root or not _TARGET.fullmatch(worktree.name)
        or repo == root or _inside(repo, root) or _inside(root, repo)
        or _inside(repo, worktree) or _inside(worktree, repo)
    ):
        raise ScopedFixtureWriteDenied("worktree is not an independent job target")
    if not (repo / ".git").is_dir() or _has_symlink_component(repo / ".git"):
        raise ScopedFixtureWriteDenied("trusted checkout gitdir missing")
    pointer = worktree / ".git"
    if not pointer.is_file() or _has_symlink_component(pointer):
        raise ScopedFixtureWriteDenied("detached Git worktree pointer required")
    if pointer.stat().st_size > 2048:
        raise ScopedFixtureWriteDenied("worktree Git pointer oversize")
    value = pointer.read_text(encoding="utf-8")
    if not value.startswith("gitdir: ") or len(value) > 2048:
        raise ScopedFixtureWriteDenied("worktree Git pointer invalid")
    target_path = Path(value[8:].strip())
    if not target_path.is_absolute() or _has_symlink_component(target_path):
        raise ScopedFixtureWriteDenied("worktree Git target not trusted")
    target = target_path.resolve(strict=True)
    if target.parent != repo / ".git" / "worktrees" or not target.is_dir():
        raise ScopedFixtureWriteDenied("worktree Git target does not match source")
    head = target / "HEAD"
    if not head.is_file() or _has_symlink_component(head) or head.stat().st_size > 128:
        raise ScopedFixtureWriteDenied("worktree HEAD cannot be attested")
    if head.read_text(encoding="ascii").strip() != expected_commit_sha:
        raise ScopedFixtureWriteDenied("detached HEAD differs from trusted source SHA")
    return worktree


def apply_one_disposable_fixture(
    plan: dict, candidate: str, scope: WorkspaceScope, *,
    expected_task_id: str,
    expected_candidate_sha256: str,
    expected_commit_sha: str,
    trusted_source_repo: Path,
    controlled_root: Path,
    enabled: bool = False,
    operator_ack: bool = False,
    write_grant: bool = False,
) -> dict:
    """Write only a NEW file inside an already-constructed isolated worktree.

    This does not call Ollama/Docker/GitHub and does not run generated Python.
    A separately trusted host must approve the candidate after isolation
    testing, and this module MUST NOT be exposed to an untrusted model/tool.
    """
    if enabled is not True or operator_ack is not True or write_grant is not True:
        raise ScopedFixtureWriteDenied("disposable source write disabled by default")
    if expected_task_id != _TASK or not isinstance(expected_candidate_sha256, str) or not (
        _HASH.fullmatch(expected_candidate_sha256)
    ):
        raise ScopedFixtureWriteDenied("trusted task/source identity missing")
    _linux_preflight()
    try:
        job = plan_python_syntax(
            plan, candidate, scope, expected_task_id=expected_task_id
        )
        if job.candidate_sha256 != expected_candidate_sha256:
            raise ScopedFixtureWriteDenied("candidate differs from trusted authorization")
        path = plan["file_proposals"][0]["path"]
        if not isinstance(path, str) or not _NAME.fullmatch(path):
            raise ScopedFixtureWriteDenied("only flat fixture Python files can be created")
        scope.check(path, "write")
        worktree = _validate_detached(
            scope, trusted_source_repo, controlled_root, expected_commit_sha
        )
    except (DockerSyntaxDenied, WorkspaceDenied, OSError, UnicodeError, ValueError,
            KeyError, IndexError, TypeError):
        raise ScopedFixtureWriteDenied("fixture write policy or detached identity denied") from None

    fdroot = fdtests = fdfixtures = -1
    temporary = None
    linked = False
    dest = path.split("/")[-1]
    uid = os.geteuid()
    try:
        fdroot = _directory(worktree, expected_uid=uid)
        fdtests = _subdir(fdroot, "tests", uid)
        fdfixtures = _subdir(fdtests, "fixtures", uid)
        temporary = ".zynoa-" + secrets.token_hex(16) + ".tmp"
        flags = os.O_WRONLY | os.O_CREAT | os.O_EXCL | os.O_NOFOLLOW | os.O_CLOEXEC
        fd = os.open(temporary, flags, 0o600, dir_fd=fdfixtures)
        try:
            start = os.fstat(fd)
            if not stat.S_ISREG(start.st_mode) or start.st_uid != uid or start.st_nlink != 1:
                raise ScopedFixtureWriteDenied("untrusted temporary draft inode")
            data = job.data
            offset = 0
            while offset < len(data):
                written = os.write(fd, data[offset:])
                if written <= 0:
                    raise ScopedFixtureWriteDenied("disposable source write incomplete")
                offset += written
            os.fsync(fd)
            after = os.fstat(fd)
            if (after.st_size != len(data) or after.st_dev != start.st_dev or
                    after.st_ino != start.st_ino):
                raise ScopedFixtureWriteDenied("disposable draft inode changed")
        finally:
            os.close(fd)

        # Atomic no-overwrite publication: hardlink fails if dest already
        # exists, even if it is a symlink. Never rename-overwrite an old file.
        os.link(temporary, dest, src_dir_fd=fdfixtures,
                dst_dir_fd=fdfixtures, follow_symlinks=False)
        linked = True
        os.fsync(fdfixtures)
        verifyfd = os.open(
            dest, os.O_RDONLY | os.O_NOFOLLOW | os.O_CLOEXEC,
            dir_fd=fdfixtures,
        )
        try:
            meta = os.fstat(verifyfd)
            if (not stat.S_ISREG(meta.st_mode) or meta.st_dev != start.st_dev
                    or meta.st_ino != start.st_ino or meta.st_size != len(data)):
                raise ScopedFixtureWriteDenied("published fixture identity changed")
            if hashlib.sha256(os.read(verifyfd, len(data) + 1)).hexdigest() != job.candidate_sha256:
                raise ScopedFixtureWriteDenied("published fixture digest mismatch")
        finally:
            os.close(verifyfd)
        os.unlink(temporary, dir_fd=fdfixtures)
        temporary = None
        os.fsync(fdfixtures)
        return {
            "status": "DISPOSABLE_WORKTREE_FIXTURE_CREATED",
            "phase": "P00", "task_id": _TASK,
            "source_commit_sha": expected_commit_sha,
            "path": path, "candidate_sha256": job.candidate_sha256,
            "bytes_written": len(job.data),
            "disposable_worktree_files_written": 1,
            "trusted_checkout_files_written": 0,
            "github_writes": 0,
            "model_source_executed": False,
            "os_sandbox_attested": False,
            "persistent_worker_deployed": False,
            "production_source_patch_verified": False,
        }
    except (OSError, ValueError, TypeError):
        # If publication had begun, do NOT claim an atomic rollback here:
        # the caller must inspect/reconcile the trusted worktree before retry.
        # Never remove an existing destination, even on a failed write.
        raise ScopedFixtureWriteDenied(
            "disposable fixture write refused; reconcile target before retry"
        ) from None
    finally:
        if temporary is not None and fdfixtures >= 0:
            try:
                os.unlink(temporary, dir_fd=fdfixtures)
            except FileNotFoundError:
                pass
            except OSError:
                # Caller must reconcile; never delete a destination we did not
                # create and never report a positive result after failure.
                pass
        for filefd in (fdfixtures, fdtests, fdroot):
            if filefd >= 0:
                os.close(filefd)
