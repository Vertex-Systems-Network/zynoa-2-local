# Persistent Autonomous Development Controller

## Worker design

Separate always-on worker with SQLite WAL, durable event queue, Git worktrees, GitHub App, scoped shell executor, model router, PR/CI observer and issue reporter. A simple chat request cannot start this persistently without installed hardware/runtime. Control plane has one active phase lease; independent agents have per-work-item leases and isolated worktrees; final patches integrate into same phase branch and PR.

## Lifecycle

1. Startup health → fetch remote GitHub current phase truth → verify branch lease.
2. Reconcile current phase/PR/checks with local recorded snapshots and on-disk Git state.
3. If no verified PR, create single `phase/NN-slug` branch from main, register and create PR after first safe vertical slice.
4. Run Pre-DEV checklist, collect research, select design, define failing tests.
5. Implement bounded increment, run fast checks; record output and warnings.
6. Repair failures under bounded retries (signature-aware), add regression test, rerun impacted and global suites.
7. Capture UI/document images from running test build, update help articles and wiki sources; check links and screenshots.
8. Commit, push active branch, update same PR; request/observe CI, audit remote statuses.
9. When all required gates pass, use repo-supported auto-merge (when allowed). Verify actual merge SHA and post-merge smoke.
10. Update state/decisions/handoff; release branch lease and create next phase branch from current main.

## Autonomous non-stop semantics

- **Never** keep retrying identical failure indefinitely. Use exponential backoff and max attempts (illustrative: 2 transient infra retries, 3 distinct code fixes before opening blocker).
- If one task blocked, switch to independent in-scope tasks; do not jump to next phase code.
- If all work blocked, worker enters `BLOCKED_WAIT_EVENT`, records status/issue and wakes on GitHub, timer or environment change; it does NOT falsely mark phase complete.
- Tools cannot self-authorize; approved capability envelope set during initial administrator setup. Pre-approved routine branch/PR/test/edit actions require no recurring approval prompts.
- Logging and snapshots require low overhead but enough evidence to diagnose. Redact tokens, user content and project secrets.

## Recovery and idempotency

Avoid re-running non-idempotent actions after crashes. Before creating branch/PR/issue, check exact remote existing state and idempotency fingerprint. Event records use sequence, attempt ID, branch SHA, tool hash, result hash and monotonic timestamp. `MERGED_VERIFIED` only after server confirms. Manual modification of protected branch cannot be silently reconciled as 'expected'.


## P00 Implementation vs full autonomous loop (2026-11-18)

Current code provides the *observation* and *guarded merge primitive*, not the complete loop: `tools/github_gateway.py`, `tools/phase_worker.py`, `tools/phase_merge_guard.py`, `tools/github_issue_bridge.py`. The merge executor is default-disabled and PR CI exercises only a read-only dry-run. Actual continuous coding needs an installed supervised host, task queue, model/agent execution, worktree permission broker, branch ruleset and end-to-end guarded merge tests. Repository Issue #3 remains open; P00 is not complete and P01 may not start. See [P00 runbook](P00_WORKER_RUNBOOK.md).

## P00 durable queue implementation — separate from full autonomy

An initial `tools/dev_job_queue.py` (SQLite WAL durable state) and `tools/dev_job_runner.py` (three allowlisted read-only governance checks) now provide job lifecycle `PENDING → RUNNING → SUCCEEDED / RETRY_WAIT / BLOCKED` with immutable job IDs, phase/branch isolation, expiry recovery, owner-token fencing and bounded retry. The CI smoke actually enqueues and completes three safe checks using a temporary database. **It does not run a coding model, create/edit product files, invoke shell, merge GitHub PRs or operate in the background on a deployed machine.** Future model-driven work must have an independent OS sandbox/worktree and non-idempotent action journal; never re-use read-only replay semantics for Git pushes or deployments. See [queue specification](P00_DURABLE_JOB_QUEUE.md). Merge guard now checks applied PR/status rules pinned to trusted CI App ID, not just `protected=true`.

