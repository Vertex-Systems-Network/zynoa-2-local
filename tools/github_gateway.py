#!/usr/bin/env python3
"""Authenticated, read-only GitHub evidence gateway for the active phase.

No merge, branch creation, issue posting or remote mutation is performed here.
A configured token and successful GitHub API roundtrips are required to claim
authenticated_remote. An unverified or incomplete response fails closed.
"""
from __future__ import annotations

import hashlib
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
# The accepted app identity is host-owned policy, not something a branch ruleset
# or PR-authored check can redefine. GitHub Actions App ID is 15368.
_TRUSTED_CHECK_APPS = {"governance-lint": 15368, "workspace-windows": 15368}
_TRUSTED_WORKFLOW_PATH = re.compile(r"^[.]github/workflows/governance[.]yml(?:@[A-Za-z0-9._/-]{1,128})?$")
_TRUSTED_ACTIONS_JOB = re.compile(
    r"^https://github[.]com/Vertex-Systems-Network/zynoa-2-local/"
    r"actions/runs/([1-9][0-9]*)/job/([1-9][0-9]*)$"
)
_APPROVED_REPO = "Vertex-Systems-Network/zynoa-2-local"


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

    def workflow_run(self, run_id: int) -> dict:
        """Authenticate an Actions run, not just a check name/provider."""
        if type(run_id) is not int or not 0 < run_id < 2**63:
            raise GitHubEvidenceError("invalid workflow run ID")
        return self._get("/actions/runs/" + str(run_id))

    def workflow_job(self, job_id: int) -> dict:
        if type(job_id) is not int or not 0 < job_id < 2**63:
            raise GitHubEvidenceError("invalid workflow job ID")
        return self._get("/actions/jobs/" + str(job_id))

    def issue(self, number: int) -> dict:
        if type(number) is not int or number < 1:
            raise GitHubEvidenceError("invalid issue number")
        return self._get("/issues/" + str(number))

    def _phase_open_issue_scope(self, phase: str) -> dict:
        """Classify all open GitHub issues from independent, explicit labels.

        Only issue metadata stored in GitHub (not PR-authored claims or issue
        titles) may certify an issue's phase and merge-blocking disposition.
        Unknown/unlabelled issues keep the phase policy incomplete.
        Pagination and duplicate identities fail closed.
        """
        if not re.fullmatch(r"P[0-9]{2}I?", phase):
            raise GitHubEvidenceError("unsupported phase for open issue classification")
        seen: set[int] = set()
        blocking: list[int] = []
        unclassified: list[int] = []
        classified_labels: list[tuple[int, tuple[str, ...]]] = []
        for page in range(1, 11):
            items = self._get("/issues", {
                "state": "open", "per_page": "100", "page": str(page),
            })
            if not isinstance(items, list) or len(items) > 100:
                raise GitHubEvidenceError("invalid open-issue inventory")
            for item in items:
                if not isinstance(item, dict):
                    raise GitHubEvidenceError("invalid GitHub issue entry")
                number = item.get("number")
                if type(number) is not int or number < 1 or number in seen:
                    raise GitHubEvidenceError("duplicate or invalid GitHub issue ID")
                seen.add(number)
                if item.get("state") != "open":
                    raise GitHubEvidenceError("GitHub open-issue query returned non-open issue")
                if "pull_request" in item:  # /issues includes PRs; never use PR labels as issue policy.
                    continue
                raw = item.get("labels")
                if not isinstance(raw, list) or not all(
                    isinstance(label, dict) and isinstance(label.get("name"), str)
                    for label in raw
                ):
                    unclassified.append(number)
                    continue
                names = [label["name"] for label in raw]
                scopes = [n for n in names if n.startswith("phase:")]
                dispositions = [n for n in names if n.startswith("merge:")]
                if (len(names) != len(set(names))
                        or not scopes
                        or any(not re.fullmatch(r"phase:(?:P[0-9]{2}I?|global)", n)
                               for n in scopes)
                        or len(dispositions) != 1
                        or dispositions[0] not in ("merge:blocker", "merge:nonblocker")):
                    unclassified.append(number)
                    continue
                classified_labels.append((number, tuple(sorted(names))))
                if dispositions[0] == "merge:blocker" and (
                    "phase:" + phase in scopes or "phase:global" in scopes
                ):
                    blocking.append(number)
            if len(items) < 100:
                # Only a fully classified inventory earns an immutable
                # fingerprint. A caller cannot pass an arbitrary count of zero
                # or hide newly opened/relabelled issues between observations.
                fingerprint = None
                if not unclassified:
                    canonical = json.dumps(sorted(classified_labels), separators=(",", ":"))
                    fingerprint = hashlib.sha256(canonical.encode("utf-8")).hexdigest()
                return {
                    "complete": not unclassified,
                    "blocking": sorted(blocking),
                    "unclassified": sorted(unclassified),
                    "issue_count": len(seen),  # GitHub /issues also includes PRs
                    "fingerprint": fingerprint,
                }
        raise GitHubEvidenceError("open-issue inventory pagination exhausted")

    def repo_settings(self) -> dict:
        return self._get("")

    def effective_rules(self, branch: str) -> list[dict]:
        """Read applied GitHub rules, not just a branch.protected boolean."""
        if not re.fullmatch(r"[A-Za-z0-9/_.-]+", branch) or ".." in branch:
            raise GitHubEvidenceError("invalid rules branch")
        try:
            rules = self._get("/rules/branches/" + urllib.parse.quote(branch, safe=""))
        except GitHubEvidenceError:
            # GitHub may deny the legacy effective-rules API to an integration
            # while allowing its repository-scoped active ruleset readback.
            # Never infer protection from branch.protected or a ruleset name.
            return self._active_repository_ruleset_fallback(branch)
        if not isinstance(rules, list) or not all(isinstance(rule, dict) for rule in rules):
            raise GitHubEvidenceError("effective rules response unavailable")
        return rules

    def _active_repository_ruleset_fallback(self, branch: str) -> list[dict]:
        """Fallback only to fully authenticated, enforced, non-bypass main rules.

        Fail closed on incomplete pagination, ambiguous conditions, inherited
        organization policies, or missing rules. Never waive PR/CI provider
        validation: _trusted_required_policy still checks those separately.
        """
        if branch != "main":
            raise GitHubEvidenceError("ruleset fallback supports protected main only")
        rows = self._get("/rulesets", {"includes_parents": "true", "per_page": "100"})
        if not isinstance(rows, list) or len(rows) >= 100:
            raise GitHubEvidenceError("ruleset list incomplete or invalid")
        matching: list[dict] = []
        for row in rows:
            if not isinstance(row, dict):
                raise GitHubEvidenceError("invalid ruleset list entry")
            if row.get("target") != "branch" or row.get("enforcement") != "active":
                continue
            # Without independently checking inheritance and exact target
            # patterns, unknown potentially applied rules are NOT certified.
            if row.get("source_type") != "Repository" or row.get("source") != self.repo:
                raise GitHubEvidenceError("unverified inherited active branch ruleset")
            rule_id = row.get("id")
            if type(rule_id) is not int or rule_id <= 0:
                raise GitHubEvidenceError("active ruleset identifier missing")
            detail = self._get("/rulesets/" + str(rule_id))
            if not isinstance(detail, dict) or (
                detail.get("id") != rule_id
                or detail.get("target") != "branch"
                or detail.get("enforcement") != "active"
                or detail.get("source_type") != "Repository"
                or detail.get("source") != self.repo
            ):
                raise GitHubEvidenceError("ruleset identity or enforcement mismatch")
            condition = detail.get("conditions")
            refs = condition.get("ref_name") if isinstance(condition, dict) else None
            if not isinstance(refs, dict):
                raise GitHubEvidenceError("ruleset target conditions unavailable")
            included, excluded = refs.get("include"), refs.get("exclude")
            if included != ["refs/heads/main"] or excluded != []:
                raise GitHubEvidenceError("ruleset target ambiguous: cannot certify main")
            if detail.get("bypass_actors") != [] or detail.get("current_user_can_bypass") != "never":
                raise GitHubEvidenceError("ruleset bypass not independently denied")
            rules = detail.get("rules")
            if not isinstance(rules, list) or not rules or not all(
                isinstance(rule, dict) for rule in rules
            ):
                raise GitHubEvidenceError("effective ruleset contents missing")
            matching.extend(rules)
        if not matching:
            raise GitHubEvidenceError("no applicable enforced non-bypass main ruleset")
        return matching

    @staticmethod
    def _trusted_required_policy(rules: list[dict], required_checks: tuple[str, ...],
                                 observed_checks: dict) -> bool:
        """Require PR rule + status checks pinned to a trusted GitHub App ID."""
        if not required_checks or not isinstance(rules, list):
            return False
        has_pr_gate = any(
            rule.get("type") == "pull_request"
            and isinstance(rule.get("parameters"), dict)
            and rule["parameters"].get("required_review_thread_resolution") is True
            for rule in rules
        )
        pinned = {}
        for rule in rules:
            if rule.get("type") != "required_status_checks":
                continue
            params = rule.get("parameters")
            if not isinstance(params, dict) or params.get("strict_required_status_checks_policy") is not True:
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
            if name not in pinned or pinned[name] != _TRUSTED_CHECK_APPS.get(name):
                return False
            matches = observed_checks.get(name)
            if not isinstance(matches, list) or len(matches) != 1:
                return False
            app = matches[0].get("app")
            if not isinstance(app, dict) or app.get("id") != pinned[name]:
                return False
        return True

    def _verify_actions_provenance(
        self, observed_checks: Mapping[str, list[dict]],
        required_checks: tuple[str, ...], head_sha: str,
        branch: str, pr_number: int,
    ) -> bool:
        """Link each required check to a trusted Actions run AND exact job.

        The Actions App ID alone does not authenticate a particular workflow.
        This verifies origin, not that PR-editable workflow code is safe.
        """
        runs: dict[int, dict] = {}
        for name in required_checks:
            matches = observed_checks.get(name)
            if not isinstance(matches, list) or len(matches) != 1:
                return False
            check = matches[0]
            if not isinstance(check, dict) or (
                check.get("name") != name or check.get("head_sha") != head_sha
                or check.get("status") != "completed"
                or check.get("conclusion") != "success"
                or not isinstance(check.get("app"), dict)
                or check["app"].get("id") != _TRUSTED_CHECK_APPS.get(name)
            ):
                return False
            details = check.get("details_url")
            match = _TRUSTED_ACTIONS_JOB.fullmatch(details) if isinstance(details, str) else None
            if match is None:
                return False
            run_id, job_id = (int(value) for value in match.groups())
            if run_id >= 2**63 or job_id >= 2**63:
                return False
            suite = check.get("check_suite")
            if not isinstance(suite, dict) or type(suite.get("id")) is not int:
                return False
            if run_id not in runs:
                runs[run_id] = self.workflow_run(run_id)
            run = runs[run_id]
            if not isinstance(run, dict) or (
                run.get("id") != run_id
                or run.get("check_suite_id") != suite["id"]
                or run.get("name") != "Governance v3.2"
                or not isinstance(run.get("path"), str)
                or not _TRUSTED_WORKFLOW_PATH.fullmatch(run["path"])
                or run.get("event") != "pull_request"
                or run.get("status") != "completed"
                or run.get("conclusion") != "success"
                or run.get("head_sha") != head_sha
                or run.get("head_branch") != branch
                or not isinstance(run.get("repository"), dict)
                or run["repository"].get("full_name") != _APPROVED_REPO
                or not isinstance(run.get("head_repository"), dict)
                or run["head_repository"].get("full_name") != _APPROVED_REPO
            ):
                return False
            prs = run.get("pull_requests")
            if not isinstance(prs, list) or not any(
                isinstance(pr, dict) and type(pr.get("number")) is int
                and pr["number"] == pr_number for pr in prs
            ):
                return False
            job = self.workflow_job(job_id)
            if not isinstance(job, dict) or (
                job.get("id") != job_id or job.get("run_id") != run_id
                or job.get("name") != name or job.get("head_sha") != head_sha
                or job.get("status") != "completed"
                or job.get("conclusion") != "success"
            ):
                return False
        return True

    def observe(self, state: Mapping[str, Any], required_checks: tuple[str, ...] = ("governance-lint",),
                blocker_numbers: tuple[int, ...] | None = None) -> dict:
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
            observed = {}
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
        # A same-named check from another Actions workflow is not trustworthy.
        workflow_provenance_verified = False
        if checks_passed:
            try:
                workflow_provenance_verified = self._verify_actions_provenance(
                    observed, required_checks, head_sha, phase_branch, number
                )
            except (GitHubEvidenceError, ValueError, TypeError):
                workflow_provenance_verified = False
        checks_passed = checks_passed and workflow_provenance_verified
        # P00's separately configured historic blocker is retained. For P01+
        # an arbitrary tuple (including ()) must NOT self-certify that all
        # issues have been independently classified. GitHub issue labels must
        # explicitly assign phase and merge disposition for EVERY open issue.
        phase_id = state.get("phase")
        unclassified_issues: list[int] = []
        issue_inventory_fingerprint = None
        issue_scope_source = "legacy_trusted_p00_issue_3"
        if phase_id == "P00":
            if blocker_numbers is None:
                blocker_numbers = (3,)
            if (not isinstance(blocker_numbers, tuple) or not blocker_numbers
                    or any(type(n) is not int or n < 1 for n in blocker_numbers)):
                raise GitHubEvidenceError("invalid P00 configured blocker scope")
            open_blockers = []
            for issue_number in blocker_numbers:
                issue = self.issue(issue_number)
                if issue.get("number") != issue_number or issue.get("state") not in ("open", "closed"):
                    raise GitHubEvidenceError("blocker issue response ambiguous")
                if issue["state"] == "open":
                    open_blockers.append(issue_number)
            blocker_policy_complete = True
        else:
            if blocker_numbers is not None:
                raise GitHubEvidenceError("manual non-P00 blocker tuples are not independent")
            issue_scope_source = "authenticated_github_open_issue_labels"
            try:
                classified = self._phase_open_issue_scope(phase_id)
                blocker_policy_complete = classified["complete"]
                open_blockers = classified["blocking"]
                unclassified_issues = classified["unclassified"]
                issue_inventory_fingerprint = classified["fingerprint"]
            except GitHubEvidenceError:
                blocker_policy_complete = False
                open_blockers = []  # No claim of zero unless scope is complete.

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
            and blocker_policy_complete and branch_protected and rules_policy_verified
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
            "workflow_provenance_verified": workflow_provenance_verified,
            "open_critical_blockers": len(open_blockers) if blocker_policy_complete else None,
            "blocker_issue_numbers": open_blockers,
            "blocker_policy_complete": blocker_policy_complete,
            "unclassified_issue_numbers": unclassified_issues,
            "issue_scope_source": issue_scope_source,
            "issue_inventory_fingerprint": issue_inventory_fingerprint,
            "branch_protected": branch_protected,
            "rules_policy_verified": rules_policy_verified,
            "auto_merge_available": auto_merge_available,
            "draft": pr.get("draft") is True,
            "pr_state": pr.get("state"),
            "mergeable": pr.get("mergeable") is True,
            "base_sha": (base.get("sha") if isinstance(base.get("sha"), str) else None),
            "transition_ready": can_proceed,
        }
