"""P00 local model-authored fixture preview; no model, Docker or GitHub network in tests."""
from __future__ import annotations

import copy
import hashlib
import json
import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch

from tools.dev_model_planner import make_model_request
from tools.docker_syntax_broker import DockerSyntaxDenied, plan_python_syntax, run_python_syntax
from tools.local_fixture_drafter import (
    LocalFixtureDenied, LocalFixtureDraft, draft_local_fixture, make_fixture_request,
)
from tools.workspace_policy import WorkspaceScope


MODEL = "coder:7b"
TASK = "P00-T20"
FILE = "tests/fixtures/model-regression.py"
SOURCE = "answer = 42\n"


class FixtureModelTests(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory()
        self.addCleanup(self.temp.cleanup)
        self.root = Path(self.temp.name)
        (self.root / "tests" / "fixtures").mkdir(parents=True)
        self.scope = WorkspaceScope(
            self.root, "P00", "phase/00-governance", ("tests/fixtures",)
        )
        self.calls = []

    def plan(self):
        return {
            "schema_version": 1, "phase": "P00",
            "branch": "phase/00-governance", "task_id": TASK,
            "summary": "Prepare a limited regression fixture",
            "file_proposals": [{
                "path": FILE, "action": "DRAFT_ONLY",
                "reason": "Candidate fixture for isolated syntax review",
            }],
            "checks": ["phase-policy"],
        }

    def answer(self, source=SOURCE, **overrides):
        payload, _, _, digest = make_fixture_request(
            MODEL, self.plan(), self.scope, expected_task_id=TASK
        )
        result = {
            "schema_version": 1, "phase": "P00",
            "branch": "phase/00-governance", "task_id": TASK,
            "plan_sha256": digest, "path": FILE, "source": source,
        }
        result.update(overrides)
        return {
            "model": MODEL, "done": True, "done_reason": "stop",
            "message": {"role": "assistant", "content": json.dumps(result)},
        }

    def transport(self, base, request):
        self.calls.append((base, request))
        return self.answer()

    def run(self, **kwargs):
        return draft_local_fixture(
            MODEL, self.plan(), self.scope, expected_task_id=TASK,
            transport=self.transport, **kwargs
        )

    def test_schema_request_is_loopback_only_without_repos_or_tools(self):
        req, plan, path, digest = make_fixture_request(
            MODEL, self.plan(), self.scope, expected_task_id=TASK
        )
        self.assertEqual(FILE, path)
        self.assertEqual(64, len(digest))
        self.assertEqual("P00", plan["phase"])
        self.assertFalse(req["stream"])
        self.assertEqual(0, req["options"]["temperature"])
        self.assertEqual(FILE, req["format"]["properties"]["path"]["const"])
        self.assertEqual(digest, req["format"]["properties"]["plan_sha256"]["const"])
        self.assertEqual({"role", "content"}, set(req["messages"][0]))
        self.assertNotIn("tools", req)
        self.assertNotIn(str(self.root), json.dumps(req))
        self.assertNotIn(SOURCE, json.dumps(req))
        self.assertIn("DRAFT_ONLY", json.dumps(self.plan()))
        self.assertNotIn("shell", str(req["format"]))

    def test_successful_generated_content_is_in_memory_only(self):
        before = {p.relative_to(self.root): p.read_bytes()
                  for p in self.root.rglob("*") if p.is_file()}
        draft = self.run()
        receipt = draft.safe_receipt()
        self.assertIsInstance(draft, LocalFixtureDraft)
        self.assertEqual(SOURCE, draft.source)
        self.assertEqual(FILE, draft.path)
        self.assertEqual(hashlib.sha256(SOURCE.encode()).hexdigest(),
                         receipt["candidate_sha256"])
        self.assertEqual("MODEL_FIXTURE_TEXT_PREVIEW_ONLY", receipt["status"])
        self.assertEqual(0, receipt["workspace_files_written"])
        self.assertEqual(0, receipt["github_writes"])
        self.assertFalse(receipt["model_source_executed"])
        self.assertFalse(receipt["os_sandbox_verified"])
        self.assertFalse(receipt["real_local_model_runtime_verified"])
        self.assertFalse(receipt["autonomous_repair_loop_verified"])
        self.assertEqual([("http://127.0.0.1:11434", self.calls[0][1])],
                         self.calls)
        self.assertNotIn(SOURCE, repr(draft))
        self.assertNotIn(SOURCE, json.dumps(receipt))
        self.assertEqual(before, {p.relative_to(self.root): p.read_bytes()
                                  for p in self.root.rglob("*") if p.is_file()})
        self.assertFalse((self.root / FILE).exists())
        self.assertEqual([], list(self.root.glob("**/zynoa-p00-fixture-preview-*")))

    def test_inert_source_can_be_forwarded_only_to_separate_syntax_broker(self):
        def mock(base, request):
            return self.answer(source="import os\nos.system('echo unsafe')\n")
        draft = draft_local_fixture(
            MODEL, self.plan(), self.scope, expected_task_id=TASK,
            transport=mock,
        )
        with patch("tools.docker_syntax_broker._invoker") as runner:
            job = plan_python_syntax(
                draft.plan, draft.source, self.scope, expected_task_id=TASK
            )
            self.assertEqual(draft.candidate_sha256, job.candidate_sha256)
            self.assertEqual(job.data, draft.source.encode())
            with self.assertRaises(DockerSyntaxDenied):
                run_python_syntax(
                    draft.plan, draft.source, self.scope, expected_task_id=TASK
                )
            runner.assert_not_called()
        self.assertFalse((self.root / FILE).exists())

    def test_endpoint_must_be_explicit_loopback(self):
        for url in (
            "https://127.0.0.1:11434", "http://localhost:11434",
            "http://192.168.1.2:11434", "http://example.org",
            "http://127.0.0.1:11434/proxy", "http://127.0.0.1:11434#fragment",
            "http://user:pass@127.0.0.1:11434",
        ):
            with self.subTest(url=url), self.assertRaises(LocalFixtureDenied):
                self.run(endpoint=url)
        self.assertEqual([], self.calls)

    def test_model_and_plan_preconditions_fail_before_network(self):
        for plan_change in (
            {"phase": "P01"}, {"branch": "main"}, {"task_id": "P00-T19"},
            {"file_proposals": []},
            {"file_proposals": self.plan()["file_proposals"] * 2},
            {"file_proposals": [{
                "path": "AGENTS.md", "action": "DRAFT_ONLY", "reason": "no"
            }]},
            {"file_proposals": [{
                "path": "tests/fixtures/nested/test.py",
                "action": "DRAFT_ONLY", "reason": "no",
            }]},
            {"file_proposals": [{
                "path": "tests/fixtures/output.txt",
                "action": "DRAFT_ONLY", "reason": "no",
            }]},
        ):
            p = self.plan()
            p.update(plan_change)
            with self.subTest(change=plan_change), self.assertRaises(LocalFixtureDenied):
                draft_local_fixture(
                    MODEL, p, self.scope, expected_task_id=TASK,
                    transport=self.transport,
                )
        for t in ("P00-T19", "P00-T26", "P01-T20", ""):
            with self.subTest(task=t), self.assertRaises(LocalFixtureDenied):
                draft_local_fixture(
                    MODEL, self.plan(), self.scope, expected_task_id=t,
                    transport=self.transport,
                )
        self.assertEqual([], self.calls)

    def test_invalid_model_name_fails_before_network(self):
        for name in ("../../secrets", "coder//7b", "coder/../secret", "model with spaces"):
            with self.subTest(model=name), self.assertRaises(LocalFixtureDenied):
                draft_local_fixture(
                    name, self.plan(), self.scope,
                    expected_task_id=TASK, transport=self.transport,
                )
        self.assertEqual([], self.calls)

    def test_identity_and_extra_fields_are_denied(self):
        mutations = (
            {"task_id": "P00-T19"},
            {"branch": "main"},
            {"phase": "P01"},
            {"path": "tests/fixtures/other.py"},
            {"plan_sha256": "a" * 64},
            {"schema_version": True},
            {"command": "merge now"},
        )
        for changed in mutations:
            self.calls.clear()
            def bad(_base, _request):
                env = self.answer(**changed)
                return env
            with self.subTest(changed=changed), self.assertRaises(LocalFixtureDenied):
                draft_local_fixture(
                    MODEL, self.plan(), self.scope,
                    expected_task_id=TASK, transport=bad,
                )
            self.assertFalse((self.root / FILE).exists())

    def test_response_envelope_and_tool_calls_are_denied(self):
        templates = [
            {"done": False},
            {"done": "true"},
            {"done_reason": "length"},
            {"model": "different:7b"},
            {"tool_calls": []},
            {"message": {"role": "tool", "content": "{}"}},
            {"message": {"role": "assistant", "tool_calls": [],
                         "content": "{}"}},
            {"message": {"role": "assistant", "content": 2}},
        ]
        for changed in templates:
            env = self.answer()
            env.update(changed)
            with self.subTest(changed=changed), self.assertRaises(LocalFixtureDenied):
                draft_local_fixture(
                    MODEL, self.plan(), self.scope,
                    expected_task_id=TASK,
                    transport=lambda _base, _payload: copy.deepcopy(env),
                )

    def test_invalid_json_duplicate_keys_and_oversized_response_denied(self):
        for content in (
            "{bad json",
            '{"schema_version":1,"schema_version":1}',
            "{" + " " * 33000 + "}",
            'null', '[1,2]', '{ "source": "ignored" }',
        ):
            env = self.answer()
            env["message"]["content"] = content
            with self.subTest(content=content[:50]), self.assertRaises(LocalFixtureDenied):
                draft_local_fixture(
                    MODEL, self.plan(), self.scope, expected_task_id=TASK,
                    transport=lambda _base, _payload: env,
                )

    def test_untrusted_unicode_text_and_limits_fail_closed(self):
        for source in (
            "", "a" * 8193, "x\x00", "x\r", "x" + chr(0x202e),
            "Cafe" + chr(0x301), ("hello\n" * 201),
        ):
            with self.subTest(size=len(source)), self.assertRaises(LocalFixtureDenied):
                draft_local_fixture(
                    MODEL, self.plan(), self.scope,
                    expected_task_id=TASK,
                    transport=lambda _base, _payload: self.answer(source=source),
                )

    def test_symlink_under_fixture_directory_denied(self):
        link = self.root / FILE
        outside = self.root.parent / "independent-outside.txt"
        outside.write_text("not user data\n")
        self.addCleanup(lambda: outside.unlink(missing_ok=True))
        try:
            link.symlink_to(outside)
        except (NotImplementedError, OSError):
            self.skipTest("symlinks unavailable")
        with self.assertRaises(LocalFixtureDenied):
            self.run()
        self.assertEqual([], self.calls)

    def test_transport_failure_never_leaks_exception_or_creates_file(self):
        secret = "TOKEN-PRIVATE-MUST-NOT-ECHO"
        def offline(_base, _payload):
            raise OSError(secret)
        with self.assertRaises(LocalFixtureDenied) as cm:
            draft_local_fixture(
                MODEL, self.plan(), self.scope,
                expected_task_id=TASK, transport=offline,
            )
        self.assertNotIn(secret, str(cm.exception))
        self.assertFalse((self.root / FILE).exists())


if __name__ == "__main__":
    unittest.main()
