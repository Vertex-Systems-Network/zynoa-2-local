"""P00 rootless Docker Python syntax broker. Explicit host opt-in, no model code execution.

It checks generated Python *syntax only* inside a constrained container. The
candidate cannot choose Docker arguments, image, socket, executable or policy.
This does not attest a production sandbox: operator must separately prove
rootless Docker isolation, image provenance, security patching and recovery.
"""
from __future__ import annotations

import hashlib
import json
import os
import re
import selectors
import secrets
import stat
import subprocess
import tempfile
import time
from dataclasses import dataclass
from pathlib import Path
from typing import Callable

from tools.dev_model_planner import ModelPlanDenied, validate_model_plan
from tools.fixture_draft_stager import FixtureStageDenied, _text_bytes
from tools.workspace_policy import WorkspaceScope, _has_symlink_component

# Indexed, multiarch official Python image digest observed on Docker Hub
# 2026-11-18. Actual host must pre-cache and verify it independently.
DEFAULT_IMAGE = (
    "docker.io/library/python@sha256:"
    "e064671ca452259bab50e8e2c7bd896e39e9a343bb06ca25234adf6fe18d0fc7"
)
_APPROVED_IMAGES = frozenset((DEFAULT_IMAGE,))  # audited, exact image references only
_PY_FILE = re.compile(r"^tests/fixtures/[A-Za-z0-9][A-Za-z0-9_.-]{0,71}\.py$")
_OK = b"ZYNOA_SYNTAX_VALID_NOT_EXECUTED"
_BAD = b"ZYNOA_SYNTAX_INVALID_NOT_EXECUTED"

# Trusted host-defined resource validator. This source is fixed by the repo,
# NEVER model-supplied. The same function body is tested without a Docker host.
# Docker may silently ignore --cpus/--memory/--pids-limit in rootless mode.
_LIMITS_CHECK = (
    "def _limits_enforced(memory, pids, cpu):\n"
    " try:\n"
    "  mem = int(memory)\n"
    "  pid = int(pids)\n"
    "  parts = cpu.split()\n"
    "  if len(parts) != 2: return False\n"
    "  quota, period = map(int, parts)\n"
    " except (ValueError, TypeError, OverflowError):\n"
    "  return False\n"
    " return 0 < mem <= 134217728 and 0 < pid <= 32 and 0 < quota and 0 < period and quota * 2 <= period\n"
)

# Trusted syntax-only compiler: enforce *container-visible* cgroup ceilings,
# root filesystem read-only and loopback-only interface BEFORE model parsing.
# A missing/ignored controller exits without success/invalid marker. No
# model bytecode is ever executed; real OS sandbox proof remains independent.
_COMPILE_CHECK = (
    "import os,socket,sys\n"
    "from pathlib import Path\n"
    + _LIMITS_CHECK +
    "try:\n"
    " root=Path('/sys/fs/cgroup')\n"
    " mem=(root/'memory.max').read_text(encoding='ascii').strip()\n"
    " pids=(root/'pids.max').read_text(encoding='ascii').strip()\n"
    " cpu=(root/'cpu.max').read_text(encoding='ascii').strip()\n"
    " if any(len(item)>64 for item in (mem,pids,cpu)): sys.exit(7)\n"
    " if not _limits_enforced(mem,pids,cpu): sys.exit(7)\n"
    " if {name for _,name in socket.if_nameindex()} != {'lo'}: sys.exit(7)\n"
    " if not (os.statvfs('/').f_flag & os.ST_RDONLY): sys.exit(7)\n"
    "except (OSError, UnicodeError, ValueError):\n"
    " sys.exit(7)\n"
    "source=sys.stdin.buffer.read(8193)\n"
    "if len(source)>8192: sys.exit(3)\n"
    "try:\n"
    " compile(source, '<fixture>', 'exec', dont_inherit=True)\n"
    "except (SyntaxError, UnicodeError, ValueError):\n"
    " print('ZYNOA_SYNTAX_INVALID_NOT_EXECUTED')\n"
    " sys.exit(2)\n"
    "print('ZYNOA_SYNTAX_VALID_NOT_EXECUTED')\n"
)


