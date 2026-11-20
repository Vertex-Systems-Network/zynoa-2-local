"""P00 path capability and trusted Git worktree plan tests.

Only a synthetic tempfile Git repo is used for the integration test. The
actual Zynoa repository is never mutated, checked out, executed or merged.
"""
from __future__ import annotations

import os
import shutil
import subprocess
import tempfile
import unittest
from pathlib import Path

from tools.workspace_policy import WorkspaceScope, WorkspaceDenied
from tools.worktree_plan import WorktreePlanDenied, plan_detached_worktree

STATE = {
    "phase": "P00", "phase_status": "IN_PROGRESS",
    "active_branch": "phase/00-governance", "primary_pr": 1,
}
SHA = "a" * 40


class ScopePolicyTests(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        self.addCleanup(self.tmp.cleanup)
        self.root = Path(self.tmp.name) / "isolated"
        self.root.mkdir()
        (self.root / "docs" / "help").mkdir(parents=True)
        (self.root / "docs" / "help" / "article.md").write_text("safe")
        self.scope = WorkspaceScope(self.root, "P00", "phase/00-governance")

    def test_read_and_write_scopes(self):
        self.assertEqual(
            (self.root / "docs" / "help" / "article.md").resolve(),
            self.scope.check("docs/help/article.md", "read"),
        )
        self.assertEqual(
            (self.root / "docs" / "help" / "new.md").resolve(),
            self.scope.check("docs/help/new.md", "write"),
        )
        self.assertTrue(self.scope.evaluate("docs/help/new.md", "write")["allowed"])

    def test_disallow_privileged_operations_and_arbitrary_paths(self):
        for operation in ("delete", "execute", "merge", "chown"):
            with self.subTest(operation=operation), self.assertRaises(WorkspaceDenied):
                self.scope.check("docs/help/article.md", operation)
        for path in ("tools/shell.py", "scripts/run.py", "src/agent.py"):
            with self.subTest(path=path), self.assertRaises(WorkspaceDenied):
                self.scope.check(path, "write")

    def test_protect_repo_policies_and_secrets(self):
        for path in (
            "AGENTS.md", ".git/config", ".github/workflows/ci.yml",
            "docs/state/PHASE.json", "docs/quality/RELEASE_GATES.md",
            "docs/adr/0010-phase-task-dag.md", "deploy/github/main-ruleset.json",
            "tools/workspace_policy.py", "tools/docker_host_smoke.py",
            ".env", ".ssh/id_rsa",
        ):
            for action in ("read", "write"):
                with self.subTest(path=path, action=action), self.assertRaises(WorkspaceDenied):
                    self.scope.check(path, action)

    def test_traversal_drive_unc_and_encoded_abuse(self):
        for path in (
            "../outside", "docs/help/../../AGENTS.md",
            "/tmp/outside", "C:/secret.txt", "C:secret.txt",
            r"docs\help\inside.md", r"\\server\share\x.md",
            "docs//help/article.md", "docs/help/./article.md",
            "docs/help/../article.md", "docs/help/file.", "docs/help/NUL.txt",
            "docs/help/CON", "docs/help/bad:stream",
            "docs/help/evil\nname", "docs/help/evil\x00name",
        ):
            with self.subTest(path=path), self.assertRaises(WorkspaceDenied):
                self.scope.check(path, "write")

    def test_existing_symlink_to_outside_denied(self):
        outside = Path(self.tmp.name) / "outside"
        outside.mkdir()
        (outside / "file.md").write_text("untrusted")
        alias = self.root / "docs" / "help" / "alias"
        try:
            alias.symlink_to(outside, target_is_directory=True)
        except (OSError, NotImplementedError):
            self.skipTest("symlinks not available on this platform")
        with self.assertRaises(WorkspaceDenied):
            self.scope.check("docs/help/alias/file.md", "write")

    def test_direct_symlink_file_denied(self):
        outside = Path(self.tmp.name) / "private.md"
        outside.write_text("private")
        alias = self.root / "docs" / "help" / "private.md"
        try:
            alias.symlink_to(outside)
        except (OSError, NotImplementedError):
            self.skipTest("symlinks not available")
        with self.assertRaises(WorkspaceDenied):
            self.scope.check("docs/help/private.md", "read")

    def test_root_symlink_denied(self):
        link = Path(self.tmp.name) / "linked"
        try:
            link.symlink_to(self.root, target_is_directory=True)
        except (OSError, NotImplementedError):
            self.skipTest("symlinks not available")
        with self.assertRaises(WorkspaceDenied):
            WorkspaceScope(link, "P00", "phase/00-governance")

    def test_write_prefix_cannot_overlap_governance(self):
        for prefix in ("docs", "tools", "docs/state", ".github", "../safe"):
            with self.subTest(prefix=prefix), self.assertRaises(WorkspaceDenied):
                WorkspaceScope(self.root, "P00", "phase/00-governance", (prefix,))

    def test_private_absolute_path_not_emitted_to_agent(self):
        decision = self.scope.evaluate("docs/help/../../private.md", "write")
        self.assertEqual({"allowed": False, "operation": "write",
                          "reason": "WORKSPACE_SCOPE_DENIED"}, decision)
        self.assertNotIn(str(self.root), str(decision))

    def test_invalid_phase_or_branch_scope_rejected(self):
        for phase, branch in (
            ("P99", "phase/00-governance"),
            ("P01", "phase/01-foundation"),
            ("P00", "main"),
            ("P00", "phase/00-impostor"),
        ):
            with self.subTest(phase=phase, branch=branch), self.assertRaises(WorkspaceDenied):
                WorkspaceScope(self.root, phase, branch)

    def test_hidden_secrets_git_attributes_and_invisible_characters_denied(self):
        for path in (
            "docs/help/.env.local", "docs/help/.gitattributes",
            "docs/help/.gitmodules", "docs/help/.aws.credentials",
            "docs/help/name\\u202emod.exe", "docs/help/name\\u200binvisible",
        ):
            with self.subTest(path=path), self.assertRaises(WorkspaceDenied):
                self.scope.check(path, "write")

    def test_missing_read_denied(self):
        with self.assertRaises(WorkspaceDenied):
            self.scope.check("docs/help/not-found.md", "read")

    def test_non_file_write_denied(self):
        with self.assertRaises(WorkspaceDenied):
            self.scope.check("docs/help", "write")


class WorktreePlanTests(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        self.addCleanup(self.tmp.cleanup)
        self.folder = Path(self.tmp.name)
        self.source = self.folder / "trusted-repo"
        self.source.mkdir()
        (self.source / ".git").mkdir()
        self.tasks = self.folder / "task-worktrees"
        self.tasks.mkdir()
        self.hooks = self.folder / "disabled-hooks"
        self.hooks.mkdir()

    def plan(self, **changes):
        kw = dict(
            trusted_repo=self.source, controlled_root=self.tasks,
            empty_hooks_dir=self.hooks, job_id="task-01",
            commit_sha=SHA, state=STATE,
        )
        kw.update(changes)
        return plan_detached_worktree(**kw)

    def test_valid_detached_plan_contains_no_mutating_remote_operation(self):
        plan = self.plan()
        self.assertFalse(plan.executed)
        self.assertFalse(plan.shell)
        self.assertEqual(SHA, plan.commit_sha)
        self.assertEqual(
            ("worktree", "add", "--detach", "--no-checkout", "--"),
            plan.argv[5:10],
        )
        for value in ("push", "pull", "merge", "fetch", "checkout"):
            self.assertNotIn(value, plan.argv)
        self.assertFalse(plan.summary()["host_sandbox_provided"])
        self.assertNotIn(str(self.tasks), str(plan.summary()))

    def test_wrong_phase_and_branch_refused(self):
        for changes in (
            {"phase": "P01"}, {"active_branch": "main"},
            {"phase_status": "MERGED_VERIFIED"}, {"primary_pr": None},
        ):
            with self.subTest(changes=changes), self.assertRaises(WorktreePlanDenied):
                self.plan(state={**STATE, **changes})

    def test_invalid_job_and_sha_refused(self):
        for job in ("-danger", "../escape", "x/y", "", "X", "foo bar", "a" * 70):
            with self.subTest(job=job), self.assertRaises(WorktreePlanDenied):
                self.plan(job_id=job)
        for sha in ("main", "HEAD", "abc", "a" * 39, "g" * 40, "-b" + "a" * 38):
            with self.subTest(sha=sha), self.assertRaises(WorktreePlanDenied):
                self.plan(commit_sha=sha)

    def test_target_already_exists_refused(self):
        self.plan().target.mkdir()
        with self.assertRaises(WorktreePlanDenied):
            self.plan()

    def test_root_overlapping_source_refused(self):
        with self.assertRaises(WorktreePlanDenied):
            self.plan(controlled_root=self.folder)

    def test_missing_or_nonempty_hook_dir_refused(self):
        (self.hooks / "post-checkout").write_text("unsafe")
        with self.assertRaises(WorktreePlanDenied):
            self.plan()
        (self.hooks / "post-checkout").unlink()
        with self.assertRaises(WorktreePlanDenied):
            self.plan(empty_hooks_dir=self.folder / "missing")

    def test_symlink_target_parent_refused(self):
        other = self.folder / "other"
        other.mkdir()
        link = self.folder / "shortcut"
        try:
            link.symlink_to(other, target_is_directory=True)
        except (OSError, NotImplementedError):
            self.skipTest("symlinks unavailable")
        with self.assertRaises(WorktreePlanDenied):
            self.plan(controlled_root=link)


@unittest.skipUnless(shutil.which("git"), "Git CLI unavailable")
class GitFixtureIntegrationTests(unittest.TestCase):
    def test_real_git_no_checkout_worktree_in_private_fixture_only(self):
        with tempfile.TemporaryDirectory() as tmp:
            base = Path(tmp)
            source = base / "fixture-repo"
            source.mkdir()
            tasks = base / "jobs"
            tasks.mkdir()
            hooks = base / "no-hooks"
            hooks.mkdir()
            env = dict(os.environ)
            env.pop("GIT_CONFIG_COUNT", None)
            env["GIT_CONFIG_NOSYSTEM"] = "1"
            env["GIT_CONFIG_GLOBAL"] = str(base / "empty-gitconfig")
            (base / "empty-gitconfig").write_text("")
            subprocess.run(["git", "init", "-q", str(source)], check=True,
                           timeout=10, env=env, capture_output=True)
            subprocess.run(
                ["git", "-C", str(source), "-c", "user.name=ZynoaFixture",
                 "-c", "user.email=test@invalid.example", "commit",
                 "-q", "--allow-empty", "-m", "fixture"],
                check=True, timeout=10, env=env, capture_output=True,
            )
            sha = subprocess.run(
                ["git", "-C", str(source), "rev-parse", "HEAD"],
                check=True, timeout=10, env=env, capture_output=True, text=True,
            ).stdout.strip()
            plan = plan_detached_worktree(
                source, tasks, hooks, "fixture-01", sha, STATE,
            )
            # This is an intentionally constructed TEST repository, not an
            # agent-chosen user repository. No AI tool can invoke this path.
            subprocess.run(
                plan.argv, check=True, timeout=10, env=env, capture_output=True,
            )
            self.assertTrue((plan.target / ".git").is_file())
            observed = subprocess.run(
                ["git", "-C", str(plan.target), "rev-parse", "HEAD"],
                check=True, timeout=10, env=env, capture_output=True, text=True,
            ).stdout.strip()
            self.assertEqual(sha, observed)
            self.assertFalse((plan.target / "README.md").exists())


if __name__ == "__main__":
    unittest.main()
