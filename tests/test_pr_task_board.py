"""PR description task-board tests. All GitHub writes are mock transport only."""
from __future__ import annotations

import copy
import json
import tempfile
import unittest
from pathlib import Path

from tools.pr_task_board import (
    TaskBoardError, _END, _START, load_manifest, merge_into_pr_body,
    render, summary, sync_task_board, validate_manifest,
)
ROOT = Path(__file__).resolve().parents[1]
MANIFEST = ROOT / "docs/state/pr-tasks/P00.json"
SHA = "a" * 40
REPO = "Vertex-Systems-Network/zynoa-2-local"


def fixture():
    return load_manifest(MANIFEST)


class TaskBoardTests(unittest.TestCase):
    def test_real_manifest_and_true_totals(self):
        m = fixture()
        self.assertEqual("P00", m["phase"])
        self.assertEqual(1, m["pr_number"])
        counts = summary(m)
        self.assertEqual(len(m["tasks"]), counts["total"])
        self.assertEqual(counts["total"],
                         counts["done"] + counts["in_progress"] +
                         counts["pending"] + counts["blocked"])
        self.assertEqual((counts["done"] * 100) // counts["total"],
                         counts["percent_done"])

    def test_render_has_every_task_exactly_once(self):
        m = fixture()
        board = render(m)
        self.assertTrue(board.startswith(_START))
        self.assertTrue(board.endswith(_END))
        self.assertEqual(1, board.count(_START))
        for task in m["tasks"]:
            self.assertEqual(1, board.count("`" + task["id"] + "`"))
        self.assertIn("**Progress:** " + str(summary(m)["percent_done"]) + "%", board)
        self.assertIn("**Blocked:** " + str(summary(m)["blocked"]), board)

    def test_existing_description_preserved_except_managed_section(self):
        m = fixture()
        original = "# Original heading\n\nHuman edits and notes remain intact."
        first = merge_into_pr_body(original, m)
        self.assertTrue(first.startswith(original + "\n\n"))
        before_done = summary(m)["done"]
        incomplete = next(task for task in m["tasks"] if task["status"] != "DONE")
        incomplete["status"] = "DONE"
        incomplete["reference"] = "https://github.com/" + REPO + "/pull/1"
        second = merge_into_pr_body(first, m)
        self.assertTrue(second.startswith(original + "\n\n"))
        self.assertEqual(1, second.count(_START))
        self.assertIn("**Done:** " + str(before_done + 1), second)
        self.assertNotIn("**Done:** " + str(before_done) + " |", second)

    def test_idempotent_description_render(self):
        m = fixture()
        start = "Normal PR description."
        once = merge_into_pr_body(start, m)
        self.assertEqual(once, merge_into_pr_body(once, m))

    def test_reject_duplicate_or_reverse_delimiters(self):
        m = fixture()
        for text in (
            _START + "\n" + _START + "\n" + _END,
            _END + "\n" + _START,
            "Text " + _END,
            _START + " no closing marker",
        ):
            with self.subTest(text=text[:30]), self.assertRaises(TaskBoardError):
                merge_into_pr_body(text, m)

    def test_reject_bad_ids_phases_and_task_keys(self):
        for modifier in (
            lambda m: m["tasks"].append(copy.deepcopy(m["tasks"][0])),
            lambda m: m["tasks"][0].update({"id": "P01-T01"}),
            lambda m: m["tasks"][0].update({"id": "P00-T99"}),
            lambda m: m["tasks"][0].update({"secret": "abc"}),
            lambda m: m.update({"phase": "P99"}),
            lambda m: m.update({"pr_number": "1"}),
            lambda m: m.update({"branch": "main"}),
            lambda m: m.update({"update_policy": "no-evidence-required"}),
        ):
            m = fixture()
            modifier(m)
            with self.assertRaises(TaskBoardError):
                validate_manifest(m)

    def test_reject_markdown_html_and_remote_links(self):
        for value in ("Bad | Markdown", "<script>alert(1)</script>",
                      "Task\nInjected", "[click](https://bad.example)"):
            m = fixture()
            m["tasks"][0]["title"] = value
            with self.subTest(value=value), self.assertRaises(TaskBoardError):
                validate_manifest(m)
        for url in (
            "https://evil.example/issue/1",
            "https://github.com/another/repo/pull/1",
            "javascript:alert(1)",
            "https://github.com/" + REPO + "/issues/3#more",
        ):
            m = fixture()
            m["tasks"][0]["reference"] = url
            with self.subTest(url=url), self.assertRaises(TaskBoardError):
                validate_manifest(m)

    def test_done_and_blocked_always_need_link(self):
        for status in ("DONE", "BLOCKED"):
            m = fixture()
            m["tasks"][0]["status"] = status
            m["tasks"][0].pop("reference", None)
            with self.assertRaises(TaskBoardError):
                validate_manifest(m)

    def test_task_state_can_change_but_not_be_inferred_from_CI(self):
        m = fixture()
        before = summary(m)
        render(m)
        self.assertEqual(before, summary(m))
        still_blocked = next(t for t in m["tasks"] if t["id"] == "P00-T24")
        self.assertEqual("BLOCKED", still_blocked["status"])

    def test_load_manifest_rejects_garbage(self):
        with tempfile.TemporaryDirectory() as td:
            p = Path(td) / "invalid.json"
            p.write_text('{"phase":"P00", "tasks": []}')
            with self.assertRaises(TaskBoardError):
                load_manifest(p)


