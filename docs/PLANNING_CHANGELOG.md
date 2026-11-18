# Engineering Specification Changelog (not product releases)

## [3.2.1] - 2026-11-18
### Added
- [DESIGN-IO](operations/DESIGN_INTEROPERABILITY.md): planned tool-neutral editable import/export with format adapters, fidelity reports, security tests and help/screenshots for Figma, Penpot, OpenPencil-A, OpenPencil-B and additional supported formats.
- ADR-0008 and deferred **P08I** implementation phase. P08 Designer core must be completed, tested, documented and remotely merged before P08I is started.
### Changed
- Phase contracts, agent constitution and designer documentation now explicitly prohibit premature cross-tool compatibility claims.
### Status
- Planning and P00 governance work; no working import/export or desktop application release.

## [3.2.0] - 2026-11-18
### Added
- M26 change intelligence, issue/PR/release traceability, user-facing What's New, version history and audit timeline requirements.
- Change schema, validation/rendering proof-of-concept, regression tests, release gates and automatic Help/Wiki sync requirements.
- 8 UI screen specifications, 20 option specifications and 28 pending real-application screenshots.
### Changed
- Universal agent rules and phase PR template require structured change records and synchronized documentation.
- Integration plan includes event persistence from P01, professional UI from P02 and release publication in P11.

## [3.1.0] - 2026-11-18
### Added
- Planned User Data Vault/backups (M23), Storage Relocation (M24) and Update Center (M25), with release publisher and recovery gates.

**These are changes to the specification package, not evidence that any desktop application feature is implemented.**


## P00 governance implementation log — 2026-11-18 (UNRELEASED)

- Added authenticated, repository-scoped read-only GitHub PR/CI/branch/issue observation and conservative phase-readiness policy.
- Added SQLite single-owner renewable lease, durable event journal and resumable bounded observation loop; no privileged actions or remote merges.
- Added sanitized developer-ci GitHub Issue bridge, explicit publishing guard and trusted default-branch workflow that activates only after its merge to main.
- Added operator runbook, service template, hosting alternatives ADR-0009 and checkpointed handoff; CI upgraded to Node24-compatible v6 actions and live authenticated observation.
- GitHub CI passing evidence recorded in P00_REMOTE_PREFLIGHT.md; change record `CHG-P00-M22-PHASE-OBSERVER-20261118` status IMPLEMENTING.
- This log records engineering development only. No application release or public changelog entry exists; M22 still partial, P00 draft PR remains open with host/ruleset blockers.


## P00 governance continuation — 2026-11-18 (UNRELEASED)

