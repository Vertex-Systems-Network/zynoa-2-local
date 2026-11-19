#!/usr/bin/env python3
"""P00 local Ollama fixture-content drafter; untrusted text, NO code execution.

This is the missing content step between the existing proposal-only planner,
disposable fixture preview, and rootless Docker syntax broker. Its return value
holds candidate source only in the trusted caller's memory; repr/receipts never
contain source. It cannot edit the checkout, invoke Docker, run tests, or write
to GitHub. Real host/Ollama deployment remains independently unverified.
"""
from __future__ import annotations

from dataclasses import dataclass, field
import hashlib
import json
from typing import Callable

from tools.dev_model_planner import (
    ModelPlanDenied, _request_local_json, make_model_request, validate_model_plan,
)
from tools.docker_syntax_broker import _PY_FILE
from tools.fixture_draft_stager import FixtureStageDenied, _text_bytes, preview_fixture_drafts
from tools.local_model_probe import LocalModelUnavailable, validate_local_base
from tools.workspace_policy import WorkspaceScope

_TASK = "P00-T20"
_MAX_ENVELOPE = 32768

_INSTRUCTIONS = (
    "Return exactly one JSON object matching the supplied schema. Generate "
    "one small Python regression-test FIXTURE as UTF-8 text at the one specified "
    "path. You have no tools and cannot read source, secrets, files or network. "
    "Never attempt Git operations, shell execution, package installation, "
    "workspace changes, deployment or phase transitions. The source remains "
    "untrusted data and will be validated/previewed without host execution."
)


class LocalFixtureDenied(ValueError):
    """Sanitized invalid proposal, response or disposable preview."""


@dataclass(frozen=True, repr=False)
class LocalFixtureDraft:
    """Raw untrusted Python is available to the trusted caller, not safe to log.

    The frozen envelope is not a capability or file-write authorization.
    A later real syntax check must independently validate this plan/source
    against the same trusted WorkspaceScope and host-issued task ID.
    """
    plan: dict = field(repr=False)
    source: str = field(repr=False)
    candidate_sha256: str
    plan_sha256: str
    preview_receipt_sha256: str
    path: str

    def safe_receipt(self) -> dict:
        return {
            "status": "MODEL_FIXTURE_TEXT_PREVIEW_ONLY",
            "phase": "P00",
            "task_id": _TASK,
            "path": self.path,
            "candidate_sha256": self.candidate_sha256,
            "plan_sha256": self.plan_sha256,
            "preview_receipt_sha256": self.preview_receipt_sha256,
            "model_response_validated": True,
            "real_local_model_runtime_verified": False,
            "model_source_executed": False,
            "workspace_files_written": 0,
            "github_writes": 0,
            "os_sandbox_verified": False,
            "persistent_worker_deployed": False,
            "autonomous_repair_loop_verified": False,
        }


def _canonical_plan(plan: dict, expected_task_id: str, scope: WorkspaceScope) -> tuple[dict, str, str]:
    if expected_task_id != _TASK:
        raise LocalFixtureDenied("only the existing P00-T20 fixture task is eligible")
    try:
        valid = validate_model_plan(plan, expected_task_id, scope)
    except (ModelPlanDenied, ValueError, OSError, TypeError):
        raise LocalFixtureDenied("trusted fixture plan rejected") from None
    proposals = valid["file_proposals"]
    if len(proposals) != 1 or not _PY_FILE.fullmatch(proposals[0]["path"]):
        raise LocalFixtureDenied("only one flat Python fixture is eligible")
    digest = hashlib.sha256(
        json.dumps(valid, sort_keys=True, separators=(",", ":")).encode("utf-8")
    ).hexdigest()
    return valid, proposals[0]["path"], digest


def make_fixture_request(
    model: str, plan: dict, scope: WorkspaceScope, *,
    expected_task_id: str,
    repair_source: str | None = None,
) -> tuple[dict, dict, str, str]:
    """Trusted-only request. Optional repair text is prior model output only.

    Source stays inside localhost Ollama. No privileged host parser or commands.
    """
    valid, path, plan_sha = _canonical_plan(plan, expected_task_id, scope)
    # Reuse the existing model-ID and phase/task authorizer; do not duplicate
    # a subtly different model naming, task or endpoint policy.
    try:
        make_model_request(model, expected_task_id, "Python fixture text preview", scope)
    except (ModelPlanDenied, ValueError, OSError, TypeError):
        raise LocalFixtureDenied("local fixture model identity rejected") from None
    schema = {
        "type": "object",
        "additionalProperties": False,
        "required": ["schema_version", "phase", "branch", "task_id",
                     "plan_sha256", "path", "source"],
        "properties": {
            "schema_version": {"type": "integer", "const": 1},
            "phase": {"type": "string", "const": "P00"},
            "branch": {"type": "string", "const": "phase/00-governance"},
            "task_id": {"type": "string", "const": _TASK},
            "plan_sha256": {"type": "string", "const": plan_sha},
            "path": {"type": "string", "const": path},
            "source": {"type": "string", "minLength": 1, "maxLength": 8192},
        },
    }
    user_context = {
        "phase": "P00", "branch": "phase/00-governance",
        "task_id": _TASK, "plan_sha256": plan_sha, "path": path,
        "summary": valid["summary"],
        "reason": valid["file_proposals"][0]["reason"],
    }
    if repair_source is not None:
        try:
            # A previous candidate must pass the same text limits as a fresh
            # model response. No model-generated command or error log is used.
            _text_bytes(repair_source)
        except FixtureStageDenied:
            raise LocalFixtureDenied("previous model fixture is invalid") from None
        user_context["previous_candidate"] = repair_source
        user_context["prior_result"] = "PYTHON_SYNTAX_INVALID_NO_CODE_EXECUTION"
        user_context["request"] = (
            "Correct Python syntax only; return the same fixture path and "
            "plan digest with complete corrected source. Do not add tools."
        )
    payload = {
        "model": model,
        "stream": False,
        "format": schema,
        "messages": [
            {"role": "system", "content": _INSTRUCTIONS},
            {"role": "user", "content": json.dumps(
                user_context, ensure_ascii=True, separators=(",", ":")
            )},
        ],
        "options": {"temperature": 0, "num_predict": 4096},
    }
    if len(json.dumps(payload, separators=(",", ":")).encode("utf-8")) > 24576:
        raise LocalFixtureDenied("fixture model request exceeds size budget")
    return payload, valid, path, plan_sha


