#!/usr/bin/env python3
"""P00 local model planning adapter (NO shell, code editing, or GitHub mutation).

Only a TRUSTED external host can instantiate WorkspaceScope; a model cannot
grant itself new directories or change phases. All Ollama responses are
untrusted data, parsed under a small schema and validated again with the
existing workspace policy. This is a planning step toward P00-T20, NOT an
autonomous code execution service or an actual installed developer worker.
"""
from __future__ import annotations

import hashlib
import json
import os
import re
import urllib.error
import urllib.request
import unicodedata
from pathlib import Path
from typing import Callable, Mapping

from tools.local_model_probe import LocalModelUnavailable, _NoRedirect, validate_local_base


def _transport_timeout() -> int:
    # CPU-only hosts (GitHub runners) need longer local inference; bounded 45..300s.
    try:
        value = int(os.environ.get("ZYNOA_MODEL_TIMEOUT", "45"))
    except ValueError:
        return 45
    return min(max(value, 45), 300)
from tools.workspace_policy import WorkspaceScope, WorkspaceDenied

_MODEL_NAME = re.compile(r"^[A-Za-z0-9][A-Za-z0-9._/+:\-]{0,127}$")
_TASK_ID = re.compile(r"^P00-T(?:1[4-9]|2[0-4])$")
_ALLOWED_CHECKS = frozenset(("phase-policy", "design-spec", "docs-integrity"))
_MAX_REQUEST = 12_000
_MAX_RESPONSE = 64_000
_MAX_PLAN = 12_000
_SCHEMA = {
    "type": "object",
    "additionalProperties": False,
    "required": ["schema_version", "phase", "branch", "task_id", "summary",
                 "file_proposals", "checks"],
    "properties": {
        "schema_version": {"type": "integer", "const": 1},
        "phase": {"type": "string", "const": "P00"},
        "branch": {"type": "string", "const": "phase/00-governance"},
        "task_id": {"type": "string"},
        "summary": {"type": "string", "maxLength": 220},
        "file_proposals": {
            "type": "array", "maxItems": 8,
            "items": {
                "type": "object",
                "additionalProperties": False,
                "required": ["path", "action", "reason"],
                "properties": {
                    "path": {"type": "string", "maxLength": 240},
                    "action": {"type": "string", "const": "DRAFT_ONLY"},
                    "reason": {"type": "string", "maxLength": 180},
                },
            },
        },
        "checks": {
            "type": "array", "maxItems": 3,
            "items": {"type": "string", "enum": sorted(_ALLOWED_CHECKS)},
        },
    },
}
_INSTRUCTIONS = (
    "You are a proposal-only AI planner. Return one JSON object matching "
    "the supplied JSON schema. You NEVER have tool access. Do not include "
    "commands, code, credentials, URLs, or file contents. Do not request "
    "git, filesystem writes, network operations, test execution or merges. "
    "Only suggest DRAFT_ONLY paths within the host-provided writable "
    "prefixes. Protected governance paths are forbidden. A trusted host "
    "will independently validate all paths; your answer is never permission."
)


class ModelPlanDenied(ValueError):
    """Structured model plan rejected. Do not log untrusted model content."""


def _safe_text(value: object, max_length: int) -> bool:
    if not isinstance(value, str) or not 1 <= len(value) <= max_length:
        return False
    if unicodedata.normalize("NFC", value) != value:
        return False
    if any(unicodedata.category(ch) in ("Cc", "Cf", "Cs") for ch in value):
        return False
    if any(ch in value for ch in "<>\x00\x1b"):
        return False
    return True


def _validate_task(task_id: str, brief: str, scope: WorkspaceScope) -> None:
    if not isinstance(task_id, str) or not _TASK_ID.fullmatch(task_id):
        raise ModelPlanDenied("task ID is outside active P00 execution scope")
    if not _safe_text(brief, 500):
        raise ModelPlanDenied("task brief is invalid or too large")
    if scope.phase != "P00" or scope.branch != "phase/00-governance":
        raise ModelPlanDenied("trusted host workspace scope does not match P00")


def make_model_request(
    model: str, task_id: str, brief: str, scope: WorkspaceScope
) -> dict:
    """Only task metadata is transmitted to the explicit local endpoint."""
    _validate_task(task_id, brief, scope)
    if not isinstance(model, str) or not _MODEL_NAME.fullmatch(model):
        raise ModelPlanDenied("model name invalid")
    if any(part in ("", ".", "..") for part in model.split("/")):
        raise ModelPlanDenied("model name has unsafe path components")
    request = {
        "model": model, "stream": False, "format": _SCHEMA,
        "messages": [
            {"role": "system", "content": _INSTRUCTIONS},
            {"role": "user", "content": json.dumps({
                "phase": scope.phase, "branch": scope.branch,
                "task_id": task_id, "brief": brief,
                "allowed_draft_prefixes": list(scope.writable_prefixes),
            }, separators=(",", ":"))},
        ],
        "options": {"temperature": 0, "num_predict": 768},
    }
    encoded = json.dumps(request, separators=(",", ":")).encode("utf-8")
    if len(encoded) > _MAX_REQUEST:
        raise ModelPlanDenied("model planning request exceeds size budget")
    return request


