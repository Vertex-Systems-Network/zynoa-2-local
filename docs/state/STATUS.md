# Status — 2026-11-18

**Specification status:** v3 expanded planning kit generated locally. **Application implemented:** NO. **GitHub phase branch/PR:** NOT VERIFIED/NOT CREATED by this action. **Persistent development worker:** NOT INSTALLED. **User Help screenshots:** PENDING REAL APP. **GitHub Wiki publication:** PENDING REPOSITORY CONFIGURATION. **Issue bridge:** local sanitization demo only, remote GitHub integration not deployed.

The next phase is P00 governance. Agent must verify real repo state before modifying source and must not reinterpret local example state as remote authority.

## v3.1 specification state — 2026-11-18

Three dossiers added: M23 User Data Vault, M24 Storage/Relocation, M25 Client Update Center. Existing M20 CI publisher expanded. No application code, desktop update notification, backup service, relocation worker, release action, GitHub Issues/PRs or published Wiki is represented as implemented. P00 remains not started until checked against actual remote GitHub state.

## v3.2 specification state — 2026-11-18

M26 change intelligence, versioned Changelog UI, event/PR audit and documentation sync are now specified. Existing product application remains **NOT IMPLEMENTED**. No real release, issue, phase PR, GitHub Wiki or in-app What's New exists. A local schema/generator prototype and tests do not change that. P00 remains PLANNED_NOT_STARTED until actual remote verification.


## P00 repository checkpoint — 2026-11-18

