# ADR-0019 — Limit local-model automatic syntax correction to two isolated attempts

**Date:** 2026-11-20 · **Status:** P00 scoped source implementation; real operator-host proof pending.

## Context
An existing validated local Ollama plan and model-authored fixture text could already reach a disposable source preview; a separate opt-in broker could syntax-compile a fixture inside rootless Docker. But they were not connected into an automatic repair flow. P00-T20 must remain incomplete until real sandboxed repository edits/tests/PR writing are independently proven.

## Decision
Introduce `tools.dev_fixture_repair_loop` as a trusted-host-only, default-disabled coordinator: validate P00-T20 plan before inference, request one model fixture, independently recheck SHA/path and preview digest, call the **existing**, opt-in, rootless **syntax-only** Docker broker; only on the exact `PYTHON_SYNTAX_INVALID_NO_CODE_EXECUTION` result request one correction using the model's own previous candidate and fixed failure label. Retry at most twice, reject duplicate candidate SHA and any invalid Docker/model receipt. No model-managed commands, exception trace exposure, dynamic shell, real workspace writes or GitHub credentials.

## Alternatives rejected
1. Privileged controller runs `compile()` on model code: host process can be exhausted/crashed by malicious syntax.
2. Execute model-authored tests or arbitrary commands and then repair: independent cgroup and filesystem/credential isolation have not been proven.
3. Unlimited retries or model-derived command/error feedback: no bounded cost, denial or policy containment.

## Consequences
The coordination contract can be simulated deterministically on Linux/Windows and run with real Ollama/Docker **only if independently authorized on a user-owned Linux host**. Syntax correctness is not semantic tests, code application, CI repair or a persistent developer. Explicit non-attestation receipt fields remain false; task P00-T20 IN_PROGRESS and Issue #3 OPEN. [Details](../operations/P00_BOUNDED_FIXTURE_REPAIR.md).
