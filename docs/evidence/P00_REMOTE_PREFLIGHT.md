# P00 Remote Pre-Development Audit — 2026-11-18

**Status:** PARTIAL / BLOCKED for full autonomous operation. No claim of production readiness.

## Verified repository facts

- Remote: https://github.com/Vertex-Systems-Network/zynoa-2-local
- Default branch: `main`; initial SHA: `8dcb546828a8fdeef40dfaa250ac8f6b8639025d`.
- Repo initially contained v3.2 specification kit only; no desktop source app or installed background worker verified.
- Original phase state: `P00 PLANNED_NOT_STARTED`. Branch, PR and Issues absent at start of audit.
- Created `phase/00-governance` and [draft PR #1](https://github.com/Vertex-Systems-Network/zynoa-2-local/pull/1).
- GitHub metadata at first audit reported `allow_auto_merge: false`. Never infer that a merge can happen without additional policy/config.
- No actual UI screenshots, signed release, installer, backup service or model runtimes have been tested.
- New DESIGN-IO future interoperability requirement is specified and tracked in [Issue #2](https://github.com/Vertex-Systems-Network/zynoa-2-local/issues/2), after full P08 merge as P08I.
- Deployment and merge-policy blockers tracked in [Issue #3](https://github.com/Vertex-Systems-Network/zynoa-2-local/issues/3).

## Actual P00 code slice

- `tools/phase_controller.py`: ordered P00-P08-P08I-P09-P12 transition contract, local state validation, SQLite WAL idempotent event journal.
- `tests/test_phase_controller.py`: transition denial and acceptance fixtures, restart-safe deduplication.
- `scripts/check_design_interop_policy.py`: specification-only P08I staging check integrated into existing governance CI.
- `tests/test_design_interop_policy.py`: static contract tests, not working Designer import/export.

**Security/authority note:** This slice takes normalized remote facts as input; it does NOT independently authenticate GitHub or run a persistent controller. Such evidence requires a separate trusted reader and worker, not AI-authored JSON.

## Research and alternatives backlog

- Official tool references to revalidate with pinned versions: Figma Plugin API; Penpot; open-pencil/open-pencil; ZSeven-W/openpencil. Licensing, capability matrix, private API limits and real fixtures are NOT yet independently benchmarked.
- Agent hosting candidates: persistent user-managed machine/service with SQLite lease vs managed runner with durable external state; compare security/latency/cost and record ADR before deployment.
- UI/OS baseline tests require actual Windows development/test environment and product build; current documentation-only repository cannot supply screenshots or measured FPS/inference performance.

## Current verification and evidence limits

Prior GitHub Action runs on intermediate P00 commits have reported success. Final PR HEAD CI must be checked again after every change; no PASS claim for an in-progress workflow. Test failures must be fixed on the same branch.

## Required before P00 exit

1. Authenticated repo PR/CI/merge evidence reader and guarded branch/PR operations.
2. Persistent worker/lease and restart/replay tested on a configured host.
3. Research bank with pinned verified source/license comparisons and security review.
4. Automated CI acceptance gate and reproducible logs; truthful screenshot/docs status.
5. Verified merge of PR #1 into main and durable state checkpoint. **Do not create P01 branch before this.**


## Remote continuation audit and CI evidence (2026-11-18)

- Latest repository settings checked: `allow_auto_merge=true` (changed since initial preflight); `main` GET branch metadata reported `protected=false`. GitHub branch-protection endpoint returned permission-denied 403 through connector, and repo rulesets listing returned empty. This is a known **P00 merge blocker**, not automatic permission to merge.
- [CI run 44213446505](https://github.com/Vertex-Systems-Network/zynoa-2-local/actions/runs/44213446505) on P00 SHA `48eee371a592fdef1a29961658a2bedb7026c550` passed 59 tests, syntax, static policy and **authenticated GitHub API observation** with read-only token; observed `transition_ready=false` and `branch_protected=false`.
- actions/checkout and setup-python upgraded to Node24-compatible v6; no deprecation warning in the reviewed CI log.
- Worker observer and issue router remain code deployed only in the PR, not an always-on host; trusted failure-to-Issue workflow is inactive on unmerged branch. Test results establish the Python code slice, not autonomous end-to-end development.
- Research comparison: [hosting options](../research/P00_WORKER_HOSTING_RESEARCH.md); architecture: [ADR-0009](../adr/0009-phase-observer-boundary.md); operator [runbook](../operations/P00_WORKER_RUNBOOK.md).

## P00 continuation: job queue + effective branch rules (2026-11-18)

- Source-of-truth audit: PR #1 open/draft on phase/00-governance; repository auto-merge available, but main branch unprotected and ruleset listing empty. No previous phase remote merge or P01 branch exists.
- New read-only queue: `tools/dev_job_queue.py` and `tools/dev_job_runner.py`. CI proves three built-in policy/doc checks are enqueued and completed from a temporary SQLite file; no user code or network write executed.
- SQLite concurrent claim, stale lease, idempotent retry, bounded blocked status and failed result prevention have automated regressions.
- GitHub security: observer/merge guard requires applied PR rules + required governance check pinned to expected GitHub App ID, not simply successful check title and `protected=true`; unknown rules are rejected. External official references: https://docs.github.com/en/rest/repos/rules and https://docs.github.com/en/repositories/configuring-branches-and-merges-in-your-repository/managing-rulesets .
- [CI run 44216634747](https://github.com/Vertex-Systems-Network/zynoa-2-local/actions/runs/44216634747): 97 tests passed, live merge-guard read-only smoke passed. Later HEAD commits require fresh CI; this result is a historical pinned evidence record.
- No protected branch/ruleset created, no autonomous development runtime deployed, no screenshot/GUI generated. Remaining P00 blocker Issue #3 stays open.

## Ruleset provisioning evidence addendum (2026-11-18)

Live GitHub check-runs endpoint for PR commit `50c478659e3c34050635615028c4b19af407c46e` reported `governance-lint` as successful from GitHub Actions App ID **15368**. This ID is recorded in `deploy/github/main-ruleset.json`. Static test suite checks active main match, PR requirement, no bypass, no forced history rewrite/deletion, strict pinned required status. Live main-branch metadata at last readback: `protected=false`; ruleset list empty. The manifest must be provisioned by a separate admin identity and read back before any protected merge. Documentation: [P00_MAIN_RULESET](../operations/P00_MAIN_RULESET.md). No rule write has occurred in this development turn.

## 2026-11-18 P00 continuation — transactional task DAG

Code committed in the same P00 phase branch and PR:
- `tools/dev_task_graph.py`: SQLite job prerequisite graph, atomic insertion, direct/indirect cycle checks, same-phase/branch constraint, durable readback.
- `tools/dev_job_queue.py`: dependency-aware claims (all parents must be SUCCEEDED) and transitive terminal-blocker propagation. Missing database parent rows now block instead of allowing accidental execution.
- `tools/dev_job_runner.py`: actual three-job DAG smoke, enforced `phase-policy -> design-spec -> docs-integrity` despite intentionally inverse numeric priorities.
- `tests/test_dev_task_graph.py`: correct order, cycles, batch rollback, restart, blocked ancestor, transient retry, independent work, orphan and invalid inputs.
- [ADR-0010](../adr/0010-phase-task-dag.md), [DAG architecture](../operations/P00_TASK_DEPENDENCY_GRAPH.md), M22 Help/Wiki and security/gates updated.
- Official research reference rechecked: [SQLite recursive CTE](https://www.sqlite.org/lang_with.html), [BEGIN IMMEDIATE](https://www.sqlite.org/lang_transaction.html). Single SQLite writer and possible SQLITE_BUSY require bounded contention handling and host testing.
- Verified pre-hardening test [CI #44219522536](https://github.com/Vertex-Systems-Network/zynoa-2-local/actions/runs/44219522536) passed **115 Python tests**. Later orphan-recovery and smoke changes need latest HEAD CI check. No privileged code execution, live GitHub write, host deployment or phase advancement is claimed.

**P00 remains OPEN/DRAFT, blocked on Issue #3:** main protection/ruleset not configured, permanent worker host absent and sandboxed AI worktree execution not verified. P01 remains not started.

## P00 trusted worktree / Windows-first CI evidence (2026-11-18)

**New actual source:** `tools/workspace_policy.py` (P00-only path capability validator) and `tools/worktree_plan.py` (detached no-checkout immutable-SHA Git plan; no implementation of execution broker). Tests: `tests/test_workspace_policy.py`; separate GitHub Actions `workspace-windows` job; detailed [policy](../operations/P00_WORKTREE_POLICY.md) and [ADR-0011](../adr/0011-worktree-is-not-sandbox.md).

**Verified CI:** [run #44224444145](https://github.com/Vertex-Systems-Network/zynoa-2-local/actions/runs/44224444145) at `1bb228c74f2e0518fe720ee52ad9ef39705238e0`: `governance-lint` passed **138 tests** (plus **21 explicitly repeated workspace tests**, all pass), `workspace-windows` passed **21 tests**, Git worktree fixture integration succeeded on Windows and Linux, changelog PR gate passed, merge dry-run made **zero** GitHub writes. A previous [Windows run #44224215132](https://github.com/Vertex-Systems-Network/zynoa-2-local/actions/runs/44224215132) exposed 8.3 short path vs canonical long path test mismatch, fixed in the same branch. No new real product executable or remote phase transition.

**Security constraints:** Git worktree ≠ sandbox; all Git subprocess integration runs on freshly constructed temporary trusted fixture only. Actual protected-main ruleset still not configured, no always-on host or sandboxed model worker deployed, actual M22 Help UI screenshots and Wiki publication unavailable; blocker [Issue #3](https://github.com/Vertex-Systems-Network/zynoa-2-local/issues/3) remains OPEN. Later commits require new HEAD CI check.

## P00 PR task board/host model check continuation (2026-11-18)

Evidence: Live draft PR #1 description has one versioned managed task table sourced from `docs/state/pr-tasks/P00.json`. Current manifest shows **24 tasks = 13 done, 2 in progress, 2 pending, 7 blocked**; task count percentage is 54%, not an acceptance pass. Table written via authenticated GitHub connector, not by a deployed background process. [P00 task board guide](../operations/PR_TASK_TABLES.md).

CI [run #44230241651](https://github.com/Vertex-Systems-Network/zynoa-2-local/actions/runs/44230241651) passed 181 Linux tests + 21 Windows tests after correcting two real regressions: `scripts/check_pr_task_board.py` must be invoked as a module, and status tests must compute dynamic totals rather than hardcode 50%. New trusted-main updater and workflow have data-only parsing/no PR-head execution guards; **they cannot run from the current draft phase branch until a safe merge to main**.

Local Ollama preflight source and mocked tests are implemented, but no actual user-owned development host has been probed; status `IN_PROGRESS` remains accurate. Main branch remains unprotected and no 24/7 worker has been deployed. Phase P00/PR #1 must not merge or advance to P01 until real infrastructure and security exit gates are verified.

## P00 host bootstrap and cross-platform recovery evidence — 2026-11-18

**Verified GitHub Actions [run #44233203055](https://github.com/Vertex-Systems-Network/zynoa-2-local/actions/runs/44233203055)**: `governance-lint` PASS with **197 Python tests**; `workspace-windows` PASS including **21 original Windows workspace tests plus 16 separate host bootstrap tests**. Both Linux and Windows Actions runner fixtures executed `python -m tools.host_bootstrap initialize` against runner-temporary owned directories, then `backup` and got `RESTORE_DRILL_PASSED` with SHA-256. Both fixtures reported `worker_running_verified=false`, `os_sandbox_verified=false` and `github_writes=0`. Governance PR check remains nonmutating dry-run.

**Previous failures fixed (not hidden):** Initial deterministic SQLite schema corruption assertion replaced an unreliable raw file overwrite under active WAL. Windows backup `fsync` on a read-only descriptor changed to a writable descriptor; Windows PowerShell task preview pinned a single actual Python executable. A second Windows run exposed unclosed SQLite connections in EventJournal/WorkerLease; those were closed explicitly and Windows test cleanup subsequently passed. Detailed operator guide: [P00_HOST_BOOTSTRAP](../operations/P00_HOST_BOOTSTRAP.md).

**Versioned deployable artifacts:** `tools/host_bootstrap.py`, `tests/test_host_bootstrap.py`, modified `tools/phase_controller.py` / `tools/phase_worker.py`, Linux systemd observer + backup service + timer, Windows least-privilege at-logon task preview. All service units/scripts are **not installed on a real user-owned host**. This evidence supports T16 only; not T17, no persistent model-backed coding, GitHub main branch protection or P00 merge. Later docs/change-record commits must have latest HEAD CI checked.

## P00 disposable fixture preview checkpoint (2026-11-18)

[GitHub Actions #44237855342](https://github.com/Vertex-Systems-Network/zynoa-2-local/actions/runs/44237855342) completed SUCCESS, including **233 Linux unit tests**, 21 Windows worktree/scope, 16 Windows host backup/recovery, 18 Windows model-planner and 18 Windows fixture-preview tests. Python fixture draft staging writes only under an isolated disposable `tempfile.TemporaryDirectory`, reads hashes and deletes directory; asserts model-authored Python is never executed or parsed with AST and all source/user files are unchanged. The trusted host passes independently verified `expected_task_id` and `WorkspaceScope`. No GitHub write, merge or real user-host deployment performed by CI.

An initial CI regression due to test call sites not supplying new required host task ID was fixed in same phase branch, and risk-review disabled host AST parsing for untrusted source per Python docs. Current P00 task manifest added **T25**, now 25 tasks with 15 DONE / 3 IN_PROGRESS / 7 BLOCKED (60%), PR #1 managed description synchronized; model code patch/run T20 and real OS sandbox T19 remain unfinished. Subsequent docs/changelog commits must be checked against latest HEAD CI. [Detailed plan](../operations/P00_FIXTURE_DRAFT_STAGING.md) · [ADR-0014](../adr/0014-staging-not-sandbox.md).

## P00 rootless Docker syntax broker contract checkpoint — 2026-11-18

[GitHub Actions #44241256704](https://github.com/Vertex-Systems-Network/zynoa-2-local/actions/runs/44241256704) SUCCESS on HEAD `6726438e1722eefb90fe725ca3343209d29a4d57`. Evidence: **250 Linux tests**, Windows **21 worktree + 16 host recovery + 18 model planning + 18 fixture staging + 17 rootless Docker broker policy tests = 90**. PR task schema/status verified **26 total / 16 DONE / 3 IN_PROGRESS / 7 BLOCKED / 61%**; changelog gate and GitHub guarded merge DRY-RUN PASS with **zero GitHub mutations**. Model Python is not executed by syntax broker, source/user files not changed, rootless Docker run tested through **mocked daemon** only. Earlier cgroup v2/systemd attestation tests were repaired to account for new mandatory Docker info probes without weakening required runtime restrictions.

**Not proved:** actual user-owned rootless Docker host, delegated CPU/memory/PIDs, image provenance/vulnerabilities, true network/filesystem/process isolation under adversarial inputs, persistent worker heartbeat, GitHub main branch protection or real autonomous coding loop. P00-T19/T20 remain blocked/in-progress and [Issue #3](https://github.com/Vertex-Systems-Network/zynoa-2-local/issues/3) is open. No P00 merge/P01. New commits after this evidence require remote current-HEAD CI re-verification.
