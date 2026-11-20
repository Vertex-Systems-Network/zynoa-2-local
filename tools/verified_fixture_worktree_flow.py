"""Trusted P00 one-candidate-at-a-time verify -> new disposable file workflow.

Only a host-owned P00-T20 plan, one detached immutable Git fixture worktree and
a separately approved WRITE grant can reach this function. One localhost model
candidate is verified by the existing syntax and fixed-function brokers and
only THAT SAME in-memory source/sha may be published as a new, non-overwriting
fixture file. At most one model revision is permitted; any broker error aborts.

IMPORTANT: This is not a developer daemon, a safe general project patcher or
independent OS sandbox attestation. The source is not executed on the host.
Default Docker/model integrations require a real authorized Linux host.
Tests inject trusted *mock* model/brokers and use real disposable Git IO.
"""
from __future__ import annotations

import os
from pathlib import Path
from typing import Callable

from tools.dev_fixture_repair_loop import (
    FixtureRepairDenied, _verify_draft, _verify_syntax,
)
from tools.dev_fixture_functional_repair_loop import (
    _VALID, _INVALID, _TEST_PASS, _TEST_FAIL,
    FunctionalRepairDenied, _validated_runtime_receipt,
)
from tools.docker_syntax_broker import (
    DockerSyntaxDenied, _docker_binary, _rootless_socket, run_python_syntax,
)
from tools.docker_fixture_runtime_broker import (
    FixtureRuntimeDenied, run_python_fixture_tests,
)
from tools.local_fixture_drafter import (
    LocalFixtureDenied, draft_local_fixture, make_fixture_request,
)
from tools.scoped_worktree_fixture_writer import (
    ScopedFixtureWriteDenied, _linux_preflight, _validate_detached,
    apply_one_disposable_fixture,
)
from tools.workspace_policy import WorkspaceScope

_TASK = "P00-T20"
_MAX_ATTEMPTS = 2


class VerifiedFixtureFlowDenied(ValueError):
    """Sanitized error with no generated source, remote token or private path."""


def _result(status: str, attempts: list[dict], written: dict | None = None) -> dict:
    """Source-free, explicitly NON-attested workflow summary."""
    return {
        "status": status, "phase": "P00", "task_id": _TASK,
        "attempt_count": len(attempts), "max_attempts": _MAX_ATTEMPTS,
        "repair_attempted": len(attempts) > 1,
        "attempts": attempts,
        "written_candidate_sha256": (
            written["candidate_sha256"] if written is not None else None
        ),
        "source_commit_sha": (
            written["source_commit_sha"] if written is not None else None
        ),
        "disposable_worktree_files_written": (
            written["disposable_worktree_files_written"]
            if written is not None else 0
        ),
        "trusted_checkout_files_written": 0,
        "github_writes": 0,
        "model_source_executed_on_controller": False,
        "actual_ollama_model_independently_verified": False,
        "rootless_container_independently_attested": False,
        "persistent_worker_deployed": False,
        "production_source_patch_verified": False,
        "autonomous_app_code_repair_verified": False,
    }