def _unique_keys(pairs: list[tuple[str, object]]) -> dict:
    result = {}
    for key, value in pairs:
        if key in result:
            raise LocalFixtureDenied("duplicate response JSON key")
        result[key] = value
    return result


def draft_local_fixture(
    model: str, plan: dict, scope: WorkspaceScope, *,
    expected_task_id: str,
    endpoint: str = "http://127.0.0.1:11434",
    transport: Callable | None = None,
    repair_source: str | None = None,
) -> LocalFixtureDraft:
    """Generate bounded untrusted text, then preview in disposable temp storage.

    The model never selects phase, task, path, endpoint, Docker command, GitHub
    account or file handle. No generated code is compiled/parsed on the host.
    A trusted external worker may later call the *separate*, default-disabled
    rootless Docker syntax broker with the returned source and validated plan.
    """
    try:
        base = validate_local_base(endpoint)
    except LocalModelUnavailable:
        raise LocalFixtureDenied("only an explicit loopback Ollama URL is eligible") from None
    payload, valid, path, plan_sha = make_fixture_request(
        model, plan, scope, expected_task_id=expected_task_id,
        repair_source=repair_source,
    )
    try:
        envelope = (transport or _request_local_json)(base, payload)
    except (ModelPlanDenied, LocalModelUnavailable, OSError, TimeoutError, ValueError):
        raise LocalFixtureDenied("local fixture model response unavailable") from None
    if not isinstance(envelope, dict) or envelope.get("done") is not True:
        raise LocalFixtureDenied("local fixture model response incomplete")
    if envelope.get("done_reason") not in (None, "stop"):
        raise LocalFixtureDenied("fixture generation was truncated")
    if envelope.get("model") != model or "tool_calls" in envelope:
        raise LocalFixtureDenied("model identity mismatch or tool call denied")
    msg = envelope.get("message")
    if not isinstance(msg, dict) or msg.get("role") != "assistant" or "tool_calls" in msg:
        raise LocalFixtureDenied("fixture message role/tools invalid")
    raw = msg.get("content")
    if not isinstance(raw, str) or len(raw.encode("utf-8")) > _MAX_ENVELOPE:
        raise LocalFixtureDenied("fixture model content oversized or absent")
    try:
        response = json.loads(raw, object_pairs_hook=_unique_keys)
    except (ValueError, TypeError, UnicodeError, RecursionError):
        raise LocalFixtureDenied("invalid fixture model JSON") from None
    expected = {"schema_version", "phase", "branch", "task_id",
                "plan_sha256", "path", "source"}
    if not isinstance(response, dict) or set(response) != expected or (
        type(response["schema_version"]) is not int or response["schema_version"] != 1
        or response["phase"] != "P00" or response["branch"] != "phase/00-governance"
        or response["task_id"] != expected_task_id
        or response["plan_sha256"] != plan_sha or response["path"] != path
    ):
        raise LocalFixtureDenied("untrusted fixture identity/path changed")
    try:
        candidate = response["source"]
        data = _text_bytes(candidate)  # validate text only; no host Python AST/compile
        preview = preview_fixture_drafts(
            valid, {path: candidate}, scope, expected_task_id=expected_task_id,
        )
    except (FixtureStageDenied, ModelPlanDenied, ValueError, OSError, TypeError):
        raise LocalFixtureDenied("fixture text/preview rejected") from None
    if (
        preview.get("status") != "EPHEMERAL_FIXTURE_PREVIEW_ONLY"
        or preview.get("workspace_files_written") != 0
        or preview.get("github_writes") != 0
        or preview.get("commands_executed") != 0
        or preview.get("model_code_executed") is not False
        or preview.get("os_sandbox_verified") is not False
        or preview.get("candidate_count") != 1
    ):
        raise LocalFixtureDenied("untrusted fixture preview receipt failed")
    receipt = preview.get("candidate_receipts")
    if not isinstance(receipt, list) or len(receipt) != 1 or (
        receipt[0].get("path") != path or
        receipt[0].get("sha256") != hashlib.sha256(data).hexdigest() or
        receipt[0].get("size_bytes") != len(data) or
        receipt[0].get("static_check") != "PYTHON_TEXT_ONLY_NO_PARSE_OR_EXECUTION"
    ):
        raise LocalFixtureDenied("fixture preview hash or path mismatch")
    return LocalFixtureDraft(
        plan=valid, source=candidate, path=path,
        plan_sha256=plan_sha, candidate_sha256=hashlib.sha256(data).hexdigest(),
        preview_receipt_sha256=preview["receipt_sha256"],
    )
