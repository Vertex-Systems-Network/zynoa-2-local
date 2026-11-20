# ADR-0009 — Read-only Authenticated Phase Observer Before Privileged Autonomy

**Status:** Accepted for P00 observer slice; privileged executor/hosting NOT approved or deployed.
**Date:** 2026-11-18
**Phase:** P00 (M22)
**Related:** [research](../research/P00_WORKER_HOSTING_RESEARCH.md), [operations](../operations/P00_WORKER_RUNBOOK.md), Issue #3.

## Context

A developer AI must reconcile exact GitHub phase, PR, checks, issues and merge state. A local status file, model text or ephemeral ChatGPT session is not an acceptable authority. The initial repo has no desktop application or persisted development host. Allowing a model to merge arbitrary PRs solely from self-reported success would violate independent quality gates.

## Decision

Build a separate minimal phase-control trust foundation with three boundaries:

1. Pure deterministic transition validation and SQLite WAL history (phase_controller.py).
2. Repository-scoped authenticated **read-only** REST client (github_gateway.py). Fail closed when PR identity, check results, blockers, branch protection, or server merge SHA is missing or inconsistent.
3. Single-owner leased observer (phase_worker.py), restart-safe with bounded retries. It only records sanitized facts and reports pending gates. No GitHub mutation authority or AI-agent shell execution in this process.

A separate developer CI incident bridge uses its own **explicitly enabled** Issues(write) authorization; workflow_run must execute reporter code from trusted main, never untrusted PR HEAD. End-user issue relay is a separate future privacy-controlled product service.

For the full autonomous development product, a **future independent policy broker** must guard all writes, process execution, model calls and GitHub merge actions. Durable worker hosting is prerequisite and is not simulated with a prompt or CI schedule.

## Why not alternatives?

- AI-produced merge status: forgeable and stale.
- All-powerful single bot token in frontend: unacceptable exfiltration/privacy risk.
- GitHub Actions schedule as perpetual process: ephemeral/delayed; cannot claim 24/7.
- Auto-merge on an unprotected main branch: lacks independent trusted gate.
- Premature P01 implementation: violates one-phase-one-PR contract.

## Verification

59 governance+unit tests passed on [GitHub Actions run 44213105650](https://github.com/Vertex-Systems-Network/zynoa-2-local/actions/runs/44213105650), with authenticated live read-only observation. Subsequent commits require fresh CI verification.

## Non-goals / unresolved

No real always-on host or AI coding executor, no live merge automation, no deployed release or app. Repository ruleset configuration is still pending (Issue #3). P00 PR #1 must remain draft until full exit gates pass and merge is verified.
