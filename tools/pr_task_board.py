#!/usr/bin/env python3
"""Evidence-based PR task board with a protected, managed description region.

Read-only validation/rendering is safe in PR CI. GitHub write synchronization
is ONLY for a separately trusted host or default-branch workflow using a
scoped Pull Requests(write) identity. Never run a PR-supplied script with a
write token. Statuses are version-controlled; this code never declares tasks
successful based solely on test or chat output.
"""
from __future__ import annotations

import argparse
import json
import os
import re
import urllib.error
import urllib.parse
import urllib.request
from pathlib import Path
from typing import Any, Callable, Mapping

from tools.phase_controller import PHASE_ORDER

_START = "<!-- ZYNOA_PR_TASK_BOARD_START v1 -->"
_END = "<!-- ZYNOA_PR_TASK_BOARD_END -->"
_STATES = ("DONE", "IN_PROGRESS", "TODO", "BLOCKED")
_BADGES = {
    "DONE": "✅ Done",
    "IN_PROGRESS": "🔄 In progress",
    "TODO": "⏳ Pending",
    "BLOCKED": "⛔ Blocked",
}
_REPO = "Vertex-Systems-Network/zynoa-2-local"
_ALLOWED_REF = re.compile(
    r"^https://github\.com/Vertex-Systems-Network/zynoa-2-local/"
    r"(?:issues/[1-9][0-9]*|pull/[1-9][0-9]*"
    r"|actions/runs/[1-9][0-9]*|commit/[a-f0-9]{40})$"
)
_SHA = re.compile(r"^[a-f0-9]{40}$")
_BRANCH = re.compile(r"^phase/[a-z0-9][a-z0-9-]{1,90}$")
_TITLE = re.compile(r"^[A-Za-z0-9][A-Za-z0-9 /.,:+()'&_-]{3,114}$")
_ID = re.compile(r"^(P(?:0[0-9]|1[0-2])|P08I)-T([0-9]{2,3})$")
_MAX_BODY = 100_000
_MAX_MANIFEST = 40_000


class TaskBoardError(ValueError):
    pass


class _NoRedirect(urllib.request.HTTPRedirectHandler):
    def redirect_request(self, req, fp, code, msg, headers, newurl):
        raise TaskBoardError("GitHub API redirect not permitted")


def _json_load(data: bytes | str) -> Any:
    if isinstance(data, bytes):
        if len(data) > _MAX_MANIFEST:
            raise TaskBoardError("manifest too large")
        data = data.decode("utf-8")
    if len(data) > _MAX_MANIFEST:
        raise TaskBoardError("manifest too large")
    try:
        return json.loads(data)
    except (ValueError, UnicodeError) as exc:
        raise TaskBoardError("manifest is not valid UTF-8 JSON") from exc


def load_manifest(path: Path) -> dict:
    raw = path.read_bytes()
    return validate_manifest(_json_load(raw))


def validate_manifest(obj: Any) -> dict:
    if not isinstance(obj, dict):
        raise TaskBoardError("manifest root must be a JSON object")
    if set(obj) != {
        "schema_version", "phase", "branch", "pr_number",
        "update_policy", "source_of_truth", "tasks",
    }:
        raise TaskBoardError("unexpected manifest keys")
    if type(obj["schema_version"]) is not int or obj["schema_version"] != 1:
        raise TaskBoardError("unsupported manifest version")
    phase = obj["phase"]
    if phase not in PHASE_ORDER or not isinstance(phase, str):
        raise TaskBoardError("unknown phase")
    branch = obj["branch"]
    if not isinstance(branch, str) or not _BRANCH.fullmatch(branch):
        raise TaskBoardError("invalid branch")
    if phase == "P08I" and branch != "phase/08i-design-interoperability":
        raise TaskBoardError("wrong Designer interop branch")
    if type(obj["pr_number"]) is not int or obj["pr_number"] < 1:
        raise TaskBoardError("invalid primary PR number")
    if obj["update_policy"] != "evidence-gated":
        raise TaskBoardError("only evidence-gated status changes allowed")
    if obj["source_of_truth"] != "docs/state/pr-tasks/" + phase + ".json":
        raise TaskBoardError("manifest path must match active phase")
    tasks = obj["tasks"]
    if not isinstance(tasks, list) or not 1 <= len(tasks) <= 120:
        raise TaskBoardError("task count must be between 1 and 120")
    seen = set()
    previous_number = 0
    for item in tasks:
        if not isinstance(item, dict) or set(item) not in (
            {"id", "title", "status"}, {"id", "title", "status", "reference"},
        ):
            raise TaskBoardError("invalid task item fields")
        identifier = item["id"]
        if not isinstance(identifier, str):
            raise TaskBoardError("invalid task ID")
        match = _ID.fullmatch(identifier)
        if not match or match.group(1) != phase or identifier in seen:
            raise TaskBoardError("task ID is duplicate or belongs to another phase")
        task_number = int(match.group(2))
        if task_number <= previous_number:
            raise TaskBoardError("tasks must have strictly increasing IDs")
        previous_number = task_number
        seen.add(identifier)
        title = item["title"]
        if not isinstance(title, str) or not _TITLE.fullmatch(title):
            raise TaskBoardError("task title contains unsafe markdown/HTML")
        status = item["status"]
        if status not in _STATES:
            raise TaskBoardError("unrecognized task status")
        reference = item.get("reference")
        if reference is not None and (
            not isinstance(reference, str) or not _ALLOWED_REF.fullmatch(reference)
        ):
            raise TaskBoardError("task evidence/reference must be a permitted repo URL")
        if status in ("DONE", "BLOCKED") and not reference:
            raise TaskBoardError("completed and blocked tasks require evidence URLs")
    return obj


