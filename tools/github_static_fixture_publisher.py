"""P00 one-time, operator-reviewed STATIC fixture GitHub write with remote readback.

This intentionally does NOT publish model-authored code. The permitted Python
source/path are constants baked into trusted controller source; the model has
NO way to select commands, paths, branch or content. Its sole value is to
exercise GitHub branch lease/write/ref/file-readback for a disposable fixture
on an OPEN DRAFT P00 PR, not to finish T21's authenticated autonomous writer.

GitHub Git Database API provides a non-force fast-forward ref update. A moved
PR head causes a non-fast-forward refusal (not atomic compare-and-swap across
all possible branch rewrites). The controller needs a dedicated token with
minimal repository Contents(write) access. It cannot be provisioned in CI.
Tests inject a fake HTTP transport. No remote calls by default.
"""
from __future__ import annotations

import base64
import binascii
import hashlib
import json
import os
import re
import urllib.error
import urllib.parse
import urllib.request
from typing import Callable, Mapping

_REPO = "Vertex-Systems-Network/zynoa-2-local"
_BRANCH = "phase/00-governance"
_PR = 1
_API = "https://api.github.com/repos/" + _REPO
_SHA = re.compile(r"^[a-f0-9]{40}$")
_B64 = re.compile(r"^[A-Za-z0-9+/=\s]+$")
_PROBE_PATH = "tests/fixtures/p00_trusted_remote_probe.py"
# The source is fixed and trusted, not a model output and NOT executed.
_PROBE_SOURCE = (
    '"""P00 static GitHub write probe; never model-generated or executed."""\n'
    '\n'
    'def solve(x: int) -> int:\n'
    '    return x * 2\n'
)
_SOURCE_SHA = hashlib.sha256(_PROBE_SOURCE.encode("utf-8")).hexdigest()
_COMMIT_MSG = "test(p00): stage trusted static remote fixture proof"
_MAX_RESPONSE = 256_000


class ProbeWriteDenied(ValueError):
    """Sanitized refusal. No token, source code or raw HTTP body is exposed."""


class _NoRedirect(urllib.request.HTTPRedirectHandler):
    def redirect_request(self, req, fp, code, msg, headers, newurl):
        raise ProbeWriteDenied("unexpected GitHub API redirect")


def _http(method: str, suffix: str, token: str, payload: dict | None, timeout: float):
    if not suffix.startswith("/") or ".." in suffix or "://" in suffix:
        raise ProbeWriteDenied("invalid GitHub API path")
    url = _API + suffix
    request = urllib.request.Request(
        url, method=method,
        data=json.dumps(payload, separators=(",", ":")).encode("utf-8")
            if payload is not None else None,
        headers={
            "Authorization": "Bearer " + token,
            "Accept": "application/vnd.github+json",
            "X-GitHub-Api-Version": "2022-11-28",
            "Content-Type": "application/json",
            "User-Agent": "Zynoa-P00-Static-Git-Probe/1",
        }
    )
    try:
        with urllib.request.build_opener(_NoRedirect).open(request, timeout=timeout) as response:
            if response.status not in (200, 201):
                raise ProbeWriteDenied("unexpected GitHub status")
            raw = response.read(_MAX_RESPONSE + 1)
        if len(raw) > _MAX_RESPONSE:
            raise ProbeWriteDenied("GitHub response limit exceeded")
        obj = json.loads(raw.decode("utf-8"))
        if not isinstance(obj, dict):
            raise ProbeWriteDenied("GitHub JSON shape unexpected")
        return obj
    except urllib.error.HTTPError as e:
        if method == "GET" and "/contents/" in suffix and e.code == 404:
            return {"not_found": True}
        raise ProbeWriteDenied("GitHub API refused write/read") from None
    except (urllib.error.URLError, OSError, TimeoutError, UnicodeError, ValueError):
        raise ProbeWriteDenied("GitHub remote transport unavailable") from None


