# ADR-0012 — Evidence-Backed Per-PR Task Table and Trusted Synchronization

**Date:** 2026-11-18
**Status:** Accepted for P00 implementation; default-branch automation pending actual merge.
**Module:** M22 · **Current branch:** `phase/00-governance` · **PR:** [#1](https://github.com/Vertex-Systems-Network/zynoa-2-local/pull/1)

## Problem

ChatGPT/Claude/Cursor/Gemini may resume a partial development phase without a reliable list of every task and its actual status. Narrative summaries can omit blocked tasks or become stale; changing a PR body manually after every commit is error-prone. The user requires **total task counts and continuous per-task status updates in EVERY primary phase PR description**.

## Decision

1. Every active phase has exactly one version-controlled manifest at `docs/state/pr-tasks/<PHASE>.json`, bound to its phase, branch and actual primary PR number. All tasks have stable IDs, sanitized plain titles, DONE/IN_PROGRESS/TODO/BLOCKED states and required evidence/blocker GitHub links for terminal states.
2. Compute progress from actual manifest data. No hand-coded percentages; adding tasks adjusts total automatically. A status cannot be promoted to DONE by the renderer because CI happens to pass.
3. The PR description has a uniquely marked managed region. Synchronization replaces **only** this block and preserves author-written rationale, test links, warnings and audit notes.
4. The normal PR CI has `pull-requests:read` only and runs `scripts/check_pr_task_board.py`; it cannot publish the table.
5. After P00 is actually merged to protected main, a separate trusted `workflow_run` action can use minimal `pull-requests:write` authority and run updater **source code from main only**. It reads PR-head task manifests as bounded JSON, checks current remote HEAD/branch/base/PR identity, and refuses stale/forked or failed-CI triggers. **Never execute PR-provided code under the write token.**
6. For the present unmerged P00 PR, update PR body via authorized GitHub connector or separately provisioned host-side PR body writer, with exact remote readback. Do not falsely claim the default-branch automation has already started.
7. The task table is a projection, not the CI/security/merge controller. Real PRE-MERGE infrastructure blockers (Issue #3) remain blocking even if task counts look impressive.

## Security & reliability limits

- GitHub's PR body PATCH is not an atomic per-section compare-and-swap; use a single trusted writer and re-read identity/body immediately before and after an update, fail closed on races.
- Model-provided Markdown/HTML/URLs in task names are rejected. Only allowlisted same-repository GitHub evidence links are accepted.
- A permitted link to a CI run does not itself prove the scoped task; agents and independent acceptance gates still need factual review.
- GitHub `workflow_run` does not run from draft feature branches unless the workflow exists in trusted default main. Even after merge, event delays/rate limits/outages can delay PR table updates; a deployed worker can reconcile pending synchronization.
- The updater must never gain permission to push code, merge PRs, change repository rulesets, create user incidents or access user data.
- This change does not deploy a persistent coding worker, bypass an unprotected main branch or start P01.

## Test plan

`tests/test_pr_task_board.py` covers schema/IDs, exact totals, markdown/URL denial, immutable managed sections, idempotency, stale PR/HEAD refusal, disabled writes, concurrent body edits and remote readback.

`tests/test_pr_task_trusted_sync.py` covers successful same-repo event, failed CI, fork, stale head, invalid phase/manifest, missing token and ambiguity; `tests/test_pr_task_workflow_policy.py` checks the workflow's trusted source checkout, constrained permissions and JSON GitHub Contents API.

## Authoritative links

[PR Task Tables](../operations/PR_TASK_TABLES.md) · [P00 task manifest](../state/pr-tasks/P00.json) · [Current PR #1](https://github.com/Vertex-Systems-Network/zynoa-2-local/pull/1) · [P00 blocker Issue #3](https://github.com/Vertex-Systems-Network/zynoa-2-local/issues/3).

GitHub official guidance: [Secure use of GitHub Actions](https://docs.github.com/en/actions/reference/security/secure-use) and [Events that trigger workflows](https://docs.github.com/en/actions/reference/workflows-and-actions/events-that-trigger-workflows).
