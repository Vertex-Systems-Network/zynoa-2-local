"""P00 trusted source SHA-binding tests plus real disposable Git worktree writes.

Linux runs a REAL git init/commit/worktree and fd-scoped single new fixture
write, with trusted *mocked* Ollama/Docker evidence. No model source is executed
in the controller/CI. Windows only runs fail-closed policy checks.
"""
from __future__ import annotations

import hashlib
import json
import os
import shutil
import subprocess
import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch

from tools.verified_fixture_worktree_flow import (
    VerifiedFixtureFlowDenied, run_verified_fixture_worktree_flow,
)
from tools.docker_syntax_broker import DEFAULT_IMAGE, DockerSyntaxDenied
from tools.docker_fixture_runtime_broker import FixtureRuntimeDenied
from tools.local_fixture_drafter import make_fixture_request
from tools.worktree_plan import plan_detached_worktree
from tools.workspace_policy import WorkspaceScope

_TASK = "P00-T20"
_PATH = "tests/fixtures/bound.py"
_BAD = "def solve(x):\n    return x\n"
_GOOD = "def solve(x):\n    return x * 2\n"
_BROKEN = "def solve(\n"
_SVALID = "PYTHON_SYNTAX_VALID_NO_CODE_EXECUTION"
_SINVALID = "PYTHON_SYNTAX_INVALID_NO_CODE_EXECUTION"
_TPASS = "FIXTURE_TESTS_PASSED_ISOLATION_UNVERIFIED"
_TFAIL = "FIXTURE_TESTS_FAILED_ISOLATION_UNVERIFIED"
_STATE = {
    "phase": "P00", "phase_status": "IN_PROGRESS",
    "active_branch": "phase/00-governance", "primary_pr": 1,
}


def _plan(path=_PATH):
    return {
        "schema_version": 1, "phase": "P00",
        "branch": "phase/00-governance", "task_id": _TASK,
        "summary": "Bind model test SHA to disposable source write",
        "file_proposals": [
            {"path": path, "action": "DRAFT_ONLY",
             "reason": "Trusted fixed-function fixture proof"},
        ],
        "checks": ["phase-policy"],
    }


