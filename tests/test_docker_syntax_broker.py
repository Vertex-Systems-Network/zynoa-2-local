"""Rootless Docker Python syntax broker policy tests: mocked daemon only.

These tests do NOT prove an installed, patched or isolated runtime. They
verify container-command policy and deny-by-default host authority.
"""
from __future__ import annotations

import hashlib
import json
import os
import subprocess
import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch

from tools.docker_syntax_broker import (
    DEFAULT_IMAGE, DockerSyntaxDenied, SyntaxJob,
    _BAD, _OK, _COMPILE_CHECK, plan_python_syntax, run_python_syntax,
)
from tools.workspace_policy import WorkspaceScope

TASK = "P00-T20"
FILE = "tests/fixtures/generated.py"
SOURCE = "print('model code must NEVER execute in host')\n"


def plan(paths=(FILE,), task=TASK):
    return {
        "schema_version": 1, "phase": "P00", "branch": "phase/00-governance",
        "task_id": task,
        "summary": "Propose a syntax-only fixture test",
        "file_proposals": [
            {"path": p, "action": "DRAFT_ONLY", "reason": "Static syntax check"}
            for p in paths
        ],
        "checks": ["phase-policy"],
    }


def done(code=0, stdout=_OK, stderr=b""):
    return subprocess.CompletedProcess(args=["fake-docker"], returncode=code,
                                       stdout=stdout, stderr=stderr)


class StubDocker:
    def __init__(self, *, features=None, output=None, fail_run=False,
                 cleanup_code=0):
        self.calls = []
        self.features = features if features is not None else [
            "name=seccomp,profile=builtin", "name=rootless",
        ]
        self.output = output or done()
        self.fail_run = fail_run
        self.cleanup_code = cleanup_code

    def __call__(self, argv, *, data, env, timeout):
        self.calls.append((argv, data, env, timeout))
        if "info" in argv:
            if argv[-1] == "{{.CgroupVersion}}":
                return done(stdout=b"2")
            if argv[-1] == "{{.CgroupDriver}}":
                return done(stdout=b"systemd")
            return done(stdout=json.dumps(self.features).encode("utf-8"))
        if "rm" in argv:
            return done(code=self.cleanup_code, stdout=b"ok")
        if "run" in argv:
            if self.fail_run:
                raise subprocess.TimeoutExpired(argv, timeout=timeout)
            return self.output
        raise AssertionError("Unexpected Docker subcommand")


