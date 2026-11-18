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


class IncidentPublishError(RuntimeError):
    pass


class _NoRedirect(urllib.request.HTTPRedirectHandler):
    def redirect_request(self, req, fp, code, msg, headers, newurl):
        raise IncidentPublishError("unexpected GitHub issue API redirect")


def issue_http(method: str, url: str, headers: Mapping[str, str],
               payload: bytes | None, timeout: float):
    if method not in ("GET", "POST") or not url.startswith(API + "/repos/"):
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
        if route not in ("/issues?state=all&per_page=100&page=1",
                         "/issues?state=all&per_page=100&page=2",
                         "/issues?state=all&per_page=100&page=3",
                         "/issues?state=all&per_page=100&page=4", "/issues"):
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

    def publish(self, event: dict) -> dict:
        record = self.safe_record(event)
        if not self.publish_enabled or not self.token:
            raise IncidentPublishError("publishing disabled")
        marker = "<!-- zynoa-incident:" + record["fingerprint"] + " -->"
        for page in range(1, 5):
            result = self._request("GET", "/issues?state=all&per_page=100&page=" + str(page))
            if not isinstance(result, list):
                raise IncidentPublishError("invalid issues list; no issue created")
            for item in result:
                if not isinstance(item, dict) or "pull_request" in item:
                    continue
                if marker in str(item.get("body") or ""):
                    return {
                        "status": "EXISTING", "fingerprint": record["fingerprint"],
                        "issue_number": item.get("number"),
                        "issue_url": item.get("html_url"),
                    }
            if len(result) < 100:
                break
        else:
            # Do not create duplicates if search exhausted; route to manual triage.
            raise IncidentPublishError("issue deduplication scan incomplete")
        created = self._request("POST", "/issues", self.format_issue(record))
        number, url = created.get("number"), created.get("html_url")
        if type(number) is not int or not isinstance(url, str) or not url.startswith(
            "https://github.com/" + self.repo + "/issues/"
        ):
            raise IncidentPublishError("issue created but response cannot be verified; recheck remote before retry")
        return {"status": "CREATED", "fingerprint": record["fingerprint"],
                "issue_number": number, "issue_url": url}

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
