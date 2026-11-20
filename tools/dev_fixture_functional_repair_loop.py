"""P00 fixed fixture syntax + *functional* test repair, source-only policy.

One isolated test contract: a candidate tests/fixtures/*.py must define
solve(x) returning x*2. First syntax-compile candidate in the pre-existing
rootless broker. If syntax is valid, the separate rootless Docker runtime
broker can actually execute candidate code inside a credential-free container.
One trusted feedback-only model correction can follow a syntax or functional
failure. No model-generated shell, workspace edit, GitHub write or merge.

No local model / Docker host is installed by this source; CI uses mocks. Even a
runtime pass does NOT prove production sandbox attestation or full AI coding.
"""
from __future__ import annotations

from typing import Callable
from tools.dev_fixture_repair_loop import (
    FixtureRepairDenied, _verify_draft, _verify_syntax,
)
from tools.docker_syntax_broker import (
    DockerSyntaxDenied, _docker_binary, _rootless_socket, run_python_syntax,
    DEFAULT_IMAGE,
)
from tools.docker_fixture_runtime_broker import (
    FixtureRuntimeDenied, run_python_fixture_tests,
)
from tools.local_fixture_drafter import (
    LocalFixtureDenied, draft_local_fixture, make_fixture_request,
)
from tools.workspace_policy import WorkspaceScope

_TASK = "P00-T20"
_TEST_PASS = "FIXTURE_TESTS_PASSED_ISOLATION_UNVERIFIED"
_TEST_FAIL = "FIXTURE_TESTS_FAILED_ISOLATION_UNVERIFIED"
_VALID = "PYTHON_SYNTAX_VALID_NO_CODE_EXECUTION"
_INVALID = "PYTHON_SYNTAX_INVALID_NO_CODE_EXECUTION"
_MAX_ATTEMPTS = 2


class FunctionalRepairDenied(ValueError):
    """Sanitized denial; no model source, exception text or host paths."""


def _validated_runtime_receipt(value: object, candidate_sha256: str) -> str:
    if not isinstance(value, dict) or value.get("status") not in (_TEST_PASS, _TEST_FAIL):
        raise FunctionalRepairDenied("functional sandbox did not return a fixed verdict")
    if (
        value.get("phase") != "P00"
        or value.get("task_id") != _TASK
        or value.get("candidate_sha256") != candidate_sha256
        or value.get("image_digest") != DEFAULT_IMAGE.split("@", 1)[1]
        or type(value.get("fixed_test_cases")) is not int
        or value["fixed_test_cases"] != 5
        or value.get("container_model_source_execution_requested") is not True
        or value.get("controller_host_source_executed") is not False
        or type(value.get("workspace_files_written")) is not int
        or value["workspace_files_written"] != 0
        or type(value.get("github_writes")) is not int
        or value["github_writes"] != 0
        or value.get("independent_host_sandbox_verified") is not False
        or value.get("real_container_run_independently_attested") is not False
        or value.get("persistent_worker_deployed") is not False
    ):
        raise FunctionalRepairDenied("functional sandbox identity or non-attestation violated")
    return value["status"]


