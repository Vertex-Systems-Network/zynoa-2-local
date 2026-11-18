# PR Task Tables — Phase Progress Source of Truth

**Status:** P00 implementation on [draft PR #1](https://github.com/Vertex-Systems-Network/zynoa-2-local/pull/1). **One phase branch → one primary PR → one versioned task manifest.**

## User-visible promise and current reality

Every phase PR description MUST contain a human-readable task table with its **total tasks**, each task ID/title, one of four explicit statuses, supporting evidence or blocker reference, and a calculated completion percentage. The table is created from the version-controlled JSON, not from a model's narrative summary. Nothing may silently mark a task complete when its tests/evidence do not support completion.

**P00 has a real table:** `docs/state/pr-tasks/P00.json` is the single versioned task source; task counts are calculated dynamically from it, not fixed in this runbook, and rendered on PR #1 using managed markers. The current PR description was updated directly through the GitHub connector. Its future automated updater is implemented in this P00 PR, but the default-branch GitHub Actions updater cannot activate **until the workflow is merged into trusted main** and Github permissions allow it. A separately installed trusted worker can sync earlier with explicitly provisioned PR-body write credentials; no such background worker is currently deployed.

## Canonical task manifest contract

Path convention: `docs/state/pr-tasks/<PHASE>.json`, one canonical file for each phase (including P08I). Required fields: `schema_version=1`, `phase`, `branch`, `pr_number`, `update_policy=evidence-gated`, `source_of_truth`, and `tasks`. Each task requires:

| Field | Meaning |
|---|---|
| `id` | Stable phase-scoped ID (e.g. P00-T13), strictly increasing |
| `title` | Short plain-text task summary; no Markdown/HTML injection |
| `status` | DONE, IN_PROGRESS, TODO or BLOCKED |
| `reference` | Real same-repository GitHub run, PR, Issue or commit URL |

`DONE` and `BLOCKED` require a reference. For DONE, the linked run/commit/PR must actually support the *specific limited task*, not just a green unrelated build. Blocked tasks should link to an accurate open issue. A reference URL's existence does NOT independently attest the task; independent reviewer and evidence collection still apply. An error or warning must be recorded as an issue/checkpoint when it affects completion.

Allowed statuses: **DONE** = exact scoped task verified; **IN_PROGRESS** = implementation ongoing but acceptance not finished; **TODO** = not started; **BLOCKED** = a real dependency/permission/test gate prevents completion. A task can move back to IN_PROGRESS/BLOCKED when evidence is invalidated; never conceal regressions.

Summary is computed every render: total, done, in progress, pending, blocked and integer percent = floor(done/total*100). No progress is inferred from CI status alone; the phase can remain blocked with a 100% status count if all task descriptions were incorrectly scoped, so the PR always retains separate release/merge gates.

## How each AI agent updates the PR table

1. Reconcile actual GitHub phase/branch/PR HEAD and current CI status, plus `AGENTS.md`, `PHASE.json`, STATUS/HANDOFF and this contract.
2. At phase start, plan all known phase tasks and create one `docs/state/pr-tasks/<PHASE>.json` in the **same phase branch**. Update its `pr_number` to the actual newly created PR before claiming sync.
3. Each coding/test/research/documentation subtask updates the manifest's status as evidence changes; commit the JSON **on the same PR branch** along with source, tests, Help/Wiki and structured changelog record. If newly discovered work is in-scope, append a new stable task ID and update total automatically.
4. Read-only CI runs `python scripts/check_pr_task_board.py` to verify manifest structure, current phase/branch/PR binding and status/evidence syntax. The test job has **no pull-requests(write)** permission.
5. The *trusted* updater replaces only the marked PR body section `<!-- ZYNOA_PR_TASK_BOARD_START v1 -->` through `<!-- ZYNOA_PR_TASK_BOARD_END -->`. It preserves all other human-authored PR notes.
6. When new code is first merged to **main**, `.github/workflows/pr-task-table-sync.yml` listens to successful Governance v3.2 PR workflows and automatically syncs subsequent phase PR descriptions. It checks live PR head SHA, repo, base and phase, reads the PR HEAD **as bounded JSON only**, then updates the body. It NEVER checks out or executes untrusted PR code with a write token.
7. Before that trusted-main workflow is installed, or for a host-initiated update, use a separately provisioned PR-body-only write token with `tools/pr_task_board.py --sync`. This is **not automatically active just by adding the file**.

## Reproducible commands

Read-only local audit:

```bash
python scripts/check_pr_task_board.py
python -m tools.pr_task_board --manifest docs/state/pr-tasks/P00.json --validate
python -m tools.pr_task_board --manifest docs/state/pr-tasks/P00.json --print
python -m unittest tests.test_pr_task_board tests.test_pr_task_trusted_sync -v
```

When a TRUSTED host-side controller has acquired the actual 40-character current PR HEAD SHA, narrow Pull Requests(write) token and explicit scoped approval from its deployment config:

```bash
# Securely inject these via the host service credentials store; NEVER commit them.
# ZYNOA_PR_TASK_WRITE_ENABLED=1
# ZYNOA_PR_TASK_WRITE_TOKEN=<scoped write identity, NOT a model-exposed token>
python -m tools.pr_task_board --manifest docs/state/pr-tasks/P00.json \
  --sync --expected-head <verified-40-char-PR-HEAD-SHA>
```

The CLI is disabled by default and verifies live PR identity, branch, repo, head SHA and base before writing. It checks for body/HEAD race changes, writes only the managed body section, then performs a GitHub readback verification. Because GitHub PATCH does not provide a task-table-specific atomic compare-and-swap, use **one trusted sync writer per repository/PR**; competing manual body edits can still race. On a mismatch, log/reconcile instead of assuming the write succeeded.

## Trusted GitHub workflow security

`.github/workflows/pr-task-table-sync.yml` uses `workflow_run`, minimal `contents:read` and `pull-requests:write`, and a trusted checkout of **main only**. It does NOT checkout PR HEAD, execute head scripts, invoke AI, run arbitrary shell from task data, or accept a fork as a trusted source. It treats a successful CI event as a **hint**, then independently fetches the original GitHub Actions run with the narrow `actions:read` permission. The trusted default-branch code verifies the exact run ID, `Governance v3.2` workflow path, completed success, repository, head SHA, phase branch and PR association, and then reconciles live PR/PHASE.json/manifest before a bounded body-only PATCH. Missing, stale, unrelated or unverifiable runs fail closed; the event alone never grants write authority. A stale run or missing PR association is skipped safely; a CI failure does not grant task status completion.

GitHub's official [Get a workflow run REST endpoint](https://docs.github.com/en/rest/actions/workflow-runs#get-a-workflow-run) supports authenticated run readback. Its reported success does not independently prove the caller has installed or deployed the future privileged task-table workflow. Mocked tests are security contracts, not operating evidence.

GitHub's official security guidance warns that privileged `workflow_run` jobs executing untrusted head code can lead to compromise: https://docs.github.com/en/actions/reference/security/secure-use . The workflow only becomes operational once merged to the default branch; GitHub's event documentation confirms the default-branch requirement: https://docs.github.com/en/actions/reference/workflows-and-actions/events-that-trigger-workflows .

## Exit gates for each phase

- Actual phase PR description contains one valid managed table with **every** task from its current manifest (no duplicate IDs).
- Every DONE task has honest relevant verification; every BLOCKED task references a real blocker. Task changes correspond to source/test/docs/changelog commits where applicable.
- Independent CI, security, actual screenshots and module release gates remain separate from task %.
- PR is not merged until all relevant **pre-merge** requirements are verified and critical blockers closed correctly, then merge is verified remotely, status/HANDOFF persisted, and the next phase manifest/PR created.
- No screenshot, published Wiki, product binary, unattended host or privileged merge is implied by a green task-board test.

**P00 still blocked:** [Issue #3](https://github.com/Vertex-Systems-Network/zynoa-2-local/issues/3). [Post-merge Issue #4](https://github.com/Vertex-Systems-Network/zynoa-2-local/issues/4) is tracked separately. All P08I Designer interoperability deferral remains unchanged.