## P00 Task Dependency DAG — implemented backend (2026-11-18)

The read-only P00 queue now has an enforced `job_dependencies` DAG: `tools/dev_task_graph.py` registers cycle-free same-phase/same-branch prerequisites; `JobQueue.claim` waits for durable predecessor SUCCESS; a blocked/corrupt/missing prerequisite blocks downstream tasks. Independently runnable checks proceed even when other tasks are blocked. The CI smoke runs `phase-policy → design-spec → docs-integrity` despite inverse priorities, proving dependencies are enforced in SQLite rather than prompt text. This is a scheduler primitive only. Actual autonomous AI task execution, protected worktrees, issue-to-fix-to-PR workflows and persistent host deployment remain P00 blockers in Issue #3. See [DAG documentation](P00_TASK_DEPENDENCY_GRAPH.md) and [ADR-0010](../adr/0010-phase-task-dag.md).

## P00 worktree plan and host capability boundary (not deployed)

The next M22 slice adds `tools/workspace_policy.py` and `tools/worktree_plan.py`, which validate model-proposed path operations and build an immutable detached/no-checkout Git worktree command from a **trusted host** source. No production model task, shell, Git write or user repository modification is executed. CI tests one real worktree against a freshly created temporary trusted fixture, which is not a sandbox and is not reusable proof for untrusted repositories. A separate OS sandbox/worktree operation broker with durable receipts, credentials isolation and verified Windows/Linux behavior remains required before any executable coding worker can be turned on. See [worktree security](P00_WORKTREE_POLICY.md) and [ADR-0011](../adr/0011-worktree-is-not-sandbox.md); [Issue #3](https://github.com/Vertex-Systems-Network/zynoa-2-local/issues/3) stays open.

## 2026-11-18 audit: why the current loop is not continuous

[Detailed audit](P00_CONTINUOUS_AUTONOMY_AUDIT.md): `phase_worker.py` is an **undeployed observer**; `dev_job_runner.py` is a fixed three-check read-only smoke; `governance.yml` is event-triggered testing (not a model developer); and `phase_merge_guard.py` is default-disabled. `PHASE.json.worker_running=false` matches the absence of a deployed host. A ChatGPT message is not a process supervisor. The system will not spontaneously resume when the chat ends.

**Correct sequence:** Provision an actual always-on developer machine/service and scoped credentials, then deploy safe model-driven job execution with OS isolation and durable receipts. CI remains independent judge; the host must watch it, repair within bounds and continue safe work. Do not use endless retries to evade true blockers. Current Issue #3 is an actual pre-merge blocker; when *its pre-merge requirements* are genuinely resolved, close it with evidence before protected merge, and track resulting merge SHA verification as a separate post-merge checkpoint. Never silently filter a still-unresolved blocker from GitHub policy.

This separates P00's external developer bootstrap from future P04 Coding Studio and P10 in-product autonomy. Full graphical screenshots are recorded when the actual UI exists, not in the backend-only bootstrap. A new prompt alone cannot make this engine persistent.

## PR task status projection after EVERY development task (2026-11-18)

Alongside the durable task DAG, the controller must maintain `docs/state/pr-tasks/<PHASE>.json`, one manifest per primary PR, and a managed task table in its description. After research/code/test/error fix/docs change, reconcile exact job/CI/issue evidence, update statuses in this file and commit on SAME phase branch. A trusted sync action updates the PR's managed table, preserving human-authored sections; if GitHub write unavailable, persist a visible pending-sync blocker and retry with bounded backoff from an actually deployed host. The new `workflow_run` writer only activates after merge to main, and must never execute PR head code with write privileges.

The table is a status projection; it is not a phase transition controller, a 24/7 agent or a replacement for secure merge prerequisites. Details: [PR Task Tables](PR_TASK_TABLES.md).