def _route_allowed(method: str, suffix: str, payload: object) -> bool:
    if method == "GET" and payload is None:
        return (
            suffix == "/pulls/1"
            or re.fullmatch(r"/git/commits/[a-f0-9]{40}", suffix) is not None
            or re.fullmatch(
                r"/contents/tests/fixtures/p00_trusted_remote_probe[.]py"
                r"[?]ref=[a-f0-9]{40}", suffix
            ) is not None
        )
    if method == "POST" and type(payload) is dict:
        if suffix == "/git/blobs":
            return payload == {"content": _PROBE_SOURCE, "encoding": "utf-8"}
        if suffix == "/git/trees":
            return (
                set(payload) == {"base_tree", "tree"}
                and isinstance(payload["base_tree"], str)
                and _SHA.fullmatch(payload["base_tree"]) is not None
                and type(payload["tree"]) is list
                and len(payload["tree"]) == 1
                and type(payload["tree"][0]) is dict
                and set(payload["tree"][0]) == {"path", "mode", "type", "sha"}
                and payload["tree"][0]["path"] == _PROBE_PATH
                and payload["tree"][0]["mode"] == "100644"
                and payload["tree"][0]["type"] == "blob"
                and isinstance(payload["tree"][0]["sha"], str)
                and _SHA.fullmatch(payload["tree"][0]["sha"]) is not None
            )
        if suffix == "/git/commits":
            return (
                set(payload) == {"message", "tree", "parents"}
                and payload["message"] == _COMMIT_MSG
                and isinstance(payload["tree"], str)
                and _SHA.fullmatch(payload["tree"]) is not None
                and type(payload["parents"]) is list
                and len(payload["parents"]) == 1
                and isinstance(payload["parents"][0], str)
                and _SHA.fullmatch(payload["parents"][0]) is not None
            )
    if method == "PATCH" and suffix == "/git/refs/heads/phase%2F00-governance":
        return (
            type(payload) is dict and set(payload) == {"sha", "force"}
            and payload["force"] is False
            and isinstance(payload["sha"], str)
            and _SHA.fullmatch(payload["sha"]) is not None
        )
    return False


def _client(method: str, suffix: str, token: str, payload: dict | None,
            transport: Callable = _http) -> dict:
    if not _route_allowed(method, suffix, payload):
        raise ProbeWriteDenied("GitHub operation outside fixed probe allowlist")
    obj = transport(method, suffix, token, payload, 10.0)
    if not isinstance(obj, dict):
        raise ProbeWriteDenied("GitHub remote payload malformed")
    return obj


def _pr_identity(info: object, sha: str) -> bool:
    return (
        isinstance(info, dict) and info.get("number") == _PR
        and info.get("state") == "open" and info.get("draft") is True
        and info.get("merged_at") is None
        and isinstance(info.get("head"), dict)
        and info["head"].get("ref") == _BRANCH
        and info["head"].get("sha") == sha
        and isinstance(info["head"].get("repo"), dict)
        and info["head"]["repo"].get("full_name") == _REPO
        and isinstance(info.get("base"), dict)
        and info["base"].get("ref") == "main"
    )


def _decode_file(data: dict) -> bytes:
    if (
        data.get("type") != "file"
        or data.get("path") != _PROBE_PATH
        or data.get("encoding") != "base64"
        or not isinstance(data.get("content"), str)
        or len(data["content"]) > 16000
        or not _B64.fullmatch(data["content"])
    ):
        raise ProbeWriteDenied("remote fixture file metadata invalid")
    try:
        raw = base64.b64decode("".join(data["content"].split()), validate=True)
    except (ValueError, UnicodeError, binascii.Error):
        raise ProbeWriteDenied("remote fixture Base64 invalid") from None
    if raw != _PROBE_SOURCE.encode("utf-8"):
        raise ProbeWriteDenied("remote fixture bytes do not match approved literal")
    return raw


