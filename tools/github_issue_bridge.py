#!/usr/bin/env python3
"""Privacy-scoped developer-only GitHub incident issue bridge (opt-in to writing).

End-user telemetry must NEVER use this direct repo credential path. Requires a
separate, scoped Issues:write token and explicit environment authorization.
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
from typing import Callable, Mapping

from tools.incident_router import sanitize

API = "https://api.github.com"
_REPO = re.compile(r"^[a-zA-Z0-9_.-]+/[a-zA-Z0-9_.-]+$")
_FP = re.compile(r"^[a-f0-9]{32}$")
_FULL_SHA = re.compile(r"^[a-f0-9]{40}$")
_RUN_ROUTE = re.compile(r"^/actions/runs/[1-9][0-9]{0,15}$")
_ISSUE_ROUTE = re.compile(r"^/issues/[1-9][0-9]{0,11}$")
_ALLOWED_CI_EVENT = frozenset(("pull_request", "push"))
_MAX_RUN_EVIDENCE = 5


class IncidentPublishError(RuntimeError):
    pass


class _NoRedirect(urllib.request.HTTPRedirectHandler):
    def redirect_request(self, req, fp, code, msg, headers, newurl):
        raise IncidentPublishError("unexpected GitHub issue API redirect")


def issue_http(method: str, url: str, headers: Mapping[str, str],
               payload: bytes | None, timeout: float):
    if method not in ("GET", "POST", "PATCH") or not url.startswith(API + "/repos/"):
        raise IncidentPublishError("unexpected issue gateway request")
    request = urllib.request.Request(url, method=method, headers=dict(headers), data=payload)
    opener = urllib.request.build_opener(_NoRedirect)
    try:
        with opener.open(request, timeout=timeout) as response:
            data = response.read(2_000_001)
            if len(data) > 2_000_000:
                raise IncidentPublishError("GitHub issue response too large")
            return json.loads(data.decode("utf-8"))
    except urllib.error.HTTPError as exc:
        # Never echo HTTP body: it can contain confidential source text.
        raise IncidentPublishError("GitHub issue API returned HTTP " + str(exc.code)) from None
    except (urllib.error.URLError, OSError, TimeoutError, ValueError):
        raise IncidentPublishError("GitHub issue transport unavailable") from None


class DeveloperIssueBridge:
    def __init__(self, repo: str, token: str | None = None, publish_enabled: bool = False,
                 transport: Callable = issue_http):
        if not _REPO.fullmatch(repo) or ".." in repo:
            raise ValueError("invalid repository")
        self.repo = repo
        self.token = token if token is not None else os.environ.get("ZYNOA_ISSUE_TOKEN", "")
        self.publish_enabled = publish_enabled
        self.transport = transport

    def _request(self, method: str, route: str, payload: dict | None = None):
        if not self.publish_enabled or not self.token:
            raise IncidentPublishError("developer issue publishing is not authorized")
        issue_list = (
            "/issues?state=all&per_page=100&page=1",
            "/issues?state=all&per_page=100&page=2",
            "/issues?state=all&per_page=100&page=3",
            "/issues?state=all&per_page=100&page=4",
        )
        allowed = (
            (method == "GET" and
             (route in issue_list or _RUN_ROUTE.fullmatch(route) is not None))
            or (method == "POST" and route == "/issues")
            or (method == "PATCH" and _ISSUE_ROUTE.fullmatch(route) is not None)
        )
        if not allowed:
            raise IncidentPublishError("disallowed issue API route")
        headers = {
            "Authorization": "Bearer " + self.token,
            "Accept": "application/vnd.github+json",
            "X-GitHub-Api-Version": "2022-11-28",
            "Content-Type": "application/json",
            "User-Agent": "Zynoa-Dev-Incident-Bridge/0.1",
        }
        body = json.dumps(payload, separators=(",", ":")).encode() if payload is not None else None
        return self.transport(method, API + "/repos/" + self.repo + route, headers, body, 12.0)

    def _verified_ci_run(self, run_id: int | None, commit_sha: str | None) -> dict | None:
        """Read back a failed GitHub Actions governance run before issue write.

        Never trust a PR-controlled issue body, run URL, job logs or user-supplied
        reporter fields as evidence. Only a trusted workflow_run event or an
        independently authorized maintainer can provide run_id and head SHA.
        """
        if run_id is None and commit_sha is None:
            return None  # Backwards compatible legacy bridge; no CI proof
        if type(run_id) is not int or not 0 < run_id <= 9999999999999999:
            raise IncidentPublishError("invalid CI run identifier")
        if not isinstance(commit_sha, str) or not _FULL_SHA.fullmatch(commit_sha):
            raise IncidentPublishError("invalid CI commit SHA")
        data = self._request("GET", "/actions/runs/" + str(run_id))
        if not isinstance(data, dict):
            raise IncidentPublishError("CI run readback invalid")
        repo = data.get("head_repository")
        if (
            type(data.get("id")) is not int or data["id"] != run_id
            or data.get("head_sha") != commit_sha
            or data.get("status") != "completed"
            or data.get("conclusion") != "failure"
            or data.get("name") != "Governance v3.2"
            or data.get("event") not in _ALLOWED_CI_EVENT
            or not isinstance(repo, dict)
            or repo.get("full_name") != self.repo
        ):
            raise IncidentPublishError("CI run identity/conclusion not verified")
        return {
            "id": run_id, "sha": commit_sha,
            "url": "https://github.com/" + self.repo +
                   "/actions/runs/" + str(run_id),
        }

    @staticmethod
    def _safe_existing_runs(text: object, repo: str) -> list[tuple[int, str]]:
        """Preserve only strict canonical run markers, not arbitrary issue text."""
        if not isinstance(text, str):
            return []
        marker = re.compile(
            r"<!-- zynoa-ci-run:([1-9][0-9]{0,15}):([a-f0-9]{40}) -->"
        )
        found = []
        for hit in marker.finditer(text[:16000]):
            ident, sha = int(hit.group(1)), hit.group(2)
            if (ident, sha) not in found:
                found.append((ident, sha))
        return found[-_MAX_RUN_EVIDENCE:]

    @classmethod
    def _evidence_body(cls, safe: dict, repo: str, history: list[tuple[int, str]]) -> dict:
        issue = cls.format_issue(safe)
        if not history:
            return issue
        rows = []
        for ident, sha in history[-_MAX_RUN_EVIDENCE:]:
            rows.append(
                "- [GitHub Actions run " + str(ident) + "](" +
                "https://github.com/" + repo + "/actions/runs/" +
                str(ident) + "), commit `" + sha + "`" +
                " <!-- zynoa-ci-run:" + str(ident) + ":" + sha + " -->"
            )
        issue["body"] += "\n\n## Verified GitHub CI failure run(s)\n\n" + "\n".join(rows)
        return issue

    @staticmethod
    def safe_record(event: dict) -> dict:
        if event.get("source_type") != "developer-ci":
            raise IncidentPublishError("end-user incident cannot be posted directly to GitHub")
        sanitized = sanitize(event)
        if sanitized["severity"] == "P0":
            raise IncidentPublishError("P0 security incidents require private reporting")
        if not _FP.fullmatch(sanitized["fingerprint"]):
            raise IncidentPublishError("invalid incident fingerprint")
        return sanitized

    @classmethod
    def format_issue(cls, record: dict) -> dict:
        # Do not include raw stacks, file paths, prompts or source code.
        title = "[DEV INCIDENT][" + record["severity"] + "] " + record["module"] + " " + record["error_code"]
        body = (
            "## Sanitized development incident\n\n"
            "- Module: `" + record["module"] + "`\n"
            "- Error code: `" + record["error_code"] + "`\n"
            "- Error class: " + record["message_class"] + "\n"
            "- Severity: " + record["severity"] + "\n"
            "- Version band: " + record["app_version"] + "\n"
            "- Status: **unverified; requires reproduction and a regression test**\n\n"
            "No raw code, prompts, paths, token or user data is attached.\n\n"
            "<!-- zynoa-incident:" + record["fingerprint"] + " -->"
        )
        return {"title": title[:200], "body": body}

    def publish(self, event: dict, *,
                run_id: int | None = None,
                commit_sha: str | None = None) -> dict:
        record = self.safe_record(event)
        if not self.publish_enabled or not self.token:
            raise IncidentPublishError("publishing disabled")
        # Fail-closed independent readback happens BEFORE issue scanning/POST.
        run = self._verified_ci_run(run_id, commit_sha)
        marker = "<!-- zynoa-incident:" + record["fingerprint"] + " -->"
        for page in range(1, 5):
            result = self._request(
                "GET", "/issues?state=all&per_page=100&page=" + str(page)
            )
            if not isinstance(result, list):
                raise IncidentPublishError("invalid issues list; no issue created")
            for item in result:
                if not isinstance(item, dict) or "pull_request" in item:
                    continue
                if marker not in str(item.get("body") or ""):
                    continue
                # The privileged default-branch workflow may update only
                # its own bot-authored issues. A public user can copy markers.
                identity = item.get("user")
                if (not isinstance(identity, dict) or
                        identity.get("login") != "github-actions[bot]" or
                        item.get("title") != self.format_issue(record)["title"]):
                    raise IncidentPublishError(
                        "incident marker matched an untrusted issue"
                    )
                number, url = item.get("number"), item.get("html_url")
                if (type(number) is not int or not 0 < number <= 999999999999
                    or url != "https://github.com/" + self.repo +
                       "/issues/" + str(number)):
                    raise IncidentPublishError("matching incident has invalid issue identity")
                if run is None:
                    return {
                        "status": "EXISTING", "fingerprint": record["fingerprint"],
                        "issue_number": number, "issue_url": url,
                    }
                history = self._safe_existing_runs(item.get("body"), self.repo)
                if (run["id"], run["sha"]) in history:
                    return {
                        "status": "EXISTING", "fingerprint": record["fingerprint"],
                        "issue_number": number, "issue_url": url,
                        "ci_run_verified": True, "run_id": run["id"],
                    }
                history.append((run["id"], run["sha"]))
                payload = self._evidence_body(record, self.repo, history)
                updated = self._request("PATCH", "/issues/" + str(number), payload)
                if (not isinstance(updated, dict)
                    or updated.get("number") != number
                    or updated.get("html_url") != url
                    or payload["body"] != updated.get("body")):
                    raise IncidentPublishError(
                        "issue update response unverified; inspect remote before retry"
                    )
                return {
                    "status": "UPDATED", "fingerprint": record["fingerprint"],
                    "issue_number": number, "issue_url": url,
                    "ci_run_verified": True, "run_id": run["id"],
                }
            if len(result) < 100:
                break
        else:
            raise IncidentPublishError("issue deduplication scan incomplete")
        payload = self._evidence_body(
            record, self.repo,
            [] if run is None else [(run["id"], run["sha"])]
        )
        created = self._request("POST", "/issues", payload)
        if not isinstance(created, dict):
            raise IncidentPublishError("issue creation response invalid")
        number, url = created.get("number"), created.get("html_url")
        if (type(number) is not int or number <= 0 or
                url != "https://github.com/" + self.repo + "/issues/" + str(number)):
            raise IncidentPublishError(
                "issue created but response cannot be verified; recheck remote"
            )
        if run is not None and payload["body"] != created.get("body"):
            raise IncidentPublishError(
                "issue created but evidence was not verified in response"
            )
        result = {
            "status": "CREATED", "fingerprint": record["fingerprint"],
            "issue_number": number, "issue_url": url,
        }
        if run is not None:
            result["ci_run_verified"] = True
            result["run_id"] = run["id"]
        return result


def main() -> int:
    cli = argparse.ArgumentParser(description="Sanitized developer incident preview or scoped issue publish")
    cli.add_argument("--event", required=True, type=Path)
    cli.add_argument("--repo", default="Vertex-Systems-Network/zynoa-2-local")
    cli.add_argument("--publish", action="store_true")
    args = cli.parse_args()
    try:
        record = DeveloperIssueBridge.safe_record(json.loads(args.event.read_text(encoding="utf-8")))
        if not args.publish:
            print(json.dumps({"mode": "LOCAL_PREVIEW", "record": record}, indent=2))
            return 0
        authorized = os.environ.get("ZYNOA_ISSUE_PUBLISH_ENABLED") == "1"
        result = DeveloperIssueBridge(args.repo, publish_enabled=authorized).publish(
            json.loads(args.event.read_text(encoding="utf-8"))
        )
        print(json.dumps(result, indent=2))
        return 0
    except (IncidentPublishError, OSError, ValueError) as exc:
        print(json.dumps({"status": "BLOCKED", "error_class": type(exc).__name__,
                          "credentials_echoed": False}))
        return 2


if __name__ == "__main__":
    raise SystemExit(main())