class FakePR:
    def __init__(self):
        self.calls = []
        self.body = "Original PR contents."
        self.head = SHA
        self.branch = "phase/00-governance"
        self.base = "main"
        self.number = 1
        self.repo = REPO
        self.state = "open"
        self.hijack_body = False
        self.hijack_head = False
        self.patch_response_invalid = False

    def __call__(self, method, url, payload):
        self.calls.append((method, url, payload))
        if method == "PATCH":
            if self.patch_response_invalid:
                return []
            self.body = payload["body"]
        if self.hijack_body and len(self.calls) >= 2 and method == "GET":
            self.body += "\nConcurrent human edit."
            self.hijack_body = False
        if self.hijack_head and len(self.calls) >= 2:
            self.head = "b" * 40
        return {
            "number": self.number, "state": self.state,
            "head": {"ref": self.branch, "sha": self.head,
                     "repo": {"full_name": self.repo}},
            "base": {"ref": self.base}, "body": self.body,
        }


class SyncTests(unittest.TestCase):
    def sync(self, transport, *, enabled=True, sha=SHA, manifest=None):
        return sync_task_board(manifest or fixture(), sha, "fake-test-token",
                               enabled=enabled, transport=transport)

    def test_opt_in_only_and_no_write_without_flag(self):
        transport = FakePR()
        with self.assertRaises(TaskBoardError):
            self.sync(transport, enabled=False)
        self.assertFalse(transport.calls)

    def test_successful_sync_and_verified_readback(self):
        transport = FakePR()
        result = self.sync(transport)
        self.assertEqual("SYNCED_VERIFIED", result["status"])
        self.assertEqual(["GET", "GET", "PATCH", "GET"],
                         [x[0] for x in transport.calls])
        self.assertEqual({"body"}, set(transport.calls[2][2]))
        self.assertEqual(1, transport.body.count(_START))
        self.assertTrue(transport.body.startswith("Original PR contents."))
        self.assertEqual("UNCHANGED", self.sync(transport)["status"])
        self.assertEqual(1, len([x for x in transport.calls if x[0] == "PATCH"]))

    def test_wrong_sha_and_cross_repo_pr_denied(self):
        for attribute, value in (
            ("head", "b" * 40), ("branch", "phase/01-start"),
            ("base", "wrong"), ("number", 4),
            ("repo", "attacker/fork"), ("state", "closed"),
        ):
            transport = FakePR()
            setattr(transport, attribute, value)
            with self.subTest(attribute=attribute), self.assertRaises(TaskBoardError):
                self.sync(transport)
            self.assertNotIn("PATCH", [x[0] for x in transport.calls])

    def test_raced_human_body_edit_blocks_mutation(self):
        transport = FakePR()
        transport.hijack_body = True
        with self.assertRaises(TaskBoardError):
            self.sync(transport)
        self.assertNotIn("PATCH", [x[0] for x in transport.calls])

    def test_head_changed_between_gets_blocks_mutation(self):
        transport = FakePR()
        transport.hijack_head = True
        with self.assertRaises(TaskBoardError):
            self.sync(transport)
        self.assertNotIn("PATCH", [x[0] for x in transport.calls])

    def test_invalid_write_result_does_not_claim_success(self):
        transport = FakePR()
        transport.patch_response_invalid = True
        with self.assertRaises(TaskBoardError):
            self.sync(transport)

    def test_invalid_expected_sha_denied_before_write(self):
        transport = FakePR()
        with self.assertRaises(TaskBoardError):
            self.sync(transport, sha="HEAD")
        self.assertNotIn("PATCH", [x[0] for x in transport.calls])


if __name__ == "__main__":
    unittest.main()