class DockerSyntaxDenied(ValueError):
    """Sanitized policy/transport failure; never show untrusted stdout/paths."""


@dataclass(frozen=True)
class SyntaxJob:
    task_id: str
    image: str
    candidate_sha256: str
    data: bytes

    def argv(self, *, docker_binary: str, rootless_socket: str, job_name: str) -> tuple[str, ...]:
        return (
            docker_binary, "--host", rootless_socket, "run",
            "--pull", "never", "--rm", "--interactive",
            "--name", job_name,
            "--label", "zynoa.phase=P00",
            "--label", "zynoa.purpose=syntax-only",
            "--network", "none", "--ipc", "none",
            "--read-only", "--cap-drop", "ALL",
            "--security-opt", "no-new-privileges:true",
            "--pids-limit", "32",
            "--memory", "128m", "--memory-swap", "128m",
            "--cpus", "0.5",
            "--user", "65534:65534",
            "--tmpfs", "/tmp:rw,nosuid,nodev,noexec,size=16m",
            "--workdir", "/tmp",
            "--log-driver", "none",
            self.image, "python", "-I", "-S", "-B", "-c", _COMPILE_CHECK,
        )


def plan_python_syntax(
    plan: dict, candidate: str, scope: WorkspaceScope,
    *, expected_task_id: str, image: str = DEFAULT_IMAGE,
) -> SyntaxJob:
    """Policy checks only: no Docker calls, file writes or host code parsing."""
    if not isinstance(plan, dict) or not isinstance(expected_task_id, str):
        raise DockerSyntaxDenied("invalid trusted task context")
    if not isinstance(image, str) or image not in _APPROVED_IMAGES:
        raise DockerSyntaxDenied("Docker image is not in the exact reviewed digest allowlist")
    try:
        verified = validate_model_plan(plan, expected_task_id, scope)
    except (ModelPlanDenied, ValueError, OSError):
        raise DockerSyntaxDenied("model plan rejected by trusted scope") from None
    proposals = verified["file_proposals"]
    if len(proposals) != 1 or not _PY_FILE.fullmatch(proposals[0]["path"]):
        raise DockerSyntaxDenied("only one flat Python test fixture is eligible for syntax check")
    try:
        data = _text_bytes(candidate)
    except FixtureStageDenied:
        raise DockerSyntaxDenied("Python fixture source failed length/text bounds") from None
    return SyntaxJob(
        task_id=expected_task_id, image=image,
        candidate_sha256=hashlib.sha256(data).hexdigest(), data=data,
    )


def _rootless_socket(socket_url: str) -> str:
    """Only current user-owned local rootless Unix Docker socket accepted."""
    if os.name != "posix" or not hasattr(os, "geteuid") or os.geteuid() == 0:
        raise DockerSyntaxDenied("rootless non-root Linux host required")
    base = f"/run/user/{os.geteuid()}/docker.sock"
    if socket_url != "unix://" + base:
        raise DockerSyntaxDenied("Docker socket outside user-owned rootless path")
    path = Path(base)
    if _has_symlink_component(path):
        raise DockerSyntaxDenied("Docker socket link or redirected directory refused")
    try:
        info = path.stat()
    except OSError:
        raise DockerSyntaxDenied("rootless Docker socket is not available") from None
    if not stat.S_ISSOCK(info.st_mode) or info.st_uid != os.geteuid():
        raise DockerSyntaxDenied("Docker socket ownership/type invalid")
    return socket_url


def _docker_binary(path: str) -> str:
    if os.name != "posix" or not isinstance(path, str) or not path.startswith("/"):
        raise DockerSyntaxDenied("Docker CLI must be absolute path on POSIX host")
    docker = Path(path)
    if _has_symlink_component(docker) or not docker.is_file() or not os.access(docker, os.X_OK):
        raise DockerSyntaxDenied("trusted Docker CLI missing, linked or not executable")
    return str(docker)


