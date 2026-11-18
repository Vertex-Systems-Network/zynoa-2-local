# Handoff (canonical starter)

Current task: implement P00 in actual destination GitHub repository after checking remote truth. Deliver: agent rules, phase controller, PRE-DEV, research bank, CI docs checks, issue integration design, GitHub Wiki mirror plan. Next: P01 foundation ONLY after verified P00 merge.

Blocked by: no designated repo URL or installed development worker in this document-only kit. Never claim branch/PR/issue/daemon exists. Sample local incident router is not production relay. Screenshots are future acceptance obligations, not present evidence.

## v3.1 agent handoff requirements

Read `docs/operations/DATA_VAULT_BACKUP_RECOVERY.md`, `docs/operations/STORAGE_DOWNLOADS_RELOCATION.md`, `docs/operations/AUTO_RELEASE_AND_UPDATES.md` before any changed modules. When implementing release, include proof a pre-update data snapshot is verified and after-update chat/file history unchanged. For storage relocation include before/after hash manifests and rollback trace. For backup include independently opened/restored verified archive, not just a successful backup-job event.

## v3.2 handoff

Read `docs/MASTER_PLAN_V3_2.md`, `docs/operations/CHANGE_INTELLIGENCE_CHANGELOG.md`, `docs/modules/M26.md`, `docs/PLANNING_CHANGELOG.md`, and `AGENTS.md`. Every future agent must log issues immediately, link meaningful code changes to a structured change record and update affected docs. Only release publisher may promote verified changes to user-visible released changelog. Current local state P00 planned, remote not verified.


## Actual GitHub handoff — 2026-11-18