def publish_static_fixture(*, token: str, expected_head_sha: str,
                           enabled: bool = False,
                           operator_ack: bool = False,
                           manual_review: bool = False,
                           transport: Callable = _http) -> dict:
    """Operator-owned fixed new-file write; NOT model-generated source delivery.

    Token permissions and PR ownership need independent host review. A model
    MUST NEVER control the token, grants, transport or remote ref. The direct
    code path is disabled in all GitHub Actions/CI workflows.
    """
    if enabled is not True or operator_ack is not True or manual_review is not True:
        raise ProbeWriteDenied("manual static GitHub proof explicitly disabled")
    if (not isinstance(token, str) or not 8 <= len(token) <= 2048
            or not token.isascii() or any(x.isspace() for x in token)):
        raise ProbeWriteDenied("GitHub probe token unavailable or invalid")
    if not isinstance(expected_head_sha, str) or not _SHA.fullmatch(expected_head_sha):
        raise ProbeWriteDenied("full immutable PR source SHA required")
    if not callable(transport):
        raise ProbeWriteDenied("trusted GitHub transport is not callable")

    get = lambda suffix: _client("GET", suffix, token, None, transport)
    post = lambda suffix, data: _client("POST", suffix, token, data, transport)
    pr = get("/pulls/1")
    if not _pr_identity(pr, expected_head_sha):
        raise ProbeWriteDenied("draft P00 PR exact SHA/branch not verified")
    parent = get("/git/commits/" + expected_head_sha)
    tree = parent.get("tree")
    tree_sha = tree.get("sha") if isinstance(tree, dict) else None
    if not isinstance(tree_sha, str) or not _SHA.fullmatch(tree_sha):
        raise ProbeWriteDenied("trusted PR tree reference invalid")
    absent = get("/contents/" + _PROBE_PATH + "?ref=" + expected_head_sha)
    if absent != {"not_found": True}:
        raise ProbeWriteDenied("fixture already exists or absence not proven")
    # Recheck head immediately before write; underlying non-force PATCH rejects
    # stale divergent commits but is not a universal per-field CAS guarantee.
    if not _pr_identity(get("/pulls/1"), expected_head_sha):
        raise ProbeWriteDenied("PR moved before static Git write")

    created_blob = post("/git/blobs", {
        "content": _PROBE_SOURCE, "encoding": "utf-8"
    })
    blob_sha = created_blob.get("sha")
    literal_bytes = _PROBE_SOURCE.encode("utf-8")
    expected_blob_sha = hashlib.sha1(
        b"blob " + str(len(literal_bytes)).encode("ascii") + b"\x00" + literal_bytes
    ).hexdigest()
    if blob_sha != expected_blob_sha:
        raise ProbeWriteDenied("created Git blob does not match fixed source")
    created_tree = post("/git/trees", {
        "base_tree": tree_sha, "tree": [{
            "path": _PROBE_PATH, "mode": "100644",
            "type": "blob", "sha": blob_sha,
        }]
    })
    new_tree = created_tree.get("sha")
    if not isinstance(new_tree, str) or not _SHA.fullmatch(new_tree):
        raise ProbeWriteDenied("created tree response invalid")
    created_commit = post("/git/commits", {
        "message": _COMMIT_MSG, "tree": new_tree,
        "parents": [expected_head_sha],
    })
    commit_sha = created_commit.get("sha")
    if not isinstance(commit_sha, str) or not _SHA.fullmatch(commit_sha):
        raise ProbeWriteDenied("created Git commit response invalid")
    parents = created_commit.get("parents")
    tree_meta = created_commit.get("tree")
    if (not isinstance(parents, list) or len(parents) != 1
            or not isinstance(parents[0], dict)
            or parents[0].get("sha") != expected_head_sha
            or not isinstance(tree_meta, dict)
            or tree_meta.get("sha") != new_tree):
        raise ProbeWriteDenied("new Git commit parent/tree identity cannot be verified")
    # GitHub refuses non-fast-forward updates if the branch changed.
    ref = _client(
        "PATCH", "/git/refs/heads/phase%2F00-governance", token,
        {"sha": commit_sha, "force": False}, transport,
    )
    obj = ref.get("object")
    if ref.get("ref") != "refs/heads/" + _BRANCH or not isinstance(obj, dict) or obj.get("sha") != commit_sha:
        raise ProbeWriteDenied("Git ref update not verified; reconcile remotely")
    if not _pr_identity(get("/pulls/1"), commit_sha):
        raise ProbeWriteDenied("PR HEAD after write not verified")
    file = get("/contents/" + _PROBE_PATH + "?ref=" + commit_sha)
    _decode_file(file)
    return {
        "status": "TRUSTED_STATIC_FIXTURE_REMOTE_WRITE_VERIFIED",
        "repo": _REPO, "pr_number": 1, "branch": _BRANCH,
        "previous_head_sha": expected_head_sha,
        "result_head_sha": commit_sha,
        "path": _PROBE_PATH,
        "source_sha256": _SOURCE_SHA,
        "file_bytes": len(_PROBE_SOURCE.encode("utf-8")),
        "github_writes": 1, "force_push": False,
        "model_generated_source": False,
        "real_worker_token_provisioning_verified": False,
        "model_sandbox_attested": False,
        "fully_autonomous_pr_writer_verified": False,
        "persistent_worker_deployed": False,
    }