@unittest.skipUnless(
    os.name == "posix" and hasattr(os, "geteuid")
    and os.geteuid() != 0 and shutil.which("git"),
    "Real detached worktree write requires a nonroot POSIX Git runner",
)
class VerifiedFlowIntegrationTests(unittest.TestCase):
    def setUp(self):
        temp = tempfile.TemporaryDirectory()
        self.addCleanup(temp.cleanup)
        self.base = Path(temp.name)
        self.repo = self.base / "trusted-source"
        self.root = self.base / "jobs"
        self.hooks = self.base / "no-hooks"
        for p in (self.repo, self.root, self.hooks):
            p.mkdir(mode=0o700)
        env = dict(os.environ)
        env.pop("GIT_CONFIG_COUNT", None)
        env["GIT_CONFIG_NOSYSTEM"] = "1"
        env["GIT_CONFIG_GLOBAL"] = str(self.base / "git-config")
        (self.base / "git-config").write_text("")
        self.env = env
        subprocess.run(["git", "init", "-q", str(self.repo)],
                       check=True, timeout=10, capture_output=True, env=env)
        subprocess.run([
            "git", "-C", str(self.repo), "-c", "user.name=ZynoaTest",
            "-c", "user.email=ci@invalid.example",
            "commit", "--allow-empty", "-q", "-m", "trusted fixture"
        ], check=True, timeout=10, capture_output=True, env=env)
        self.sha = subprocess.run(
            ["git", "-C", str(self.repo), "rev-parse", "HEAD"],
            check=True, timeout=10, capture_output=True, text=True, env=env,
        ).stdout.strip()
        work = plan_detached_worktree(
            self.repo, self.root, self.hooks, "e2e-01", self.sha, _STATE
        )
        subprocess.run(work.argv, check=True, timeout=10,
                       capture_output=True, env=env)
        self.worktree = work.target
        (self.worktree / "tests").mkdir(mode=0o700)
        (self.worktree / "tests/fixtures").mkdir(mode=0o700)
        self.scope = WorkspaceScope(
            self.worktree, "P00", "phase/00-governance", ("tests/fixtures",)
        )
        self.sources = [_GOOD]
        self.syntax_results = [_SVALID]
        self.runtime_results = [_TPASS]
        self.model_calls = []
        self.syntax_calls = []
        self.runtime_calls = []
        self.operator_plan = _plan()

    def model(self, base, payload):
        self.assertEqual("http://127.0.0.1:11434", base)
        self.assertNotIn("tools", payload)
        context = json.loads(payload["messages"][1]["content"])
        self.model_calls.append(context)
        _, _, path, digest = make_fixture_request(
            "coder:7b", self.operator_plan, self.scope,
            expected_task_id=_TASK,
        )
        self.assertEqual(digest, context["plan_sha256"])
        self.assertEqual(path, context["path"])
        source = self.sources[min(len(self.model_calls)-1, len(self.sources)-1)]
        return {
            "model": "coder:7b", "done": True, "done_reason": "stop",
            "message": {"role": "assistant", "content": json.dumps({
                "schema_version": 1, "phase": "P00",
                "branch": "phase/00-governance", "task_id": _TASK,
                "plan_sha256": digest, "path": path, "source": source,
            })},
        }

    def syntax(self, plan, source, scope, **options):
        self.assertEqual(plan, self.operator_plan)
        self.assertIs(scope, self.scope)
        self.assertIs(options["enabled"], True)
        self.assertEqual(_TASK, options["expected_task_id"])
        self.syntax_calls.append(source)
        status = self.syntax_results[min(len(self.syntax_calls)-1, len(self.syntax_results)-1)]
        return {
            "phase": "P00", "task_id": _TASK, "status": status,
            "candidate_sha256": hashlib.sha256(source.encode()).hexdigest(),
            "image_digest": DEFAULT_IMAGE.split("@", 1)[1],
            "docker_commands_executed": 4, "rootless_daemon_status_observed": True,
            "model_source_executed": False,
            "workspace_files_written": 0, "github_writes": 0,
            "independent_host_sandbox_verified": False,
            "persistent_worker_deployed": False,
        }

    def runtime(self, plan, source, scope, **options):
        self.assertEqual(plan, self.operator_plan)
        self.assertIs(scope, self.scope)
        self.assertIs(options["operator_ack"], True)
        self.assertIs(options["execution_grant"], True)
        self.runtime_calls.append(source)
        status = self.runtime_results[min(len(self.runtime_calls)-1,len(self.runtime_results)-1)]
        return {
            "phase": "P00", "task_id": _TASK, "status": status,
            "candidate_sha256": hashlib.sha256(source.encode()).hexdigest(),
            "image_digest": DEFAULT_IMAGE.split("@", 1)[1],
            "fixed_test_cases": 5,
            "container_model_source_execution_requested": True,
            "controller_host_source_executed": False,
            "workspace_files_written": 0, "github_writes": 0,
            "independent_host_sandbox_verified": False,
            "real_container_run_independently_attested": False,
            "persistent_worker_deployed": False,
        }

    def invoke(self, **kwargs):
        options = {
            "expected_task_id": _TASK, "expected_commit_sha": self.sha,
            "trusted_source_repo": self.repo, "controlled_root": self.root,
            "enabled": True, "operator_ack": True,
            "syntax_enabled": True, "execution_grant": True,
            "write_grant": True, "model_transport": self.model,
            "syntax_broker": self.syntax, "runtime_broker": self.runtime,
        }
        options.update(kwargs)
        return run_verified_fixture_worktree_flow(
            "coder:7b", self.operator_plan, self.scope, **options,
        )

    def test_real_new_file_written_only_when_same_candidate_passes_both_checks(self):
        report = self.invoke()
        self.assertEqual("FIXTURE_VERIFIED_AND_WRITTEN_TO_DISPOSABLE_WORKTREE",
                         report["status"])
        self.assertEqual(hashlib.sha256(_GOOD.encode()).hexdigest(),
                         report["written_candidate_sha256"])
        self.assertEqual(self.sha, report["source_commit_sha"])
        self.assertEqual(1, report["disposable_worktree_files_written"])
        self.assertEqual(0, report["trusted_checkout_files_written"])
        self.assertEqual(0, report["github_writes"])
        self.assertFalse(report["actual_ollama_model_independently_verified"])
        self.assertFalse(report["rootless_container_independently_attested"])
        self.assertFalse(report["persistent_worker_deployed"])
        self.assertFalse(report["production_source_patch_verified"])
        self.assertFalse(report["model_source_executed_on_controller"])
        self.assertEqual([_GOOD], self.syntax_calls)
        self.assertEqual([_GOOD], self.runtime_calls)
        self.assertEqual(_GOOD, (self.worktree / _PATH).read_text())
        self.assertFalse((self.repo / _PATH).exists())
        self.assertNotIn(_GOOD, json.dumps(report))
        self.assertNotIn(str(self.worktree), json.dumps(report))

    def test_failed_initial_behavior_fixed_second_candidate_written(self):
        self.sources = [_BAD, _GOOD]
        self.runtime_results = [_TFAIL, _TPASS]
        report = self.invoke()
        self.assertEqual(2, report["attempt_count"])
        self.assertTrue(report["repair_attempted"])
        self.assertEqual(_TFAIL, report["attempts"][0]["functional_status"])
        self.assertEqual(_TPASS, report["attempts"][1]["functional_status"])
        self.assertEqual(_BAD, self.model_calls[1]["previous_candidate"])
        self.assertEqual(_TFAIL, self.model_calls[1]["prior_result"])
        self.assertEqual(_GOOD, (self.worktree / _PATH).read_text())
        self.assertNotEqual(
            hashlib.sha256(_BAD.encode()).hexdigest(),
            report["written_candidate_sha256"],
        )

    def test_initial_syntax_invalid_repairs_and_writes_only_second(self):
        self.sources = [_BROKEN, _GOOD]
        self.syntax_results = [_SINVALID, _SVALID]
        self.runtime_results = [_TPASS]
        report = self.invoke()
        self.assertEqual(_SINVALID, report["attempts"][0]["syntax_status"])
        self.assertEqual("NOT_RUN", report["attempts"][0]["functional_status"])
        self.assertEqual(_SINVALID, self.model_calls[1]["prior_result"])
        self.assertEqual(1, len(self.runtime_calls))
        self.assertEqual(_GOOD, (self.worktree / _PATH).read_text())

    def test_two_functional_failures_leave_worktree_empty(self):
        self.sources = [_BAD, "def solve(x):\n    return x + 1\n"]
        self.runtime_results = [_TFAIL, _TFAIL]
        report = self.invoke()
        self.assertEqual("FIXTURE_UNRESOLVED_NO_WORKTREE_WRITE", report["status"])
        self.assertIsNone(report["written_candidate_sha256"])
        self.assertEqual(0, report["disposable_worktree_files_written"])
        self.assertFalse((self.worktree / _PATH).exists())

    def test_two_syntax_failures_leave_worktree_empty(self):
        self.sources = [_BROKEN, "def still_broken(\n"]
        self.syntax_results = [_SINVALID, _SINVALID]
        report = self.invoke()
        self.assertEqual(0, report["disposable_worktree_files_written"])
        self.assertEqual(0, len(self.runtime_calls))
        self.assertFalse((self.worktree / _PATH).exists())

    def test_repeated_invalid_model_candidate_is_denied_without_write(self):
        self.sources = [_BAD, _BAD]
        self.runtime_results = [_TFAIL, _TPASS]
        with self.assertRaises(VerifiedFixtureFlowDenied):
            self.invoke()
        self.assertEqual(1, len(self.runtime_calls))
        self.assertFalse((self.worktree / _PATH).exists())

    def test_syntax_receipt_wrong_sha_never_reaches_runtime_or_write(self):
        def forged(plan, source, scope, **kwargs):
            receipt = self.syntax(plan, source, scope, **kwargs)
            receipt["candidate_sha256"] = "a"*64
            return receipt
        with self.assertRaises(VerifiedFixtureFlowDenied):
            self.invoke(syntax_broker=forged)
        self.assertFalse(self.runtime_calls)
        self.assertFalse((self.worktree / _PATH).exists())

    def test_runtime_receipt_wrong_sha_cannot_approve_write(self):
        def forged(plan, source, scope, **kwargs):
            receipt = self.runtime(plan, source, scope, **kwargs)
            receipt["candidate_sha256"] = "b"*64
            return receipt
        with self.assertRaises(VerifiedFixtureFlowDenied):
            self.invoke(runtime_broker=forged)
        self.assertFalse((self.worktree / _PATH).exists())

    def test_container_transport_error_not_used_as_model_repair_feedback(self):
        def failing(*args, **kwargs):
            raise FixtureRuntimeDenied("PRIVATE-ROOTLESS-PATH")
        with self.assertRaises(VerifiedFixtureFlowDenied) as ex:
            self.invoke(runtime_broker=failing)
        self.assertNotIn("PRIVATE", str(ex.exception))
        self.assertEqual(1, len(self.model_calls))
        self.assertFalse((self.worktree / _PATH).exists())

    def test_existing_target_cannot_be_overwritten_after_test_pass(self):
        target = self.worktree / _PATH
        target.write_text("operator-owned original\n")
        with self.assertRaises(VerifiedFixtureFlowDenied):
            self.invoke()
        self.assertEqual("operator-owned original\n", target.read_text())
        self.assertEqual(1, len(self.runtime_calls))

    def test_malformed_worktree_head_refused_before_model_or_docker(self):
        original = (self.worktree / ".git").read_text()
        (self.worktree / ".git").write_text("gitdir: /tmp/different\n")
        with self.assertRaises(VerifiedFixtureFlowDenied):
            self.invoke()
        self.assertFalse(self.model_calls)
        self.assertFalse(self.syntax_calls)
        (self.worktree / ".git").write_text(original)

    def test_wrong_commit_refused_before_model_or_docker(self):
        with self.assertRaises(VerifiedFixtureFlowDenied):
            self.invoke(expected_commit_sha="f"*40)
        self.assertFalse(self.model_calls)
        self.assertFalse(self.syntax_calls)

    def test_unapproved_path_refused_before_model_or_docker(self):
        self.operator_plan = _plan(path="AGENTS.md")
        with self.assertRaises(VerifiedFixtureFlowDenied):
            self.invoke()
        self.assertFalse(self.model_calls)
        self.assertFalse(self.syntax_calls)

    def test_direct_replay_wont_overwrite_existing_file(self):
        self.invoke()
        with self.assertRaises(VerifiedFixtureFlowDenied):
            self.invoke()
        self.assertEqual(_GOOD, (self.worktree / _PATH).read_text())

    def test_model_identity_drift_or_tools_cannot_approve(self):
        def forged(base, payload):
            result = self.model(base, payload)
            obj = json.loads(result["message"]["content"])
            obj["path"] = "tests/fixtures/different.py"
            result["message"]["content"] = json.dumps(obj)
            return result
        with self.assertRaises(VerifiedFixtureFlowDenied):
            self.invoke(model_transport=forged)
        self.assertFalse(self.syntax_calls)
        self.assertFalse((self.worktree / _PATH).exists())

    def test_default_denies_missing_real_rootless_broker_before_inference(self):
        with patch("tools.verified_fixture_worktree_flow._docker_binary",
                   side_effect=DockerSyntaxDenied("not configured")):
            with self.assertRaises(VerifiedFixtureFlowDenied):
                self.invoke(syntax_broker=None)
        self.assertFalse(self.model_calls)

    def test_rootless_file_write_identity_cannot_be_model_supplied(self):
        # A wrongly chosen source repository is stopped before inference.
        with self.assertRaises(VerifiedFixtureFlowDenied):
            self.invoke(trusted_source_repo=self.worktree)
        self.assertFalse(self.model_calls)


class CrossPlatformDefaultDeniedTests(unittest.TestCase):
    def test_requires_exact_five_grants_without_inference_or_file_writes(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            scope = WorkspaceScope(root, "P00", "phase/00-governance",
                                   ("tests/fixtures",))
            for grants in (
                {}, {"enabled": True},
                {"enabled": True, "operator_ack": True},
                {"enabled": True, "operator_ack": True, "syntax_enabled": True},
                {"enabled": True, "operator_ack": True, "syntax_enabled": True,
                 "execution_grant": True},
                {"enabled": 1, "operator_ack": True, "syntax_enabled": True,
                 "execution_grant": True, "write_grant": True},
            ):
                with self.subTest(grants=grants), self.assertRaises(
                    VerifiedFixtureFlowDenied
                ):
                    run_verified_fixture_worktree_flow(
                        "coder:7b", _plan(), scope,
                        expected_task_id=_TASK,
                        expected_commit_sha="a"*40,
                        trusted_source_repo=root, controlled_root=root,
                        **grants,
                    )


if __name__ == "__main__":
    unittest.main()
