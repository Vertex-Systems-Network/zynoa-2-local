#!/usr/bin/env python3
"""Guarded P00 PR merge executor — disabled unless explicitly provisioned.

This module is never called from PR CI or the desktop application. It requires
independent authenticated GitHub evidence, a non-bypass merge identity and a
separate write token. No unprotected/draft/blocked PR can be merged by it.
"""
from __future__ import annotations

import json
import os
import re
import urllib.error
import urllib.request
from typing import Callable, Mapping

from tools.github_gateway import GitHubGateway, GitHubEvidenceError

_SHA = re.compile(r"^[a-f0-9]{40}$")


class MergeBlocked(RuntimeError):
    pass


class _NoRedirect(urllib.request.HTTPRedirectHandler):
    def redirect_request(self, req, fp, code, msg, headers, newurl):
        raise MergeBlocked("GitHub merge API redirect prohibited")


def merge_http(url: str, token: str, payload: dict) -> dict:
    if not re.fullmatch(r"https://api\.github\.com/repos/[A-Za-z0-9_.-]+/[A-Za-z0-9_.-]+/pulls/[1-9][0-9]*/merge", url):
        raise MergeBlocked("merge endpoint not allowlisted")
    request = urllib.request.Request(
        url, method="PUT",
        headers={
            "Authorization": "Bearer " + token,
            "Accept": "application/vnd.github+json",
            "X-GitHub-Api-Version": "2022-11-28",
            "Content-Type": "application/json",
            "User-Agent": "Zynoa-Guarded-Merge/0.1",
        },
        data=json.dumps(payload, separators=(",", ":")).encode(),
    )
    try:
        with urllib.request.build_opener(_NoRedirect).open(request, timeout=15) as resp:
            if resp.status != 200:
                raise MergeBlocked("GitHub merge returned unexpected status")
            result = json.loads(resp.read(16385).decode("utf-8"))
    except urllib.error.HTTPError as exc:
        # Never log an API response body, which could contain sensitive data.
        raise MergeBlocked("GitHub merge refused (HTTP " + str(exc.code) + ")") from None
    except (urllib.error.URLError, OSError, TimeoutError, ValueError):
        raise MergeBlocked("GitHub merge transport failed") from None
    if not isinstance(result, dict):
        raise MergeBlocked("GitHub merge response invalid")
    return result


