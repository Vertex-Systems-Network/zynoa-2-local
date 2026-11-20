"""P00 scoped Python fixture execution broker contracts; no live Docker in CI.

The only subprocess in this suite evaluates a hardcoded trusted reference
function to verify the fixed child harness. Generated/model input is never
run by the test runner. All Docker daemon responses are synthetic.
"""
from __future__ import annotations

import hashlib
import json
import os
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch

from tools.docker_fixture_runtime_broker import (
    _CHILD, _PARENT, _PASS, _FAIL, _CASES,
    FixtureRuntimeDenied, RuntimeJob,
    plan_python_fixture_tests, run_python_fixture_tests,
)
from tools.docker_syntax_broker import DEFAULT_IMAGE, DockerSyntaxDenied
from tools.workspace_policy import WorkspaceScope

TASK = "P00-T20"
FILE = "tests/fixtures/runtime-check.py"
REF = "def solve(x):\n    return x * 2\n"


def plan(path=FILE, task=TASK):
    return {
        "schema_version": 1, "phase": "P00", "branch": "phase/00-governance",
        "task_id": task, "summary": "Fixed rootless fixture runtime contract",
        "file_proposals": [
            {"path": path, "action": "DRAFT_ONLY", "reason": "Test in fixture container"},
        ],
        "checks": ["phase-policy"],
    }


def result(code=0, stdout=_PASS, stderr=b""):
    return subprocess.CompletedProcess(["mock-docker"], code, stdout, stderr)


class DockerMock:
    def __init__(self, *, output=None, security=None, cg_version=b"2",
                 cg_driver=b"systemd", broken_run=False, cleanup_code=0):
        self.calls = []
        self.output = output if output is not None else result()
        self.security = security if security is not None else ["name=rootless"]
        self.cg_version = cg_version
        self.cg_driver = cg_driver
        self.broken_run = broken_run
        self.cleanup_code = cleanup_code

    def __call__(self, argv, *, data, env, timeout):
        self.calls.append((argv, data, dict(env), timeout))
        if "info" in argv:
            if argv[-1] == "{{json .SecurityOptions}}":
                return result(stdout=json.dumps(self.security).encode("utf-8"))
            if argv[-1] == "{{.CgroupVersion}}":
                return result(stdout=self.cg_version)
            return result(stdout=self.cg_driver)
        if "run" in argv:
            if self.broken_run:
                raise subprocess.TimeoutExpired(argv, timeout)
            return self.output
        if "rm" in argv:
            return result(code=self.cleanup_code)
        raise AssertionError("unexpected mock Docker command")


