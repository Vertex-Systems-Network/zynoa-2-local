# ADR-0014 — Ephemeral Preview Is Not an Operating-System Sandbox

**Date:** 2026-11-18 · **Status:** Accepted as P00 staging-only bridge; source edits and OS isolation remain BLOCKED.
**Phase:** P00 · **Module:** M22 · **Primary PR:** [#1](https://github.com/Vertex-Systems-Network/zynoa-2-local/pull/1).

## Context

The local Ollama adapter can emit a validated `DRAFT_ONLY` plan, but turning that proposal directly into repository changes would bypass host-controlled file handles, process/network isolation and independent CI. The user needs autonomous software development, but security/phase gates cannot be waived merely because test fixtures are available.

## Decision

Introduce `tools/fixture_draft_stager.py` as an **ephemeral fixture preview**:

- A trusted, independently supplied P00 task ID and `WorkspaceScope` are required; never use the model's claimed task ID as authorization.
- Accept only exact, bounded `tests/fixtures/<file>.json|.py|.txt|.md` draft paths and 32 KiB maximum total untrusted candidate text.
- Revalidate the model's draft-only plan using existing workspace scope before any staging.
- Stage inside a newly generated temporary directory outside the checkout, with exclusive creation, then immediately delete it; do not touch source or user files.
- Compute SHA-256 receipt, lengths and status; never echo raw source, private paths, credentials or user data.
- Treat untrusted Python **only as text**. Parsing it with `ast.parse` in the privileged host process is explicitly rejected because parser recursion/resource exhaustion is possible. JSON payloads are size-bounded and decoded but not executed.
- Use Linux and Windows CI fixtures for cleanup/negative-case verification; do not claim these prove an OS sandbox.

## Alternatives considered

1. **Run AI generated Python directly in the agent process:** rejected; arbitrary code execution in host privileges.
2. **`ast.parse` as a cheap privileged security scan:** rejected; syntax checks are not isolation and AST parsing can exhaust resources or crash on complex adversarial input. See [Python 3.12 ast](https://docs.python.org/3.12/library/ast.html).
3. **Write directly to a Git worktree after `WorkspaceScope.check`:** rejected for now; path validation has TOCTOU limitations and a worktree is not a sandbox (ADR-0011).
4. **Only dry-run without writing any bytes:** safe but does not test cross-platform staging/cleanup. Chosen limited temporary-file path verifies a small real filesystem lifecycle without touching the repository.
5. **Start a Docker/WSL2 executor immediately:** deferred until a trusted host/identity, daemon privileges, image pinning, mount isolation, resource caps, credential segregation and independent OS tests are actually available.

## Consequences

A new reproducible, inspectable preview/receipt contract exists, but **no model-written code is ever run**, no repository patch is applied, no user file/chat data is touched, no GitHub action runs, and no autonomous worker is deployed. P00-T20 stays IN_PROGRESS; P00-T19 stays BLOCKED by [Issue #3](https://github.com/Vertex-Systems-Network/zynoa-2-local/issues/3).

Real isolated execution must be separately designed, installed, independently verified and authorized by a privileged host controller. A developer cannot convert a successful preview into an automatic privileged action. The future host must also verify actual PR/CI/GitHub merge receipts. No P01 phase may start until P00's protected merge SHA is verified.

[Preview contract](../operations/P00_FIXTURE_DRAFT_STAGING.md) · [Model planning](../operations/P00_LOCAL_MODEL_PLANNING.md) · [P00 task board](../state/pr-tasks/P00.json) · [Release gates](../quality/RELEASE_GATES.md).
