"""Trusted-main-only postmerge receipt publisher; never merges or starts phases.

Writes a sanitized phase-journal receipt as a bot comment on its merged primary
PR. The GitHub record is remotely readable after CI runner shutdown, but can
still be edited/deleted by authorized users; it is not an immutable archive.
"""
from __future__ import annotations

import argparse
import json
import os
import re
import tempfile
import urllib.error
import urllib.request
from pathlib import Path
from typing import Any, Callable, Mapping

from tools.github_gateway import GitHubGateway, GitHubEvidenceError
from tools.phase_controller import EventJournal, PhasePolicyError, next_phase, validate_snapshot

REPO = "Vertex-Systems-Network/zynoa-2-local"
API = "https://api.github.com/repos/" + REPO
_SHA = re.compile(r"^[a-f0-9]{40}$")
_MARKER = "<!-- zynoa-phase-transition:v1:"


class TransitionPublishDenied(RuntimeError):
    """Sanitized refusal without raw HTTP bodies or credentials."""


class _NoRedirect(urllib.request.HTTPRedirectHandler):
    def redirect_request(self, req, fp, code, msg, headers, newurl):
        raise TransitionPublishDenied("unexpected GitHub redirect")


def _post_issue_comment(pr: int, body: str, token: str) -> dict:
    if (type(pr) is not int or not 0 < pr < 1_000_000_000
            or not isinstance(body, str) or len(body) > 4096
            or not isinstance(token, str) or not 8 <= len(token) <= 2048
            or not token.isascii() or any(c.isspace() for c in token)):
        raise TransitionPublishDenied("issue comment write parameters refused")
    url = API + "/issues/" + str(pr) + "/comments"
    req = urllib.request.Request(
        url,
        data=json.dumps({"body": body}, separators=(",", ":")).encode(),
        method="POST",
        headers={
            "Authorization": "Bearer " + token,
            "Accept": "application/vnd.github+json",
            "X-GitHub-Api-Version": "2022-11-28",
            "Content-Type": "application/json",
            "User-Agent": "Zynoa-Verified-Transition-Receipt/1",
        },
    )
    try:
        with urllib.request.build_opener(_NoRedirect).open(req, timeout=12) as response:
            if response.status != 201:
                raise TransitionPublishDenied("GitHub comment was not created")
            raw = response.read(65537)
            if len(raw) > 65536:
                raise TransitionPublishDenied("GitHub response too large")
            result = json.loads(raw.decode("utf-8"))
    except urllib.error.HTTPError:
        raise TransitionPublishDenied("GitHub refused receipt publication") from None
    except (urllib.error.URLError, OSError, UnicodeError, ValueError):
        raise TransitionPublishDenied("GitHub receipt publication unavailable") from None
    if not isinstance(result, dict):
        raise TransitionPublishDenied("GitHub comment response malformed")
    return result


def _verified_comment(obj: object, body: str, pr: int) -> bool:
    return (
        isinstance(obj, dict)
        and type(obj.get("id")) is int and obj["id"] > 0
        and obj.get("body") == body
        and isinstance(obj.get("user"), dict)
        and obj["user"].get("login") == "github-actions[bot]"
        and obj.get("issue_url") == API + "/issues/" + str(pr)
    )


def _receipt_body(source: str, target: str, event_id: str,
                  pr: int, merge_sha: str, fingerprint: str) -> str:
    marker = _MARKER + source + ":" + target + ":" + merge_sha + " -->"
    return (
        "## Verified phase-transition journal receipt (v1)\n\n" + marker
        + "\n\n- Source phase: " + source
        + "\n- Next authorized phase: " + target
        + "\n- Merged primary PR: #" + str(pr)
        + "\n- Verified merge SHA: " + merge_sha
        + "\n- Local verified journal event: " + event_id
        + "\n- Independently labelled issue inventory SHA-256: " + fingerprint
        + "\n\nRecorded after authenticated merge and protected-main checks."
        + " This GitHub comment can be changed or deleted; it is not a"
        + " cryptographic signature, immutable ledger, merge approval,"
        + " or proof the next phase has started."
    )


