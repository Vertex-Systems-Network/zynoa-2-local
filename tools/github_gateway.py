#!/usr/bin/env python3
"""Authenticated, read-only GitHub evidence gateway for P00.

No merge, branch creation, issue posting or remote mutation is performed here.
A configured token and successful GitHub API roundtrips are required to claim
authenticated_remote. An unverified or incomplete response fails closed.
"""
from __future__ import annotations

import json
import os
import re
import urllib.error
import urllib.parse
import urllib.request
from typing import Any, Callable, Mapping

_API = "https://api.github.com"
_REPO_PATTERN = re.compile(r"^[a-zA-Z0-9_.-]+/[a-zA-Z0-9_.-]+$")
_SHA_PATTERN = re.compile(r"^[0-9a-f]{40}$")


class GitHubEvidenceError(RuntimeError):
    """A remote fact cannot be authenticated or validated."""


class _NoRedirect(urllib.request.HTTPRedirectHandler):
    def redirect_request(self, req, fp, code, msg, headers, newurl):
        raise GitHubEvidenceError("unexpected GitHub API redirect")


def http_json(method: str, url: str, headers: Mapping[str, str], data: bytes | None, timeout: float) -> Any:
    """Minimal stdlib HTTP client; never includes credentials in exceptions."""
    if not url.startswith(_API + "/") or method != "GET" or data is not None:
        raise GitHubEvidenceError("disallowed network destination or method")
    request = urllib.request.Request(url, headers=dict(headers), method=method)
    opener = urllib.request.build_opener(_NoRedirect)
    try:
        with opener.open(request, timeout=timeout) as response:
            if response.status != 200:
                raise GitHubEvidenceError("unexpected GitHub status " + str(response.status))
            payload = response.read(1_048_577)
            if len(payload) > 1_048_576:
                raise GitHubEvidenceError("GitHub response too large")
            result = json.loads(payload.decode("utf-8"))
    except urllib.error.HTTPError as exc:
        # The body may include sensitive data; do not echo it or the headers.
        if exc.code in (401, 403):
            raise GitHubEvidenceError("GitHub access unavailable (authentication or permission)") from None
        if exc.code == 404:
            raise GitHubEvidenceError("GitHub resource missing or inaccessible") from None
        if exc.code in (429, 500, 502, 503, 504):
            raise GitHubEvidenceError("temporary GitHub API failure") from None
        raise GitHubEvidenceError("GitHub API request failed") from None
    except (urllib.error.URLError, TimeoutError, OSError) as exc:
        raise GitHubEvidenceError("GitHub network unavailable") from None
    except (json.JSONDecodeError, UnicodeError, ValueError):
        raise GitHubEvidenceError("invalid GitHub JSON response") from None
    if not isinstance(result, (dict, list)):
        raise GitHubEvidenceError("unexpected GitHub response shape")
    return result


