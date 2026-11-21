# ADR-0013 — Model-Only Plans Cannot Become Developer Execution Authority

**Date:** 2026-11-18 · **Status:** Accepted for P00 proposal adapter; safe execution remains BLOCKED.
**Phase/PR:** P00 / [draft PR #1](https://github.com/Vertex-Systems-Network/zynoa-2-local/pull/1)
**Module:** M22 · **Task:** P00-T20 IN_PROGRESS.

## Context

The user wants a continuously running AI software developer. The existing P00 observer, SQLite queue, local model inventory and worktree planner do not invoke a coding model. A naïve LLM connection that executes generated JSON/shell could cross repository privilege boundaries, leak secrets or bypass the per-phase guarded merge contract.

## Decision

Implement a **proposal-only** Ollama adapter first, using [Ollama's official chat JSON-schema format](https://docs.ollama.com/capabilities/structured-outputs). Only a host-generated task scope may request local model inference; permitted outputs are small validated JSON proposals, not code, patches or tool invocations.

The host must validate all proposed paths using the independently provisioned `WorkspaceScope`, fixed P00 task/branch and one of the existing read-only tests. No output confers write/shell/network/GitHub privileges. Explicit loopback, disabled proxies and redirects and strict response size limits reduce network/data exposure. Unicode control/bidi spoofing and file paths to planner/host/security authority sources are refused.

## Alternatives

- **Prompt-only safety:** rejected; cannot enforce file/command scope.
- **Model-generated arbitrary shell commands:** rejected; requires OS sandbox, file broker, credentials segregation and attested remote execution first.
- **Provider-agnostic remote API as the first adapter:** deferred; violates initial local-first preference and adds external data/credential exposure. A future normalized abstraction can use equivalent verified contracts.
- **No model integration until OS sandbox deployed:** safer operationally but prevents a testable data-only inference contract. The chosen implementation provides a testable **non-executing** bridge without granting capabilities.

## Residual gaps and evidence

- Only mocked Ollama responses have been tested in CI; no user-owned host model availability or quality benchmark exists.
- No code execution, worktree mutation, error repair, issue posting or automatic PR merge is implemented by this adapter.
- Existing path validation does not defeat filesystem races; isolated host file-handle broker still required.
- Independent P00-T17/T19/T21/T23 security, deployment and end-to-end gates remain required. A green CI run on this adapter does not authorize P00 merge or P01.

References: [model gateway](../operations/P00_LOCAL_MODEL_PLANNING.md), [scope policy](../operations/P00_WORKTREE_POLICY.md), [P00 task manifest](../state/pr-tasks/P00.json), [infrastructure Issue #3](https://github.com/Vertex-Systems-Network/zynoa-2-local/issues/3).

## Consequences

The request/response schema becomes a fixed host-facing interface. Later execution components must receive a **new, separate, independently granted capability**, not assume that a validated proposal permits writes. Real model inference, sandboxed patch/test/retry, GitHub receipts and full incident/documentation lifecycle require separate evidence before any phase transition.