def _main_ancestry(reader: GitHubGateway, observed: dict, expected_sha: str) -> bool:
    merge_sha, main_sha = observed.get("merge_sha"), observed.get("main_sha")
    if not (isinstance(merge_sha, str) and _SHA.fullmatch(merge_sha)
            and isinstance(main_sha, str) and _SHA.fullmatch(main_sha)
            and isinstance(expected_sha, str) and _SHA.fullmatch(expected_sha)
            and expected_sha == main_sha):
        return False
    if main_sha == merge_sha:
        return observed.get("main_matches_merge") is True
    # A legitimate closeout PR advances protected main. Verify the merged
    # primary PR's exact SHA is an ancestor using GitHub's live comparison.
    comparison = reader.compare_commits(merge_sha, main_sha)
    base = comparison.get("base_commit") if isinstance(comparison, dict) else None
    common = comparison.get("merge_base_commit") if isinstance(comparison, dict) else None
    return (
        isinstance(comparison, dict)
        and comparison.get("status") == "ahead"
        and type(comparison.get("behind_by")) is int
        and comparison["behind_by"] == 0
        and type(comparison.get("ahead_by")) is int
        and comparison["ahead_by"] > 0
        and isinstance(base, dict) and base.get("sha") == merge_sha
        and isinstance(common, dict) and common.get("sha") == merge_sha
    )


def _find_existing(reader: GitHubGateway, pr: int,
                   marker: str, body: str) -> int | None:
    found: int | None = None
    seen: set[int] = set()
    for page in range(1, 11):
        comments = reader._get("/issues/" + str(pr) + "/comments", {
            "per_page": "100", "page": str(page),
        })
        if not isinstance(comments, list) or len(comments) > 100:
            raise TransitionPublishDenied("incomplete GitHub comment inventory")
        for entry in comments:
            if not isinstance(entry, dict):
                raise TransitionPublishDenied("malformed GitHub comment")
            ident = entry.get("id")
            if type(ident) is not int or ident <= 0 or ident in seen:
                raise TransitionPublishDenied("duplicate or invalid comment ID")
            seen.add(ident)
            if marker in str(entry.get("body", "")):
                if found is not None or not _verified_comment(entry, body, pr):
                    raise TransitionPublishDenied("receipt collision or untrusted author")
                found = ident
        if len(comments) < 100:
            return found
    raise TransitionPublishDenied("comment listing truncated")