def run_fixture_functional_repair(
    model: str, plan: dict, scope: WorkspaceScope, *, expected_task_id: str,
    enabled: bool = False, operator_ack: bool = False,
    syntax_enabled: bool = False, execution_grant: bool = False,
    endpoint: str = "http://127.0.0.1:11434",
    docker_binary: str = "/usr/bin/docker", socket_url: str | None = None,
    model_transport: Callable | None = None,
    syntax_broker: Callable = run_python_syntax,
    runtime_broker: Callable = run_python_fixture_tests,
) -> dict:
    """Default-denied, two-attempt fixture-only plan/draft/compile/test/repair.

    Broker function parameters are TRUSTED TEST INJECTION ONLY; never pass
    model-provided functions, commands, Docker flags or arbitrary shell.
    """
    if (enabled is not True or operator_ack is not True
            or syntax_enabled is not True or execution_grant is not True):
        raise FunctionalRepairDenied("functional repair requires four trusted host grants")
    if expected_task_id != _TASK:
        raise FunctionalRepairDenied("functional repair restricted to P00-T20")

    try:
        _, valid, path, plan_sha = make_fixture_request(
            model, plan, scope, expected_task_id=expected_task_id
        )
    except (LocalFixtureDenied, ValueError, OSError, TypeError):
        raise FunctionalRepairDenied("functional repair host-plan preflight denied") from None

    # Real non-injected brokers cannot be used until the operator host has
    # independently authorized a local non-root Docker CLI/socket. Merely
    # mocking these conditions in CI cannot attest a real sandbox.
    if syntax_broker is run_python_syntax or runtime_broker is run_python_fixture_tests:
        try:
            _docker_binary(docker_binary)
            _rootless_socket(socket_url or "")
        except (DockerSyntaxDenied, OSError, ValueError):
            raise FunctionalRepairDenied("rootless execution preflight unavailable") from None

    seen = set()
    attempts = []
    previous = None
    feedback = _INVALID
    for index in range(1, _MAX_ATTEMPTS + 1):
        try:
            draft = draft_local_fixture(
                model, valid, scope, expected_task_id=expected_task_id,
                endpoint=endpoint, transport=model_transport,
                repair_source=previous, repair_feedback=feedback,
            )
            sha = _verify_draft(draft, valid, path, plan_sha, scope)
        except (LocalFixtureDenied, FixtureRepairDenied, OSError, ValueError, TypeError):
            raise FunctionalRepairDenied("model draft/preflight rejected") from None
        if sha in seen:
            raise FunctionalRepairDenied("repeated invalid candidate refused")
        seen.add(sha)

        try:
            syntax = syntax_broker(
                valid, draft.source, scope, expected_task_id=expected_task_id,
                enabled=True, docker_binary=docker_binary, socket_url=socket_url,
            )
            syntax_status = _verify_syntax(syntax, sha)
        except (DockerSyntaxDenied, FixtureRepairDenied, OSError, ValueError,
                TimeoutError, TypeError):
            raise FunctionalRepairDenied("syntax broker denied or timed out") from None
        step = {
            "attempt": index, "candidate_sha256": sha,
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
                runtime_status = _validated_runtime_receipt(runtime, sha)
            except (FixtureRuntimeDenied, FunctionalRepairDenied, OSError,
                    TimeoutError, TypeError, ValueError):
                raise FunctionalRepairDenied("functional sandbox refused or failed") from None
            step["functional_status"] = runtime_status
            attempts.append(step)
            if runtime_status == _TEST_PASS:
                return _receipt("FIXTURE_FUNCTIONAL_PASS_HOST_UNATTESTED", attempts)
            feedback = _TEST_FAIL
        else:
            attempts.append(step)
            feedback = _INVALID
        if index == _MAX_ATTEMPTS:
            return _receipt("FIXTURE_FUNCTIONAL_UNRESOLVED", attempts)
        previous = draft.source
    raise FunctionalRepairDenied("unexpected functional repair boundary")


def _receipt(status: str, attempts: list[dict]) -> dict:
    return {
        "status": status, "phase": "P00", "task_id": _TASK,
        "attempt_count": len(attempts),
        "max_attempts": _MAX_ATTEMPTS,
        "repair_attempted": len(attempts) > 1,
        "attempts": attempts,
        "functional_runtime_broker_invoked": any(x["functional_status"] != "NOT_RUN" for x in attempts),
        "real_model_execution_independently_verified": False,
        "trusted_host_model_source_execution": False,
        "workspace_files_written": 0,
        "github_writes": 0,
        "repository_patches_applied": 0,
        "independent_host_sandbox_verified": False,
        "persistent_worker_deployed": False,
        "full_autonomous_development_verified": False,
    }