def summary(manifest: Mapping) -> dict:
    totals = {key: 0 for key in _STATES}
    for task in manifest["tasks"]:
        totals[task["status"]] += 1
    n = len(manifest["tasks"])
    return {
        "total": n,
        "done": totals["DONE"],
        "in_progress": totals["IN_PROGRESS"],
        "pending": totals["TODO"],
        "blocked": totals["BLOCKED"],
        "percent_done": (100 * totals["DONE"]) // n,
    }


def render(manifest: Mapping) -> str:
    validated = validate_manifest(dict(manifest))
    s = summary(validated)
    out = [
        _START,
        "## Phase " + validated["phase"] + " — Task Progress (Auto-generated)",
        "",
        "**Total:** " + str(s["total"]) +
        " | **Done:** " + str(s["done"]) +
        " | **In progress:** " + str(s["in_progress"]) +
        " | **Pending:** " + str(s["pending"]) +
        " | **Blocked:** " + str(s["blocked"]) +
        " | **Progress:** " + str(s["percent_done"]) + "%",
        "",
        "| ID | Task | Status | Evidence / Blocker |",
        "|---|---|---|---|",
    ]
    for task in validated["tasks"]:
        ref = task.get("reference")
        evidence = ("[View](" + ref + ")") if ref else "—"
        out.append(
            "| `" + task["id"] + "` | " + task["title"] + " | " +
            _BADGES[task["status"]] + " | " + evidence + " |"
        )
    out.extend([
        "",
        "Source: `" + validated["source_of_truth"] + "` on `" +
        validated["branch"] + "`. Status changes require tracked evidence; "
        "**CI pass is not a declaration that the entire phase is complete.**",
        _END,
    ])
    return "\n".join(out)


def merge_into_pr_body(body: str, manifest: Mapping) -> str:
    if not isinstance(body, str) or len(body) > _MAX_BODY:
        raise TaskBoardError("invalid or oversize PR description")
    block = render(manifest)
    if body.count(_START) != body.count(_END) or body.count(_START) > 1:
        raise TaskBoardError("duplicate or mismatched PR task section markers")
    if _START not in body:
        new_body = body.rstrip() + "\n\n" + block + "\n"
    else:
        start = body.index(_START)
        end = body.index(_END)
        if end < start:
            raise TaskBoardError("task section markers in reverse order")
        end += len(_END)
        new_body = body[:start] + block + body[end:]
    if len(new_body) > _MAX_BODY:
        raise TaskBoardError("PR description exceeds size budget")
    return new_body


class _GitHubJson:
    """Allowlisted GitHub API for task-board-only writes."""

    def __init__(self, repo: str, token: str, transport: Callable | None = None):
        if repo != _REPO or not isinstance(token, str) or not token or "\n" in token:
            raise TaskBoardError("repository or scoped token invalid")
        self.repo = repo
        self.token = token
        self.transport = transport

    def request(self, method: str, path: str, payload: dict | None = None) -> dict:
        if not re.fullmatch(r"/pulls/[1-9][0-9]*", path):
            raise TaskBoardError("only one pull request endpoint is allowed")
        if method not in ("GET", "PATCH"):
            raise TaskBoardError("unapproved GitHub mutation")
        if method == "PATCH" and (not isinstance(payload, dict) or set(payload) != {"body"}):
            raise TaskBoardError("only PR description may be modified")
        url = "https://api.github.com/repos/" + self.repo + path
        if self.transport is not None:
            response = self.transport(method, url, payload)
            if not isinstance(response, dict):
                raise TaskBoardError("invalid GitHub response")
            return response
        body = json.dumps(payload, separators=(",", ":")).encode() if payload else None
        req = urllib.request.Request(
            url, method=method, data=body,
            headers={
                "Authorization": "Bearer " + self.token,
                "Accept": "application/vnd.github+json",
                "X-GitHub-Api-Version": "2022-11-28",
                "Content-Type": "application/json",
                "User-Agent": "Zynoa-PR-Task-Board/1",
            },
        )
        try:
            with urllib.request.build_opener(_NoRedirect).open(req, timeout=15) as resp:
                if resp.status != 200:
                    raise TaskBoardError("unexpected PR API response")
                raw = resp.read(_MAX_BODY * 2 + 1)
            if len(raw) > _MAX_BODY * 2:
                raise TaskBoardError("oversize PR API response")
            data = json.loads(raw)
        except urllib.error.HTTPError as exc:
            raise TaskBoardError("GitHub PR API HTTP " + str(exc.code)) from None
        except (urllib.error.URLError, OSError, ValueError, UnicodeError):
            raise TaskBoardError("GitHub PR API transport failed") from None
        if not isinstance(data, dict):
            raise TaskBoardError("invalid PR response")
        return data