class RuntimeFixturePolicyTests(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        self.addCleanup(self.tmp.cleanup)
        self.root = Path(self.tmp.name)
        (self.root / "tests/fixtures").mkdir(parents=True)
        self.scope = WorkspaceScope(
            self.root, "P00", "phase/00-governance", ("tests/fixtures",)
        )

    def run_mocked(self, fake=None, source=REF, **kwargs):
        fake = fake or DockerMock()
        with patch("tools.docker_fixture_runtime_broker._docker_binary",
                   return_value="/usr/bin/docker"), \
             patch("tools.docker_fixture_runtime_broker._rootless_socket",
                   return_value="unix:///run/user/1000/docker.sock"):
            receipt = run_python_fixture_tests(
                plan(), source, self.scope,
                expected_task_id=TASK, enabled=True,
                operator_ack=True, execution_grant=True,
                socket_url="unix:///run/user/1000/docker.sock",
                runner=fake, **kwargs,
            )
        return receipt, fake

    def test_default_denied_without_any_model_or_docker_calls(self):
        fake = DockerMock()
        for flags in (
            {}, {"enabled": True},
            {"enabled": True, "operator_ack": True},
            {"enabled": True, "execution_grant": True},
            {"operator_ack": True, "execution_grant": True},
            {"enabled": 1, "operator_ack": True, "execution_grant": True},
        ):
            with self.subTest(flags=flags), self.assertRaises(FixtureRuntimeDenied):
                run_python_fixture_tests(
                    plan(), REF, self.scope,
                    expected_task_id=TASK, runner=fake, **flags,
                )
        self.assertEqual([], fake.calls)

    def test_path_task_phase_extra_file_and_source_limits(self):
        for p in (
            plan(path="AGENTS.md"),
            plan(path=".github/workflows/governance.yml"),
            plan(path="tests/fixtures/nested/r.py"),
            plan(path="tests/fixtures/run.js"),
            plan(path="tests/fixtures/../escape.py"),
            plan(task="P00-T19"),
        ):
            with self.subTest(p=p), self.assertRaises(FixtureRuntimeDenied):
                plan_python_fixture_tests(p, REF, self.scope, expected_task_id=TASK)
        for source in ("", "a"*8193, "x\x00", "x\r",
                       "caf" + chr(0x301), "x" + chr(0x202e)):
            with self.subTest(size=len(source)), self.assertRaises(FixtureRuntimeDenied):
                plan_python_fixture_tests(plan(), source, self.scope,
                                          expected_task_id=TASK)
        with self.assertRaises(FixtureRuntimeDenied):
            plan_python_fixture_tests(plan(), REF, self.scope,
                                      expected_task_id="P01-T20")

    def test_plan_is_pure_and_hides_source(self):
        before = list(self.root.rglob("*"))
        job = plan_python_fixture_tests(plan(), REF, self.scope,
                                        expected_task_id=TASK)
        self.assertIsInstance(job, RuntimeJob)
        self.assertEqual(hashlib.sha256(REF.encode()).hexdigest(),
                         job.candidate_sha256)
        self.assertEqual(REF.encode(), job.data)
        self.assertNotIn(REF, repr(job))
        self.assertEqual(before, list(self.root.rglob("*")))
        self.assertFalse((self.root/FILE).exists())

    def test_container_command_has_fixed_isolation_and_no_host_mount(self):
        job = plan_python_fixture_tests(plan(), REF, self.scope,
                                        expected_task_id=TASK)
        argv = job.argv("/usr/bin/docker", "unix:///run/user/1000/docker.sock",
                        "zynoa-p00-fixture-test123")
        must = {
            "--network", "none", "--ipc", "--read-only", "--cap-drop", "ALL",
            "--security-opt", "no-new-privileges:true", "seccomp=builtin",
            "--pids-limit", "32", "--memory", "128m", "--memory-swap",
            "--cpus", "0.5", "--user", "65534:65534", "--tmpfs",
            "--log-driver", "never", "--pull",
        }
        self.assertTrue(must.issubset(set(argv)))
        self.assertIn(DEFAULT_IMAGE, argv)
        self.assertEqual("never", argv[argv.index("--pull")+1])
        self.assertEqual("128m", argv[argv.index("--memory-swap")+1])
        self.assertEqual("none", argv[argv.index("--network")+1])
        self.assertEqual("none", argv[argv.index("--log-driver")+1])
        self.assertEqual(_PARENT, argv[-1])
        self.assertIn("python", argv)
        self.assertNotIn(REF, " ".join(argv))
        for illegal in ("--privileged", "--mount", "-v", "--volume",
                        "--device", "--publish", "-p", "--network=host",
                        "--cap-add", "bash", "sh", "sudo", "curl"):
            with self.subTest(option=illegal):
                self.assertNotIn(illegal, argv)

    def test_fixed_parent_gate_compiles_and_checks_before_candidate_read(self):
        compile(_PARENT, "<trusted-container-parent>", "exec")
        compile(_CHILD, "<trusted-container-child>", "exec")
        for condition in ("memory.max", "pids.max", "cpu.max",
                          "socket.if_nameindex()", "os.statvfs('/')"):
            self.assertIn(condition, _PARENT)
            self.assertLess(_PARENT.index(condition),
                            _PARENT.index("data=sys.stdin.buffer.read"))
        self.assertIn("exec(compiled,scope)", _CHILD)
        self.assertNotIn("exec(compiled", _PARENT)
        self.assertIn("subprocess.run(", _PARENT)
        self.assertIn("stderr=subprocess.DEVNULL", _PARENT)
        self.assertIn("timeout=3", _PARENT)
        self.assertIn("outputs==[0,2,-6,14,200]", _PARENT)

    def test_trusted_harness_reference_execution_under_tight_python_cli(self):
        # This is trusted, literal REF code, not model-generated. It tests
        # fixed harness functionality only, NOT Docker OS sandbox isolation.
        p = subprocess.run(
            [sys.executable, "-I", "-S", "-B", "-c", _CHILD],
            input=REF.encode(), capture_output=True, timeout=4,
        )
        self.assertEqual(0, p.returncode, p.stderr.decode()[:300])
        self.assertEqual([0, 2, -6, 14, 200], json.loads(p.stdout))

    def test_mock_success_receipt_cannot_claim_real_attestation(self):
        receipt, fake = self.run_mocked()
        self.assertEqual("FIXTURE_TESTS_PASSED_ISOLATION_UNVERIFIED",
                         receipt["status"])
        self.assertEqual(TASK, receipt["task_id"])
        self.assertEqual(5, receipt["fixed_test_cases"])
        self.assertFalse(receipt["independent_host_sandbox_verified"])
        self.assertFalse(receipt["real_container_run_independently_attested"])
        self.assertFalse(receipt["persistent_worker_deployed"])
        self.assertFalse(receipt["controller_host_source_executed"])
        self.assertEqual(0, receipt["github_writes"])
        self.assertEqual(0, receipt["workspace_files_written"])
        self.assertEqual(4, len(fake.calls))
        self.assertEqual(REF.encode(), fake.calls[-1][1])
        self.assertEqual({"PATH", "HOME", "DOCKER_CONFIG"}, set(fake.calls[-1][2]))
        self.assertEqual(12, fake.calls[-1][3])
        self.assertNotIn(REF, json.dumps(receipt))
        self.assertFalse((self.root/FILE).exists())

    def test_test_failure_is_result_not_permission_to_edit(self):
        receipt, fake = self.run_mocked(fake=DockerMock(output=result(2, _FAIL)))
        self.assertEqual("FIXTURE_TESTS_FAILED_ISOLATION_UNVERIFIED",
                         receipt["status"])
        self.assertEqual(0, receipt["workspace_files_written"])
        self.assertFalse(receipt["independent_host_sandbox_verified"])
        self.assertEqual(4, len(fake.calls))

    def test_ambiguous_marker_or_returncode_denied(self):
        for output in (result(0, _FAIL), result(2, _PASS),
                       result(0, _PASS+b"extra"), result(1, _PASS),
                       result(0, b""), result(0, b"hello"),
                       result(True, _PASS)):
            with self.subTest(output=(output.returncode,output.stdout)), \
                 self.assertRaises(FixtureRuntimeDenied):
                self.run_mocked(fake=DockerMock(output=output))

    def test_host_daemon_rootless_cgroup_is_mandatory(self):
        fake_cases = [
            DockerMock(security=["name=seccomp"]),
            DockerMock(security=["name=rootless", "something"], cg_version=b"1"),
            DockerMock(cg_driver=b"none"),
            DockerMock(security="name=rootless"),
        ]
        for fake in fake_cases:
            with self.subTest(fake=fake.__dict__), \
                 self.assertRaises(FixtureRuntimeDenied):
                self.run_mocked(fake=fake)
            self.assertLess(len(fake.calls), 4)

    def test_timeout_cleanup_is_exact_name_only(self):
        fake = DockerMock(broken_run=True)
        with self.assertRaises(FixtureRuntimeDenied):
            self.run_mocked(fake=fake)
        self.assertEqual(5, len(fake.calls))
        argv = fake.calls[3][0]
        target_name = argv[argv.index("--name")+1]
        self.assertEqual(("rm", "--force", target_name),
                         fake.calls[4][0][3:])
        self.assertTrue(target_name.startswith("zynoa-p00-fixture-"))

    def test_failed_cleanup_cannot_claim_success(self):
        fake = DockerMock(broken_run=True, cleanup_code=1)
        with self.assertRaises(FixtureRuntimeDenied):
            self.run_mocked(fake=fake)
        self.assertEqual(5, len(fake.calls))

    def test_no_real_docker_without_rootless_host(self):
        # This CI is not an authorized nonroot rootless Docker host.
        with patch("tools.docker_fixture_runtime_broker._docker_binary",
                   side_effect=DockerSyntaxDenied("not configured")):
            with self.assertRaises(FixtureRuntimeDenied):
                run_python_fixture_tests(
                    plan(), REF, self.scope, expected_task_id=TASK,
                    enabled=True, operator_ack=True, execution_grant=True,
                )

    def test_same_candidate_bytes_stay_off_host_command_line(self):
        receipt, fake = self.run_mocked(
            source="import os\ndef solve(x):\n    return x * 2\n"
        )
        last = fake.calls[-1]
        self.assertNotIn("import os", " ".join(last[0]))
        self.assertEqual("import os\ndef solve(x):\n    return x * 2\n".encode(),
                         last[1])
        self.assertNotIn("import os", json.dumps(receipt))


if __name__ == "__main__":
    unittest.main()