class DockerSyntaxBrokerTests(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        self.addCleanup(self.tmp.cleanup)
        self.root = Path(self.tmp.name).resolve()
        (self.root / "tests" / "fixtures").mkdir(parents=True)
        self.scope = WorkspaceScope(self.root, "P00", "phase/00-governance")

    def make(self, *, source=SOURCE, paths=(FILE,), task=TASK, image=DEFAULT_IMAGE):
        return plan_python_syntax(
            plan(paths, task), source, self.scope, expected_task_id=TASK, image=image
        )

    def test_compiles_plan_without_modifying_checkout_or_shell(self):
        before = list(self.root.rglob("*"))
        job = self.make()
        self.assertIsInstance(job, SyntaxJob)
        self.assertEqual(TASK, job.task_id)
        self.assertEqual(hashlib.sha256(SOURCE.encode()).hexdigest(), job.candidate_sha256)
        self.assertEqual(SOURCE.encode(), job.data)
        self.assertEqual(before, list(self.root.rglob("*")))
        self.assertFalse((self.root / FILE).exists())

    def test_docker_args_are_fixed_hardened_and_digest_pinned(self):
        args = self.make().argv(
            docker_binary="/usr/bin/docker",
            rootless_socket="unix:///run/user/1234/docker.sock",
            job_name="zynoa-p00-syntax-0000000000000000",
        )
        expected = {
            "--pull", "never", "--rm", "--interactive", "--network", "none",
            "--ipc", "--read-only", "--cap-drop", "ALL",
            "--security-opt", "no-new-privileges:true",
            "--pids-limit", "32", "--memory", "128m",
            "--memory-swap", "--cpus", "0.5", "--user", "65534:65534",
            "--tmpfs", "--workdir", "--log-driver",
        }
        self.assertTrue(expected.issubset(set(args)))
        self.assertIn("/tmp:rw,nosuid,nodev,noexec,size=16m", args)
        self.assertIn(DEFAULT_IMAGE, args)
        self.assertIn(_COMPILE_CHECK, args)
        self.assertEqual("-I", args[-5])
        self.assertEqual("-S", args[-4])
        self.assertEqual("-B", args[-3])
        for forbidden in ("--privileged", "--mount", "-v", "--volume",
                          "--device", "--publish", "-p", "--network=host",
                          "--cap-add", "sh", "bash", "sudo", "curl"):
            with self.subTest(forbidden=forbidden):
                self.assertNotIn(forbidden, args)
        self.assertNotIn(SOURCE, " ".join(args))
        self.assertIn("compile(source", _COMPILE_CHECK)
        self.assertNotIn("exec(", _COMPILE_CHECK)
        self.assertNotIn("eval(", _COMPILE_CHECK)

    def test_disabled_gate_never_invokes_docker(self):
        stub = StubDocker()
        with self.assertRaises(DockerSyntaxDenied):
            run_python_syntax(plan(), SOURCE, self.scope,
                              expected_task_id=TASK, runner=stub)
        self.assertEqual([], stub.calls)

    def test_untrusted_model_cannot_change_phase_task_or_authorize_itself(self):
        for task in ("P00-T19", "P00-T26", "P01-T20", "P00-T02"):
            with self.subTest(task=task), self.assertRaises(DockerSyntaxDenied):
                plan_python_syntax(plan(task=task), SOURCE, self.scope,
                                   expected_task_id=TASK)

    def test_rejects_non_fixture_and_extra_file_proposals(self):
        for paths in (
            ("AGENTS.md",), (".github/workflows/governance.yml",),
            ("docs/help/example.py",), ("tests/fixtures/file.js",),
            ("tests/fixtures/dir/nested.py",),
            ("tests/fixtures/../../escape.py",),
            (FILE, "tests/fixtures/second.py"),
        ):
            with self.subTest(paths=paths), self.assertRaises(DockerSyntaxDenied):
                self.make(paths=paths)

    def test_requires_digest_pinned_official_image(self):
        for image in (
            "python:3.12", "python:latest",
            "evilcorp/python@sha256:" + "a" * 64,
            "docker.io/library/python@sha256:" + "a" * 63,
            "docker.io/library/python@sha256:" + "Z" * 64,
            "docker.io/library/python@sha256:" + "a" * 64 + " --privileged",
        ):
            with self.subTest(image=image), self.assertRaises(DockerSyntaxDenied):
                self.make(image=image)

    def test_text_and_size_budget_enforced_before_docker(self):
        for content in ("", "x" * 8193, "no" + chr(0), "x" + chr(0x202e),
                        "Cafe" + chr(0x301)):
            with self.subTest(len=len(content)), self.assertRaises(DockerSyntaxDenied):
                self.make(source=content)

    @unittest.skipUnless(os.name == "posix", "rootless Unix socket only")
    def test_syntax_success_requires_attested_rootless_and_exact_marker(self):
        stub = StubDocker()
        with patch("tools.docker_syntax_broker._docker_binary", return_value="/usr/bin/docker"), \
             patch("tools.docker_syntax_broker._rootless_socket", return_value="unix:///run/user/1234/docker.sock"):
            result = run_python_syntax(
                plan(), SOURCE, self.scope, expected_task_id=TASK,
                enabled=True, socket_url="unix:///run/user/1234/docker.sock",
                runner=stub,
            )
        self.assertEqual("PYTHON_SYNTAX_VALID_NO_CODE_EXECUTION", result["status"])
        self.assertEqual(4, len(stub.calls))
        self.assertEqual("info", stub.calls[0][0][3])
        self.assertIn("run", stub.calls[3][0])
        self.assertEqual(SOURCE.encode(), stub.calls[3][1])
        self.assertEqual({"PATH", "HOME", "DOCKER_CONFIG"},
                         set(stub.calls[3][2]))
        self.assertEqual(0, result["workspace_files_written"])
        self.assertEqual(0, result["github_writes"])
        self.assertFalse(result["model_source_executed"])
        self.assertFalse(result["independent_host_sandbox_verified"])
        self.assertFalse(result["persistent_worker_deployed"])

    @unittest.skipUnless(os.name == "posix", "rootless Unix socket only")
    def test_syntax_invalid_is_not_transport_success(self):
        stub = StubDocker(output=done(code=2, stdout=_BAD))
        with patch("tools.docker_syntax_broker._docker_binary", return_value="/usr/bin/docker"), \
             patch("tools.docker_syntax_broker._rootless_socket", return_value="unix:///run/user/1234/docker.sock"):
            result = run_python_syntax(
                plan(), SOURCE, self.scope, expected_task_id=TASK,
                enabled=True, socket_url="unix:///run/user/1234/docker.sock",
                runner=stub,
            )
        self.assertEqual("PYTHON_SYNTAX_INVALID_NO_CODE_EXECUTION", result["status"])

    @unittest.skipUnless(os.name == "posix", "rootless Unix socket only")
    def test_daemon_attestation_denies_rootful_and_spoofed_status(self):
        for features in (
            [], ["name=seccomp,profile=builtin"], ["name=not-rootless"],
            ["rootless-but-disabled"], "name=rootless",
        ):
            stub = StubDocker(features=features)
            with patch("tools.docker_syntax_broker._docker_binary", return_value="/usr/bin/docker"), \
                 patch("tools.docker_syntax_broker._rootless_socket", return_value="unix:///run/user/1234/docker.sock"), \
                 self.subTest(features=features), self.assertRaises(DockerSyntaxDenied):
                run_python_syntax(plan(), SOURCE, self.scope,
                                  expected_task_id=TASK, enabled=True,
                                  socket_url="unix:///run/user/1234/docker.sock",
                                  runner=stub)
            self.assertEqual(1, len(stub.calls))

    @unittest.skipUnless(os.name == "posix", "rootless Unix socket only")
    def test_cgroups_v1_or_missing_systemd_driver_refused(self):
        for key, bad_value in (("{{.CgroupVersion}}", b"1"),
                               ("{{.CgroupDriver}}", b"none")):
            class NoResourcesDocker(StubDocker):
                def __call__(self, argv, *, data, env, timeout):
                    if "info" in argv and argv[-1] == key:
                        self.calls.append((argv, data, env, timeout))
                        return done(stdout=bad_value)
                    return super().__call__(argv, data=data, env=env, timeout=timeout)
            stub = NoResourcesDocker()
            with patch("tools.docker_syntax_broker._docker_binary", return_value="/usr/bin/docker"), \
                 patch("tools.docker_syntax_broker._rootless_socket", return_value="unix:///run/user/1234/docker.sock"), \
                 self.subTest(key=key), self.assertRaises(DockerSyntaxDenied):
                run_python_syntax(plan(), SOURCE, self.scope,
                                  expected_task_id=TASK, enabled=True,
                                  socket_url="unix:///run/user/1234/docker.sock",
                                  runner=stub)
            self.assertFalse(any("run" in x[0] for x in stub.calls))

    @unittest.skipUnless(os.name == "posix", "rootless Unix socket only")
    def test_unexpected_exit_never_claims_valid_syntax_or_leaks_stderr(self):
        stub = StubDocker(output=done(code=5, stdout=b"NO", stderr=b"PRIVATE SECRET"))
        with patch("tools.docker_syntax_broker._docker_binary", return_value="/usr/bin/docker"), \
             patch("tools.docker_syntax_broker._rootless_socket", return_value="unix:///run/user/1234/docker.sock"):
            with self.assertRaises(DockerSyntaxDenied) as cm:
                run_python_syntax(plan(), SOURCE, self.scope,
                                  expected_task_id=TASK, enabled=True,
                                  socket_url="unix:///run/user/1234/docker.sock",
                                  runner=stub)
        self.assertNotIn("PRIVATE SECRET", str(cm.exception))

    @unittest.skipUnless(os.name == "posix", "rootless Unix socket only")
    def test_timeout_tries_only_scoped_container_cleanup(self):
        stub = StubDocker(fail_run=True)
        with patch("tools.docker_syntax_broker._docker_binary", return_value="/usr/bin/docker"), \
             patch("tools.docker_syntax_broker._rootless_socket", return_value="unix:///run/user/1234/docker.sock"):
            with self.assertRaises(DockerSyntaxDenied):
                run_python_syntax(plan(), SOURCE, self.scope,
                                  expected_task_id=TASK, enabled=True,
                                  socket_url="unix:///run/user/1234/docker.sock",
                                  runner=stub)
        self.assertEqual(5, len(stub.calls))
        self.assertEqual("rm", stub.calls[-1][0][3])
        self.assertEqual("--force", stub.calls[-1][0][4])
        self.assertEqual(stub.calls[3][0][stub.calls[3][0].index("--name") + 1],
                         stub.calls[-1][0][-1])

    @unittest.skipUnless(os.name == "posix", "rootless Unix socket only")
    def test_timeout_cleanup_failure_is_blocker(self):
        stub = StubDocker(fail_run=True, cleanup_code=1)
        with patch("tools.docker_syntax_broker._docker_binary", return_value="/usr/bin/docker"), \
             patch("tools.docker_syntax_broker._rootless_socket", return_value="unix:///run/user/1234/docker.sock"):
            with self.assertRaises(DockerSyntaxDenied) as cm:
                run_python_syntax(plan(), SOURCE, self.scope,
                                  expected_task_id=TASK, enabled=True,
                                  socket_url="unix:///run/user/1234/docker.sock",
                                  runner=stub)
        self.assertIn("cleanup failed", str(cm.exception))

    @unittest.skipUnless(os.name == "posix", "rootless Unix socket only")
    def test_no_image_or_restricted_cli_yields_blocked_not_fake_result(self):
        with patch("tools.docker_syntax_broker._docker_binary", return_value="/usr/bin/docker"), \
             patch("tools.docker_syntax_broker._rootless_socket", return_value="unix:///run/user/1234/docker.sock"):
            with self.assertRaises(DockerSyntaxDenied):
                run_python_syntax(plan(), SOURCE, self.scope, expected_task_id=TASK,
                                  enabled=True, socket_url="unix:///run/user/1234/docker.sock",
                                  runner=lambda *a, **kw: done(code=1, stderr=b"not found"))

    def test_rootless_authority_checks_fail_without_real_socket(self):
        from tools.docker_syntax_broker import _rootless_socket
        with self.assertRaises(DockerSyntaxDenied):
            _rootless_socket("unix:///var/run/docker.sock")
        with self.assertRaises(DockerSyntaxDenied):
            _rootless_socket("https://untrusted:2375")

    def test_compiled_code_not_executed_by_host_process(self):
        before = list(self.root.rglob("*"))
        with patch("os.system", side_effect=AssertionError("would execute")) as call:
            job = self.make(source="import os\nos.system('whoami')\n")
        call.assert_not_called()
        self.assertEqual(before, list(self.root.rglob("*")))
        self.assertIn(b"os.system", job.data)


if __name__ == "__main__":
    unittest.main()
