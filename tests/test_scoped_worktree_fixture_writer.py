"""P00 fd-scoped new-file writes into real disposable Git worktree fixtures.

Only trusted test-owned git repositories are constructed here. Never patch a
user checkout or source from a model on the host without external authorization.
Linux actually creates a candidate FILE in its isolated worktree; Windows
verifies the broker is disabled (not a Windows ACL/reparse-point implementation).
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

from tools.scoped_worktree_fixture_writer import (
    ScopedFixtureWriteDenied, apply_one_disposable_fixture,
)
from tools.worktree_plan import plan_detached_worktree
from tools.workspace_policy import WorkspaceScope

TASK = "P00-T20"
PATH = "tests/fixtures/generated.py"
SOURCE = "def solve(x):\n    return x * 2\n"
STATE = {
    "phase": "P00", "phase_status": "IN_PROGRESS",
    "active_branch": "phase/00-governance", "primary_pr": 1,
}


def proposal(path=PATH, task=TASK):
    return {
        "schema_version": 1, "phase": "P00",
        "branch": "phase/00-governance", "task_id": task,
        "summary": "Draft a fixed contained test fixture",
        "file_proposals": [{
            "path": path, "action": "DRAFT_ONLY",
            "reason": "Model-generated draft approved by operator only",
        }],
        "checks": ["phase-policy"],
    }


@unittest.skipUnless(
    os.name == "posix" and hasattr(os, "geteuid")
    and os.geteuid() != 0 and shutil.which("git"),
    "Real fd-scoped detached worktree write requires Linux non-root Git runner",
)
class ScopedWorktreeWriterTests(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory()
        self.addCleanup(self.temp.cleanup)
        self.base = Path(self.temp.name)
        self.repo = self.base / "trusted-immutable-source"
        self.root = self.base / "jobs"
        self.hooks = self.base / "no-hooks"
        for p in (self.repo, self.root, self.hooks):
            p.mkdir(mode=0o700)
        env = dict(os.environ)
        env.pop("GIT_CONFIG_COUNT", None)
        env["GIT_CONFIG_NOSYSTEM"] = "1"
        env["GIT_CONFIG_GLOBAL"] = str(self.base / "empty-gitconfig")
        (self.base / "empty-gitconfig").write_text("")
        self.git_env = env
        subprocess.run(["git", "init", "-q", str(self.repo)], check=True, timeout=10,
                       env=env, capture_output=True)
        subprocess.run(
            ["git", "-C", str(self.repo),
             "-c", "user.name=ZynoaDisposableFixture",
             "-c", "user.email=operator-test@invalid.example",
             "commit", "-q", "--allow-empty", "-m", "trusted empty fixture"],
            check=True, timeout=10, env=env, capture_output=True,
        )
        self.commit = subprocess.run(
            ["git", "-C", str(self.repo), "rev-parse", "HEAD"],
            check=True, timeout=10, env=env, capture_output=True, text=True,
        ).stdout.strip()
        workplan = plan_detached_worktree(
            self.repo, self.root, self.hooks, "draft-01", self.commit, STATE,
        )
        subprocess.run(workplan.argv, check=True, timeout=10,
                       env=env, capture_output=True)
        self.worktree = workplan.target
        (self.worktree / "tests").mkdir(mode=0o700)
        (self.worktree / "tests/fixtures").mkdir(mode=0o700)
        self.scope = WorkspaceScope(
            self.worktree, "P00", "phase/00-governance", ("tests/fixtures",)
        )
        self.before = subprocess.run(
            ["git", "-C", str(self.repo), "rev-parse", "HEAD"],
            check=True, timeout=10, env=env, capture_output=True, text=True,
        ).stdout.strip()

    def apply(self, *, plan=None, source=SOURCE, **overrides):
        args = {
            "expected_task_id": TASK,
            "expected_candidate_sha256": hashlib.sha256(source.encode()).hexdigest(),
            "expected_commit_sha": self.commit,
            "trusted_source_repo": self.repo,
            "controlled_root": self.root,
            "enabled": True, "operator_ack": True, "write_grant": True,
        }
        args.update(overrides)
        return apply_one_disposable_fixture(
            plan if plan is not None else proposal(),
            source, self.scope, **args,
        )

    def test_real_new_file_written_to_detached_worktree_only(self):
        receipt = self.apply()
        self.assertEqual("DISPOSABLE_WORKTREE_FIXTURE_CREATED", receipt["status"])
        self.assertEqual(PATH, receipt["path"])
        self.assertEqual(hashlib.sha256(SOURCE.encode()).hexdigest(),
                         receipt["candidate_sha256"])
        self.assertEqual(len(SOURCE.encode()), receipt["bytes_written"])
        self.assertEqual(1, receipt["disposable_worktree_files_written"])
        self.assertEqual(0, receipt["trusted_checkout_files_written"])
        self.assertEqual(0, receipt["github_writes"])
        self.assertFalse(receipt["model_source_executed"])
        self.assertFalse(receipt["os_sandbox_attested"])
        self.assertFalse(receipt["persistent_worker_deployed"])
        self.assertFalse(receipt["production_source_patch_verified"])
        self.assertNotIn(str(self.worktree), json.dumps(receipt))
        self.assertNotIn(SOURCE, json.dumps(receipt))
        file = self.worktree / PATH
        self.assertEqual(SOURCE, file.read_text(encoding="utf-8"))
        self.assertFalse((self.repo / PATH).exists())
        self.assertEqual(self.before, subprocess.run(
            ["git", "-C", str(self.repo), "rev-parse", "HEAD"],
            check=True, timeout=10, env=self.git_env,
            capture_output=True, text=True,
        ).stdout.strip())
        self.assertEqual([], list((self.worktree / "tests/fixtures").glob(".zynoa-*")))

    def test_existing_file_never_overwritten(self):
        path = self.worktree / PATH
        path.write_text("operator-content\n")
        with self.assertRaises(ScopedFixtureWriteDenied):
            self.apply()
        self.assertEqual("operator-content\n", path.read_text())
        self.assertEqual([], list(path.parent.glob(".zynoa-*")))

    def test_existing_symlink_destination_never_overwritten(self):
        outside = self.base / "operator-secret"
        outside.write_text("keep safe\n")
        link = self.worktree / PATH
        try:
            link.symlink_to(outside)
        except (NotImplementedError, OSError):
            self.skipTest("symlink unavailable")
        with self.assertRaises(ScopedFixtureWriteDenied):
            self.apply()
        self.assertEqual("keep safe\n", outside.read_text())
        self.assertTrue(link.is_symlink())

    def test_parent_symlink_escape_denied(self):
        other = self.base / "outside"
        other.mkdir()
        fixture = self.worktree / "tests/fixtures"
        fixture.rmdir()
        try:
            fixture.symlink_to(other, target_is_directory=True)
        except (NotImplementedError, OSError):
            self.skipTest("symlink unavailable")
        with self.assertRaises(ScopedFixtureWriteDenied):
            self.apply()
        self.assertEqual([], list(other.iterdir()))

    def test_group_world_writable_parent_denied(self):
        folder = self.worktree / "tests/fixtures"
        folder.chmod(0o777)
        with self.assertRaises(ScopedFixtureWriteDenied):
            self.apply()
        self.assertFalse((self.worktree / PATH).exists())

    def test_scoped_phase_path_and_candidate_bytes_before_any_write(self):
        for data in (
            proposal("AGENTS.md"),
            proposal("docs/state/PHASE.json"),
            proposal("tests/fixtures/subdir/evil.py"),
            proposal("tests/fixtures/../outside.py"),
            proposal("tests/fixtures/a.js"),
            proposal("tests/fixtures/.env"),
            proposal(task="P00-T19"),
        ):
            with self.subTest(data=data), self.assertRaises(ScopedFixtureWriteDenied):
                self.apply(plan=data)
        for source in ("", "x" * 8193, "x\x00",
                       "Cafe" + chr(0x301), "x" + chr(0x202e)):
            with self.subTest(source=repr(source)), self.assertRaises(ScopedFixtureWriteDenied):
                self.apply(source=source)
        self.assertFalse((self.worktree / PATH).exists())

    def test_four_host_bound_identities_are_independently_required(self):
        for kwargs in (
            {"expected_task_id": "P00-T19"},
            {"expected_candidate_sha256": "a" * 64},
            {"expected_candidate_sha256": ""},
            {"expected_commit_sha": "0" * 40},
            {"expected_commit_sha": "main"},
            {"controlled_root": self.repo},
            {"trusted_source_repo": self.worktree},
        ):
            with self.subTest(kwargs=kwargs), self.assertRaises(ScopedFixtureWriteDenied):
                self.apply(**kwargs)
        self.assertFalse((self.worktree / PATH).exists())

    def test_denies_source_checkout_and_non_git_staging_as_worktree(self):
        normal_scope = WorkspaceScope(
            self.repo, "P00", "phase/00-governance", ("tests/fixtures",)
        )
        with self.assertRaises(ScopedFixtureWriteDenied):
            apply_one_disposable_fixture(
                proposal(), SOURCE, normal_scope,
                expected_task_id=TASK,
                expected_candidate_sha256=hashlib.sha256(SOURCE.encode()).hexdigest(),
                expected_commit_sha=self.commit,
                trusted_source_repo=self.repo, controlled_root=self.root,
                enabled=True, operator_ack=True, write_grant=True,
            )
        pointer = self.worktree / ".git"
        old = pointer.read_text()
        pointer.write_text("gitdir: /tmp/attacker\n")
        with self.assertRaises(ScopedFixtureWriteDenied):
            self.apply()
        pointer.write_text(old)

    def test_explicit_three_optins_and_truthy_values_refused(self):
        for grants in (
            {}, {"enabled": True}, {"enabled": True, "operator_ack": True},
            {"enabled": True, "write_grant": True},
            {"operator_ack": True, "write_grant": True},
            {"enabled": 1, "operator_ack": True, "write_grant": True},
        ):
            params = {
                "expected_task_id": TASK,
                "expected_candidate_sha256": hashlib.sha256(SOURCE.encode()).hexdigest(),
                "expected_commit_sha": self.commit,
                "trusted_source_repo": self.repo, "controlled_root": self.root,
            }
            params.update(grants)
            with self.subTest(grants=grants), self.assertRaises(ScopedFixtureWriteDenied):
                apply_one_disposable_fixture(proposal(), SOURCE, self.scope, **params)
        self.assertFalse((self.worktree / PATH).exists())

    def test_no_candidate_exec_or_shell_on_trusted_controller(self):
        hostile = "import os\nos.system('echo never-execute')\n"
        with patch("subprocess.Popen") as popen, patch("os.system") as system:
            receipt = self.apply(source=hostile)
        system.assert_not_called()
        popen.assert_not_called()
        self.assertFalse(receipt["model_source_executed"])
        self.assertEqual(hostile, (self.worktree / PATH).read_text())

    def test_atomic_link_failure_cleans_temporary_file(self):
        with patch("tools.scoped_worktree_fixture_writer.os.link",
                   side_effect=OSError("busy")):
            with self.assertRaises(ScopedFixtureWriteDenied):
                self.apply()
        self.assertEqual([], list((self.worktree / "tests/fixtures").glob(".zynoa-*")))
        self.assertFalse((self.worktree / PATH).exists())

    def test_replay_same_source_refused_without_overwrite(self):
        self.apply()
        with self.assertRaises(ScopedFixtureWriteDenied):
            self.apply()
        self.assertEqual(SOURCE, (self.worktree / PATH).read_text())


class CrossPlatformDefaultDenied(unittest.TestCase):
    def test_no_host_grants_refused_everywhere(self):
        with tempfile.TemporaryDirectory() as tmp:
            scope = WorkspaceScope(Path(tmp), "P00", "phase/00-governance",
                                   ("tests/fixtures",))
            with self.assertRaises(ScopedFixtureWriteDenied):
                apply_one_disposable_fixture(
                    proposal(), SOURCE, scope,
                    expected_task_id=TASK,
                    expected_candidate_sha256=hashlib.sha256(SOURCE.encode()).hexdigest(),
                    expected_commit_sha="a"*40, trusted_source_repo=Path(tmp),
                    controlled_root=Path(tmp),
                )


if __name__ == "__main__":
    unittest.main()
