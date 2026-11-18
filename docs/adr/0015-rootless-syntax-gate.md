# ADR-0015 — Rootless Docker Syntax Checks Require Independent Host Authority

**Date:** 2026-11-18 • **Status:** Accepted for P00 contract implementation; actual container isolation NOT VERIFIED.
**Module:** M22 • **Primary PR:** [#1](https://github.com/Vertex-Systems-Network/zynoa-2-local/pull/1).

## Problem

P00 has validated Ollama `DRAFT_ONLY` plans and disposable file preview; it lacks any independently bounded way to check untrusted Python syntax. The privileged host cannot safely AST-parse complex adversarial input. A Docker CLI invocation with default privileges, mutable image tags, working directory mounts, rootful Docker socket or ignored cgroup limits would violate the separation of model output and host authority.

## Decision

Implement `tools/docker_syntax_broker.py` with two separate operations:

1. `plan_python_syntax` validates one bounded Python `tests/fixtures/*.py` candidate under independent trusted P00 `WorkspaceScope` and `expected_task_id`, returns an immutable digest-bound internal job and performs NO Docker or filesystem operation.
2. `run_python_syntax` is disabled by default. If an independently installed operator host enables it, it **recreates the job from the trusted scope** (no forged model-created job), requires non-root Linux and owner-matching rootless Unix Docker socket, actual daemon rootless attestation plus cgroup v2/systemd, digest-pinned pre-cached official Python image, no network/host mounts, read-only root, all Linux capabilities dropped, no-new-privileges, nonroot user, PID/memory/CPU limits and private ephemeral temp storage. The candidate is sent via STDIN to a fixed compiler script; it is **compiled but not executed**.
3. Return only fixed sanitized valid/invalid result, expected task, digest, and explicit `model_source_executed=false`, `workspace_files_written=0`, `github_writes=0`, `independent_host_sandbox_verified=false`. On timeout attempt cleanup of the exact random container name, and block on uncertain cleanup.

Docker's official [rootless resource limit documentation](https://docs.docker.com/engine/security/rootless/tips/) confirms cgroup limits may be silently ignored without cgroup v2 and systemd. Merely setting Docker flags does not prove actual enforcement; these reports are required by the broker and **the operator must independently verify delegated controllers and resource ceilings**. [Docker image digest documentation](https://docs.docker.com/reference/cli/docker/image/pull/) explains content pinning; a digest is not signature or vulnerability verification.

## Alternatives

- Parse Python in the privileged host using `ast.parse`: rejected due to parser crash/resource exhaustion risk.
- Execute a direct subprocess with Python OS resource limits: rejected because POSIX rlimits do not isolate filesystem, network, credentials and kernel access.
- Use a rootful Docker daemon with restrictive `docker run` flags: rejected; Docker daemon socket grants extensive host privileges.
- Allow dynamic runtime image tags or auto-pulls: rejected, breaks reproducibility and opens dependency/supply-chain path to model-controlled network.
- Launch an ephemeral container on every CI without a real rootless host: not treated as security proof; mock contract tests are usable on both OSs and actual live host tests are a **mandatory later gate**.

## Consequences / remaining risks

The broker is real source code, with cross-platform unit tests and a clearly fixed command, but **no actual user-owned host has run the container**. Rootless Docker can still have kernel/daemon vulnerabilities, image supply-chain risks, ignored CPU delegation and incomplete timeout cleanup after an external process crash. Docker syntax-only compilation does not test a program's behavior or satisfy autonomous code patch/test/repair. P00-T19 remains BLOCKED, P00-T20 remains IN_PROGRESS, PR #1 remains DRAFT, Issue #3 open, and P01 is forbidden until actual P00 remote merge evidence.

[Detailed operator contract](../operations/P00_DOCKER_SYNTAX_BROKER.md) · [P00 task table](../state/pr-tasks/P00.json) · [Infrastructure blocker](https://github.com/Vertex-Systems-Network/zynoa-2-local/issues/3).

## P00 decision extension — operator-owned live syntax smoke (2026-11-18)

Provide a **separate, two-flag operator CLI** around the existing compile-only rootless broker, with fixed known-safe valid/invalid fixtures. Rejected alternatives: invoking privileged Docker implicitly from untrusted PR CI, or using arbitrary model-authored programs for a host self-test. Neither was acceptable. The narrow CLI can be run by a verified Linux host operator without creating new file/command authority or claiming a deployed AI coding worker. Mock tests cannot establish real isolation; P00-T19 remains BLOCKED pending independent host and negative-containment evidence.