def _invoker(argv: tuple[str, ...], *, data: bytes | None, env: dict, timeout: int):
    """Bound Docker CLI output while reading, before it can exhaust host memory.

    This runner is Linux-only (the rootless socket gate denies Windows). The
    model never controls argv or environment. Drain both pipes concurrently so
    a noisy daemon cannot block the other pipe while we enforce size limits.
    """
    deadline = time.monotonic() + timeout
    with subprocess.Popen(
        argv, stdin=subprocess.PIPE if data is not None else subprocess.DEVNULL,
        stdout=subprocess.PIPE, stderr=subprocess.PIPE, env=env, shell=False,
    ) as proc:
        output = {"stdout": bytearray(), "stderr": bytearray()}
        limits = {"stdout": 2048, "stderr": 16384}
        try:
            with selectors.DefaultSelector() as selector:
                for stream in ("stdout", "stderr"):
                    pipe = getattr(proc, stream)
                    os.set_blocking(pipe.fileno(), False)
                    selector.register(pipe, selectors.EVENT_READ, stream)
                if data is not None:
                    os.set_blocking(proc.stdin.fileno(), False)
                    selector.register(proc.stdin, selectors.EVENT_WRITE, "stdin")
                sent = 0
                while selector.get_map():
                    remaining = deadline - time.monotonic()
                    if remaining <= 0:
                        raise subprocess.TimeoutExpired(argv, timeout)
                    for key, _ in selector.select(remaining):
                        stream = key.data
                        if stream == "stdin":
                            try:
                                sent += os.write(key.fileobj.fileno(), data[sent:sent + 4096])
                            except BrokenPipeError:
                                sent = len(data)
                            if sent >= len(data) or proc.poll() is not None:
                                selector.unregister(key.fileobj)
                                key.fileobj.close()
                            continue
                        chunk = os.read(key.fileobj.fileno(), 4096)
                        if not chunk:
                            selector.unregister(key.fileobj)
                            continue
                        if len(output[stream]) + len(chunk) > limits[stream]:
                            raise DockerSyntaxDenied("Docker process emitted excessive output")
                        output[stream].extend(chunk)
            remaining = deadline - time.monotonic()
            if remaining <= 0:
                raise subprocess.TimeoutExpired(argv, timeout)
            proc.wait(timeout=remaining)
            return subprocess.CompletedProcess(
                argv, proc.returncode, bytes(output["stdout"]), bytes(output["stderr"])
            )
        finally:
            if proc.poll() is None:
                proc.kill()
                proc.wait()


def _limited_result(result: object) -> tuple[int, bytes]:
    code = getattr(result, "returncode", None)
    stdout = getattr(result, "stdout", None)
    stderr = getattr(result, "stderr", None)
    if type(code) is not int or not isinstance(stdout, bytes) or not isinstance(stderr, bytes):
        raise DockerSyntaxDenied("Docker CLI returned invalid bounded result")
    if len(stdout) > 2048 or len(stderr) > 16384:
        raise DockerSyntaxDenied("Docker process emitted excessive output")
    return code, stdout.strip()


