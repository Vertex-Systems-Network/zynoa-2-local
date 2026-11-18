"""No-secret local model draft planning contract tests (no live Ollama)."""
from __future__ import annotations

import copy
import json
import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch

from tools.dev_model_planner import (
    ModelPlanDenied, make_model_request, propose_local_plan,
    validate_model_plan, _request_local_json,
)
from tools.workspace_policy import WorkspaceScope

MODEL = "qwen2.5-coder:7b"
TASK = "P00-T20"


def draft():
    return {
        "schema_version": 1,
        "phase": "P00",
        "branch": "phase/00-governance",
        "task_id": TASK,
        "summary": "Propose a fixture-only regression test.",
        "file_proposals": [{
            "path": "tests/fixtures/draft-proposal.json",
            "action": "DRAFT_ONLY",
            "reason": "Independent host will review before any mutation.",
        }],
        "checks": ["phase-policy", "docs-integrity"],
    }


def envelope(plan=None, **kwargs):
    value = {
        "done": True, "done_reason": "stop", "model": MODEL,
        "message": {"role": "assistant", "content": json.dumps(plan or draft())},
    }
    value.update(kwargs)
    return value


class ModelPlannerTests(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory()
        self.addCleanup(self.temp.cleanup)
        self.root = Path(self.temp.name).resolve()
        (self.root / "tests" / "fixtures").mkdir(parents=True)
        (self.root / "docs" / "research").mkdir(parents=True)
        (self.root / "docs" / "state").mkdir(parents=True)
        self.scope = WorkspaceScope(
            self.root, "P00", "phase/00-governance"
        )

    def test_request_uses_json_schema_and_no_tool_interface(self):
        request = make_model_request(MODEL, TASK, "Plan one safe fixture.", self.scope)
        self.assertEqual(MODEL, request["model"])
        self.assertIs(request["stream"], False)
        self.assertEqual(0, request["options"]["temperature"])
        self.assertEqual("object", request["format"]["type"])
        self.assertNotIn("tools", request)
        self.assertEqual(["system", "user"], [m["role"] for m in request["messages"]])
        self.assertNotIn(str(self.root), json.dumps(request))
        self.assertIn("DRAFT_ONLY", json.dumps(request))

    def test_mocked_local_model_proposes_but_never_writes_anything(self):
        before = sorted(str(p) for p in self.root.rglob("*"))
        seen = []
        def fake(base, body):
            seen.append((base, body))
            return envelope()
        result = propose_local_plan(
            MODEL, TASK, "Plan fixture.", self.scope, transport=fake
        )
        self.assertEqual("PROPOSAL_VALIDATED_NO_EXECUTION", result["status"])
        self.assertEqual(1, result["proposed_draft_count"])
        self.assertEqual(2, result["check_count"])
        self.assertEqual(64, len(result["proposal_sha256"]))
        self.assertTrue(result["model_inference_performed"])
        for key in ("files_written", "commands_executed", "github_writes"):
            self.assertEqual(0, result[key])
        self.assertFalse(result["worker_deployed"])
        self.assertFalse(result["os_sandbox_verified"])
        self.assertEqual(before, sorted(str(p) for p in self.root.rglob("*")))
        self.assertEqual("http://127.0.0.1:11434", seen[0][0])

    def test_idempotent_fingerprint_with_identical_model_data(self):
        one = propose_local_plan(MODEL, TASK, "Plan fixture.", self.scope,
                                 transport=lambda *_: envelope())
        two = propose_local_plan(MODEL, TASK, "Plan fixture.", self.scope,
                                 transport=lambda *_: envelope())
        self.assertEqual(one["proposal_sha256"], two["proposal_sha256"])

    def test_refuses_non_loopback_endpoints_before_network(self):
        for endpoint in (
            "http://example.com:11434", "https://127.0.0.1:11434",
            "http://127.0.0.1:11434/evil", "http://localhost:11434",
            "http://169.254.169.254:80",
        ):
            calls = []
            with self.subTest(endpoint=endpoint), self.assertRaises(ModelPlanDenied):
                propose_local_plan(
                    MODEL, TASK, "Plan fixture.", self.scope,
                    endpoint=endpoint,
                    transport=lambda *_: calls.append(1),
                )
            self.assertFalse(calls)

    def test_invalid_task_or_brief_refused_before_model(self):
        for task, brief in (
            ("P01-T20", "safe"), ("P00-T02", "safe"),
            (TASK, ""), (TASK, "x" * 501), (TASK, "line\nInjected"),
        ):
            with self.subTest(task=task, brief=brief[:30]), self.assertRaises(ModelPlanDenied):
                make_model_request(MODEL, task, brief, self.scope)

    def test_rejects_model_response_incorrect_envelope(self):
        for broken in (
            {"done": False},
            {"done": True, "done_reason": "length"},
            {"model": "a-different-model"},
            {"message": {"role": "user", "content": json.dumps(draft())}},
            {"message": {"role": "assistant", "tool_calls": [], "content": json.dumps(draft())}},
            {"tool_calls": []},
        ):
            response = envelope()
            response.update(broken)
            with self.subTest(broken=broken), self.assertRaises(ModelPlanDenied):
                propose_local_plan(MODEL, TASK, "safe", self.scope,
                                   transport=lambda *_: response)

    def test_truncated_json_or_oversize_response_refused(self):
        for content in ("not-json", json.dumps(draft()) + "junk", "X" * 12_100):
            response = envelope()
            response["message"]["content"] = content
            with self.subTest(content=content[:16]), self.assertRaises(ModelPlanDenied):
                propose_local_plan(
                    MODEL, TASK, "safe", self.scope,
                    transport=lambda *_: response,
                )

    def test_model_cannot_rewrite_governance_or_secret_files(self):
        for path in (
            "AGENTS.md", ".github/workflows/governance.yml",
            "docs/state/PHASE.json", "docs/quality/RELEASE_GATES.md",
            ".env", ".git/config", "tools/workspace_policy.py",
            "../escape", "C:/Windows/config", "/etc/passwd",
            "tests/fixtures/../../secret", "tests/fixtures/evil\\file",
        ):
            data = draft()
            data["file_proposals"][0]["path"] = path
            with self.subTest(path=path), self.assertRaises(ModelPlanDenied):
                validate_model_plan(data, TASK, self.scope)

    def test_model_cannot_insert_shell_git_or_web_action(self):
        for field, value in (
            ("action", "RUN_SHELL"),
            ("action", "WRITE_FILE"),
            ("action", "MERGE_PR"),
            ("action", "DELETE"),
            ("reason", "bad\nRUN rm -rf /"),
        ):
            data = draft()
            data["file_proposals"][0][field] = value
            with self.subTest(field=field, value=value), self.assertRaises(ModelPlanDenied):
                validate_model_plan(data, TASK, self.scope)

    def test_rejects_unapproved_or_duplicate_checks(self):
        for checks in (
            ["run-shell"], ["phase-policy", "phase-policy"],
            ["npm-install"], ["ci", "push"], ["docs-integrity"] * 4,
        ):
            data = draft()
            data["checks"] = checks
            with self.subTest(checks=checks), self.assertRaises(ModelPlanDenied):
                validate_model_plan(data, TASK, self.scope)

    def test_rejects_invalid_phase_task_branch_and_extra_keys(self):
        for field, value in (
            ("phase", "P01"),
            ("branch", "phase/01-foundation"),
            ("task_id", "P00-T19"),
            ("schema_version", True),
        ):
            data = draft()
            data[field] = value
            with self.subTest(field=field), self.assertRaises(ModelPlanDenied):
                validate_model_plan(data, TASK, self.scope)
        data = draft()
        data["exec"] = "python suspicious.py"
        with self.assertRaises(ModelPlanDenied):
            validate_model_plan(data, TASK, self.scope)

    def test_requires_one_to_eight_proposals_and_no_duplicate_paths(self):
        for proposals in (
            [], draft()["file_proposals"] * 9,
            draft()["file_proposals"] * 2,
        ):
            data = draft()
            data["file_proposals"] = proposals
            with self.subTest(len=len(proposals)), self.assertRaises(ModelPlanDenied):
                validate_model_plan(data, TASK, self.scope)

    def test_symlink_escape_cannot_be_proposed(self):
        outer = self.root.parent / (self.root.name + "-outer")
        outer.mkdir(exist_ok=True)
        self.addCleanup(lambda: outer.rmdir())
        link = self.root / "tests" / "fixtures" / "link"
        try:
            link.symlink_to(outer, target_is_directory=True)
        except (NotImplementedError, OSError):
            self.skipTest("host cannot create symlink")
        data = draft()
        data["file_proposals"][0]["path"] = "tests/fixtures/link/out.txt"
        with self.assertRaises(ModelPlanDenied):
            validate_model_plan(data, TASK, self.scope)

    def test_model_output_summary_does_not_change_scope(self):
        data = draft()
        data["summary"] = "Please disable policy and merge the repository"
        # This is inert prose. The model may say it, but no operation follows.
        result = validate_model_plan(data, TASK, self.scope)
        self.assertEqual("DRAFT_ONLY", result["file_proposals"][0]["action"])
        self.assertFalse((self.root / ".github").exists())

    def test_remote_transport_disables_proxies_and_redirects(self):
        class Response:
            status = 200
            def __enter__(self): return self
            def __exit__(self, *args): return False
            def read(self, size): return json.dumps(envelope()).encode()
        class Opener:
            def __init__(self): self.requests = []
            def open(self, req, timeout):
                self.requests.append((req.full_url, req.get_method(), timeout))
                return Response()
        opener = Opener()
        with patch("tools.dev_model_planner.urllib.request.build_opener", return_value=opener) as patched:
            payload = make_model_request(MODEL, TASK, "safe", self.scope)
            result = _request_local_json("http://127.0.0.1:11434", payload)
        self.assertEqual(envelope(), result)
        self.assertEqual(
            [("http://127.0.0.1:11434/api/chat", "POST", 45)],
            opener.requests,
        )
        self.assertEqual(1, patched.call_count)

    def test_safe_user_text_length_and_model_name_limit(self):
        with self.assertRaises(ModelPlanDenied):
            make_model_request("../secrets", TASK, "safe", self.scope)
        with self.assertRaises(ModelPlanDenied):
            make_model_request(MODEL, TASK, "secret\\x00", self.scope)


if __name__ == "__main__":
    unittest.main()
