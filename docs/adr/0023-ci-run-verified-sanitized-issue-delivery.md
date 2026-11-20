# ADR-0023 — Verify CI run by GitHub API before privileged sanitized Issue write

**Date:** 2026-11-20 · **Status:** source-only, default-branch activation still blocked by P00 merge.

## Context
The unmerged P00 branch already contained an incident bridge and privileged `workflow_run` listener. It could publish a generic developer issue only after merge, but without verifying *which* failed run caused delivery or safely updating a deduplicated issue with new run evidence.

## Decision
Use a separately permissioned trusted-default-branch `workflow_run` job (`actions:read`, `issues:write`, no untrusted PR checkout). Independently GET the failed Governance run, check its exact id/SHA/status/conclusion/workflow/repository identity, and attach only its canonical GitHub Actions URL and full SHA. Fingerprint only sanitized metadata, skip identical run, PATCH only verified bot-owned matching issue with a rebuilt bounded five-run history; POST otherwise. Require canonical API response readback; private P0/user telemetry never published. No default-branch permission change or active CI issue delivery until policy-verified P00 merge.

## Rejected
Privileged `pull_request` direct write; raw logs/artifacts on privileged event; issue body reuse; unbounded duplicate issue/comment floods; merging PR to activate source before host security gates.

## Consequences
Mock tests can verify redaction, idempotency and allowed GitHub REST operations now. A separately authorized connector can prove manual live Issue creation, **not** future CI worker issue publishing. T22 remains BLOCKED until a genuine failed workflow triggers postmerge listener with authenticated Issue URL readback. [Runbook](../operations/P00_VERIFIED_CI_ISSUE_DELIVERY.md).