class GuardedMerger:
    def __init__(self, reader: GitHubGateway, write_token: str | None = None,
                 enabled: bool = False, transport: Callable = merge_http):
        self.reader = reader
        self.token = write_token if write_token is not None else os.environ.get("ZYNOA_GITHUB_WRITE_TOKEN", "")
        self.enabled = enabled
        self.transport = transport

    @staticmethod
    def verify_premerge(state: Mapping, observed: Mapping) -> None:
        if not observed.get("authenticated_remote"):
            raise MergeBlocked("GitHub evidence not authenticated")
        if observed.get("phase") != state.get("phase"):
            raise MergeBlocked("active phase mismatch")
        if state.get("phase_status") != "IN_PROGRESS":
            raise MergeBlocked("phase must be in progress")
        if observed.get("head_branch") != state.get("active_branch"):
            raise MergeBlocked("phase branch mismatch")
        if observed.get("pr_number") != state.get("primary_pr"):
            raise MergeBlocked("primary PR mismatch")
        if observed.get("base_branch") != "main":
            raise MergeBlocked("PR target must be main")
        if observed.get("merged") or observed.get("draft") or observed.get("pr_state") != "open":
            raise MergeBlocked("PR already merged, draft or not open")
        if observed.get("mergeable") is not True:
            raise MergeBlocked("GitHub has not confirmed PR mergeability")
        if (observed.get("checks_passed") is not True
                or observed.get("workflow_provenance_verified") is not True
                or observed.get("workflow_source_verified") is not True
                or observed.get("branch_protected") is not True
                or observed.get("rules_policy_verified") is not True):
            raise MergeBlocked("trusted CI provenance or branch protection not verified")
        if observed.get("auto_merge_available") is not True:
            raise MergeBlocked("repository auto-merge policy not enabled")
        # A count of zero is meaningless without an independently configured
        # phase-scoped blocker policy. Refuse absent, null, or bool values;
        # P01 has no trusted scope yet and therefore remains unmergeable.
        if observed.get("blocker_policy_complete") is not True:
            raise MergeBlocked("independent critical-blocker policy not verified")
        if state.get("phase") != "P00" and not re.fullmatch(
            r"[0-9a-f]{64}", str(observed.get("issue_inventory_fingerprint") or "")
        ):
            raise MergeBlocked("independent phase issue inventory fingerprint missing")
        count = observed.get("open_critical_blockers")
        if type(count) is not int or count != 0:
            raise MergeBlocked("critical-blocker inventory missing or nonzero")
        for key in ("pr_head_sha", "base_sha", "main_sha"):
            if not _SHA.fullmatch(str(observed.get(key) or "")):
                raise MergeBlocked("missing GitHub SHA evidence")
        if observed["base_sha"] != observed["main_sha"]:
            raise MergeBlocked("PR base does not match latest main")

    def merge_current(self, state: Mapping) -> dict:
        if not self.enabled or not self.token or "\n" in self.token:
            raise MergeBlocked("merge write authority disabled")
        observed = self.reader.observe(state)
        self.verify_premerge(state, observed)
        # Check main again just before the mutation; head_sha is also supplied
        # to GitHub's merge endpoint to reject a stale PR head.
        main_sha = (self.reader.branch("main").get("commit") or {}).get("sha")
        if main_sha != observed["main_sha"]:
            raise MergeBlocked("main advanced during merge preflight")
        # Re-fetch PR, trusted checks/rules and every independently labelled
        # open issue immediately before the write. A changing PR, a newly
        # opened blocker, or a relabelled nonblocker must invalidate this
        # attempt; GitHub's head SHA parameter additionally rejects a stale
        # head at the merge endpoint itself.
        fresh = self.reader.observe(state)
        self.verify_premerge(state, fresh)
        unchanged = (
            "pr_head_sha", "base_sha", "main_sha",
            "head_branch", "base_branch", "pr_number",
            "blocker_policy_complete", "open_critical_blockers",
            "blocker_issue_numbers", "unclassified_issue_numbers",
            "issue_scope_source", "issue_inventory_fingerprint",
            "workflow_source_verified",
        )
        if any(fresh.get(key) != observed.get(key) for key in unchanged):
            raise MergeBlocked("GitHub PR or issue-scope evidence changed during merge preflight")
        observed = fresh
        url = (
            "https://api.github.com/repos/" + self.reader.repo
            + "/pulls/" + str(state["primary_pr"]) + "/merge"
        )
        result = self.transport(url, self.token, {
            "sha": observed["pr_head_sha"],
            "merge_method": "squash",
            "commit_title": "phase(" + str(state["phase"]) + "): verified delivery",
        })
        if result.get("merged") is not True or not _SHA.fullmatch(str(result.get("sha") or "")):
            raise MergeBlocked("merge result unverified; query GitHub before retry")
        # The PR and branch may be updated concurrently. Never claim a verified
        # next-phase transition from the response alone.
        after = self.reader.observe(state)
        verified = bool(
            after.get("merged") and after.get("merge_sha") == result["sha"]
            and after.get("main_matches_merge")
        )
        return {
            "merge_api_accepted": True,
            "merge_sha": result["sha"],
            "remote_merge_verified": verified,
            "next_phase_started": False,
            "phase": state["phase"],
            "pr_number": state["primary_pr"],
        }


def main() -> int:
    """Operator entrypoint; default inspection never mutates GitHub."""
    import argparse
    from pathlib import Path

    parser = argparse.ArgumentParser(description="Guarded GitHub phase merge (default dry-run)")
    parser.add_argument("--repo", default="Vertex-Systems-Network/zynoa-2-local")
    parser.add_argument("--state", type=Path, default=Path("docs/state/PHASE.json"))
    parser.add_argument("--apply", action="store_true")
    args = parser.parse_args()
    try:
        state = json.loads(args.state.read_text(encoding="utf-8"))
        reader = GitHubGateway(args.repo)
        if args.apply:
            enabled = os.environ.get("ZYNOA_ENABLE_MERGE") == "1"
            result = GuardedMerger(reader, enabled=enabled).merge_current(state)
        else:
            observed = reader.observe(state)
            GuardedMerger.verify_premerge(state, observed)
            result = {
                "status": "ELIGIBLE_FOR_SEPARATELY_AUTHORIZED_MERGE",
                "pr_number": observed["pr_number"],
                "branch": observed["head_branch"],
                "commit": observed["pr_head_sha"],
                "merge_performed": False,
            }
        print(json.dumps(result, indent=2))
        return 0
    except (MergeBlocked, GitHubEvidenceError, OSError, ValueError) as exc:
        print(json.dumps({
            "status": "BLOCKED", "error_class": type(exc).__name__,
            "merge_performed": False, "credentials_echoed": False,
        }))
        return 2


if __name__ == "__main__":
    raise SystemExit(main())
