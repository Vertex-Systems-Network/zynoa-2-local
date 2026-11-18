"""Trusted PR table workflow and JSON GitHub contents transport regressions."""
from __future__ import annotations

import base64
import io
import json
import unittest
from pathlib import Path
from unittest.mock import patch

from tools.pr_task_board import TaskBoardError
from tools.pr_task_trusted_sync import _read_file_at_commit

ROOT = Path(__file__).resolve().parents[1]
SHA = "a" * 40


class _FakeResponse:
    status = 200
    def __init__(self, payload):
        self.payload = payload
    def __enter__(self):
        return self
    def __exit__(self, *args):
        return False
    def read(self, n):
        return self.payload[:n]


class _Opener:
    def __init__(self, payload):
        self.payload = payload
        self.requests = []
    def open(self, request, timeout):
        self.requests.append((request.full_url, request.get_method(), timeout))
        return _FakeResponse(self.payload)


class ContentsAPITests(unittest.TestCase):
    def test_reads_only_allowlisted_phase_file_at_exact_commit(self):
        original = {"phase": "P00", "primary_pr": 1}
        raw = base64.b64encode(json.dumps(original).encode()).decode()
        encoded = raw[:15] + "\n" + raw[15:] + "\n"
        payload = json.dumps({"encoding": "base64", "content": encoded}).encode()
        fake = _Opener(payload)
        with patch("tools.pr_task_trusted_sync.urllib.request.build_opener", return_value=fake):
            result = _read_file_at_commit("test-token", SHA, "docs/state/PHASE.json")
        self.assertEqual(original, result)
        self.assertEqual(1, len(fake.requests))
        self.assertIn("ref=" + SHA, fake.requests[0][0])
        self.assertEqual("GET", fake.requests[0][1])

    def test_rejects_nonallowlisted_paths_prior_to_fetch(self):
        for path in (
            ".github/workflows/governance.yml", "docs/state/../secrets",
            "docs/state/pr-tasks/../PHASE.json",
            "docs/state/pr-tasks/P99.json",
            "docs/state/PR_TASKS.json",
        ):
            with self.subTest(path=path), self.assertRaises(TaskBoardError):
                _read_file_at_commit("token", SHA, path)

    def test_invalid_base64_or_non_json_blocked(self):
        for result in (
            {"encoding": "base64", "content": "AAAA-not-base64!"},
            {"encoding": "utf-8", "content": "eyJ4IjoxfQ=="},
            {"encoding": "base64", "content": base64.b64encode(b"not-json").decode()},
        ):
            fake = _Opener(json.dumps(result).encode())
            with patch("tools.pr_task_trusted_sync.urllib.request.build_opener", return_value=fake):
                with self.assertRaises(TaskBoardError):
                    _read_file_at_commit("token", SHA, "docs/state/PHASE.json")


class WorkflowSafetyTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.workflow = (
            ROOT / ".github/workflows/pr-task-table-sync.yml"
        ).read_text(encoding="utf-8")

    def test_uses_only_trusted_main_code_and_workflow_run(self):
        s = self.workflow
        self.assertIn("workflow_run:", s)
        self.assertIn('workflows: ["Governance v3.2"]', s)
        self.assertIn("ref: main", s)
        self.assertNotIn("ref: ${{ github.event.workflow_run.head_sha }}", s)
        self.assertNotIn("pull_request_target:", s)

    def test_write_scope_limited_to_pr_description(self):
        s = self.workflow
        self.assertIn("pull-requests: write", s)
        self.assertIn("contents: read", s)
        self.assertNotIn("contents: write", s)
        self.assertNotIn("issues: write", s)
        self.assertIn("persist-credentials: false", s)

    def test_runs_only_successful_same_repository_pr(self):
        s = self.workflow
        self.assertIn("workflow_run.conclusion == 'success'", s)
        self.assertIn("workflow_run.event == 'pull_request'", s)
        self.assertIn("workflow_run.head_repository.full_name == github.repository", s)


if __name__ == "__main__":
    unittest.main()