GitHub audit: `Vertex-Systems-Network/zynoa-2-local`, `main` baseline `8dcb546828a8fdeef40dfaa250ac8f6b8639025d`. Created `phase/00-governance` and [draft PR #1](https://github.com/Vertex-Systems-Network/zynoa-2-local/pull/1). **P00 IN_PROGRESS**, not completed. No desktop client, background worker or live Designer import/export is running. Added future P08I DESIGN-IO contract/ADR-0008; execution deferred until P08 core is finished and its merge verified. Repo auto-merge was disabled on initial audit; do not claim automation or merge success absent confirmation.


## P00 implementation slice 1 — 2026-11-18

Actual code added on [draft PR #1](https://github.com/Vertex-Systems-Network/zynoa-2-local/pull/1): `tools/phase_controller.py` pure phase transition/SQLite event journal, unit tests, and DESIGN-IO policy gate. Registered future P08I after native P08 in `docs/state/PHASES.json`; this is **planned interoperability only**. See [P00 preflight evidence](../evidence/P00_REMOTE_PREFLIGHT.md). Worker still NOT DEPLOYED, auto-merge disabled on initial audit, so P00 is **IN_PROGRESS**, not verified complete. [Issue #2](https://github.com/Vertex-Systems-Network/zynoa-2-local/issues/2) tracks future import/export; [Issue #3](https://github.com/Vertex-Systems-Network/zynoa-2-local/issues/3) tracks automation infrastructure.


## P00 resumed implementation slice 2 — 2026-11-18

**Remote truth:** current phase P00, branch `phase/00-governance`, draft PR [#1](https://github.com/Vertex-Systems-Network/zynoa-2-local/pull/1); `main` initial SHA `8dcb546828a8fdeef40dfaa250ac8f6b8639025d`. GitHub repository auto-merge now **enabled**, but `main` reported **unprotected** during live readback; new branch ruleset required. No verified P00 merge, P01 branch or app release.

**Added actual code:** authenticated read-only GitHub evidence gateway, durable single-lease observer with SQLite WAL, safe developer-ci Issue bridge and trusted default-branch failure workflow, 59 passing Python unit/governance tests and authenticated CI observation. Last verified passing CI evidence at [run 44213446505](https://github.com/Vertex-Systems-Network/zynoa-2-local/actions/runs/44213446505) (commit `48eee371a592fdef1a29961658a2bedb7026c550`). Later commits require new CI evidence. Local worker remains **NOT DEPLOYED**; M22 not complete; Wiki source updated, published Wiki and actual screenshots pending.

**Remaining:** [Issue #3](https://github.com/Vertex-Systems-Network/zynoa-2-local/issues/3) dedicated host+secret store, independent guarded write/merge controller, verified ruleset and live end-to-end issue/recovery proof. [Issue #2](https://github.com/Vertex-Systems-Network/zynoa-2-local/issues/2) P08I deferred Designer import/export unchanged.


## P00 resumed implementation slice 3 — 2026-11-18

Guarded merge executor `tools/phase_merge_guard.py` has been added with default-off write permission, fresh authenticated PR/CI/branch-protection/blocker checks, stale-head/stale-base defense, GitHub merge SHA readback and 11 mocked refusal/success tests. CI also runs its **live dry-run with zero GitHub writes**. Long retry sleeps now heartbeat the SQLite lease so no second worker can steal an active lease; regression test included. [Verified GitHub Actions 44214670015](https://github.com/Vertex-Systems-Network/zynoa-2-local/actions/runs/44214670015), code SHA `2a8f0f67b4846603d5d11c02cc029af1c3ab9a66`: **71 Python tests PASS**, guard dry-run PASS, source syntax/spec checks PASS. This is not a real PR merge, deployment or user app test.

**P00 remains IN_PROGRESS / PR #1 DRAFT**. GitHub `main` still unprotected during live observation; issue #3 open; no service host deployed or live trusted write-token workflow exercised. No P01 branch exists. M22 UI/screenshots and published Wiki remain pending.

## P00 resumed implementation slice 4 — 2026-11-18

**Current GitHub authority remains P00**: branch `phase/00-governance`, existing [draft PR #1](https://github.com/Vertex-Systems-Network/zynoa-2-local/pull/1), `main` baseline `8dcb546828a8fdeef40dfaa250ac8f6b8639025d`, unprotected and no applied rulesets at live audit. GitHub `allow_auto_merge=true` does not override missing rules. [Issue #3](https://github.com/Vertex-Systems-Network/zynoa-2-local/issues/3) remains OPEN.

**Implemented:** read-only SQLite WAL development job queue with immutable task IDs, exact phase/branch scheduling, concurrent claim fencing, priority, restart-safe checks, bounded retries, terminal blocked state and digest-only completion; `tools/dev_job_runner.py` fixed handlers for phase policy, DESIGN-IO and docs integrity; CI smoke runs three real checks and performs zero GitHub writes/model tasks. Strengthened GitHub observer/merge guard to require *effective applied PR+status check rules with trusted CI App ID* rather than only the `protected` flag. Changelog gate now counts tools/scripts/workflows.

**Verified tests:** [CI run 44216634747](https://github.com/Vertex-Systems-Network/zynoa-2-local/actions/runs/44216634747) passed 97 Python tests and nonmutating merge guard. Additional documentation commits require newest HEAD CI check before merging. New [P00 job queue runbook](../operations/P00_DURABLE_JOB_QUEUE.md) documents capabilities and limitations.

**Not completed:** no actual persistent host, unrestricted/sandboxed AI coding executor, applied main protection, live auto-merge, product UI, model inference, real screenshots or published Wiki. P00 PR #1 remains draft; P01 must NOT start before verified P00 merge. [P08I DESIGN-IO Issue #2](https://github.com/Vertex-Systems-Network/zynoa-2-local/issues/2) stays deferred.

## P00 resumed implementation slice 5 — 2026-11-18

P00 remains `IN_PROGRESS` on `phase/00-governance` / [draft PR #1](https://github.com/Vertex-Systems-Network/zynoa-2-local/pull/1). Added [declared main ruleset](../../deploy/github/main-ruleset.json) with require-PR, no bypass, no force-push/deletion, strict `governance-lint` required status pinned to authenticated GitHub Actions App ID **15368**, plus its [setup runbook](../operations/P00_MAIN_RULESET.md) and static tests. The template is NOT deployed to GitHub. Last actual live branch API observation still reports `main.protected=false` and zero effective rules. Required ruleset installation requires separate repository Administration(write) authority. No host worker deployed; no real PR merged; no P01 branch.

The continued phase implementation now contains **read-only persistent queue**, stronger policy attestation, protected-main manifest and test/docs evidence. Most recent completed CI on [run 44217456133](https://github.com/Vertex-Systems-Network/zynoa-2-local/actions/runs/44217456133) passed; check the current draft PR HEAD CI again after later commits before claiming final readiness. [Issue #3](https://github.com/Vertex-Systems-Network/zynoa-2-local/issues/3) stays open. Developer product changelog remains unreleased.

## P00 resumed implementation slice 6 — 2026-11-18

**Actual remote:** P00, branch `phase/00-governance`, existing draft [PR #1](https://github.com/Vertex-Systems-Network/zynoa-2-local/pull/1); baseline `main` `8dcb546828a8fdeef40dfaa250ac8f6b8639025d`, protected=false; Issue #3 open. No merge/P01 or installed worker.

**Implemented and tested:** Transactional SQLite task dependency DAG in `tools/dev_task_graph.py`, dependency-aware `JobQueue.claim`, cycle and cross-phase/branch checks, same-DB persistence, permanent-block propagation, corrupt/missing parent denial, and fixed read-only three-task CI smoke order despite inverse priorities. Independent safe jobs remain runnable, but **no model-backed coding or privileged automation** has been enabled. Security gates, ADR-0010, module M22 Help and Wiki source updated.

**Verified CI:** [GitHub Actions #44220171663](https://github.com/Vertex-Systems-Network/zynoa-2-local/actions/runs/44220171663) passed **117 Python tests**, documentation/changelog gate, authenticated observation, nonmutating merge dry-run and dependency-ordered read-only smoke. Later doc/record commits must get fresh HEAD CI verification. P00 remains IN_PROGRESS and draft. Full host/ruleset/sandbox/remote issue/merge delivery remain blocked [Issue #3](https://github.com/Vertex-Systems-Network/zynoa-2-local/issues/3).

## P00 continuation — worktree capability and Windows CI (2026-11-18)

**Remote truth:** Current phase `P00 / IN_PROGRESS` on `phase/00-governance` and existing [draft PR #1](https://github.com/Vertex-Systems-Network/zynoa-2-local/pull/1). Last verified main remains `8dcb546828a8fdeef40dfaa250ac8f6b8639025d` (main unprotected, zero active rulesets); no P00 PR merge or P01 branch. Existing DAG, SQLite journal, branch/CI observer and policies preserved.

**New code:** `tools/workspace_policy.py` and `tools/worktree_plan.py` with P00 scope checks, privileged file denial, Windows drive/traversal/symlink/junction/Unicode guards, and immutable full-SHA detached no-checkout Git worktree plan. No actual agent/privileged OS execution exists; real Git commands run only in disposable trusted CI fixture. Extra `workspace-windows` GitHub Actions job added.

**Tests/fixes:** [GitHub Actions #44224444145](https://github.com/Vertex-Systems-Network/zynoa-2-local/actions/runs/44224444145) on `1bb228c74f2e0518fe720ee52ad9ef39705238e0`: **138 Linux tests + 21 Windows tests passed**. Earlier Windows short 8.3 path vs canonical path test failure was repaired on same branch, no failing tests on pinned verification. Subsequently added docs require CI HEAD readback before phase exit.

**Pending:** [Issue #3](https://github.com/Vertex-Systems-Network/zynoa-2-local/issues/3) live GitHub ruleset and branch protection, persistent secured worker deployment, OS sandbox & trusted host grants, safe file changes, model-backed execution and crash-safe worktree receipts. M22 Help/Wiki *source* updated; no real GUI/screenshot/published Wiki or release. Future DESIGN-IO [Issue #2](https://github.com/Vertex-Systems-Network/zynoa-2-local/issues/2) still deferred to P08I after P08 verified merge. **P00 remains draft / not merge-ready.**

## P00 critical autonomy audit checkpoint — 2026-11-18

**Verified GitHub:** P00 `IN_PROGRESS`, existing draft PR #1 on `phase/00-governance`, `main` SHA `8dcb546828a8fdeef40dfaa250ac8f6b8639025d`, `protected=false`, zero repository rulesets, no phase merge or P01 branch. Last verified run before this audit: [CI #44224825917](https://github.com/Vertex-Systems-Network/zynoa-2-local/actions/runs/44224825917), PASS. The current audit documentation changes require a fresh HEAD CI check.

[Continuous Autonomy Audit](../operations/P00_CONTINUOUS_AUTONOMY_AUDIT.md) confirms the **root reason for repeat user prompts**: no deployed persistent model-backed coding worker. Existing `phase_worker.py` only observes; GitHub Actions tests are event-triggered and bounded; queue runs three fixed read-only validators; guarded merger is disabled/draft/protection blocked. No ChatGPT conversation can continue automatically after its current run without independently installed execution infrastructure.

**Plan and issue lifecycle corrected:** clarified P00 external developer bootstrap vs P02 product GUI/P04 Coding/P10 advanced product autonomy; no future GUI screenshots as pre-UI proof and no waiver of required actual host/security checks. [Issue #3](https://github.com/Vertex-Systems-Network/zynoa-2-local/issues/3) is the unresolved **PRE-MERGE** deployment/protection blocker, while [Issue #4](https://github.com/Vertex-Systems-Network/zynoa-2-local/issues/4) tracks **POST-MERGE** SHA/next-phase verification to remove lifecycle deadlock. Neither is closed or falsely verified. No service, sandbox or AI execution system deployed by the audit itself.

## P00 PR task table and local-model bootstrap slice — 2026-11-18

**Live repository:** `Vertex-Systems-Network/zynoa-2-local`, active phase P00 `IN_PROGRESS`, branch `phase/00-governance`, open draft [PR #1](https://github.com/Vertex-Systems-Network/zynoa-2-local/pull/1). `main` protected=false and no deployed persistent developer worker. **No P00 merge/P01 branch.**

**New user-visible result:** PR #1 description now contains the managed, versioned **P00 task table** sourced from [P00.json](pr-tasks/P00.json): **24 total, 13 DONE, 2 IN_PROGRESS, 2 TODO, 7 BLOCKED = 54% task count done**. This percentage represents scoped tasks, not release readiness; Issue #3 remains blocking. Table update executed through authorized GitHub connector and readback; automatic trusted workflow remains **NOT INSTALLED** on main until the P00 PR passes and merges.

**Code:** `tools/pr_task_board.py` validates task statuses, IDs, same-repo evidence, generates exact Markdown and offers default-disabled PR body-only write with live head, branch, base, race and remote readback checks. `tools/pr_task_trusted_sync.py` reads only bounded PR-head phase and task JSON on successful CI events, never PR script execution with write token. `scripts/check_pr_task_board.py` integrated into CI and PR template; `.github/workflows/pr-task-table-sync.yml` is a future trusted-main writer. `tools/local_model_probe.py` provides loopback-only Ollama readiness probe without inference, user data access or GitHub mutations; actual user host probe remains PENDING.

**Tests:** [GitHub Actions #44230241651](https://github.com/Vertex-Systems-Network/zynoa-2-local/actions/runs/44230241651) passed **181 Linux tests + 21 Windows tests**, PR task manifest counts and nonmutating guarded merge dry-run. Subsequent doc/change-record commits require current HEAD CI recheck. New docs [PR Task Tables](../operations/PR_TASK_TABLES.md), [ADR-0012](../adr/0012-pr-task-table-trust.md), [Local Ollama Preflight](../operations/P00_LOCAL_MODEL_PREFLIGHT.md), M22 Help/Wiki source and structured unreleased change records updated.

**Still blocking P00 release:** [Issue #3](https://github.com/Vertex-Systems-Network/zynoa-2-local/issues/3) deployed host/Ollama and safe model-coding sandbox, admin-installed protected main ruleset, separate merge/incident integration proof and full unattended safe task. [Issue #4](https://github.com/Vertex-Systems-Network/zynoa-2-local/issues/4) is post-merge only. No app UI screenshots, Wiki publication or signed product release claimed.

## P00 host bootstrap and recovery implementation — 2026-11-18

**Actual GitHub:** Active P00 `IN_PROGRESS`, one existing `phase/00-governance` branch and [draft PR #1](https://github.com/Vertex-Systems-Network/zynoa-2-local/pull/1). Remote `main` remains unprotected and 0 rulesets applied at last audit; no P00 merge or P01 branch. **No real 24/7 developer worker deployed.**

**Implementation completed for scoped T16:** `tools/host_bootstrap.py` provisions an operator-authorized P00 host data root **outside source**, initializes persistent SQLite journal/lease tables, validates path/schema/mode, creates WAL-consistent `Connection.backup()` snapshots with SHA-256 sidecar and performs a non-destructive restore drill. Existing `EventJournal`/`WorkerLease` now explicitly close SQLite connections (Windows file-lock fix). Linux observer systemd template now runs host DB preflight and points to `state/controller.db`; backup service/timer templates added. Windows least-privilege **at-logon** task preview and opt-in registration script added; does not guarantee service after user logoff. [Host operator guide](../operations/P00_HOST_BOOTSTRAP.md).

**Verified CI:** [Actions #44233203055](https://github.com/Vertex-Systems-Network/zynoa-2-local/actions/runs/44233203055) passed, including **197 Linux tests, 21 Windows workspace tests and 16 additional Windows host recovery tests** with live disposable SQLite backup/restore on Linux and Windows. Several actual Windows errors (SQLite WAL fixture, file sync, Python executable path, locked connection files) were resolved on same branch without disabling tests. Later status/changelog commits require latest HEAD CI readback.

**PR task board:** `docs/state/pr-tasks/P00.json` now has **24 total: 14 DONE, 2 IN_PROGRESS, 1 TODO, 7 BLOCKED (58% scoped tasks)**, and PR #1 body was synchronized with the same totals. T16 (installer/data package) DONE with passing fixture CI evidence; T17 (real persistent host/heartbeat) remains BLOCKED under [Issue #3](https://github.com/Vertex-Systems-Network/zynoa-2-local/issues/3).

**Remaining release blockers:** Real supervised OS host with credentials/backup retention, model-backed secure coding worker and sandbox, live GitHub issue/PR write test, protected main required status rules, and true unattended end-to-end safe PR correction/merge proof. No app GUI screenshots, published Wiki, signed update or completed module claimed. Postmerge [Issue #4](https://github.com/Vertex-Systems-Network/zynoa-2-local/issues/4) only after actual P00 merge.
