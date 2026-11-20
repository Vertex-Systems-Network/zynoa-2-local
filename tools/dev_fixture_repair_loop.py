"""P00 bounded model fixture syntax-repair coordinator. No workspace edits.

A trusted operator may opt in to local-model fixture TEXT generation followed
by the existing rootless-Docker PYTHON SYNTAX check (no candidate code run).
If syntax is invalid, send ONLY that generic status and the model's preceding
candidate back to the SAME localhost Ollama endpoint for one corrective draft.
Never shell, test-run model code, patch user/repo files or write to GitHub.

CI exercises the coordinator with fake model replies and a fake syntax broker;
mock success is NOT proof of a live Ollama, a sandbox or autonomous development.
"""
from __future__ import annotations

import hashlib
from typing import Callable

from tools.dev_model_planner import ModelPlanDenied, validate_model_plan
from tools.docker_syntax_broker import (
    DEFAULT_IMAGE, DockerSyntaxDenied, _docker_binary, _rootless_socket,
    run_python_syntax,
)
from tools.fixture_draft_stager import FixtureStageDenied, _text_bytes
from tools.local_fixture_drafter import (
    LocalFixtureDenied, LocalFixtureDraft, draft_local_fixture,
    make_fixture_request,
)
from tools.workspace_policy import WorkspaceScope

_TASK = "P00-T20"
_MAX_ATTEMPTS = 2
_VALID = "PYTHON_SYNTAX_VALID_NO_CODE_EXECUTION"
_INVALID = "PYTHON_SYNTAX_INVALID_NO_CODE_EXECUTION"


class FixtureRepairDenied(ValueError):
    """Sanitized rejection: never expose model source or host Docker diagnostics."""


def _verify_draft(
    draft: object, plan: dict, path: str, plan_sha256: str,
    scope: WorkspaceScope,
) -> str:
    """Check the untrusted candidate/preview identity on EACH attempt."""
    if type(draft) is not LocalFixtureDraft:
        raise FixtureRepairDenied("model fixture draft envelope invalid")
    if draft.path != path or draft.plan_sha256 != plan_sha256:
        raise FixtureRepairDenied("model fixture changed trusted plan identity")
    try:
        original = validate_model_plan(draft.plan, _TASK, scope)
        data = _text_bytes(draft.source)
    except (ModelPlanDenied, FixtureStageDenied, OSError, ValueError, TypeError):
        raise FixtureRepairDenied("model fixture draft did not pass scope/text validation") from None
    if original != plan or hashlib.sha256(data).hexdigest() != draft.candidate_sha256:
        raise FixtureRepairDenied("model fixture draft hash or plan changed")
    if not isinstance(draft.preview_receipt_sha256, str) or not (
        len(draft.preview_receipt_sha256) == 64
        and all(c in "0123456789abcdef" for c in draft.preview_receipt_sha256)
    ):
        raise FixtureRepairDenied("fixture staging proof is absent")
    return draft.candidate_sha256


def _verify_syntax(result: object, sha: str) -> str:
    """Reject forged/ambiguous broker receipts before retrying or succeeding."""
    if not isinstance(result, dict):
        raise FixtureRepairDenied("syntax broker receipt is invalid")
    status = result.get("status")
    if status not in (_VALID, _INVALID):
        raise FixtureRepairDenied("syntax broker did not return a syntax verdict")
    if (
        result.get("phase") != "P00" or
        result.get("task_id") != _TASK or
        result.get("candidate_sha256") != sha or
        result.get("image_digest") != DEFAULT_IMAGE.split("@", 1)[1] or
        type(result.get("docker_commands_executed")) is not int or
        result["docker_commands_executed"] != 4 or
        result.get("rootless_daemon_status_observed") is not True or
        type(result.get("workspace_files_written")) is not int or
        result["workspace_files_written"] != 0 or
        type(result.get("github_writes")) is not int or
        result["github_writes"] != 0 or
        result.get("model_source_executed") is not False or
        result.get("independent_host_sandbox_verified") is not False or
        result.get("persistent_worker_deployed") is not False
    ):
        raise FixtureRepairDenied("syntax broker identity or nonexecution proof failed")
    return status