- Added default-disabled guarded GitHub PR merge library/CLI with remote-check authentication, PR head/base SHA fencing, protected branch enforcement and readback verification.
- Added authenticated read-only CI merge dry-run that asserts zero GitHub mutations, plus GitHub writer refusal/success unit tests.
- Fixed long retry backoff lease expiration and added virtual-clock regression test.
- [CI 44214670015](https://github.com/Vertex-Systems-Network/zynoa-2-local/actions/runs/44214670015) passed **71** tests and read-only merge dry-run. P00 remains draft/partial with unprotected main and no host deployment; nothing is shipped in product changelog.

## P00 autonomous controller queue and rules hardening — 2026-11-18 (UNRELEASED)

- Added `tools/dev_job_queue.py`, a SQLite WAL phase-scoped, owner-token-fenced, crash-recoverable job queue for **read-only** governance checks; added fixed allowlisted `tools/dev_job_runner.py` and CI smoke.
- Added concurrency, idempotency, retry/failure, stale lease and false-success prevention regression tests.
- Strengthened GitHub remote evidence and guarded merge to require effective applied PR/status rules pinned to a trusted CI App ID; name-only green checks and hollow branch protection cannot authorize a merge.
- Expanded the changelog PR gate to include `tools/`, `scripts/` and workflow changes, with existing developer change record retained.
- Added detailed queue documentation, threat model, AI agent rules, M22 Help/Wiki source and release/predevelopment quality gates.
- [CI #44216634747](https://github.com/Vertex-Systems-Network/zynoa-2-local/actions/runs/44216634747) passed 97 tests. This is backend governance development, not a released AI desktop feature; host deployment/protected main/AI sandbox remain blocking.

## P00 protected-main policy manifest — 2026-11-18 (UNRELEASED)

- Added declarative `deploy/github/main-ruleset.json` for main branch requiring PR, no bypass, protected history and trusted required `governance-lint` GitHub Actions check (App ID 15368 verified on actual P00 CI).
- Added static manifest contract tests and operator instructions for authorized GitHub repository admin to apply and independently validate effective rules.
- **Not applied** to GitHub; remote `main` remains unprotected and Phase P00 cannot merge or advance. Neither this manifest nor passing unit tests is a release.

## P00 phase-scoped dependency DAG — 2026-11-18 (UNRELEASED)

- Added transactional `tools/dev_task_graph.py` prerequisite graph for replay-safe development jobs, with same-phase/branch edges and SQLite recursive cycle prevention.
- Enforced DAG dependencies in durable queue claims, terminal failure propagation, and explicit BLOCKED status for orphan/corrupt parent records; independent jobs can proceed safely.
- Updated governance smoke to execute actual `phase-policy → design-spec → docs-integrity` jobs despite inverted priority order; still zero GitHub writes/model tasks.
- Added direct/indirect cycle, atomic batch rollback, wrong phase, crash persistence, retry/cascade/orphan and malformed input tests, plus ADR-0010, security gates, module Help/Wiki source and design notes.
- [CI #44220171663](https://github.com/Vertex-Systems-Network/zynoa-2-local/actions/runs/44220171663) passed **117 tests**. P00 remains a draft backend-only development PR; no user-facing release or published Wiki/screenshot evidence.

## P00 trusted worktree scope and cross-platform tests — 2026-11-18 (UNRELEASED)

- Added `tools/workspace_policy.py`: narrow P00/phase-bound file access policy for future host-controlled agent operations, with traversal/UNC/drive/link/junction/Git metadata/secret/Unicode control denial, protected phase/CI/credential paths and privacy-safe decisions.
- Added `tools/worktree_plan.py`: deterministic, SHA-pinned detached `git worktree add --no-checkout` plan for trusted existing repo + separate root/hooks directory; module **does not execute** it or grant a sandbox.
- Added `tests/test_workspace_policy.py`: real Git worktree integration on a **synthetic disposable trusted repository** and hostile path/scoping fixtures.
- Added `workspace-windows` GitHub Actions job for Windows-first path and Git fixture verification, alongside Linux governance tests. Fixed Windows short-path / long-path test assertion using canonical paths after failing early Windows CI.
- Added [ADR-0011](adr/0011-worktree-is-not-sandbox.md), [worktree policy guide](operations/P00_WORKTREE_POLICY.md), additional M22 Help/Wiki source and threat/release/predevelopment rules.
- [CI #44224444145](https://github.com/Vertex-Systems-Network/zynoa-2-local/actions/runs/44224444145) passed 138 Linux tests plus 21 Windows tests. This change is **not released**; a production OS sandbox, user worktrees, deployed model worker and P00 merge remain pending.

## P00 continuous-autonomy plan audit and lifecycle correction — 2026-11-18 (UNRELEASED)

- Audited why repeated chat prompts were needed: chat runs are bounded; there is no deployed persistent AI coder; PR CI only validates and ends; the existing queue and GitHub observer cannot implement, test-fix, merge and advance phases autonomously.
- Recorded the exact problems and staged remedy in [P00 Continuous Autonomy Audit](operations/P00_CONTINUOUS_AUTONOMY_AUDIT.md).
- Clarified P00 **developer bootstrap** versus later P02 graphical UI, P04 product Coding Studio and P10 advanced in-product autonomy, preserving all quality/security requirements at their appropriate phases.
- Split pre-merge infrastructure blocker [Issue #3](https://github.com/Vertex-Systems-Network/zynoa-2-local/issues/3) from [post-merge SHA/phase checkpoint Issue #4](https://github.com/Vertex-Systems-Network/zynoa-2-local/issues/4) to prevent circular issue/merge gating. True unresolved blockers still forbid merge.
- No product release or autonomous host was delivered by this documentation/policy update. Current PR #1 remains OPEN DRAFT.

## P00 per-PR task tracking and local Ollama readiness — 2026-11-18 (UNRELEASED)

- Created `docs/state/pr-tasks/P00.json` with 24 evidence-backed, stable P00 task IDs, DONE/IN_PROGRESS/TODO/BLOCKED statuses; PR #1 GitHub description now contains a generated table showing totals, status, evidence links and derived 54% task count completion (P00 remains blocked).
- Implemented `tools/pr_task_board.py` to validate and render managed PR table, reject unsafe Markdown/external references and support separately authorized body-only sync with race/head/readback checking; default is read-only.
- Implemented `tools/pr_task_trusted_sync.py` with JSON-only PR-head inspection, exact CI event/PR/phase/SHA checks and future trusted-main `workflow_run` GitHub Action; the workflow is NOT active while P00 is unmerged.
- Added `scripts/check_pr_task_board.py` to governance CI and changed PR template/agent/plan to require the table for EVERY subsequent phase PR; tests use dynamically derived counts, not brittle hardcoded values.
- Added `tools/local_model_probe.py` with loopback-only Ollama version/model-list discovery, no proxies/inference, unsafe model ID rejection and negative unit tests; actual development host not inspected.
- Added detailed [PR Task Tables](operations/PR_TASK_TABLES.md), [ADR-0012](adr/0012-pr-task-table-trust.md), [Local Model Preflight](operations/P00_LOCAL_MODEL_PREFLIGHT.md), M22 Help/Wiki source and 2 distinct unreleased change records.
- A transient CI failure caused by importing a script as a file was fixed by module invocation; a later failure caused by hardcoded 50% test assertions was fixed to compute counts dynamically. [CI #44230241651](https://github.com/Vertex-Systems-Network/zynoa-2-local/actions/runs/44230241651) passed **181 Linux + 21 Windows tests** and all task manifest checks.
- **NOT RELEASED:** No persistent AI developer host, protected GitHub main, deployed trusted workflow, model-backed code executor, sandbox, GUI, screenshot or public product changelog is claimed.

## P00 host bootstrap, SQLite WAL recovery and Windows file-handle repair — 2026-11-18 (UNRELEASED)

- Added `tools/host_bootstrap.py` for explicit host data-root initialization **outside source**, private metadata/database initialization, SQLite online backup with checksum sidecar, integrity checks and disposable restore drill without overwriting live journal.
- Added `tests/test_host_bootstrap.py` covering real WAL event snapshot vs current journal, corruption/missing receipt/missing schema, unapproved initialization, symlink/junction, overlapping paths, idempotent preservation and POSIX permission checks.
- Repaired existing controller `EventJournal` and worker `WorkerLease` to CLOSE SQLite connections explicitly. Windows test teardown had previously failed with file-lock errors after transaction context managers, which committed but did not close connections.
- Extended Linux systemd observer template with host DB preflight and moved observer DB to `/var/lib/zynoa/state/controller.db`; added systemd daily online backup service and timer templates.
- Added Windows current-user least-privilege **at-logon** task script, preview default and explicit `-Install`; cannot guarantee 24/7 runtime after logoff. Resolved PowerShell multiple-Python-path selection and Windows backup file-descriptor sync failures found by actual CI.
- [CI #44233203055](https://github.com/Vertex-Systems-Network/zynoa-2-local/actions/runs/44233203055) passed **197 Linux + 21 Windows workspace + 16 Windows host** tests and real disposable SQLite backups/restores on both OS runners.
- Updated Help/Wiki *source*, security/release/pre-development checks, host operator guide and structured unreleased developer change record. **No product release, actual service installation, model/host inference, GUI screenshot or published Wiki** is claimed.
- PR #1 task table now **24 total / 14 done / 2 in progress / 1 pending / 7 blocked = 58% scoped completion**. External deployment T17 and [Issue #3](https://github.com/Vertex-Systems-Network/zynoa-2-local/issues/3) remain unresolved and block merge.

## P00 strict local Ollama proposal-only gateway — 2026-11-18 (UNRELEASED)

- Added `tools/dev_model_planner.py`: bounded localhost-only Ollama `/api/chat` JSON schema request, exact P00 task/branch validation, no proxies/redirects and no model tool calls. Independently revalidates generated proposals against host-controlled `WorkspaceScope`; allows only `DRAFT_ONLY` paths and fixed read-only checks.
- Added `tests/test_dev_model_planner.py` and Windows CI step; mocked success/error cases, untrusted model formats/IDs, prompt control/Unicode/bidi spoofing, protected repo governance, symlink escapes and no mutation claims.
- Expanded `tools/workspace_policy.py` authority protection to cover model adapter, local probe, host bootstrap, PR task renderer and trusted PR sync source. Added [P00 local model planning contract](operations/P00_LOCAL_MODEL_PLANNING.md) and [ADR-0013](adr/0013-model-plans-not-execution.md), revised M22 Help/Wiki source and threat/acceptance gates.
- The first CI failure came from a deliberately unsafe test fixture containing literal escaped text rather than an actual NUL; corrected the fixture and verified clean CI. This did not weaken model input policy.
- Updated PR #1 managed task table: 24 total / 14 Done / 3 In progress / 0 Pending / 7 Blocked = 58%. T20 now IN_PROGRESS because only planning was built, not full autonomous coding.
- **Not released/deployed:** No real local coding model inference, OS sandbox, safe patch/test/repair worker, persistent host or protected main has been verified. Entire P00 remains DRAFT and in progress, no P01.

## P00 ephemeral AI fixture draft staging and 25-task progress — 2026-11-18 (UNRELEASED)

- Created `tools/fixture_draft_stager.py` to turn validated `DRAFT_ONLY` model file proposals plus separately trusted host task ID into bounded disposable fixture previews, SHA-256 receipts and cleanup. It writes only to a new temporary OS directory, never source/user files or GitHub.
- Added `tests/test_fixture_draft_stager.py` with real temporary-file lifecycle, deterministic digests, mismatched host task ID, path/control/Unicode size/format denial, malformed JSON, preserved actual fixture contents and no subprocess/code execution; included dedicated Windows CI tests.
- Security correction: requiring an independent host task ID initially caused fixture tests to fail due to stale test call sites; updated test invocations, retained the strict authority gate and reverified.
- Further risk review from official Python docs resulted in **removing host-side `ast.parse` for untrusted Python** because complex inputs can exhaust parser resources; Python staging is now text-only, with actual syntax/runtime work deferred to a real OS sandbox.
- [CI #44237855342](https://github.com/Vertex-Systems-Network/zynoa-2-local/actions/runs/44237855342) passed **233 Linux tests + 73 Windows tests**, including no-GitHub-write merge dry-run, after bounded fixes.
- Added [P00 staging operator contract](operations/P00_FIXTURE_DRAFT_STAGING.md), [ADR-0014](adr/0014-staging-not-sandbox.md), M22 Help/Wiki *source*, security/release/pre-development rules and unreleased structured change record.
- Added P00-T25 as an honest newly discovered **scoped** verified task in the same PR; task manifest/PR body now **25 total, 15 DONE, 3 IN_PROGRESS, 7 BLOCKED (60%)**. Full OS sandbox T19 and plan/edit/test/fix T20 are still unverified. No persistent host, app, product release or published Wiki claimed.

## P00 T25 task table regression fixed — 2026-11-18 (UNRELEASED)

- Appending new verified `P00-T25` changed task manifest order. Existing `tests/test_pr_task_board.py` assumed `m["tasks"][-1]` was always BLOCKED, causing genuine GitHub Actions failure even though P00-T24 remained blocked.
- Corrected assertion to locate stable `P00-T24` by ID; did not alter task status, skip a test or disable CI. [Exact success run #44238887078](https://github.com/Vertex-Systems-Network/zynoa-2-local/actions/runs/44238887078) passed **233 Linux and 73 Windows** tests, 25-task validation, changelog gate and no-write merge guard.
- P00-T25 remains DONE (ephemeral fixture preview only); external OS sandbox and actual unattended coding remain UNRELEASED/BLOCKED under [Issue #3](https://github.com/Vertex-Systems-Network/zynoa-2-local/issues/3).

## P00 default-disabled rootless Docker syntax gate — 2026-11-18 (UNRELEASED)

- Added `tools/docker_syntax_broker.py` and `tests/test_docker_syntax_broker.py`: trusted P00 task/scope + Python fixture-only syntax check plan; optional strict rootless Docker CLI invocation using official Python image pinned by digest, pre-cache-only policy, no network, no mounts, read-only filesystem, unprivileged UID, dropped capabilities and bounded CPU/memory/PIDs. Candidate is compiled only, never executed.
- Host opt-in disabled by default; rootful/remote Docker sockets refused. Independent Docker CLI/rootless daemon/cgroup-v2/systemd attestation is mandatory before any invocation. Docker docs warn otherwise resource flags can be silently ignored; actual host controller delegation remains a separate release blocker.
- Added separate Windows mock Docker contract tests; protected broker authority source against AI-written proposals; defined fixed success/invalid markers, bounded output, exact container-name timeout cleanup and sanitized/no-GitHub-write receipts.
- CI initially failed after new cgroup attestation because mock runner returned the old security options for the additional `info` calls; repaired tests to verify cgroup version and driver rather than weakening the security requirement. [CI #44241256704](https://github.com/Vertex-Systems-Network/zynoa-2-local/actions/runs/44241256704) passed **250 Linux + 90 Windows tests**, 26-task validation and change records.
- Added [broker documentation](operations/P00_DOCKER_SYNTAX_BROKER.md), [ADR-0015](adr/0015-rootless-syntax-gate.md), security/release/predevelopment rules, M22 Help/Wiki SOURCE and new unreleased change record. **No live Docker host, real OS sandbox attestation, AI code execution, autonomous patch/test/repair or user-facing release has happened.**
- Added **P00-T26 DONE** strictly for broker contract source + mocked cross-platform tests. Existing T19 OS sandbox BLOCKED and T20 autonomous coding loop IN_PROGRESS. P00 PR #1 task table **26 total / 16 done / 3 in progress / 7 blocked = 61%**, P00 NOT merge-ready.


## P00 owner-fenced observer success heartbeat — 2026-11-19 (UNRELEASED)

- Added additive SQLite `worker_observation_health` separate from worker lease and deduplicated journal, plus `tools.worker_health` local read-only last-success freshness/ownership probe, tests, M22 source Help/Wiki/ADR and explicit T27 scope. A refreshed lease during GitHub failure no longer counts as a recent successful observation.
- CI #44405053946 detected real Linux/Windows mistakes: WAL-mode SQLite read-only readers may create sidecars, and test DB context managers did not close Windows handles. Corrected with SQLite connection `closing()` and no-application-record-mutation assertions; did not suppress tests or use unsafe `immutable=1` for live WAL.
- [Exact source CI #44405471351](https://github.com/Vertex-Systems-Network/zynoa-2-local/actions/runs/44405471351) passed **285 Linux tests**, all Windows suites including **10 new heartbeat tests**, change-record gate and no-GitHub-write merge dry-run. P00-T27 DONE means only code/fixture contract: **no actual host deployment or continuous worker service observed**.
- The same draft PR #1 continues; P00 host/protected-merge blockers Issue #3 remain open. No product app, released UI, screenshots, actual Wiki publication or P01 phase is claimed.
