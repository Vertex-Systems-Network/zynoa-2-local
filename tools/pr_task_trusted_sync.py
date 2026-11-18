#!/usr/bin/env python3
"""Trusted default-branch GitHub Actions PR task-table synchronizer.

Only RUN THIS FILE FROM TRUSTED MAIN. Never checkout/run a PR head with the
Pull Requests(write) token. PR head is read as bounded JSON data ONLY.
The source must be approved under protected main policy before deployment.
"""
from __future__ import annotations

import argparse
import base64
import binascii
import json
import os
import re
import urllib.error
import urllib.parse
import urllib.request
from pathlib import Path
from typing import Callable, Mapping

from tools.phase_controller import PHASE_ORDER
from tools.pr_task_board import (
    TaskBoardError, _GitHubJson, _NoRedirect, _REPO, _SHA,
    _json_load, sync_task_board, validate_manifest,
)


def _read_file_at_commit(token: str, sha: str, path: str) -> dict:
    if not _SHA.fullmatch(sha) or not path.startswith("docs/state/"):
        raise TaskBoardError("invalid trusted file lookup")
    if path != "docs/state/PHASE.json" and not re.fullmatch(
        r"docs/state/pr-tasks/(P(?:0[0-9]|1[0-2])|P08I)\.json", path
    ):
        raise TaskBoardError("file path not allowlisted")
    url = (
        "https://api.github.com/repos/" + _REPO +
        "/contents/" + urllib.parse.quote(path, safe="/") +
        "?ref=" + sha
    )
    req = urllib.request.Request(
        url, headers={
            "Authorization": "Bearer " + token,
            "Accept": "application/vnd.github+json",
            "X-GitHub-Api-Version": "2022-11-28",
            "User-Agent": "Zynoa-Trusted-PR-Board/1",
        },
    )
    try:
        with urllib.request.build_opener(_NoRedirect).open(req, timeout=15) as result:
            if result.status != 200:
                raise TaskBoardError("GitHub contents unavailable")
            raw = result.read(85_000)
        if len(raw) >= 85_000:
            raise TaskBoardError("GitHub contents too large")
        payload = json.loads(raw)
    except urllib.error.HTTPError as exc:
        raise TaskBoardError("GitHub contents HTTP " + str(exc.code)) from None
    except (urllib.error.URLError, UnicodeError, OSError, ValueError):
        raise TaskBoardError("GitHub contents read failed") from None
    if not isinstance(payload, dict) or payload.get("encoding") != "base64":
        raise TaskBoardError("GitHub contents encoding invalid")
    content = payload.get("content")
    if not isinstance(content, str) or len(content) > 60_000:
        raise TaskBoardError("GitHub contents malformed")
    try:
        return _json_load(base64.b64decode(content.replace("\n", "").replace("\r", ""), validate=True))
    except (ValueError, UnicodeError, binascii.Error):
        raise TaskBoardError("GitHub contents malformed") from None


def run_trusted_sync(
    event: Mapping, token: str, *,
    enabled: bool,
    file_loader: Callable = _read_file_at_commit,
    pr_transport: Callable | None = None,
    writer: Callable = sync_task_board,
) -> dict:
    """Reconcile current PR head against success-event and validated JSON.

    GitHub workflow_run events are untrusted signals. The readback of current
    PR head, repo identity, phase state and manifest is mandatory. Source code
    from PR head is never executed, imported, checked out or shelled.
    """
    if not enabled or not isinstance(token, str) or not token:
        raise TaskBoardError("trusted task-table writer not provisioned")
    if not isinstance(event, Mapping):
        raise TaskBoardError("workflow event invalid")
    run = event.get("workflow_run")
    if not isinstance(run, dict):
        raise TaskBoardError("not a workflow_run event")
    if run.get("event") != "pull_request" or run.get("conclusion") != "success":
        return {"status": "SKIPPED_NON_SUCCESS_PR_RUN", "github_writes": 0}
    head_repo = run.get("head_repository")
    if not isinstance(head_repo, dict) or head_repo.get("full_name") != _REPO:
        return {"status": "SKIPPED_UNTRUSTED_REPOSITORY", "github_writes": 0}
    sha = run.get("head_sha")
    if not isinstance(sha, str) or not _SHA.fullmatch(sha):
        raise TaskBoardError("event missing exact commit SHA")
    prs = run.get("pull_requests")
    if not isinstance(prs, list) or len(prs) != 1:
        return {"status": "SKIPPED_AMBIGUOUS_PR", "github_writes": 0}
    pr_info = prs[0]
    number = pr_info.get("number") if isinstance(pr_info, dict) else None
    if type(number) is not int or number < 1:
        raise TaskBoardError("invalid triggering PR")
    # Verify LIVE GitHub PR identity first. A stale run must not overwrite
    # the current table on a newer PR head.
    client = _GitHubJson(_REPO, token, pr_transport)
    live = client.request("GET", "/pulls/" + str(number))
    head = live.get("head")
    base = live.get("base")
    if (
        live.get("state") != "open" or
        not isinstance(head, dict) or head.get("sha") != sha or
        not isinstance(head.get("repo"), dict) or
        head["repo"].get("full_name") != _REPO or
        not isinstance(base, dict) or base.get("ref") != "main"
    ):
        return {"status": "SKIPPED_STALE_OR_FOREIGN_PR", "github_writes": 0}

    state = file_loader(token, sha, "docs/state/PHASE.json")
    if not isinstance(state, dict):
        raise TaskBoardError("invalid phase document")
    phase = state.get("phase")
    if phase not in PHASE_ORDER:
        raise TaskBoardError("phase not recognized")
    if (
        state.get("active_branch") != head.get("ref") or
        state.get("primary_pr") != number or
        state.get("phase_status") != "IN_PROGRESS"
    ):
        raise TaskBoardError("phase metadata does not match live primary PR")
    manifest = validate_manifest(
        file_loader(token, sha, "docs/state/pr-tasks/" + phase + ".json")
    )
    if (
        manifest["phase"] != phase or manifest["pr_number"] != number
        or manifest["branch"] != head["ref"]
    ):
        raise TaskBoardError("manifest and live phase diverge")
    return writer(manifest, sha, token, enabled=True, transport=pr_transport)


def main() -> int:
    parser = argparse.ArgumentParser(
        description="Trusted default-branch PR task board updater"
    )
    parser.add_argument("--event-file", type=Path, required=True)
    args = parser.parse_args()
    try:
        if args.event_file.stat().st_size > 128_000:
            raise TaskBoardError("workflow event too large")
        event = json.loads(args.event_file.read_text(encoding="utf-8"))
        result = run_trusted_sync(
            event,
            token=os.environ.get("ZYNOA_PR_TASK_WRITE_TOKEN", ""),
            enabled=os.environ.get("ZYNOA_PR_TASK_WRITE_ENABLED") == "1",
        )
        print(json.dumps(result, sort_keys=True))
        return 0
    except (TaskBoardError, OSError, ValueError, UnicodeError) as exc:
        print(json.dumps({
            "status": "BLOCKED", "error_class": type(exc).__name__,
            "credentials_echoed": False,
        }))
        return 2


if __name__ == "__main__":
    raise SystemExit(main())