def _check_pr_identity(pr: Mapping, manifest: Mapping, expected_sha: str) -> None:
    if not _SHA.fullmatch(expected_sha):
        raise TaskBoardError("expected HEAD SHA must be trusted full Git SHA")
    if pr.get("number") != manifest["pr_number"] or pr.get("state") != "open":
        raise TaskBoardError("PR number/state mismatch")
    head = pr.get("head")
    base = pr.get("base")
    if not isinstance(head, dict) or not isinstance(base, dict):
        raise TaskBoardError("missing PR branch identity")
    if (
        head.get("ref") != manifest["branch"] or
        head.get("sha") != expected_sha or
        base.get("ref") != "main" or
        not isinstance(head.get("repo"), dict) or
        head["repo"].get("full_name") != _REPO
    ):
        raise TaskBoardError("PR branch, base or HEAD does not match current evidence")
    if not isinstance(pr.get("body"), str):
        raise TaskBoardError("PR has no textual description")


def sync_task_board(manifest: dict, expected_sha: str, token: str, *,
                    enabled: bool = False,
                    transport: Callable | None = None) -> dict:
    """Update PR body only when trusted host grants write; re-fetch to verify.

    GitHub PATCH lacks an atomic body revision compare-and-swap. We recheck
    identical HEAD immediately before PATCH, leave all non-managed body
    content intact, and verify readback. Concurrent human PR body edits still
    require a trusted single-writer policy.
    """
    manifest = validate_manifest(manifest)
    if not enabled:
        raise TaskBoardError("PR body synchronization disabled by default")
    client = _GitHubJson(_REPO, token, transport)
    path = "/pulls/" + str(manifest["pr_number"])
    first = client.request("GET", path)
    _check_pr_identity(first, manifest, expected_sha)
    updated = merge_into_pr_body(first["body"], manifest)
    if updated == first["body"]:
        return {"status": "UNCHANGED", "pr_number": manifest["pr_number"], "github_writes": 0}
    latest = client.request("GET", path)
    _check_pr_identity(latest, manifest, expected_sha)
    if latest["body"] != first["body"]:
        raise TaskBoardError("PR description changed during reconciliation")
    client.request("PATCH", path, {"body": updated})
    receipt = client.request("GET", path)
    _check_pr_identity(receipt, manifest, expected_sha)
    if receipt["body"] != updated:
        raise TaskBoardError("PR table write needs reconciliation; do not retry blindly")
    return {"status": "SYNCED_VERIFIED", "pr_number": manifest["pr_number"],
            "github_writes": 1}


def main() -> int:
    parser = argparse.ArgumentParser(description="Versioned PR task tracking")
    parser.add_argument("--manifest", type=Path, required=True)
    actions = parser.add_mutually_exclusive_group(required=True)
    actions.add_argument("--validate", action="store_true")
    actions.add_argument("--print", dest="print_board", action="store_true")
    actions.add_argument("--sync", action="store_true")
    parser.add_argument("--expected-head", default="")
    args = parser.parse_args()
    try:
        manifest = load_manifest(args.manifest)
        if args.validate:
            print(json.dumps({"status": "VALID", "phase": manifest["phase"],
                              **summary(manifest)}, sort_keys=True))
        elif args.print_board:
            print(render(manifest))
        else:
            enabled = os.environ.get("ZYNOA_PR_TASK_WRITE_ENABLED") == "1"
            token = os.environ.get("ZYNOA_PR_TASK_WRITE_TOKEN", "")
            result = sync_task_board(manifest, args.expected_head, token, enabled=enabled)
            print(json.dumps(result, sort_keys=True))
        return 0
    except (TaskBoardError, OSError, UnicodeError) as exc:
        # Do not echo raw token, body, paths or untrusted content.
        print(json.dumps({"status": "BLOCKED", "error_class": type(exc).__name__,
                          "credentials_echoed": False}))
        return 2


if __name__ == "__main__":
    raise SystemExit(main())