def validate_model_plan(
    value: object, task_id: str, scope: WorkspaceScope
) -> dict:
    """Host-controlled policy gate: validation ONLY; no file opens or writes."""
    if not isinstance(task_id, str) or not _TASK_ID.fullmatch(task_id):
        raise ModelPlanDenied("model output task ID outside P00 scope")
    if scope.phase != "P00" or scope.branch != "phase/00-governance":
        raise ModelPlanDenied("host-provided phase or branch is invalid")
    if not isinstance(value, dict) or set(value) != set(_SCHEMA["required"]):
        raise ModelPlanDenied("plan root does not match exact schema")
    if (
        type(value["schema_version"]) is not int or value["schema_version"] != 1 or
        value["phase"] != scope.phase or
        value["branch"] != scope.branch or
        value["task_id"] != task_id
    ):
        raise ModelPlanDenied("model attempted phase, task or branch change")
    if not _safe_text(value["summary"], 220):
        raise ModelPlanDenied("plan summary invalid")
    proposals = value["file_proposals"]
    if not isinstance(proposals, list) or not 1 <= len(proposals) <= 8:
        raise ModelPlanDenied("model must propose one to eight drafts")
    paths = set()
    for p in proposals:
        if not isinstance(p, dict) or set(p) != {"path", "action", "reason"}:
            raise ModelPlanDenied("proposal fields invalid")
        if p["action"] != "DRAFT_ONLY" or not _safe_text(p["reason"], 180):
            raise ModelPlanDenied("model requested privileged action")
        path = p["path"]
        if not isinstance(path, str) or len(path) > 240 or path.casefold() in paths:
            raise ModelPlanDenied("duplicate or unsafe path proposal")
        paths.add(path.casefold())
        try:
            scope.check(path, "write")
        except (WorkspaceDenied, OSError, ValueError):
            raise ModelPlanDenied("draft path denied by trusted workspace scope") from None
    checks = value["checks"]
    if (
        not isinstance(checks, list) or len(checks) > 3 or
        any(not isinstance(c, str) or c not in _ALLOWED_CHECKS for c in checks) or
        len(set(checks)) != len(checks)
    ):
        raise ModelPlanDenied("nonallowlisted or duplicate validation check")
    return {
        "schema_version": 1, "phase": scope.phase, "branch": scope.branch,
        "task_id": task_id, "summary": value["summary"],
        "file_proposals": [
            {"path": x["path"], "action": "DRAFT_ONLY", "reason": x["reason"]}
            for x in proposals
        ],
        "checks": list(checks),
    }


def _request_local_json(base: str, payload: dict) -> dict:
    req = urllib.request.Request(
        base + "/api/chat",
        data=json.dumps(payload, separators=(",", ":")).encode("utf-8"),
        method="POST",
        headers={
            "Content-Type": "application/json",
            "Accept": "application/json",
            "User-Agent": "Zynoa-P00-Local-Plan/1",
        },
    )
    opener = urllib.request.build_opener(
        urllib.request.ProxyHandler({}), _NoRedirect
    )
    try:
        with opener.open(req, timeout=_transport_timeout()) as response:
            if response.status != 200:
                raise ModelPlanDenied("local Ollama HTTP response not successful")
            raw = response.read(_MAX_RESPONSE + 1)
    except (urllib.error.URLError, OSError, TimeoutError, LocalModelUnavailable):
        raise ModelPlanDenied("local model transport unavailable") from None
    if len(raw) > _MAX_RESPONSE:
        raise ModelPlanDenied("model response exceeds size budget")
    try:
        value = json.loads(raw)
    except (ValueError, UnicodeError):
        raise ModelPlanDenied("model response is not valid JSON") from None
    if not isinstance(value, dict):
        raise ModelPlanDenied("model response shape invalid")
    return value


def propose_local_plan(
    model: str, task_id: str, brief: str, scope: WorkspaceScope,
    *, endpoint: str = "http://127.0.0.1:11434",
    transport: Callable | None = None,
) -> dict:
    """Request structured JSON, revalidate and expose sanitized metadata only.

    No filesystem mutations, queue jobs, shell operations, GitHub writes or
    direct consumption of returned text as a code patch occur in this module.
    """
    try:
        base = validate_local_base(endpoint)
    except LocalModelUnavailable:
        raise ModelPlanDenied("only local Ollama endpoint allowed") from None
    request = make_model_request(model, task_id, brief, scope)
    data = (transport or _request_local_json)(base, request)
    if not isinstance(data, dict) or data.get("done") is not True:
        raise ModelPlanDenied("model response unfinished")
    if data.get("done_reason") not in (None, "stop"):
        raise ModelPlanDenied("model answer incomplete or truncated")
    if data.get("model") != model or "tool_calls" in data:
        raise ModelPlanDenied("model identity mismatch or tool use attempted")
    msg = data.get("message")
    if not isinstance(msg, dict) or msg.get("role") != "assistant" or "tool_calls" in msg:
        raise ModelPlanDenied("invalid assistant response envelope")
    content = msg.get("content")
    if not isinstance(content, str) or len(content.encode("utf-8")) > _MAX_PLAN:
        raise ModelPlanDenied("model content missing or oversized")
    try:
        parsed = json.loads(content)
    except (ValueError, UnicodeError):
        raise ModelPlanDenied("model plan content is not JSON") from None
    plan = validate_model_plan(parsed, task_id, scope)
    fingerprint = hashlib.sha256(
        json.dumps(plan, sort_keys=True, separators=(",", ":")).encode("utf-8")
    ).hexdigest()
    return {
        "status": "PROPOSAL_VALIDATED_NO_EXECUTION",
        "phase": scope.phase, "branch": scope.branch, "task_id": task_id,
        "proposal_sha256": fingerprint,
        "proposed_draft_count": len(plan["file_proposals"]),
        "check_count": len(plan["checks"]),
        "model_inference_performed": True,
        "files_written": 0, "commands_executed": 0,
        "github_writes": 0, "worker_deployed": False,
        "os_sandbox_verified": False,
        "plan": plan,
    }
