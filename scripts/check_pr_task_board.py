#!/usr/bin/env python3
"""Require a versioned task manifest in every active phase PR (read-only CI)."""
import json
import os
from pathlib import Path

from tools.pr_task_board import TaskBoardError, load_manifest, summary


def main() -> int:
    root = Path(".")
    try:
        phase = json.loads((root / "docs/state/PHASE.json").read_text(encoding="utf-8"))
        if not isinstance(phase, dict):
            raise TaskBoardError("phase state invalid")
        phase_id = phase.get("phase")
        if not isinstance(phase_id, str):
            raise TaskBoardError("missing phase")
        path = root / "docs/state/pr-tasks" / (phase_id + ".json")
        manifest = load_manifest(path)
        if (
            manifest["phase"] != phase_id or
            manifest["branch"] != phase.get("active_branch") or
            manifest["pr_number"] != phase.get("primary_pr")
        ):
            raise TaskBoardError("PR task manifest does not match active phase")
        expected_pr = os.environ.get("ZYNOA_CI_PR_NUMBER", "")
        if expected_pr:
            if not expected_pr.isascii() or not expected_pr.isdecimal():
                raise TaskBoardError("CI PR number invalid")
            if manifest["pr_number"] != int(expected_pr):
                raise TaskBoardError("CI PR does not match task manifest")
        print(json.dumps({
            "status": "PR_TASKS_VALID", "phase": phase_id,
            "pr_number": manifest["pr_number"], **summary(manifest),
        }, sort_keys=True))
        return 0
    except (OSError, ValueError, TaskBoardError, UnicodeError):
        print(json.dumps({"status": "PR_TASKS_BLOCKED", "secret_output": False}))
        return 2


if __name__ == "__main__":
    raise SystemExit(main())
