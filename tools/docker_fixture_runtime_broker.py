"""P00 opt-in rootless Docker FUNCTIONAL fixture checks, not a general code runner.

This is the first *execution* broker: only a short, single Python fixture with
a fixed solve(x)->2*x contract may be evaluated INSIDE a separately authorized
rootless container. It cannot modify the checkout, receive secrets, use network,
mount repositories or run commands chosen by the model. The model's source is
NEVER parsed/imported/executed by this trusted controller process.

An untrusted test pass is NOT host security attestation, full semantic coverage,
approval for repository writes, or proof of a running agent. CI uses mock Docker
except a trusted-source harness contract test; production host is not deployed.
"""
from __future__ import annotations

import hashlib
import json
import os
import secrets
import subprocess
import tempfile
from dataclasses import dataclass
from typing import Callable

from tools.docker_syntax_broker import (
    DEFAULT_IMAGE, DockerSyntaxDenied, _LIMITS_CHECK,
    _docker_binary, _rootless_socket, _invoker, _limited_result,
    plan_python_syntax,
)
from tools.workspace_policy import WorkspaceScope

# The host defines the tests, Python image, Docker argv, and all budgets.
# No project/repo files or application secrets are available inside the
# candidate's namespace. These tests are intentionally a tiny fixture contract,
# not a general full-app unit-test executor.
_CASES = ((0, 0), (1, 2), (-3, -6), (7, 14), (100, 200))
_PASS = b"ZYNOA_FIXTURE_PASSED_UNATTESTED"
_FAIL = b"ZYNOA_FIXTURE_FAILED_UNATTESTED"

# Fixed child code. An untrusted candidate only receives limited integers and
# must define solve(x). Its output is captured and interpreted by the separate
# fixed parent; arbitrary print statements fail strict output schema.
_CHILD = (
    "import sys,json\n"
    "raw=sys.stdin.buffer.read(8193)\n"
    "if not 0<len(raw)<=8192: sys.exit(3)\n"
    "scope={'__name__':'__fixture__'}\n"
    "try:\n"
    " compiled=compile(raw,'<untrusted-fixture>','exec',dont_inherit=True)\n"
    " exec(compiled,scope)\n"
    " f=scope.get('solve')\n"
    " if not callable(f): sys.exit(4)\n"
    " results=[]\n"
    " for x in (0,1,-3,7,100):\n"
    "  value=f(x)\n"
    "  if type(value) is not int: sys.exit(5)\n"
    "  results.append(value)\n"
    " sys.stdout.write(json.dumps(results,separators=(',',':')))\n"
    "except BaseException: sys.exit(6)\n"
)