Repo: `Vertex-Systems-Network/zynoa-2-local` · phase `P00` · branch `phase/00-governance` · primary [draft PR #1](https://github.com/Vertex-Systems-Network/zynoa-2-local/pull/1) · baseline `main` SHA `8dcb546828a8fdeef40dfaa250ac8f6b8639025d`. P00 must continue on this PR, with verified CI/security/docs/controller gates before any merge or next-phase branch. New future requirement [DESIGN-IO](../operations/DESIGN_INTEROPERABILITY.md): cross-tool editable import/export ONLY **P08I** following fully verified and merged P08 Designer core. No importer/exporter has been implemented, no product screenshots have been captured, and no persistent worker deployed. Next safe step: complete P00 controller, preflight evidence, CI and research contracts; reconcile PR and blockers.


## P00 slice 1 resume checkpoint — 2026-11-18

Continue in **existing draft PR #1** (`phase/00-governance`), not a new phase PR. Completed: DESIGN-IO specification, ADR-0008, P08I phase registry, cross-agent phase gates, static CI and regression tests; partial native Phase Controller policy + idempotent SQLite journal. Verify real current GitHub HEAD CI after any new commit; inspect [P00 preflight](../evidence/P00_REMOTE_PREFLIGHT.md). Blockers: [Issue #3](https://github.com/Vertex-Systems-Network/zynoa-2-local/issues/3) authenticated persistent worker, guarded merge policy; additional P00 research and final gates. Deferred work: [Issue #2](https://github.com/Vertex-Systems-Network/zynoa-2-local/issues/2) design file imports/exports implemented ONLY in P08I after verified P08 merge. Do not claim real UI, working import/export, automatic merge, deployed 24/7 worker or P00 finished. Next safe step: build authenticated GitHub adapter and durable worker tests in same P00 PR, reconcile CI, resolve blockers, complete research then evaluate exit gates.


## Latest P00 resume checkpoint — 2026-11-18

Remote phase is P00, active `phase/00-governance`, draft PR [#1](https://github.com/Vertex-Systems-Network/zynoa-2-local/pull/1); baseline `main` SHA `8dcb546828a8fdeef40dfaa250ac8f6b8639025d`. Added `tools/github_gateway.py`, `tools/phase_worker.py`, `tools/github_issue_bridge.py`, CI read-only live observer, trusted CI failure reporter, unit tests, operator runbook/systemd template, hosting research and ADR-0009. Last observed GitHub CI success: [44213446505](https://github.com/Vertex-Systems-Network/zynoa-2-local/actions/runs/44213446505) with 59 tests; **recheck latest PR SHA/CI**, since documentation commits continue. No external host has been deployed and CI alone is not 24/7 automation. Repository `allow_auto_merge=true` but main protection `false` at audit; must implement/verify ruleset and trusted write controller. Do not merge prematurely or create P01 until P00 actual remote merge is verified. Complete remaining [Issue #3](https://github.com/Vertex-Systems-Network/zynoa-2-local/issues/3) and full P00 gates in the SAME draft PR. Future cross-tool design import/export [Issue #2](https://github.com/Vertex-Systems-Network/zynoa-2-local/issues/2) only after P08 as P08I.


## Latest verified P00 controller checkpoint — 2026-11-18

Continue existing draft [PR #1](https://github.com/Vertex-Systems-Network/zynoa-2-local/pull/1) on `phase/00-governance`; do not create a new phase branch. Working code: `tools/github_gateway.py`, `tools/phase_worker.py`, `tools/phase_merge_guard.py`, `tools/github_issue_bridge.py`, plus pure `tools/phase_controller.py`. Includes 71 passing tests in [CI 44214670015](https://github.com/Vertex-Systems-Network/zynoa-2-local/actions/runs/44214670015) on `2a8f0f67b4846603d5d11c02cc029af1c3ab9a66`; authenticated remote observer and **nonmutating** merge dry-run passed. Important fix: worker renews lease throughout error backoff (previous 300s delay could outlive 180s TTL). All later doc/record commits need new CI check.

**Blockers:** issue #3 unprotected main/ruleset, no actual persistent host+credential provisioning/independent merge principal, no live end-to-end guarded GitHub write/reporter test, remaining model-backed task queue/worktree executor and P00 security review. Update repo ruleset via authorized admin route, not bypass, before any merge. Keep PR draft until full P00 acceptance. Issue #2 P08I interoperability is future only. Main still baseline `8dcb546828a8fdeef40dfaa250ac8f6b8639025d`, no verified P00 merge; never start P01 prematurely.

## P00 slice 4 handoff — 2026-11-18

Resume from **live GitHub** `Vertex-Systems-Network/zynoa-2-local`, active **P00**, branch `phase/00-governance`, **draft PR #1**. Main SHA remains initial `8dcb546828a8fdeef40dfaa250ac8f6b8639025d` at last audit. DO NOT create a second PR, merge unsafely or create P01 branch.

New files: `tools/dev_job_queue.py`, `tools/dev_job_runner.py`, `tests/test_dev_job_queue.py`, [P00 queue documentation](../operations/P00_DURABLE_JOB_QUEUE.md); CI smoke and stricter changelog path classification. Updated `tools/github_gateway.py`/merge guard to require effective PR+required-status rules pinned to trusted GitHub App ID, with mock tests for missing/mismatched rules. Unit tests for concurrent claims, expired/stale completion, blocked retry and no arbitrary shell. Latest confirmed [CI 44216634747](https://github.com/Vertex-Systems-Network/zynoa-2-local/actions/runs/44216634747) passed **97 tests** after code hardening. Re-fetch *current PR HEAD and its CI* after newer docs/record commits.

Pending [Issue #3](https://github.com/Vertex-Systems-Network/zynoa-2-local/issues/3): actually configure/verify GitHub main protection ruleset + trusted governance check source; install supervised worker on host with credentials/backups/heartbeat; build safe sandboxed model-backed code/worktree execution and dependency-safe task planner; verify live sanitized issue write and remote guarded merge. All blockers remain; M22 has no completed GUI/screenshots and Wiki not published. Designer import/export [Issue #2](https://github.com/Vertex-Systems-Network/zynoa-2-local/issues/2) stays future P08I after P08 verified merge.

## Next-agent handoff — P00 slice 5, 2026-11-18

Keep working on **existing** `phase/00-governance`, draft [PR #1](https://github.com/Vertex-Systems-Network/zynoa-2-local/pull/1), and do not start P01 or merge while incomplete. New queue/test files: `tools/dev_job_queue.py`, `tools/dev_job_runner.py`, `tests/test_dev_job_queue.py`; documentation [P00 Durable Job Queue](../operations/P00_DURABLE_JOB_QUEUE.md). GitHub gateway now requires effective branch PR+status-check rules pinned to trusted CI App ID, and merge guard must verify `rules_policy_verified=true`. New [main-ruleset.json](../../deploy/github/main-ruleset.json) plus [P00_MAIN_RULESET](../operations/P00_MAIN_RULESET.md) pins `governance-lint` to GitHub Actions app ID 15368 as verified from real GitHub checks; **this is a manifest, not an applied policy**. CI smoke runs safe governance queue with zero GitHub writes.

Required next work: provision active main branch protection through an authorized admin credential, verify effective rules readback; deploy/recover actual supervisor host; implement and test sandboxed autonomous model/worktree executor and issue/merge lifecycle before completing P00. [Issue #3](https://github.com/Vertex-Systems-Network/zynoa-2-local/issues/3) open. Do not misrepresent tested read-only queue as 24/7 AI developer. Re-fetch real PR SHA and CI after this checkpoint. Deferred DESIGN-IO [Issue #2](https://github.com/Vertex-Systems-Network/zynoa-2-local/issues/2) stays P08I only after verified P08 merge.

## Latest P00 checkpoint — dependency DAG (2026-11-18)

Use actual GitHub remote truth: `Vertex-Systems-Network/zynoa-2-local`, phase **P00**, branch `phase/00-governance`, only active **draft PR #1**. Main initial SHA `8dcb546828a8fdeef40dfaa250ac8f6b8639025d`; unprotected with no active rulesets; not merged. Changes in this continuation: `tools/dev_task_graph.py`, `tests/test_dev_task_graph.py`, dependency-aware SQLite `tools/dev_job_queue.py`, enforced three-stage `tools/dev_job_runner.py --smoke` DAG, [ADR-0010](../adr/0010-phase-task-dag.md) and [task DAG operator documentation](../operations/P00_TASK_DEPENDENCY_GRAPH.md). Missing/corrupt dependency cannot be counted as success. [CI #44220171663](https://github.com/Vertex-Systems-Network/zynoa-2-local/actions/runs/44220171663) passed **117 tests** and safe smoke. Revalidate PR HEAD/CI on every subsequent commit.

**Next safe work:** implement trusted sandbox/worktree policy broker and its tests, then provision actual supervised controller host with securely scoped identities and backup/recovery. Repo main protection (manifest exists but NOT applied), live issue reporting and guarded merge proof remain pending [Issue #3](https://github.com/Vertex-Systems-Network/zynoa-2-local/issues/3). No AI coding agent or UI screenshots are claimed. Designer cross-tool interoperability stays deferred to **P08I after verified P08 merge** [Issue #2](https://github.com/Vertex-Systems-Network/zynoa-2-local/issues/2). Keep PR #1 draft and do NOT start P01 before real P00 acceptance/merge.
