# ADR-0022 — Bind exact tested model fixture to one detached-worktree file creation

**Date:** 2026-11-20 · **Status:** P00 source implementation; real sandbox and worker deployment UNVERIFIED.

## Context
P00 had independent model generation, syntax validation, fixed-function sandbox contracts and an fd-scoped disposable worktree writer, but a model's passing test receipt did not directly authorize the *identical in-memory candidate* for file publication. A digest alone is not proof of genuine container provenance.

## Decision
New `run_verified_fixture_worktree_flow` composes the existing validated P00-T20 components in a single trusted-host call. Independently check the model plan, exact SHA, detached Git source commit and worktree identity before inference. Require five explicit operator grants and the real-broker rootless preflight. Validate every syntax and functional receipt against that specific candidate SHA, then publish ONLY the same candidate bytes with the existing O_NOFOLLOW/dirfd/fsync/no-replace writer after exact functional pass. Retry one model candidate at most on exact functional/syntax failure, refuse repeats, and never write to trusted source checkout or GitHub. In CI, provider/sandbox are mocked but new Git fixture file IO is real.

## Rejected
1. Separate model result and later free-form workspace write: attacker may swap content after a test; source identity not causally tied to publication.
2. Rehydrate candidate bytes from a model/test-supplied receipt or allow arbitrary Git patch/tool calls: untrusted data becomes authority.
3. Grant production PR writes or treat mocked sandbox PASS as deployment/host attestation: unsupported proof.

## Limitations
Single-process test-to-write flow is NOT a signed, independent attestation protocol and relies on trusted host operator and code, model/real Docker API security, same-UID control and file creation permissions. Functional checks cover only `solve(x)=2*x`; not full app edits/tests. A passing mock receipt cannot certify actual sandbox isolation or independently verified tests. No real deployed worker, local model, GitHub write/merge or P01; P00-T20 IN_PROGRESS. [Runbook](../operations/P00_VERIFIED_FIXTURE_WORKTREE_FLOW.md).
