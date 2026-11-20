"""P00 two-pass fixture syntax-only repair: all provider and Docker calls are mocked.

Never run model-generated code here. The real operator must independently
authorize the already restricted rootless Docker syntax broker on Linux.
"""
from __future__ import annotations

import copy
import hashlib
import json
import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch

from tools.dev_fixture_repair_loop import FixtureRepairDenied, run_fixture_syntax_repair
from tools.docker_syntax_broker import DEFAULT_IMAGE, DockerSyntaxDenied
from tools.local_fixture_drafter import make_fixture_request
from tools.workspace_policy import WorkspaceScope

MODEL = "coder:7b"
TASK = "P00-T20"
FILE = "tests/fixtures/model-repair.py"
BROKEN = "def broken(\n"
FIXED = "answer = 2\n"
_VALID = "PYTHON_SYNTAX_VALID_NO_CODE_EXECUTION"
_INVALID = "PYTHON_SYNTAX_INVALID_NO_CODE_EXECUTION"


class FixtureRepairTests(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        self.addCleanup(self.tmp.cleanup)
        self.root = Path(self.tmp.name)
        (self.root / "tests/fixtures").mkdir(parents=True)
        self.scope = WorkspaceScope(self.root, "P00", "phase/00-governance",
                                    ("tests/fixtures",))
        self.model_calls = []
        self.syntax_calls = []
        self.model_sources = [BROKEN, FIXED]
        self.syntax_statuses = [_INVALID, _VALID]

    def plan(self):
        return {
            "schema_version": 1, "phase": "P00",
            "branch": "phase/00-governance", "task_id": TASK,
            "summary": "Repair one small disposable fixture",
            "file_proposals": [{
                "path": FILE, "action": "DRAFT_ONLY",
                "reason": "Validate tiny Python syntax in isolation",
            }],
            "checks": ["phase-policy"],
        }

    def model(self, base, request):
        self.model_calls.append((base, copy.deepcopy(request)))
        assert base == "http://127.0.0.1:11434"
        context = json.loads(request["messages"][1]["content"])
        _, _, _, digest = make_fixture_request(
            MODEL, self.plan(), self.scope, expected_task_id=TASK
        )
        assert context["plan_sha256"] == digest
        assert context["path"] == FILE
        assert "tools" not in request
        source = self.model_sources[min(len(self.model_calls) - 1,
                                        len(self.model_sources) - 1)]
        return {
            "model": MODEL, "done": True, "done_reason": "stop",
            "message": {"role": "assistant", "content": json.dumps({
                "schema_version": 1, "phase": "P00",
                "branch": "phase/00-governance", "task_id": TASK,
                "plan_sha256": digest, "path": FILE, "source": source,
            })},
        }

    def syntax(self, plan, candidate, scope, **kwargs):
        self.syntax_calls.append((copy.deepcopy(plan), candidate, scope, kwargs))
        index = len(self.syntax_calls) - 1
        return {
            "status": self.syntax_statuses[min(index, len(self.syntax_statuses) - 1)],
            "phase": "P00", "task_id": TASK,
            "candidate_sha256": hashlib.sha256(candidate.encode()).hexdigest(),
            "image_digest": DEFAULT_IMAGE.split("@", 1)[1],
            "docker_commands_executed": 4, "rootless_daemon_status_observed": True,
            "model_source_executed": False, "workspace_files_written": 0,
            "github_writes": 0, "independent_host_sandbox_verified": False,
            "persistent_worker_deployed": False,
        }

    def execute(self, **kwargs):
        return run_fixture_syntax_repair(
            MODEL, self.plan(), self.scope,
            expected_task_id=TASK,
            enabled=True, operator_ack=True, syntax_enabled=True,
            model_transport=self.model, syntax_broker=self.syntax,
            **kwargs,
        )

    def test_invalid_first_then_repaired_second_via_local_model(self):
        before = {p.relative_to(self.root): p.read_bytes()
                  for p in self.root.rglob("*") if p.is_file()}
        result = self.execute()
        self.assertEqual("FIXTURE_SYNTAX_VALID_NO_CODE_EXECUTION", result["status"])
        self.assertEqual(2, result["attempt_count"])
        self.assertTrue(result["repair_attempted"])
        self.assertEqual(2, len(result["attempts"]))
        self.assertEqual(2, len(self.model_calls))
        self.assertEqual(2, len(self.syntax_calls))
        self.assertEqual(_INVALID, result["attempts"][0]["syntax_status"])
        self.assertEqual(_VALID, result["attempts"][1]["syntax_status"])
        p0 = json.loads(self.model_calls[0][1]["messages"][1]["content"])
        p1 = json.loads(self.model_calls[1][1]["messages"][1]["content"])
        self.assertNotIn("previous_candidate", p0)
        self.assertEqual(BROKEN, p1["previous_candidate"])
        self.assertEqual(_INVALID, p1["prior_result"])
        self.assertEqual(p0["plan_sha256"], p1["plan_sha256"])
        self.assertEqual(p0["path"], p1["path"])
        self.assertEqual([BROKEN, FIXED], [x[1] for x in self.syntax_calls])
        for plan, _candidate, scope, opts in self.syntax_calls:
            self.assertEqual(self.plan(), plan)
            self.assertIs(self.scope, scope)
            self.assertIs(opts["enabled"], True)
            self.assertEqual(TASK, opts["expected_task_id"])
            self.assertNotIn("command", opts)
            self.assertNotIn("mounts", opts)
        self.assertFalse(result["independent_host_sandbox_verified"])
        self.assertFalse(result["actual_model_runtime_independently_verified"])
        self.assertFalse(result["autonomous_plan_edit_test_repair_verified"])
        self.assertFalse(result["model_source_executed"])
        self.assertEqual(0, result["patches_applied"])
        self.assertEqual(0, result["github_writes"])
        self.assertEqual(0, result["workspace_files_written"])
        self.assertNotIn(BROKEN, json.dumps(result))
        self.assertNotIn(FIXED, json.dumps(result))
        self.assertEqual(
            before, {p.relative_to(self.root): p.read_bytes()
                     for p in self.root.rglob("*") if p.is_file()}
        )

    def test_one_valid_candidate_does_not_retry(self):
        self.model_sources = [FIXED]
        self.syntax_statuses = [_VALID]
        result = self.execute()
        self.assertEqual(1, result["attempt_count"])
        self.assertFalse(result["repair_attempted"])
        self.assertEqual(1, len(self.model_calls))
        self.assertEqual(1, len(self.syntax_calls))

    def test_second_invalid_candidate_stops_at_fixed_bound(self):
        self.model_sources = [BROKEN, "def still_broken(\n"]
        self.syntax_statuses = [_INVALID, _INVALID]
        result = self.execute()
        self.assertEqual("FIXTURE_SYNTAX_UNRESOLVED_AFTER_REPAIR", result["status"])
        self.assertEqual(2, result["attempt_count"])
        self.assertEqual(2, result["max_attempts"])
        self.assertEqual(2, len(self.model_calls))
        self.assertEqual(2, len(self.syntax_calls))

    def test_model_repeating_invalid_candidate_is_denied(self):
        self.model_sources = [BROKEN, BROKEN]
        self.syntax_statuses = [_INVALID, _VALID]
        with self.assertRaises(FixtureRepairDenied):
            self.execute()
        self.assertEqual(2, len(self.model_calls))
        self.assertEqual(1, len(self.syntax_calls))

    def test_default_refuses_before_any_model_or_docker_activity(self):
        for opts in (
            {}, {"enabled": True},
            {"operator_ack": True}, {"syntax_enabled": True},
            {"enabled": True, "operator_ack": True},
            {"enabled": True, "syntax_enabled": True},
            {"operator_ack": True, "syntax_enabled": True},
            {"enabled": 1, "operator_ack": True, "syntax_enabled": True},
        ):
            with self.subTest(opts=opts), self.assertRaises(FixtureRepairDenied):
                run_fixture_syntax_repair(
                    MODEL, self.plan(), self.scope,
                    expected_task_id=TASK, model_transport=self.model,
                    syntax_broker=self.syntax, **opts,
                )
        self.assertEqual([], self.model_calls)
        self.assertEqual([], self.syntax_calls)

    def test_preflight_bad_phase_task_path_and_model_deny_without_calls(self):
        for patch_plan in (
            {"phase": "P01"}, {"branch": "main"}, {"task_id": "P00-T19"},
            {"file_proposals": []},
            {"file_proposals": [
                {"path": "AGENTS.md", "action": "DRAFT_ONLY", "reason": "bad"}
            ]},
            {"file_proposals": [
                {"path": "tests/fixtures/out.js", "action": "DRAFT_ONLY", "reason": "bad"}
            ]},
            {"file_proposals": self.plan()["file_proposals"] * 2},
        ):
            p = self.plan()
            p.update(patch_plan)
            with self.subTest(patch=patch_plan), self.assertRaises(FixtureRepairDenied):
                run_fixture_syntax_repair(
                    MODEL, p, self.scope, expected_task_id=TASK,
                    enabled=True, operator_ack=True, syntax_enabled=True,
                    model_transport=self.model, syntax_broker=self.syntax,
                )
        for task in ("P01-T20", "P00-T19", "P00-T26", ""):
            with self.subTest(task=task), self.assertRaises(FixtureRepairDenied):
                run_fixture_syntax_repair(
                    MODEL, self.plan(), self.scope, expected_task_id=task,
                    enabled=True, operator_ack=True, syntax_enabled=True,
                    model_transport=self.model, syntax_broker=self.syntax,
                )
        self.assertEqual([], self.model_calls)
        self.assertEqual([], self.syntax_calls)

    def test_missing_rootless_host_fails_before_model_inference(self):
        with patch("tools.dev_fixture_repair_loop._docker_binary",
                   side_effect=DockerSyntaxDenied("missing")):
            with self.assertRaises(FixtureRepairDenied):
                run_fixture_syntax_repair(
                    MODEL, self.plan(), self.scope, expected_task_id=TASK,
                    enabled=True, operator_ack=True, syntax_enabled=True,
                    model_transport=self.model,
                )
        self.assertFalse(self.model_calls)

    def test_invalid_model_content_never_retries_or_runs_broker(self):
        def invalid(base, request):
            self.model_calls.append((base, request))
            return {"done": False}
        with self.assertRaises(FixtureRepairDenied):
            run_fixture_syntax_repair(
                MODEL, self.plan(), self.scope, expected_task_id=TASK,
                enabled=True, operator_ack=True, syntax_enabled=True,
                model_transport=invalid, syntax_broker=self.syntax,
            )
        self.assertEqual(1, len(self.model_calls))
        self.assertEqual([], self.syntax_calls)

    def test_syntax_transport_failure_never_retries_or_leaks_error(self):
        secret = "DOCKER_SECRET_NOT_PUBLIC"
        def fail(*args, **kwargs):
            self.syntax_calls.append(1)
            raise DockerSyntaxDenied(secret)
        with self.assertRaises(FixtureRepairDenied) as caught:
            run_fixture_syntax_repair(
                MODEL, self.plan(), self.scope, expected_task_id=TASK,
                enabled=True, operator_ack=True, syntax_enabled=True,
                model_transport=self.model, syntax_broker=fail,
            )
        self.assertNotIn(secret, str(caught.exception))
        self.assertEqual(1, len(self.model_calls))
        self.assertEqual(1, len(self.syntax_calls))

    def test_forged_broker_receipts_cannot_be_success(self):
        cases = [
            ("status", "VALID"),
            ("phase", "P01"), ("task_id", "P00-T19"),
            ("candidate_sha256", "0" * 64),
            ("image_digest", "sha256:" + "a" * 64),
            ("docker_commands_executed", True),
            ("rootless_daemon_status_observed", "true"),
            ("workspace_files_written", True), ("workspace_files_written", 1),
            ("github_writes", 1), ("model_source_executed", True),
            ("independent_host_sandbox_verified", True),
            ("persistent_worker_deployed", True),
        ]
        self.syntax_statuses = [_VALID]
        for key, value in cases:
            self.model_calls.clear()
            self.syntax_calls.clear()
            def forged(*args, **kwargs):
                v = self.syntax(*args, **kwargs)
                v[key] = value
                return v
            with self.subTest(field=key, value=value), self.assertRaises(FixtureRepairDenied):
                run_fixture_syntax_repair(
                    MODEL, self.plan(), self.scope, expected_task_id=TASK,
                    enabled=True, operator_ack=True, syntax_enabled=True,
                    model_transport=self.model, syntax_broker=forged,
                )
            self.assertEqual(1, len(self.model_calls))
            self.assertEqual(1, len(self.syntax_calls))

    def test_no_shell_or_source_execution_even_with_hostile_fixture_text(self):
        self.model_sources = ["import subprocess\nsubprocess.run(['echo','unsafe'])\n"]
        self.syntax_statuses = [_VALID]
        with patch("subprocess.Popen") as process:
            result = self.execute()
        process.assert_not_called()
        self.assertEqual("FIXTURE_SYNTAX_VALID_NO_CODE_EXECUTION", result["status"])
        self.assertEqual(0, result["patches_applied"])
        self.assertFalse((self.root / FILE).exists())

    def test_existing_model_source_repair_prompt_limits(self):
        plan = self.plan()
        req, _, _, _ = make_fixture_request(
            MODEL, plan, self.scope, expected_task_id=TASK,
            repair_source=BROKEN,
        )
        msg = json.loads(req["messages"][1]["content"])
        self.assertEqual(BROKEN, msg["previous_candidate"])
        self.assertEqual(_INVALID, msg["prior_result"])
        self.assertNotIn("tools", req)
        self.assertNotIn(str(self.root), json.dumps(req))
        self.assertTrue(req["stream"] is False)
        for bad in ("", "x" * 8193, "x\x00", "x\r",
                    "x" + chr(0x202e), "Cafe" + chr(0x301)):
            with self.subTest(size=len(bad)), self.assertRaises(Exception):
                make_fixture_request(
                    MODEL, plan, self.scope, expected_task_id=TASK,
                    repair_source=bad,
                )

    def test_tampered_second_candidate_identity_cannot_succeed(self):
        def malicious(base, request):
            result = self.model(base, request)
            if len(self.model_calls) == 2:
                parsed = json.loads(result["message"]["content"])
                parsed["path"] = "tests/fixtures/attacker.py"
                result["message"]["content"] = json.dumps(parsed)
            return result
        with self.assertRaises(FixtureRepairDenied):
            run_fixture_syntax_repair(
                MODEL, self.plan(), self.scope, expected_task_id=TASK,
                enabled=True, operator_ack=True, syntax_enabled=True,
                model_transport=malicious, syntax_broker=self.syntax,
            )
        self.assertEqual(2, len(self.model_calls))
        self.assertEqual(1, len(self.syntax_calls))


if __name__ == "__main__":
    unittest.main()