class GitHubGateway:
    """Repository-constrained authenticated REST evidence, read-only by design."""

    def __init__(
        self, repo: str, token: str | None = None,
        transport: Callable[[str, str, Mapping[str, str], bytes | None, float], dict] = http_json,
        timeout: float = 12.0,
    ):
        if not _REPO_PATTERN.fullmatch(repo) or ".." in repo:
            raise ValueError("invalid repository name")
        self.repo = repo
        self.token = token if token is not None else os.environ.get("ZYNOA_GITHUB_TOKEN", "")
        if not self.token or "\n" in self.token or "\r" in self.token:
            raise GitHubEvidenceError("ZYNOA_GITHUB_TOKEN is not configured")
        self.transport = transport
        self.timeout = timeout

    def _get(self, suffix: str, params: Mapping[str, str] | None = None) -> Any:
        if (suffix and not suffix.startswith("/")) or ".." in suffix or "://" in suffix or "#" in suffix:
            raise GitHubEvidenceError("unsafe API route")
        query = ("?" + urllib.parse.urlencode(params)) if params else ""
        return self.transport(
            "GET", _API + "/repos/" + self.repo + suffix + query,
            {
                "Accept": "application/vnd.github+json",
                "Authorization": "Bearer " + self.token,
                "X-GitHub-Api-Version": "2022-11-28",
                "User-Agent": "Zynoa-Phase-Controller/0.1",
            },
            None, self.timeout,
        )

    def pull_request(self, number: int) -> dict:
        if type(number) is not int or number < 1:
            raise GitHubEvidenceError("invalid PR number")
        return self._get("/pulls/" + str(number))

    def branch(self, name: str) -> dict:
        if not name or not re.fullmatch(r"[A-Za-z0-9/_.-]+", name) or ".." in name:
            raise GitHubEvidenceError("invalid branch name")
        return self._get("/branches/" + urllib.parse.quote(name, safe=""))

    def check_runs(self, sha: str) -> dict:
        if not _SHA_PATTERN.fullmatch(sha):
            raise GitHubEvidenceError("invalid commit SHA")
        return self._get("/commits/" + sha + "/check-runs", {"per_page": "100"})

    def issue(self, number: int) -> dict:
        if type(number) is not int or number < 1:
            raise GitHubEvidenceError("invalid issue number")
        return self._get("/issues/" + str(number))

    def repo_settings(self) -> dict:
        return self._get("")

    def effective_rules(self, branch: str) -> list[dict]:
        """Read applied GitHub rules, not just a branch.protected boolean."""
        if not re.fullmatch(r"[A-Za-z0-9/_.-]+", branch) or ".." in branch:
            raise GitHubEvidenceError("invalid rules branch")
        rules = self._get("/rules/branches/" + urllib.parse.quote(branch, safe=""))
        if not isinstance(rules, list) or not all(isinstance(rule, dict) for rule in rules):
            raise GitHubEvidenceError("effective rules response unavailable")
        return rules

    @staticmethod
    def _trusted_required_policy(rules: list[dict], required_checks: tuple[str, ...],
                                 observed_checks: dict) -> bool:
        """Require PR rule + status checks pinned to a trusted GitHub App ID."""
        if not required_checks or not isinstance(rules, list):
            return False
        has_pr_gate = any(rule.get("type") == "pull_request" for rule in rules)
        pinned = {}
        for rule in rules:
            if rule.get("type") != "required_status_checks":
                continue
            params = rule.get("parameters")
            if not isinstance(params, dict):
                continue
            checks = params.get("required_status_checks")
            if not isinstance(checks, list):
                continue
            for check in checks:
                if not isinstance(check, dict):
                    continue
                context = check.get("context")
                integration_id = check.get("integration_id")
                if isinstance(context, str) and type(integration_id) is int and integration_id > 0:
                    pinned[context] = integration_id
        if not has_pr_gate:
            return False
        for name in required_checks:
            if name not in pinned:
                return False
            matches = observed_checks.get(name)
            if not isinstance(matches, list) or len(matches) != 1:
                return False
            app = matches[0].get("app")
            if not isinstance(app, dict) or app.get("id") != pinned[name]:
                return False
        return True

    def observe(self, state: Mapping[str, Any], required_checks: tuple[str, ...] = ("governance-lint",),
                blocker_numbers: tuple[int, ...] = (3,)) -> dict:
        """Live authoritative observation. Read-only; not a merge authorization.

        Requires authenticated API success. Missing/stale/ambiguous checks or
        inaccessible blockers make readiness False. Never trust state file alone.
        """
        phase_branch, number = state.get("active_branch"), state.get("primary_pr")
        if not phase_branch or type(number) is not int:
            raise GitHubEvidenceError("active phase branch and primary PR required")
        pr = self.pull_request(number)
        head = pr.get("head") or {}
        base = pr.get("base") or {}
        head_sha = head.get("sha")
        if head.get("ref") != phase_branch or base.get("ref") != "main":
            raise GitHubEvidenceError("remote primary PR branch mismatch")
        if not isinstance(head_sha, str) or not _SHA_PATTERN.fullmatch(head_sha):
            raise GitHubEvidenceError("remote PR SHA invalid")
        main = self.branch("main")
        main_sha = (main.get("commit") or {}).get("sha")
        if not isinstance(main_sha, str) or not _SHA_PATTERN.fullmatch(main_sha):
            raise GitHubEvidenceError("remote main commit invalid")
        check_result = self.check_runs(head_sha)
        all_checks = check_result.get("check_runs")
        if not isinstance(all_checks, list):
            raise GitHubEvidenceError("missing GitHub check runs")
        if check_result.get("total_count", len(all_checks)) > len(all_checks):
            # A single page is not exhaustive; fail closed rather than missing failures.
            checks_passed = False
        else:
            observed = {}
            for check in all_checks:
                if not isinstance(check, dict):
                    raise GitHubEvidenceError("unexpected GitHub check")
                if check.get("head_sha", head_sha) != head_sha:
                    continue
                observed.setdefault(check.get("name"), []).append(check)
            checks_passed = bool(required_checks) and all(
                len(observed.get(name, [])) == 1
                and observed[name][0].get("status") == "completed"
                and observed[name][0].get("conclusion") == "success"
                for name in required_checks
            )
            # Required passed checks do not excuse any failed workflow check.
            if any(c.get("status") == "completed" and c.get("conclusion") in ("failure", "timed_out", "cancelled")
                   for c in all_checks):
                checks_passed = False
        open_blockers = []
        for issue_number in blocker_numbers:
            issue = self.issue(issue_number)
            if issue.get("number") != issue_number or issue.get("state") not in ("open", "closed"):
                raise GitHubEvidenceError("blocker issue response ambiguous")
            if issue["state"] == "open":
                open_blockers.append(issue_number)
        repo_settings = self.repo_settings()
        auto_merge_available = repo_settings.get("allow_auto_merge") is True
        branch_protected = main.get("protected") is True
        # The protected flag alone is insufficient. A rule may protect only
        # deletions or pushes without requiring CI or pull requests. Require
        # applied PR and required-status rules pinned to the expected check app.
        rules_policy_verified = False
        if branch_protected and checks_passed:
            try:
                rules = self.effective_rules("main")
                rules_policy_verified = self._trusted_required_policy(
                    rules, required_checks, observed
                )
            except GitHubEvidenceError:
                # Missing permissions or unsupported rule API: fail closed,
                # but allow CI's read-only observation to report the blocker.
                rules_policy_verified = False
        merged = pr.get("merged") is True or pr.get("merged_at") is not None
        merge_sha = pr.get("merge_commit_sha") if merged else None
        if merged and (not isinstance(merge_sha, str) or not _SHA_PATTERN.fullmatch(merge_sha)):
            raise GitHubEvidenceError("merged PR missing verified merge SHA")
        # A main branch may advance after merge; at merge time SHA equality is
        # required here for a conservative, immediate transition.
        main_matches_merge = bool(merged and main_sha == merge_sha)
        can_proceed = bool(
            merged and main_matches_merge and checks_passed and not open_blockers
            and branch_protected and rules_policy_verified
        )
        return {
            "authenticated_remote": True,
            "repo": self.repo,
            "phase": state.get("phase"),
            "pr_number": number,
            "head_branch": phase_branch,
            "base_branch": "main",
            "pr_head_sha": head_sha,
            "main_sha": main_sha,
            "merged": bool(merged),
            "merge_sha": merge_sha,
            "main_matches_merge": main_matches_merge,
            "checks_passed": checks_passed,
            "open_critical_blockers": len(open_blockers),
            "blocker_issue_numbers": open_blockers,
            "branch_protected": branch_protected,
            "rules_policy_verified": rules_policy_verified,
            "auto_merge_available": auto_merge_available,
            "draft": pr.get("draft") is True,
            "pr_state": pr.get("state"),
            "mergeable": pr.get("mergeable") is True,
            "base_sha": (base.get("sha") if isinstance(base.get("sha"), str) else None),
            "transition_ready": can_proceed,
        }
