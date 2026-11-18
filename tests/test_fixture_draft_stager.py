"""Ephemeral fixture-only code/text staging, including unsafe input regression."""
from __future__ import annotations

import copy
import json
import os
import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch

from tools.fixture_draft_stager import FixtureStageDenied, preview_fixture_drafts
from tools.workspace_policy import WorkspaceScope

TASK = "P00-T20"
ONE_PATH = "tests/fixtures/candidate.py"


def proposal(paths=(ONE_PATH,)):
    return {
        "schema_version": 1,
        "phase": "P00", "branch": "phase/00-governance",
        "task_id": TASK, "summary": "Preview only inside disposable fixture",
        "file_proposals": [
            {"path": path, "action": "DRAFT_ONLY", "reason": "Safe test fixture preview"}
            for path in paths
        ],
        "checks": ["phase-policy"],
    }


class FixtureStagerTests(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        self.addCleanup(self.tmp.cleanup)
        self.root = Path(self.tmp.name).resolve()
        (self.root / "tests" / "fixtures").mkdir(parents=True)
        (self.root / "docs" / "help").mkdir(parents=True)
        (self.root / "docs" / "state").mkdir(parents=True)
        self.scope = WorkspaceScope(self.root, "P00", "phase/00-governance")

    def preview(self, paths=(ONE_PATH,), contents=None):
        if contents is None:
            contents = {p: "pass\n" for p in paths}
        return preview_fixture_drafts(proposal(paths), contents, self.scope, expected_task_id=TASK)

    def test_stage_static_python_then_remove_all_disposable_files(self):
        before = list(self.root.rglob("*"))
        result = self.preview()
        self.assertEqual("EPHEMERAL_FIXTURE_PREVIEW_ONLY", result["status"])
        self.assertEqual(1, result["disposable_files_staged_and_removed"])
        self.assertEqual(0, result["workspace_files_written"])
        self.assertEqual(0, result["user_files_written"])
        self.assertEqual(0, result["github_writes"])
        self.assertEqual(0, result["commands_executed"])
        self.assertFalse(result["model_code_executed"])
        self.assertFalse(result["os_sandbox_verified"])
        self.assertFalse(result["persistent_worker_deployed"])
        self.assertEqual("PYTHON_AST_PARSED_NOT_EXECUTED",
                         result["candidate_receipts"][0]["static_check"])
        self.assertEqual(64, len(result["candidate_receipts"][0]["sha256"]))
        self.assertEqual(before, list(self.root.rglob("*")))
        self.assertFalse((self.root / ONE_PATH).exists())

    def test_json_and_unicode_text_parse_without_execution(self):
        paths = ("tests/fixtures/data.json", "tests/fixtures/guide.md")
        docs = {paths[0]: '{"ok":true,"n":1}', paths[1]: "Urdu: سلام\n"}
        result = self.preview(paths, docs)
        self.assertEqual(2, result["candidate_count"])
        self.assertEqual([
            "JSON_PARSED_NOT_EXECUTED", "TEXT_VALIDATED_NOT_EXECUTED",
        ], [x["static_check"] for x in result["candidate_receipts"]])
        self.assertEqual(sum(len(x.encode()) for x in docs.values()),
                         result["total_candidate_bytes"])
        for path in paths:
            self.assertFalse((self.root / path).exists())

    def test_receipt_is_deterministic_and_does_not_include_source_code(self):
        one = self.preview()
        two = self.preview()
        self.assertEqual(one["receipt_sha256"], two["receipt_sha256"])
        self.assertNotIn("pass", json.dumps(one))

    def test_rejects_nonmatching_inventory_before_any_staging(self):
        for paths, contents in (
            ((ONE_PATH,), {}),
            ((ONE_PATH,), {"tests/fixtures/other.py": "pass"}),
            ((ONE_PATH,), {ONE_PATH: "pass", "tests/fixtures/extra.py": "pass"}),
        ):
            with self.subTest(paths=paths, contents=list(contents)):
                with self.assertRaises(FixtureStageDenied):
                    self.preview(paths, contents)
        self.assertFalse((self.root / ONE_PATH).exists())

    def test_rejects_malformed_python_and_json(self):
        for filename, content in (
            ("tests/fixtures/a.py", "def broken(:\n    pass"),
            ("tests/fixtures/a.json", '{"unfinished":'),
        ):
            with self.subTest(filename=filename), self.assertRaises(FixtureStageDenied):
                self.preview((filename,), {filename: content})

    def test_no_code_execution_even_when_candidate_contains_system_calls(self):
        candidate = "import os\nos.system('echo should-never-execute')\n"
        with patch("os.system", side_effect=AssertionError("execution forbidden")) as mock_exec:
            result = self.preview(contents={ONE_PATH: candidate})
        mock_exec.assert_not_called()
        self.assertFalse((self.root / ONE_PATH).exists())
        self.assertEqual("PYTHON_AST_PARSED_NOT_EXECUTED",
                         result["candidate_receipts"][0]["static_check"])

    def test_disallows_non_fixture_proposals_even_when_scope_allows(self):
        path = "docs/help/unauthorized-source.txt"
        with self.assertRaises(FixtureStageDenied):
            self.preview((path,), {path: "only fixture files allowed"})

    def test_nested_paths_and_python_script_traversal_denied(self):
        for path in (
            "tests/fixtures/dir/child.py",
            "tests/fixtures/../state/PHASE.json",
            "tests/fixtures/.env",
            "tests/fixtures/evil.exe",
            "tests/fixtures/../../agent.py",
            "tests/fixtures/a\\name.py",
        ):
            with self.subTest(path=path), self.assertRaises(FixtureStageDenied):
                self.preview((path,), {path: "pass"})

    def test_one_file_and_total_size_budgets(self):
        with self.assertRaises(FixtureStageDenied):
            self.preview(contents={ONE_PATH: "a" * 8193})
        paths = tuple("tests/fixtures/x" + str(i) + ".txt" for i in range(5))
        with self.assertRaises(FixtureStageDenied):
            self.preview(paths, {p: "a" * 8000 for p in paths})

    def test_rejects_control_bidi_and_non_normalized_text(self):
        for text in ("x" + chr(0), "x" + chr(0x202e), "x" + chr(0x200d),
                     "Cafe" + chr(0x301), "x\rhidden"):
            with self.subTest(value=repr(text)), self.assertRaises(FixtureStageDenied):
                self.preview(contents={ONE_PATH: text})

    def test_excessive_lines_and_empty_content_denied(self):
        for text in ("", "\n" * 200, " " * 8193):
            with self.subTest(n=len(text)), self.assertRaises(FixtureStageDenied):
                self.preview(contents={ONE_PATH: text})

    def test_model_cannot_select_dangerous_action(self):
        data = proposal()
        data["file_proposals"][0]["action"] = "EXECUTE"
        with self.assertRaises(FixtureStageDenied):
            preview_fixture_drafts(data, {ONE_PATH: "pass"}, self.scope, expected_task_id=TASK)

    def test_model_cannot_mutate_phase_or_branch(self):
        for field, value in (("phase", "P01"), ("branch", "main"),
                             ("task_id", "P00-T19")):
            data = proposal()
            data[field] = value
            with self.subTest(field=field), self.assertRaises(FixtureStageDenied):
                preview_fixture_drafts(data, {ONE_PATH: "pass"}, self.scope, expected_task_id=TASK)

    def test_protected_existing_file_and_link_escapes_denied(self):
        protected = "AGENTS.md"
        with self.assertRaises(FixtureStageDenied):
            self.preview((protected,), {protected: "modified policy"})
        outside = self.root.parent / (self.root.name + "-outside")
        outside.mkdir(exist_ok=True)
        self.addCleanup(lambda: outside.rmdir())
        link = self.root / "tests" / "fixtures" / "linked"
        try:
            link.symlink_to(outside, target_is_directory=True)
        except (NotImplementedError, OSError):
            self.skipTest("host does not permit symlinks")
        path = "tests/fixtures/linked/unsafe.py"
        with self.assertRaises(FixtureStageDenied):
            self.preview((path,), {path: "pass"})

    def test_unsafe_model_input_never_creates_a_source_file(self):
        source = self.root / "tests" / "fixtures" / "existing.txt"
        source.write_text("ORIGINAL", encoding="utf-8")
        path = "tests/fixtures/existing.txt"
        self.preview((path,), {path: "REPLACEMENT"})
        self.assertEqual("ORIGINAL", source.read_text(encoding="utf-8"))

    def test_invalid_input_types_refused(self):
        for candidates in (None, [], {"tests/fixtures/candidate.py": None}):
            with self.subTest(candidate_type=type(candidates).__name__):
                with self.assertRaises(FixtureStageDenied):
                    preview_fixture_drafts(proposal(), candidates, self.scope, expected_task_id=TASK)


if __name__ == "__main__":
    unittest.main()
