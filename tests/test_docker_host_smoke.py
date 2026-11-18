"""P00 operator-only syntax smoke: mocked backend, no real Docker launch."""
import copy
import hashlib
import json
import os
import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch

from tools.docker_host_smoke import (
    HostSmokeDenied, _CASES, _TASK, _trusted_scope, run_host_syntax_smoke,
)
from tools.docker_syntax_broker import DEFAULT_IMAGE, DockerSyntaxDenied


class HostSmokeTests(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory()
        self.addCleanup(self.temp.cleanup)
        self.root = Path(self.temp.name) / "repo"
        (self.root / "docs/state").mkdir(parents=True)
        (self.root / "AGENTS.md").write_text("P00 authority is in git\n", encoding="utf-8")
        self.phase = self.root / "docs/state/PHASE.json"
        self.state = {
            "phase": "P00", "phase_status": "IN_PROGRESS",
            "active_branch": "phase/00-governance", "primary_pr": 1,
            "worker_running": False,
        }
        self.write_state()
        self.calls = []

    def write_state(self):
        self.phase.write_text(json.dumps(self.state), encoding="utf-8")

    def fake_broker(self, plan, source, scope, **kwargs):
        self.calls.append((copy.deepcopy(plan), source, scope, kwargs))
        status = next(expected for _, value, expected in _CASES if value == source)
        return {
            "status": status, "phase": "P00", "task_id": _TASK,
            "image_digest": DEFAULT_IMAGE.split("@", 1)[1],
            "candidate_sha256": hashlib.sha256(source.encode("utf-8")).hexdigest(),
            "rootless_daemon_status_observed": True,
            "model_source_executed": False, "workspace_files_written": 0,
            "github_writes": 0, "independent_host_sandbox_verified": False,
            "persistent_worker_deployed": False,
        }

    def execute(self, **kwargs):
        with patch("tools.docker_host_smoke._linux_nonroot", return_value=True), \
             patch("tools.docker_host_smoke.run_python_syntax",
                   side_effect=self.fake_broker):
            return run_host_syntax_smoke(
                self.root, enabled=True, operator_ack=True, **kwargs
            )

    def test_default_disabled_and_both_approvals_required(self):
        for enabled, acknowledged in ((False, False), (True, False), (False, True)):
            with self.subTest(flags=(enabled, acknowledged)), \
                 patch("tools.docker_host_smoke.run_python_syntax") as broker:
                with self.assertRaises(HostSmokeDenied):
                    run_host_syntax_smoke(
                        self.root, enabled=enabled, operator_ack=acknowledged
                    )
                broker.assert_not_called()

    def test_non_linux_or_root_refused_before_broker(self):
        with patch("tools.docker_host_smoke._linux_nonroot", return_value=False), \
             patch("tools.docker_host_smoke.run_python_syntax") as broker:
            with self.assertRaises(HostSmokeDenied):
                run_host_syntax_smoke(self.root, enabled=True, operator_ack=True)
            broker.assert_not_called()

    def test_fixed_two_case_smoke_and_sanitized_receipt(self):
        original = {p.relative_to(self.root): p.read_bytes()
                    for p in self.root.rglob("*") if p.is_file()}
        report = self.execute()
        self.assertEqual("ROOTLESS_SYNTAX_SMOKE_ONLY", report["status"])
        self.assertEqual(["valid", "invalid"], report["cases"])
        self.assertFalse(report["independent_host_sandbox_verified"])
        self.assertFalse(report["remote_git_branch_verified"])
        self.assertFalse(report["persistent_worker_deployed"])
        self.assertEqual(2, len(self.calls))
        self.assertEqual(
            original, {p.relative_to(self.root): p.read_bytes()
                       for p in self.root.rglob("*") if p.is_file()}
        )
        for plan, source, scope, opts in self.calls:
            self.assertEqual("P00-T20", plan["task_id"])
            self.assertEqual("DRAFT_ONLY", plan["file_proposals"][0]["action"])
            self.assertEqual(("tests/fixtures",), scope.writable_prefixes)
            self.assertIs(opts["enabled"], True)
            self.assertEqual("P00-T20", opts["expected_task_id"])
            self.assertNotIn("image", opts)
            self.assertNotIn("command", opts)
            self.assertNotIn("mounts", opts)
            self.assertIn(source, [case[1] for case in _CASES])

    def test_phase_branch_pr_and_worker_flags_are_immutable(self):
        for key, bad in (
            ("phase", "P01"), ("phase_status", "MERGED_VERIFIED"),
            ("active_branch", "main"), ("primary_pr", 2),
            ("primary_pr", True), ("worker_running", True),
        ):
            self.state[key] = bad
            self.write_state()
            with self.subTest(field=key), self.assertRaises(HostSmokeDenied):
                self.execute()
            self.assertEqual([], self.calls)
            self.state[key] = {
                "phase": "P00", "phase_status": "IN_PROGRESS",
                "active_branch": "phase/00-governance",
                "primary_pr": 1, "worker_running": False,
            }[key]

    def test_missing_or_oversized_phase_refuses(self):
        self.phase.write_bytes(b"x" * 4097)
        with self.assertRaises(HostSmokeDenied):
            self.execute()
        self.phase.unlink()
        with self.assertRaises(HostSmokeDenied):
            self.execute()
        self.assertFalse(self.calls)

    def test_symlinked_phase_document_refuses(self):
        original = self.root / "outside-phase.json"
        original.write_text(json.dumps(self.state), encoding="utf-8")
        self.phase.unlink()
        try:
            self.phase.symlink_to(original)
        except (NotImplementedError, OSError):
            self.skipTest("host disallows symlinks")
        with self.assertRaises(HostSmokeDenied):
            self.execute()
        self.assertFalse(self.calls)

    def test_broker_denial_cannot_be_marked_success(self):
        with patch("tools.docker_host_smoke._linux_nonroot", return_value=True), \
             patch("tools.docker_host_smoke.run_python_syntax",
                   side_effect=DockerSyntaxDenied("secret host token: xyz")):
            with self.assertRaises(HostSmokeDenied) as cm:
                run_host_syntax_smoke(self.root, enabled=True, operator_ack=True)
            self.assertNotIn("secret", str(cm.exception))

    def test_fake_receipts_rejected_before_second_case_or_completion(self):
        for field, bad in (
            ("status", "PYTHON_SYNTAX_VALID_NO_CODE_EXECUTION_MAYBE"),
            ("candidate_sha256", "a" * 64),
            ("image_digest", "sha256:" + "a" * 64),
            ("github_writes", 1),
            ("workspace_files_written", True),
            ("model_source_executed", True),
            ("independent_host_sandbox_verified", True),
            ("persistent_worker_deployed", True),
            ("rootless_daemon_status_observed", False),
        ):
            self.calls.clear()
            def faulty(plan, source, scope, **kwargs):
                receipt = self.fake_broker(plan, source, scope, **kwargs)
                receipt[field] = bad
                return receipt
            with self.subTest(field=field), \
                 patch("tools.docker_host_smoke._linux_nonroot", return_value=True), \
                 patch("tools.docker_host_smoke.run_python_syntax",
                       side_effect=faulty):
                with self.assertRaises(HostSmokeDenied):
                    run_host_syntax_smoke(self.root, enabled=True, operator_ack=True)
                self.assertEqual(1, len(self.calls))

    def test_invalid_syntax_second_case_must_be_verified(self):
        self.calls.clear()
        def second_fails(plan, source, scope, **kwargs):
            item = self.fake_broker(plan, source, scope, **kwargs)
            if len(self.calls) == 2:
                item["status"] = "PYTHON_SYNTAX_VALID_NO_CODE_EXECUTION"
            return item
        with patch("tools.docker_host_smoke._linux_nonroot", return_value=True), \
             patch("tools.docker_host_smoke.run_python_syntax",
                   side_effect=second_fails):
            with self.assertRaises(HostSmokeDenied):
                run_host_syntax_smoke(self.root, enabled=True, operator_ack=True)
        self.assertEqual(2, len(self.calls))


if __name__ == "__main__":
    unittest.main()