def run_python_syntax(
    plan: dict, candidate: str, scope: WorkspaceScope, *,
    expected_task_id: str, image: str = DEFAULT_IMAGE,
    enabled: bool = False,
    docker_binary: str = "/usr/bin/docker",
    socket_url: str | None = None,
    runner: Callable = _invoker,
) -> dict:
    """Host-opt-in syntax check. No untrusted code is *executed* by this broker.

    Rootless daemon and Docker CLI are not exposed to models. The engine must
    pre-cache and verify the pinned image; `--pull never` forbids auto-fetch.
    Actual OS isolation/CI E2E evidence is REQUIRED before marking T19 done.
    """
    if not enabled:
        raise DockerSyntaxDenied("Docker syntax gate disabled without host authorization")
    # Rebuild from the independently trusted scope and expected task. Callers
    # cannot bypass file policy by forging a SyntaxJob dataclass instance.
    job = plan_python_syntax(
        plan, candidate, scope, expected_task_id=expected_task_id, image=image
    )
    if hashlib.sha256(job.data).hexdigest() != job.candidate_sha256:
        raise DockerSyntaxDenied("job payload was changed after planning")
    binary = _docker_binary(docker_binary)
    endpoint = _rootless_socket(socket_url or "")
    name = "zynoa-p00-syntax-" + secrets.token_hex(8)
    with tempfile.TemporaryDirectory(prefix="zynoa-empty-docker-client-") as tmp:
        env = {"HOME": tmp, "DOCKER_CONFIG": tmp, "PATH": "/usr/bin:/bin"}
        # Real daemon MUST report rootless. Socket path/ownership alone is not enough.
        try:
            attestation = runner(
                (binary, "--host", endpoint, "info", "--format", "{{json .SecurityOptions}}"),
                data=None, env=env, timeout=8,
            )
        except (OSError, subprocess.TimeoutExpired):
            raise DockerSyntaxDenied("rootless Docker attestation unavailable") from None
        status, output = _limited_result(attestation)
        try:
            features = json.loads(output) if status == 0 else None
        except (ValueError, UnicodeError):
            features = None
        if not isinstance(features, list) or not any(
            isinstance(x, str) and x.lower() in ("name=rootless", "rootless") for x in features
        ):
            raise DockerSyntaxDenied("Docker daemon rootless status is not attested")
        # Docker's official rootless docs warn that --memory/--cpus/--pids-limit
        # may be silently ignored without cgroups-v2 + systemd.
        for fmt, expected in (("{{.CgroupVersion}}", b"2"),
                              ("{{.CgroupDriver}}", b"systemd")):
            try:
                probe = runner(
                    (binary, "--host", endpoint, "info", "--format", fmt),
                    data=None, env=env, timeout=8,
                )
            except (OSError, subprocess.TimeoutExpired):
                raise DockerSyntaxDenied("Docker cgroup attestation unavailable") from None
            probe_status, probe_output = _limited_result(probe)
            if probe_status != 0 or probe_output != expected:
                raise DockerSyntaxDenied("required cgroup-v2/systemd enforcement not attested")
        argv = job.argv(docker_binary=binary, rootless_socket=endpoint, job_name=name)
        try:
            result = runner(argv, data=job.data, env=env, timeout=12)
        except (OSError, subprocess.TimeoutExpired, DockerSyntaxDenied):
            # Cleanup attempt is scoped to the unpredictable job name only.
            # If cleanup fails, the host operator must investigate before retry.
            try:
                cleanup = runner(
                    (binary, "--host", endpoint, "rm", "--force", name),
                    data=None, env=env, timeout=5,
                )
                code, _ = _limited_result(cleanup)
            except (OSError, subprocess.TimeoutExpired, DockerSyntaxDenied):
                raise DockerSyntaxDenied("sandbox timeout/launch failure; cleanup unverified") from None
            if code != 0:
                raise DockerSyntaxDenied("sandbox timeout/launch failure; cleanup failed")
            raise DockerSyntaxDenied("sandbox timeout or startup failure; job cleaned") from None
        code, stdout = _limited_result(result)
    if code == 0 and stdout == _OK:
        validation = "PYTHON_SYNTAX_VALID_NO_CODE_EXECUTION"
    elif code == 2 and stdout == _BAD:
        validation = "PYTHON_SYNTAX_INVALID_NO_CODE_EXECUTION"
    else:
        raise DockerSyntaxDenied("sandbox returned unexpected result; do not infer validity")
    return {
        "status": validation,
        "phase": "P00", "task_id": job.task_id,
        "image_digest": job.image.split("@", 1)[1],
        "candidate_sha256": job.candidate_sha256,
        "docker_commands_executed": 4,
        "model_source_executed": False,
        "workspace_files_written": 0, "github_writes": 0,
        "rootless_daemon_status_observed": True,
        "independent_host_sandbox_verified": False,
        "persistent_worker_deployed": False,
    }