def run_fixture_syntax_repair(
    model: str, plan: dict, scope: WorkspaceScope, *,
    expected_task_id: str,
    enabled: bool = False,
    operator_ack: bool = False,
    syntax_enabled: bool = False,
    endpoint: str = "http://127.0.0.1:11434",
    docker_binary: str = "/usr/bin/docker",
    socket_url: str | None = None,
    model_transport: Callable | None = None,
    syntax_broker: Callable = run_python_syntax,
) -> dict:
    """Two-attempt trusted-host *syntax-only* coordinator, default-denied.

    All grant flags must be independently supplied by the trusted operator.
    A model response cannot set them. The syntax_broker parameter is strictly
    for trusted test injection; never accept a broker function from model text.
    """
    if enabled is not True or operator_ack is not True or syntax_enabled is not True:
        raise FixtureRepairDenied("fixture repair requires all trusted host opt-ins")
    if expected_task_id != _TASK:
        raise FixtureRepairDenied("fixture repair task outside active P00 scope")
    try:
        _, valid, path, plan_sha = make_fixture_request(
            model, plan, scope, expected_task_id=expected_task_id
        )
    except (LocalFixtureDenied, ModelPlanDenied, ValueError, OSError, TypeError):
        raise FixtureRepairDenied("fixture repair preflight rejected") from None

    # On real host use, refuse a missing/unsafe rootless CLI/socket BEFORE
    # initiating inference. Tests inject a separately trusted fake broker.
    if syntax_broker is run_python_syntax:
        try:
            _docker_binary(docker_binary)
            _rootless_socket(socket_url or "")
        except (DockerSyntaxDenied, OSError, ValueError):
            raise FixtureRepairDenied("independent rootless host preflight unavailable") from None

    previous = None
    attempts = []
    seen = set()
    for attempt in range(1, _MAX_ATTEMPTS + 1):
        try:
            draft = draft_local_fixture(
                model, valid, scope, expected_task_id=expected_task_id,
                endpoint=endpoint, transport=model_transport,
                repair_source=previous,
            )
        except (LocalFixtureDenied, ModelPlanDenied, OSError, ValueError, TypeError):
            raise FixtureRepairDenied("local model fixture draft rejected") from None
        sha = _verify_draft(draft, valid, path, plan_sha, scope)
        if sha in seen:
            raise FixtureRepairDenied("model repeated the same syntax-invalid fixture")
        seen.add(sha)
        try:
            result = syntax_broker(
                valid, draft.source, scope, expected_task_id=expected_task_id,
                enabled=True, docker_binary=docker_binary, socket_url=socket_url,
            )
        except (DockerSyntaxDenied, OSError, ValueError, TimeoutError, TypeError):
            # A Docker timeout, bad cgroup, host outage, permission failure,
            # malicious marker or cleanup failure NEVER triggers model retry.
            raise FixtureRepairDenied("isolated syntax broker unavailable or denied") from None
        status = _verify_syntax(result, sha)
        attempts.append({
            "attempt": attempt,
            "candidate_sha256": sha,
            "preview_receipt_sha256": draft.preview_receipt_sha256,
            "syntax_status": status,
        })
        if status == _VALID:
            return _safe_report("FIXTURE_SYNTAX_VALID_NO_CODE_EXECUTION", attempts)
        if attempt == _MAX_ATTEMPTS:
            return _safe_report("FIXTURE_SYNTAX_UNRESOLVED_AFTER_REPAIR", attempts)
        previous = draft.source
    raise FixtureRepairDenied("unexpected repair loop boundary")  # defensive only


def _safe_report(status: str, attempts: list[dict]) -> dict:
    return {
        "status": status, "phase": "P00", "task_id": _TASK,
        "attempt_count": len(attempts),
        "repair_attempted": len(attempts) > 1,
        "max_attempts": _MAX_ATTEMPTS,
        "attempts": attempts,
        "syntax_only": True,
        "model_source_executed": False,
        "workspace_files_written": 0,
        "github_writes": 0,
        "patches_applied": 0,
        "independent_host_sandbox_verified": False,
        "persistent_worker_deployed": False,
        "actual_model_runtime_independently_verified": False,
        "autonomous_plan_edit_test_repair_verified": False,
    }