# Fixed parent code executes *inside* constrained Docker, not on the privileged
# controller host. It reads cgroup ceilings and root mount flags BEFORE opening
# the untrusted input, spawns a bounded child, discards its stderr, checks exact
# expected behavior, then emits its own fixed marker. No user shell or argv.
_PARENT = (
    "import json,os,socket,subprocess,sys\n"
    "from pathlib import Path\n"
    + _LIMITS_CHECK +
    "try:\n"
    " root=Path('/sys/fs/cgroup')\n"
    " mem=(root/'memory.max').read_text(encoding='ascii').strip()\n"
    " pids=(root/'pids.max').read_text(encoding='ascii').strip()\n"
    " cpu=(root/'cpu.max').read_text(encoding='ascii').strip()\n"
    " if any(len(x)>64 for x in (mem,pids,cpu)): sys.exit(7)\n"
    " if not _limits_enforced(mem,pids,cpu): sys.exit(7)\n"
    " if {name for _,name in socket.if_nameindex()} != {'lo'}: sys.exit(7)\n"
    " if not (os.statvfs('/').f_flag & os.ST_RDONLY): sys.exit(7)\n"
    "except (OSError,ValueError,UnicodeError): sys.exit(7)\n"
    "data=sys.stdin.buffer.read(8193)\n"
    "if not 0<len(data)<=8192: sys.exit(8)\n"
    "try:\n"
    " child=subprocess.run(\n"
    "  (sys.executable,'-I','-S','-B','-c'," + repr(_CHILD) + "),\n"
    "  input=data,stdout=subprocess.PIPE,stderr=subprocess.DEVNULL,\n"
    "  env={'PYTHONHASHSEED':'0'},cwd='/tmp',timeout=3,check=False)\n"
    " if child.returncode != 0 or len(child.stdout)>256: raise ValueError()\n"
    " outputs=json.loads(child.stdout)\n"
    " if type(outputs) is list and len(outputs)==5 and\n"
    "    all(type(x) is int for x in outputs) and\n"
    "    outputs==[0,2,-6,14,200]:\n"
    "  print('ZYNOA_FIXTURE_PASSED_UNATTESTED')\n"
    "  sys.exit(0)\n"
    "except (OSError,subprocess.TimeoutExpired,ValueError,UnicodeError,RecursionError):\n"
    " pass\n"
    "print('ZYNOA_FIXTURE_FAILED_UNATTESTED')\n"
    "sys.exit(2)\n"
)
# Syntax fix: parent multiline if must use a parenthesized condition rather
# than a raw line break. The script remains a string and is only compiled as
# trusted controller code in tests or inside the container.
_PARENT = _PARENT.replace(
    " if type(outputs) is list and len(outputs)==5 and\n"
    "    all(type(x) is int for x in outputs) and\n"
    "    outputs==[0,2,-6,14,200]:\n",
    " if (type(outputs) is list and len(outputs)==5 and\n"
    "     all(type(x) is int for x in outputs) and\n"
    "     outputs==[0,2,-6,14,200]):\n",
)


class FixtureRuntimeDenied(ValueError):
    """Sanitized refusal. Raw model code/Docker stdout is never disclosed."""


@dataclass(frozen=True, repr=False)
class RuntimeJob:
    task_id: str
    candidate_sha256: str
    data: bytes = __import__("dataclasses").field(repr=False)

    def argv(self, docker_binary: str, socket_url: str, name: str) -> tuple[str, ...]:
        return (
            docker_binary, "--host", socket_url, "run",
            "--pull", "never", "--rm", "--interactive",
            "--name", name,
            "--label", "zynoa.phase=P00",
            "--label", "zynoa.purpose=fixture-test",
            "--network", "none", "--ipc", "none", "--read-only",
            "--cap-drop", "ALL",
            "--security-opt", "no-new-privileges:true",
            "--security-opt", "seccomp=builtin",
            "--pids-limit", "32", "--memory", "128m", "--memory-swap", "128m",
            "--cpus", "0.5", "--user", "65534:65534",
            "--tmpfs", "/tmp:rw,nosuid,nodev,noexec,size=16m",
            "--workdir", "/tmp", "--log-driver", "none",
            DEFAULT_IMAGE, "python", "-I", "-S", "-B", "-c", _PARENT,
        )


def plan_python_fixture_tests(plan: dict, candidate: str, scope: WorkspaceScope, *,
                              expected_task_id: str) -> RuntimeJob:
    """No file writes, Docker calls or host-side Python candidate compilation."""
    try:
        job = plan_python_syntax(
            plan, candidate, scope, expected_task_id=expected_task_id,
        )
    except DockerSyntaxDenied:
        raise FixtureRuntimeDenied("fixture scope/size/identity denied") from None
    if expected_task_id != "P00-T20":
        raise FixtureRuntimeDenied("fixture task outside P00-T20")
    return RuntimeJob(task_id=expected_task_id,
                      candidate_sha256=job.candidate_sha256, data=job.data)


