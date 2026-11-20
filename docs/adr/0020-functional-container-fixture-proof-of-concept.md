# ADR-0020 — Test one model-authored function only inside a rootless container

**Date:** 2026-11-20 · **Status:** P00 experimental source implementation; NOT real host sandbox attestation.

## Context
Prior P00-T20 components can plan and generate a small Python fixture, preview it without checkout writes and run a syntax-only check inside opt-in rootless Docker. None evaluates model-authored Python behavior. Running or importing arbitrary model code in the privileged controller process is explicitly disallowed.

## Decision
Introduce a **separate, default-denied** `tools/docker_fixture_runtime_broker.py`. It runs one small `tests/fixtures/*.py` candidate under a fixed `solve(int) == 2*int` five-case test interface **inside** a no-network/no-mount/non-root/read-only rootless Docker container with cgroups checked both outside and inside. Host model source is only stdin bytes, never executable argv or privileged host interpreter input. A bounded local-model functional repair coordinator may request a second candidate only after exact invalid-syntax or failed-functional status. All responses are explicitly **isolation-unverified** and cannot authorize project writes or remote lifecycle operations.

## Rejected alternatives
1. Host-side `exec`, `compile`, model-generated shell commands and mutable worktrees — inadequate OS isolation.
2. Unlimited model/tool-driven Docker retries — no bounded permission, attack or resource policy.
3. Treating a fixed function check or mocked Docker as general correctness/secure deployment proof — incomplete and misleading.

## Caveats and follow-up
Even a rootless container is not an absolute boundary; default Docker seccomp and current kernel/runtime require independent host security review, cgroup delegation and containment failure injection before this is used with real adversarial model content. In-container source can still deliberately manipulate test logic or make the sandbox fail, so the result cannot substitute for trusted CI or peer review. No live host, real Ollama, Github write executor or model-authored application edit has been deployed. P00-T20 remains IN_PROGRESS; Issue #3 remains OPEN. [Full contract](../operations/P00_SANDBOXED_FUNCTIONAL_FIXTURE.md).