def publish_verified_transition(
    reader: GitHubGateway, journal: EventJournal, state: Mapping[str, Any],
    *, enabled: bool = False, workflow_ref: str = "", workflow_sha: str = "",
    transport: Callable = _post_issue_comment,
) -> dict:
    """Write then remotely re-read a bot PR comment; no phase mutation."""
    if enabled is not True or workflow_ref != "refs/heads/main":
        raise TransitionPublishDenied("main-only receipt publishing disabled")
    if not isinstance(reader, GitHubGateway) or reader.repo != REPO:
        raise TransitionPublishDenied("trusted GitHub repository required")
    if not isinstance(journal, EventJournal) or not isinstance(state, Mapping):
        raise TransitionPublishDenied("journal or phase snapshot invalid")
    if (state.get("phase_status") != "MERGED_VERIFIED"
            or state.get("lease_holder") is not None
            or state.get("worker_running") is not False
            or state.get("phase") == "P00"):
        raise TransitionPublishDenied("no eligible new postmerge checkpoint")
    if validate_snapshot(state):
        raise TransitionPublishDenied("phase snapshot policy rejected")
    source = state["phase"]
    target = next_phase(source)
    if target is None:
        raise TransitionPublishDenied("no next phase")

    try:
        observed = reader.observe(state)
        if (observed.get("authenticated_remote") is not True
                or observed.get("phase") != source
                or observed.get("pr_number") != state["primary_pr"]
                or observed.get("merge_sha") != state["last_verified_remote_sha"]
                or not _main_ancestry(reader, observed, workflow_sha)):
            raise TransitionPublishDenied("authenticated merge ancestry not verified")
        observed = dict(observed, main_matches_merge=True)
        local = journal.record_verified_transition(state, target, observed)
        pr = state["primary_pr"]
        if type(pr) is not int:
            raise TransitionPublishDenied("primary PR invalid")
        sha = state["last_verified_remote_sha"]
        marker = _MARKER + source + ":" + target + ":" + sha + " -->"
        body = _receipt_body(source, target, local["event_id"], pr, sha,
                             observed["issue_inventory_fingerprint"])
        prior = _find_existing(reader, pr, marker, body)
        if prior is None:
            remote_pr = reader.pull_request(pr)
            remote_main = reader.branch("main")
            if (remote_pr.get("merged") is not True
                    or remote_pr.get("merge_commit_sha") != sha
                    or (remote_pr.get("head") or {}).get("ref") != state["active_branch"]
                    or (remote_main.get("commit") or {}).get("sha") != workflow_sha):
                raise TransitionPublishDenied("remote PR or main changed")
            created = transport(pr, body, reader.token)
            if not isinstance(created, dict) or type(created.get("id")) is not int:
                raise TransitionPublishDenied("GitHub creation acknowledgement invalid")
            comment_id = created["id"]
            was_created = True
        else:
            comment_id = prior
            was_created = False
        # Independent readback. A failed GET cannot claim publication success;
        # a later re-run can recover by discovering the already-posted comment.
        readback = reader._get("/issues/comments/" + str(comment_id))
        if not _verified_comment(readback, body, pr) or readback["id"] != comment_id:
            raise TransitionPublishDenied("independent GitHub readback failed")
        return {
            "status": "REMOTE_PHASE_RECEIPT_VERIFIED",
            "source_phase": source, "target_phase": target,
            "primary_pr": pr, "merge_sha": sha,
            "event_id": local["event_id"], "comment_id": comment_id,
            "comment_created": was_created,
            "local_journal_readback_verified": local["readback_verified"],
            "external_checkpoint_published": True,
            "external_checkpoint_mutable": True,
            "next_phase_started": False,
            "comment_url": (
                "https://github.com/" + REPO + "/pull/" + str(pr)
                + "#issuecomment-" + str(comment_id)
            ),
        }
    except (GitHubEvidenceError, PhasePolicyError, KeyError, TypeError, ValueError):
        raise TransitionPublishDenied("verified receipt prerequisites failed") from None


def main() -> int:
    parser = argparse.ArgumentParser(description="Trusted-main phase receipt publisher")
    parser.add_argument("--publish", action="store_true")
    args = parser.parse_args()
    if not args.publish:
        print(json.dumps({"status": "DISABLED", "external_checkpoint_published": False}))
        return 0
    try:
        if (os.environ.get("GITHUB_REPOSITORY") != REPO
                or os.environ.get("GITHUB_REF") != "refs/heads/main"
                or os.environ.get("GITHUB_ACTIONS") != "true"):
            raise TransitionPublishDenied("trusted default branch required")
        state = json.loads(Path("docs/state/PHASE.json").read_text(encoding="utf-8"))
        if not isinstance(state, dict):
            raise TransitionPublishDenied("phase JSON invalid")
        reader = GitHubGateway(REPO, token=os.environ.get("ZYNOA_GITHUB_TOKEN", ""))
        with tempfile.TemporaryDirectory(prefix="zynoa-phase-journal-") as tmp:
            journal = EventJournal(Path(tmp) / "local.db")
            result = publish_verified_transition(
                reader, journal, state, enabled=True,
                workflow_ref=os.environ["GITHUB_REF"],
                workflow_sha=os.environ.get("GITHUB_SHA", ""),
            )
        print(json.dumps(result, sort_keys=True))
        return 0
    except (TransitionPublishDenied, GitHubEvidenceError, OSError, ValueError, KeyError):
        print(json.dumps({"status": "BLOCKED", "external_checkpoint_published": False,
                          "next_phase_started": False}))
        return 2


if __name__ == "__main__":
    raise SystemExit(main())