def run_python_fixture_tests(
    plan: dict, candidate: str, scope: WorkspaceScope, *,
    expected_task_id: str,
    enabled: bool = False, operator_ack: bool = False,
    execution_grant: bool = False,
    docker_binary: str = "/usr/bin/docker",
    socket_url: str | None = None,
    runner: Callable = _invoker,
) -> dict:
    """Opt-in, Linux rootless Docker only; model-source runs in-container ONLY.

    This is *not* independent container vulnerability/host-resource attestation.
    It returns untrusted functional-test evidence pending an external host
    security review, never grants a PR write, merge or phase change.
    """
    if enabled is not True or operator_ack is not True or execution_grant is not True:
        raise FixtureRuntimeDenied("fixture execution disabled without host grant")
    job = plan_python_fixture_tests(plan, candidate, scope,
                                    expected_task_id=expected_task_id)
    try:
        binary = _docker_binary(docker_binary)
        endpoint = _rootless_socket(socket_url or "")
    except (DockerSyntaxDenied, OSError, ValueError):
        raise FixtureRuntimeDenied("trusted rootless CLI/socket unavailable") from None
    name = "zynoa-p00-fixture-" + secrets.token_hex(8)
    with tempfile.TemporaryDirectory(prefix="zynoa-empty-fixture-docker-") as root:
        env = {"HOME": root, "DOCKER_CONFIG": root, "PATH": "/usr/bin:/bin"}
        for fmt, expected in (
            ("{{json .SecurityOptions}}", None),
            ("{{.CgroupVersion}}", b"2"),
            ("{{.CgroupDriver}}", b"systemd"),
        ):
            try:
                result = runner((binary, "--host", endpoint, "info", "--format", fmt),
                                data=None, env=env, timeout=8)
                code, output = _limited_result(result)
            except (DockerSyntaxDenied, OSError, subprocess.TimeoutExpired):
                raise FixtureRuntimeDenied("rootless Docker readiness unavailable") from None
            if code != 0:
                raise FixtureRuntimeDenied("rootless Docker status unavailable")
            if expected is None:
                try:
                    options = json.loads(output)
                except (ValueError, UnicodeError):
                    options = None
                if not isinstance(options, list) or not any(
                    isinstance(x, str) and x.lower() in ("name=rootless", "rootless")
                    for x in options
                ):
                    raise FixtureRuntimeDenied("rootless daemon not proven")
            elif output != expected:
                raise FixtureRuntimeDenied("Docker cgroup-v2/systemd limits not proven")
        try:
            result = runner(job.argv(binary, endpoint, name), data=job.data,
                            env=env, timeout=12)
        except (DockerSyntaxDenied, OSError, subprocess.TimeoutExpired):
            try:
                cleanup = runner((binary, "--host", endpoint, "rm", "--force", name),
                                 data=None, env=env, timeout=5)
                code, _ = _limited_result(cleanup)
            except (DockerSyntaxDenied, OSError, subprocess.TimeoutExpired):
                raise FixtureRuntimeDenied("fixture container cleanup unverified") from None
            if code != 0:
                raise FixtureRuntimeDenied("fixture container cleanup failed")
            raise FixtureRuntimeDenied("fixture container failed; targeted cleanup attempted") from None
        try:
            code, output = _limited_result(result)
        except DockerSyntaxDenied:
            raise FixtureRuntimeDenied("fixture container output invalid") from None
    if code == 0 and output == _PASS:
        status = "FIXTURE_TESTS_PASSED_ISOLATION_UNVERIFIED"
    elif code == 2 and output == _FAIL:
        status = "FIXTURE_TESTS_FAILED_ISOLATION_UNVERIFIED"
    else:
        raise FixtureRuntimeDenied("fixture container verdict not recognized")
    return {
        "status": status,
        "phase": "P00", "task_id": "P00-T20",
        "image_digest": DEFAULT_IMAGE.split("@", 1)[1],
        "candidate_sha256": job.candidate_sha256,
        "fixed_test_cases": 5,
        "container_model_source_execution_requested": True,
        "controller_host_source_executed": False,
        "workspace_files_written": 0,
        "github_writes": 0,
        "independent_host_sandbox_verified": False,
        "real_container_run_independently_attested": False,
        "persistent_worker_deployed": False,
    }
