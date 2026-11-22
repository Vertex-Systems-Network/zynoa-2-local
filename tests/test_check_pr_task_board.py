import json
import os
import shutil
import tempfile
import unittest
from pathlib import Path
from unittest import mock

from scripts import check_pr_task_board

ROOT = Path(__file__).resolve().parents[1]


class CheckPrTaskBoardTests(unittest.TestCase):
    def run_with(self, status, pr):
        tmp = Path(tempfile.mkdtemp())
        self.addCleanup(shutil.rmtree, tmp)
        (tmp / "docs/state/pr-tasks").mkdir(parents=True)
        shutil.copy(ROOT / "docs/state/pr-tasks/P00.json", tmp / "docs/state/pr-tasks/P00.json")
        phase = json.loads((ROOT / "docs/state/PHASE.json").read_text())
        phase["phase_status"] = status
        (tmp / "docs/state/PHASE.json").write_text(json.dumps(phase))
        cwd = os.getcwd()
        os.chdir(tmp)
        try:
            with mock.patch.dict(os.environ, {"ZYNOA_CI_PR_NUMBER": pr}), \
                    mock.patch("builtins.print"):
                return check_pr_task_board.main()
        finally:
            os.chdir(cwd)

    def test_open_phase_rejects_other_pr(self):
        self.assertEqual(2, self.run_with("IN_PROGRESS", "8"))

    def test_merged_phase_allows_closeout_pr(self):
        self.assertEqual(0, self.run_with("MERGED_VERIFIED", "8"))

    def test_primary_pr_always_valid(self):
        self.assertEqual(0, self.run_with("IN_PROGRESS", "1"))
