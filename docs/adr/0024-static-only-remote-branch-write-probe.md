# ADR-0024 — Only a fixed trusted fixture may exercise remote Git branch write/readback

**Date:** 2026-11-20 · **Status:** P00 source implementation; actual persistent writer credentials and model-backed repo patch E2E UNVERIFIED.

## Context
P00 has model fixtures and mock-sandbox test receipts, plus a real detached-worktree file creation path; it lacks an independently attested host sandbox and a reviewed authenticated remote Git writer. A direct model→PR push or general worktree patcher is too powerful before those protections exist.

## Decision
Implement `tools/github_static_fixture_publisher.py` as a narrow **separately manually authorized** proof: fixed inert Python fixture bytes, fixed `tests/fixtures` path, fixed PR #1/phase branch, exact HEAD/PR draft check, proof target file absent, Git blob/tree/commit creation with pinned parent, `force:false` ref update, and independent immutable-commit file/readback verification. CI mocks transport; a connector-authenticated real repo write can be separately demonstrated but is not evidence the Python host worker is installed or provisioned. The module has no model-source or shell API.

## Rejected
- Exposing general model-written `git push` or `PUT /contents` with an existing file SHA: broad mutation and overwrite authority without host containment.
- Trusting a model-supplied "tests passed" receipt for GitHub permission: known unverified sandbox and credential boundary.
- Force-update of the branch or merge into protected main to demonstrate capability: violates project governance.

## Consequences
Proves branch-oriented Git data protocol and error/readback handling without expanding the model's authority. GitHub token itself remains a powerful credential; source-side URL filtering is insufficient to prove non-bypass permissions. Genuine model/host/sandbox/PR write and protected merge acceptance remain blocked under Issue #3. [Operations](../operations/P00_TRUSTED_STATIC_GIT_PROBE.md).