def run_verified_fixture_worktree_flow(
    model: str, plan: dict, scope: WorkspaceScope, *,
    expected_task_id: str,
    expected_commit_sha: str,
    trusted_source_repo: Path,
    controlled_root: Path,
    enabled: bool = False,
    operator_ack: bool = False,
    syntax_enabled: bool = False,
    execution_grant: bool = False,
    write_grant: bool = False,
    endpoint: str = "http://127.0.0.1:11434",
    docker_binary: str = "/usr/bin/docker",
    socket_url: str | None = None,
    model_transport: Callable | None = None,
    syntax_broker: Callable = run_python_syntax,
    runtime_broker: Callable = run_python_fixture_tests,
) -> dict:
    """Safely bind a tested candidate SHA to a NEW file in one disposable Git worktree.

    Never expose broker/callable or trusted path/grant injection to a model or
    user-facing API. Fake brokers are allowed for trusted CI tests ONLY and
    cannot prove actual model execution or independent OS sandbox isolation.
    """
    if (
        enabled is not True or operator_ack is not True or
        syntax_enabled is not True or execution_grant is not True or
        write_grant is not True
    ):
        raise VerifiedFixtureFlowDenied("five independent trusted host grants required")
    if expected_task_id != _TASK:
        raise VerifiedFixtureFlowDenied("only P00-T20 fixture workflow authorized")

    # Host-owned worktree/commit and OS security are checked BEFORE model
    # inference or container work, not after receiving adversarial source.
    try:
        _linux_preflight()
        _validate_detached(scope, trusted_source_repo, controlled_root,
                           expected_commit_sha)
        _, valid, path, plan_sha = make_fixture_request(
            model, plan, scope, expected_task_id=expected_task_id,
        )
    except (ScopedFixtureWriteDenied, LocalFixtureDenied, OSError,
            ValueError, TypeError, KeyError):
        raise VerifiedFixtureFlowDenied("fixture worktree/plan preflight rejected") from None

    if syntax_broker is run_python_syntax or runtime_broker is run_python_fixture_tests:
        try:
            _docker_binary(docker_binary)
            _rootless_socket(socket_url or "")
        except (DockerSyntaxDenied, OSError, ValueError):
            raise VerifiedFixtureFlowDenied("rootless broker preflight unavailable") from None

    previous = None
    feedback = _INVALID
    seen = set()
    attempts = []
    for attempt in range(1, _MAX_ATTEMPTS + 1):
        try:
            draft = draft_local_fixture(
                model, valid, scope, expected_task_id=expected_task_id,
                endpoint=endpoint, transport=model_transport,
                repair_source=previous, repair_feedback=feedback,
            )
            candidate_sha = _verify_draft(draft, valid, path, plan_sha, scope)
        except (LocalFixtureDenied, FixtureRepairDenied, OSError,
                TypeError, ValueError):
            raise VerifiedFixtureFlowDenied("candidate/model proposal rejected") from None
        if candidate_sha in seen:
            raise VerifiedFixtureFlowDenied("repeated failed candidate refused")
        seen.add(candidate_sha)

        try:
            syntax = syntax_broker(
                valid, draft.source, scope, expected_task_id=expected_task_id,
                enabled=True, docker_binary=docker_binary, socket_url=socket_url,
            )
            syntax_status = _verify_syntax(syntax, candidate_sha)
        except (DockerSyntaxDenied, FixtureRepairDenied, OSError,
                TypeError, ValueError, TimeoutError):
            raise VerifiedFixtureFlowDenied("isolated syntax broker denied") from None

        stage = {
            "attempt": attempt,
            "candidate_sha256": candidate_sha,
            "preview_receipt_sha256": draft.preview_receipt_sha256,
            "syntax_status": syntax_status, "functional_status": "NOT_RUN",
        }
        if syntax_status == _VALID:
            try:
                runtime = runtime_broker(
                    valid, draft.source, scope, expected_task_id=expected_task_id,
                    enabled=True, operator_ack=True, execution_grant=True,
                    docker_binary=docker_binary, socket_url=socket_url,
                )
                functional_status = _validated_runtime_receipt(
                    runtime, candidate_sha
                )
            except (FunctionalRepairDenied, FixtureRuntimeDenied,
                    OSError, TypeError, ValueError, TimeoutError):
                raise VerifiedFixtureFlowDenied("isolated functional broker denied") from None
            stage["functional_status"] = functional_status
            attempts.append(stage)

            if functional_status == _TEST_PASS:
                # Never accept an untrusted *receipt-provided* source. The
                # verified draft SOURCE object is passed directly to the fd
                # writer with its independently checked exact SHA.
                try:
                    written = apply_one_disposable_fixture(
                        valid, draft.source, scope,
                        expected_task_id=expected_task_id,
                        expected_candidate_sha256=candidate_sha,
                        expected_commit_sha=expected_commit_sha,
                        trusted_source_repo=trusted_source_repo,
                        controlled_root=controlled_root,
                        enabled=True, operator_ack=True, write_grant=True,
                    )
                except (ScopedFixtureWriteDenied, OSError, ValueError, TypeError):
                    raise VerifiedFixtureFlowDenied(
                        "disposable write denied; reconcile worktree before retry"
                    ) from None
                if (
                    type(written) is not dict or
                    written.get("status") != "DISPOSABLE_WORKTREE_FIXTURE_CREATED" or
                    written.get("candidate_sha256") != candidate_sha or
                    written.get("source_commit_sha") != expected_commit_sha or
                    written.get("path") != path or
                    type(written.get("disposable_worktree_files_written")) is not int or
                    written["disposable_worktree_files_written"] != 1 or
                    written.get("trusted_checkout_files_written") != 0 or
                    written.get("github_writes") != 0 or
                    written.get("model_source_executed") is not False or
                    written.get("os_sandbox_attested") is not False or
                    written.get("persistent_worker_deployed") is not False or
                    written.get("production_source_patch_verified") is not False
                ):
                    raise VerifiedFixtureFlowDenied("unexpected write receipt identity")
                return _result(
                    "FIXTURE_VERIFIED_AND_WRITTEN_TO_DISPOSABLE_WORKTREE",
                    attempts, written,
                )
            feedback = _TEST_FAIL
        else:
            attempts.append(stage)
            feedback = _INVALID
        if attempt == _MAX_ATTEMPTS:
            return _result("FIXTURE_UNRESOLVED_NO_WORKTREE_WRITE", attempts)
        previous = draft.source
    raise VerifiedFixtureFlowDenied("unexpected bounded loop exit")
