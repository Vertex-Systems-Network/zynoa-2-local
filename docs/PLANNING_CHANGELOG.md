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


## P00 Linux systemd remote-work watchdog (2026-11-19 — UNRELEASED, SOURCE)

- Added `tools/systemd_watchdog.py`: opt-in Linux AF_UNIX main-service `READY=1/WATCHDOG=1` with strict environment validation. `tools.phase_worker --systemd-watchdog` notifies only after authenticated GitHub remote reconciliation and owner-fenced SQLite success commit, and denies one-shot or finite worker runs.
- Changed the **uninstalled template** `deploy/systemd/zynoa-phase-observer.service` to `Type=notify`, `NotifyAccess=main`, `WatchdogSec=300`, `TimeoutStartSec=150`, bounded automatic restart; retained non-root and systemd isolation restrictions.
- Added Linux socket-level and cross-platform synthetic outage/identity/test-denial coverage; M22 Help/unpublished Wiki, ADR-0017 and operator guide. **Not a deployed service, local model inference or real sandbox.** Issue #3 and P00-T17 remain open; do not merge PR #1 or start P01.


## P00-T28 Linux systemd remote-success watchdog — exact source CI verified (2026-11-19)

A new code slice on the **same** `phase/00-governance` branch added opt-in Linux systemd `READY/WATCHDOG` datagrams exclusively after authenticated GitHub observation and committed same-owner last-success SQLite evidence, plus restricted `Type=notify`/watchdog systemd **template** and Windows/Linux tests. The initial [CI #44412517931](https://github.com/Vertex-Systems-Network/zynoa-2-local/actions/runs/44412517931) failed one security test on both OSes: it expected zero journal events after unauthenticated remote refusal, but the production worker correctly persisted one sanitized `observation_blocked` audit event. This was fixed **in the test expectation only**, retaining failure logging and zero readiness/keepalive. No security check was relaxed.

Exact source commit [`1f8d0b284826`](https://github.com/Vertex-Systems-Network/zynoa-2-local/commit/1f8d0b28482681525a8b67aa2384e40923f705f9) succeeded on authenticated GitHub Actions [#44412717005](https://github.com/Vertex-Systems-Network/zynoa-2-local/actions/runs/44412717005): Linux `governance-lint` **298 Python tests PASS**, Windows suites including **13 systemd policy tests PASS (2 Linux-only datagram tests skipped on Windows)**, CHG-PR-GATE PASS (15 change records), PR task-manifest and non-mutating guarded-merge dry-run PASS. Tests include actual AF_UNIX Linux datagrams, hostile/missing systemd environment, notification send failure, no READY on unauthenticated or failed remote observation, durable heartbeat ordering, recovery/lease release, bounded Linux unit configuration and Windows fail-closed policy.

P00-T28 DONE means only a **tested P00 service/notification source contract**; change record `CHG-P00-M22-SYSTEMD-REMOTE-WATCHDOG-20261119` remains `implementing`, unmerged and unreleased, source SHA/run stored. Canonical task board is **28 total / 18 DONE / 3 IN_PROGRESS / 0 TODO / 7 BLOCKED = 64% scoped task count**, not evidence of P00 completion. The evidence-only checkpoint commit itself needs exact-HEAD CI verification. No real service/systemd, user-owned host, live model-backed edit/test/repair, OS sandbox, protected GitHub main, privileged PR writes, published Wiki/GUI, remote merge or P01 has been verified. Issue #3 remains OPEN; PR #1 DRAFT.

Next: exact HEAD evidence CI, maintain one phase/PR, and obtain independent operator-owned host/systemd/credential/remote API/restart proof, rootless sandbox and model repair, plus admin-installed protected main before closing Issue #3 or merging. Do not start P01 before independently verified P00 remote merge SHA.


## P00-T20 one-file local model content drafting (2026-11-20 — UNRELEASED)

- Added `tools/local_fixture_drafter.py`: request **one** bounded Python `tests/fixtures` draft from a local Ollama model using exact host-approved P00-T20 plan/branch/path/digest. Reuses existing loopback schema/transport, independent validation, UTF-8 limits and disposable fixture staging; holds raw source in a hidden-repr in-memory object while returning a sanitized SHA-256-only receipt.
- Added negative cross-platform tests, CI, workspace protected authority source, ADR-0018, operator guide and M22 Help/unpublished Wiki. Model output cannot grant tool calls or cause host Python execution, checkout edits or GitHub writes.
- **Partial P00-T20 work only.** Actual Ollama inference, rootless host, full plan→edit→test→repair loop, PR updates/merge and release remain unverified; Issue #3 stays open and P00 PR #1 draft.


## P00-T20 local model fixture-content drafting — corrected source CI (2026-11-20)

**Verified source:** [`185767c82182`](https://github.com/Vertex-Systems-Network/zynoa-2-local/commit/185767c82182645267acfddb2ad8b48f3776e998), authenticated GitHub Actions [#44630397210](https://github.com/Vertex-Systems-Network/zynoa-2-local/actions/runs/44630397210) **SUCCESS**, both `governance-lint` and `workspace-windows` via trusted GitHub Actions App 15368. **315 Linux Python tests PASS**, **12 Windows `tests.test_local_fixture_drafter` PASS**, CHG-PR-GATE PASS (17 change records), versioned P00 task manifest PASS (28 tasks: 19 DONE / 3 IN_PROGRESS / 6 BLOCKED = 67%) and guarded merge DRY-RUN PASS (zero GitHub mutations).

Initial [CI #44630275074](https://github.com/Vertex-Systems-Network/zynoa-2-local/actions/runs/44630275074) FAILED on both OSes because `FixtureModelTests.run(self,**kwargs)` accidentally overrode `unittest.TestCase.run` and aborted test execution. Renamed the test helper to `generate` and updated its uses, **without weakening any production policy or skipping a test**. Corrected exact-HEAD CI now green.

New `tools/local_fixture_drafter.py` implements a structured loopback Ollama request for **one model-authored P00-T20 Python fixture** as untrusted text. Checks host-defined task/branch/path and canonical plan SHA-256, bounded JSON with duplicate-key refusal, no tools, UTF-8/Unicode and size restrictions, independent disposable fixture preview hash parity. The candidate remains in a hidden-repr in-memory container; safe receipts have only hashes and conservative false deployment/execution facts. This connects proposal-only model planning to preexisting disposable preview and separately default-disabled syntax-broker planning but **DOES NOT parse/execute generated code on the host, write checkout/source/GitHub, or attest a running Ollama**. Relevant docs: [operator guide](../operations/P00_LOCAL_FIXTURE_DRAFTING.md), [ADR-0018](../adr/0018-untrusted-local-fixture-content-boundary.md), M22 module + Help + unpublished Wiki, unreleased change `CHG-P00-M22-LOCAL-FIXTURE-CONTENT-20261120`.

**Truth boundary unchanged:** P00-T20 stays IN_PROGRESS (not model-driven plan/edit/test/repair); P00-T17 real supervisor, T19 sandbox, T21 remote writer and T23 E2E remain BLOCKED by [Issue #3](https://github.com/Vertex-Systems-Network/zynoa-2-local/issues/3). GitHub main **is now protected** with active ruleset (T18 DONE). PR #1 is still DRAFT/UNMERGED, `PHASE.json.worker_running=false`, no GUI screenshots, Wiki publication, release or P01. This evidence-only commit will need its own exact-HEAD CI result. Next external step is genuine dedicated host/model + rootless sandbox independent proof and trusted GitHub write integration; do not mark the phase complete from CI mocks.


## P00-T20 bounded local fixture syntax-repair orchestration (2026-11-20 — UNRELEASED)

- Connected existing local model fixture-content adapter and optional rootless Docker syntax-only broker through a new deny-by-default, two-attempt `tools/dev_fixture_repair_loop.py` coordinator. A syntax-invalid result allows precisely one correction from the same local model using only its previous fixture and a generic status; invalid broker receipts/errors stop rather than retry. No model-generated code executed, no real repo file edits/PR writes.
- Added Windows policy suite, Linux tests, M22 Help/unpublished Wiki, ADR-0019, operator runbook and structured developer-only change record. Live host/Ollama/rootless resource-controller verification and full autonomous edit/test/repair remain pending under Issue #3. This is not a shipped feature or increase in P00 completed tasks by itself.


## P00-T29 bounded model fixture syntax repair — source CI verified (2026-11-20)

Verified **source commit** [`e4aeb401e5cb`](https://github.com/Vertex-Systems-Network/zynoa-2-local/commit/e4aeb401e5cb24d482b2f4f78d3b88e9870cd0d7) passed authenticated GitHub Actions [#44636074965](https://github.com/Vertex-Systems-Network/zynoa-2-local/actions/runs/44636074965) exact-HEAD both `governance-lint` and `workspace-windows` SUCCESS (trusted GitHub Actions App ID 15368): **328 Python tests Linux PASS**, **13 dedicated new Windows repair coordinator tests PASS**, CHG-PR-GATE PASS (18 developer change records), PR board source validation PASS, guarded merge DRY-RUN PASS (zero GitHub mutations). This verification covers **mocked provider and Docker contracts** only; no model inference or Docker daemon was deployed by CI.

The new **P00-T29 DONE** task narrowly covers this validated **source-only two-attempt model syntax correction contract** on existing branch/PR. It connects existing local Ollama fixture draft + disposable preview + optional restricted rootless Docker syntax broker, permits a single model repair ONLY on exact syntax-invalid, and rejects forged receipts, repeated candidate SHA, transport failures, altered task/path and security grant attempts. Generated Python is not executed; the checkout and GitHub are not modified by the coordinator. Structured record `CHG-P00-M22-BOUNDED-FIXTURE-SYNTAX-REPAIR-20261120` remains **implementing/unmerged/unreleased**, with source SHA and CI URL. M22 module/help/unpublished Wiki, ADR-0019, runbook, master plan, gates and engineering changelog updated.

**Manifest now 29 total / 20 DONE / 3 IN_PROGRESS / 0 TODO / 6 BLOCKED = 68% scoped-task completion (floor).** This is **not** 68% overall product readiness or evidence that P00-T20 full autonomous model **plan → apply source edits → test → fix → PR** loop is DONE. P00-T20 remains IN_PROGRESS. T17 deployed host, T19 independently attested OS sandbox, T21 trusted GitHub write identity, T22 CI-to-Issue live delivery, T23 unattended safe E2E and T24 protected PR merge remain BLOCKED by [Issue #3](https://github.com/Vertex-Systems-Network/zynoa-2-local/issues/3). Active main remains protected by ruleset #27593065 and T18 DONE. PR #1 remains DRAFT/UNMERGED, `PHASE.json.worker_running=false`, P01 not started, no GUI screenshots, published Wiki or release. This evidence-only checkpoint commit requires exact HEAD CI verification.

**Next:** check evidence checkpoint CI; sync managed PR task board while preserving human PR sections. The next material pre-merge evidence requires a user-owned persistent host with actual local model, rootless cgroup enforcement/readback, source file-handle broker, sandboxed execution and real trusted PR write/CI-repair E2E. Do NOT claim continuous background coding from these source mocks.


## P00-T20 experimental fixed-function sandboxed test execution (2026-11-20 — UNRELEASED)

- Added `tools/docker_fixture_runtime_broker.py`: an explicit operator-opt-in, non-root rootless Docker-only fixed five-case Python `solve(x)` contract, with no repository mount, no network, nonroot process, read-only root, cgroup resource check before candidate input, isolated subprocess, bounded output/timeout, fixed verdicts and source-free SHA receipts. Unlike earlier syntax-only broker, model source *may execute in the container* on a separately authorized real Linux host; never in the privileged controller.
- Added `tools/dev_fixture_functional_repair_loop.py` to sequence local model fixture draft → isolated syntax check → isolated functional test → at most one correction after exact failures. The model receives only its previous fixture source plus fixed generic failure label; no shell/GitHub/file editing authority.
- Added Linux/Windows mock safety tests and trusted literal reference harness smoke, ADR-0020, operator guide and M22 Help/unpublished Wiki. Production rootless isolation, live model, actual code editing, GitHub write credentials and persistent worker still NOT VERIFIED. P00-T20 stays IN_PROGRESS and Issue #3 remains OPEN.


## P00-T20 functional fixture sandbox source checkpoint — verified CI (2026-11-20)

**New source:** [`0edd656b70ab`](https://github.com/Vertex-Systems-Network/zynoa-2-local/commit/0edd656b70ab8bf6db92db83437f057a7350c60a) adds `tools/docker_fixture_runtime_broker.py`, `tools/dev_fixture_functional_repair_loop.py` and two cross-platform test suites. The first [Actions #44643161979](https://github.com/Vertex-Systems-Network/zynoa-2-local/actions/runs/44643161979) FAILED two **test assertions only**, on Linux/Windows: (1) the parent-harness test falsely found `exec(compiled` in the separately quoted child script embedded in the parent's code literal; test was scoped to only the true parent *prelude*; (2) `caf` + a combining acute on `f` is actually Unicode NFC-normalized, so it was replaced with genuinely non-NFC `Cafe` + combining accent. No production security restriction or check was removed or skipped.

**Verified corrected exact source commit:** [`6e9c306beabe`](https://github.com/Vertex-Systems-Network/zynoa-2-local/commit/6e9c306beabecbaec2458a713b5ea15208a2541e), authenticated [GitHub Actions #44643332113](https://github.com/Vertex-Systems-Network/zynoa-2-local/actions/runs/44643332113) **SUCCESS**, both `governance-lint` and `workspace-windows` by GitHub Actions App 15368. **353 Linux Python tests PASS**; Windows includes new fixed-runtime broker and model functional-repair policy suites PASS. CHG-PR-GATE PASS (19 structured developer change records); P00 29-task manifest validation PASS; guarded merge DRY-RUN PASS with zero GitHub mutations. Structured `CHG-P00-M22-FIXTURE-RUNTIME-FUNCTIONAL-20261120` records source SHA+CI, remains **implementing**, unmerged/unreleased.

A trusted-host-enabled rootless Docker fixture **runtime execution path** is now source-implemented; model-generated Python is only passed by stdin to a fixed five-case `solve(x)=2*x` harness **inside** a separately secured container, never parsed/executed in the privileged controller. The implementation revalidates task/path/source SHA and current-user rootless Docker CLI/socket, rootless daemon/cgroup v2/systemd, in-container resource limits, no-network/no-repo-mount/nonroot/read-only security options; accepts only fixed sanitized outcome markers. The two-attempt functional coordinator composes local draft → independent syntax-only broker → fixed functional broker → one model correction if exact syntax/functional failure. It denies repeated candidate SHA, forged broker receipt, Docker transport failure, changed phase/path/plan and missing independent host grants. No code patch, arbitrary command, GitHub write, phase action, published app or UI was performed.

**Limitation:** GitHub Actions exercises mocked Ollama/Docker and **only a trusted literal reference** Python harness execution. No actual user-host Ollama, rootless Docker code execution or independently attested cgroup/OS sandbox is evidenced. Fixture output is `ISOLATION_UNVERIFIED` and cannot authorize privileged merges or close Issue #3. This is narrower than real model-backed plan→source-edit→unit-test→repair→PR. P00-T20 **IN_PROGRESS**, T17/T19/T21–T24 blocked; task manifest unchanged **29 total / 20 DONE / 3 IN_PROGRESS / 6 BLOCKED = 68% scoped task count**, not product completion. `PHASE.json.worker_running=false`; P00 PR #1 still DRAFT/UNMERGED; main protected by ruleset #27593065. No P01, GUI screenshots, published GitHub Wiki or release.

**Next independent acceptance:** operator-provisioned dedicated non-root Linux host with real credentials, service heartbeat/restart + actual Ollama inference; verify rootless isolation with hostile fixture failure injection; add scoped safe worktree file-handle writes, isolated real test/repair and GitHub authenticated PR/CI receipts; guarded P00 merge, independently verify merge SHA, then and only then P01. This source evidence checkpoint commit itself requires exact latest HEAD CI verification. [Operator runbook](../operations/P00_SANDBOXED_FUNCTIONAL_FIXTURE.md) · [Infrastructure Issue #3](https://github.com/Vertex-Systems-Network/zynoa-2-local/issues/3).


## P00-T20 actual fd-scoped disposable worktree fixture file creation (2026-11-20 — UNRELEASED)

- Added default-denied `tools/scoped_worktree_fixture_writer.py` that **actually creates** one new `tests/fixtures/*.py` draft in a separate host-approved immutable-HEAD Git worktree on nonroot Linux; denies ordinary checkouts, existing files, unapproved paths, symlink components, wrong ownership, Windows and stale commit/candidate hashes. No GitHub writes or user checkout changes.
- Linux CI fixture creates a real empty Git repo, real detached no-checkout worktree and a real source candidate file, then checks source isolation, no-overwrite, digest, attack denial and temp cleanup. Windows denies runtime and validates no authority without grants. ADR-0021, M22 Help/unpublished Wiki, runbook and security/release documentation updated.
- This is a narrow and auditable step toward P00-T20 full model plan/edit/test/repair, not deployed model runtime, independently attested sandbox, hosted worker, production app patch or release. Issue #3 remains a blocker, PR #1 remains DRAFT and P00 stays IN_PROGRESS.


## P00-T30 disposable Git worktree new-file writer — verified actual Linux fixture IO (2026-11-20)

**Verified source commit** [`f505cacc575d`](https://github.com/Vertex-Systems-Network/zynoa-2-local/commit/f505cacc575d300f35d94cb06e1c81f315075e64) and authenticated exact-HEAD [GitHub Actions #44646826831](https://github.com/Vertex-Systems-Network/zynoa-2-local/actions/runs/44646826831) **SUCCESS** for both trusted GitHub Actions App 15368 checks `governance-lint` and `workspace-windows`. **366 Linux Python tests PASS**, including the new `tests.test_scoped_worktree_fixture_writer` real disposable Git/FS tests; Windows ran **13 fixture writer tests with 12 Linux-only tests correctly SKIPPED, 1 default-deny test PASS**, with no unsafe Windows write fallback. Structured changelog gate PASS (20 change records), P00 task manifest check PASS at source baseline (29 tasks before acceptance checkpoint), guarded merge DRY-RUN PASS (zero GitHub mutations). No actual AI model generation or customer/developer host installed by these tests.

**Narrow P00-T30 DONE** now tracked with real GitHub CI evidence: the new operator-only Linux nonroot `tools/scoped_worktree_fixture_writer.py` can **create one new bounded model-source Python fixture** under `tests/fixtures` in a detached `git worktree add --detach --no-checkout` *disposable Git fixture worktree* with trusted full commit SHA, independent candidate SHA and explicitly granted write permission. Linux CI actually creates the trusted test Git repository and separate detached target, invokes descriptor-relative ownership-checked O_NOFOLLOW opens, fsync + no-overwrite hardlink publication, hash verification, then confirms original source checkout is untouched. Tests deny symlink escape, symlink destination, existing file, group/world writable parent, bad source hash, wrong branch/task, forged worktree .git pointer, wrong model content and missing operator grants. The broker itself does not execute model source or issue a Git/GitHub command. This is an actual **isolated fixture file write** but NOT general existing-file source edit, model patch/test/repair, an independently attested OS sandbox or production GitHub integration. The permissions/ownership model still requires an operator-owned host with exclusive UID and real lease fencing; the writer does not attempt Windows file-handle writes.

Updated task manifest now **30 total / 21 DONE / 3 IN_PROGRESS / 0 TODO / 6 BLOCKED = 70% scoped P00 subtask completion**. This percentage counts only P00 tracked subdeliverables, **not the finished AI Workspace product or autonomous developer**. `P00-T20` full plan→edit→test→repair remains IN_PROGRESS; real persistent host T17, independently attested sandbox T19, trusted nonbypass GitHub PR writer T21, verified CI-to-Issue delivery T22, full unattended E2E T23 and policy merge T24 remain BLOCKED by [Issue #3](https://github.com/Vertex-Systems-Network/zynoa-2-local/issues/3). Main is actually PROTECTED by active ruleset #27593065 (T18 DONE), PR #1 OPEN/DRAFT/UNMERGED, `PHASE.json.worker_running=false`, no P01/UI screenshots/published Wiki/release. Structured change `CHG-P00-M22-SCOPED-GIT-WORKTREE-WRITE-20261120` records source commit+passing run and remains **implementing/unmerged/unreleased**.

**Next:** verify this status/evidence checkpoint exact HEAD CI, sync authoritative PR task table without disturbing human text, and preserve the runbook + ADR-0021. Operator must then provide independently secured developer host, local-model inference, container/sandbox failure-injection, lease-fenced signed candidate authorization, actual code edit/test/repair with safe source operations and authenticated GitHub PR/issue receipts. Never merge PR #1 or transition P01 on disposable-source tests alone.


## P00-T20 exact tested-candidate → detached-worktree file binding (2026-11-20 — UNRELEASED)

- Added a separate default-denied trusted-host `tools/verified_fixture_worktree_flow.py` that holds one model Python source candidate and SHA through syntax and fixed-function test receipts before it can create that **exact candidate** as a new file under `tests/fixtures` in a detached, pinned-source Git worktree. Up to one model correction after exact failure; no write on failure, Docker error, repeated candidate, spoofed test SHA or missing grants.
- Added `tests/test_verified_fixture_worktree_flow.py` with real private Linux Git worktree/new-file IO after *mocked* Ollama/Docker checks, negative test-result→zero-file cases, mismatched digests, security denial and protected original repository. Windows runs default-deny contract only. ADR-0022, runbook, M22 Help and unpublished Wiki, master plan/agent constitution and release gates updated.
- Full autonomous app edits, genuine Ollama/Docker host attestation, source-lease/restart, GitHub write identity and protected merge are NOT verified by this source. P00-T20 remains IN_PROGRESS; Issue #3 and existing P00 release blockers remain OPEN.


## P00-T31 exact candidate SHA binding — real disposable Git IO CI verified (2026-11-20)

**Source commit:** [`1d6b14ad32ec`](https://github.com/Vertex-Systems-Network/zynoa-2-local/commit/1d6b14ad32ec381390cdacb5b5bb64e33f136602) passed authenticated [GitHub Actions #44653308893](https://github.com/Vertex-Systems-Network/zynoa-2-local/actions/runs/44653308893) **SUCCESS** on both `governance-lint` and `workspace-windows` (trusted GitHub Actions App ID 15368). **385 Linux Python tests PASS** including new `tests.test_verified_fixture_worktree_flow` full in-process *mocked Ollama/Docker* → **real** isolated Git fixture new-file test and fail-closed negatives. Windows required policy suite PASS (Linux-only actual file writes intentionally skipped). CHG-PR-GATE PASS (21 structured developer records), PR manifest validator PASS, guarded merge dry-run PASS with zero GitHub mutations. Initial [CI #44652995831](https://github.com/Vertex-Systems-Network/zynoa-2-local/actions/runs/44652995831) FAILED one incorrect preflight test setup (injected `None` syntax callback did not represent default real broker), corrected on [`1d6b14ad32ec`](https://github.com/Vertex-Systems-Network/zynoa-2-local/commit/1d6b14ad32ec381390cdacb5b5bb64e33f136602) by explicitly rejecting invalid callable injection before model inference and testing default runtime-broker identity. No security restrictions weakened.

**New narrowly scoped P00-T31 DONE:** `tools/verified_fixture_worktree_flow.py` composes local model draft, SHA-validated transient preview, optional rootless syntax-only receipt, restricted five-case functional Docker receipt and the Linux fd-scoped new-only detached Git fixture writer in one SAME in-memory model source chain. Requires a trusted P00-T20 `DRAFT_ONLY` plan, fixed source Git HEAD and worktree, and five exact independent host grants. Rejects candidate SHA drift or fake broker status, changed plan/file, repeated failure candidate and Docker errors. At most one source correction can be proposed, and only a final exact SHA-matched functional PASS can create that same source as a new file in the **CI-owned disposable detached Git worktree**. Existing files and original trusted source checkout remain untouched; no GitHub writes or model source execution on the privileged host. This confirms a real file-write-to-tested-source *policy path* in CI with synthetic model/container evidence, **NOT** actual model inference, secure rootless runtime, signed independent host sandbox attestation, general application code editing or autonomous source PR updates.

**Manifest now 31 total / 22 DONE / 3 IN_PROGRESS / 0 TODO / 6 BLOCKED = 70% P00 scoped task-count (floor rounding)**. The displayed percentage stays 70% despite one newly completed scoped task because 22/31=70.97% and task-board validation uses integer floor. This is NOT full AI Workspace product completion. P00-T20 remains IN_PROGRESS; deployed host T17, OS sandbox T19, trusted GitHub writes T21, CI-to-Issue delivery T22, unattended E2E T23, protected merge T24 still BLOCKED by [Issue #3](https://github.com/Vertex-Systems-Network/zynoa-2-local/issues/3). Main remains protected by actual ruleset #27593065; PR #1 OPEN/DRAFT/UNMERGED, `PHASE.json.worker_running=false`, no P01, GUI screenshot, Wiki publication or release. `CHG-P00-M22-TESTED-CANDIDATE-WORKTREE-BINDING-20261120` remains implementing/unmerged/unreleased with source SHA/run. This evidence-only checkpoint needs exact latest HEAD CI verification.

**Next actual infrastructure milestone:** a persistent nonroot developer host with real Ollama model, rootless Docker resource/namespace/credential isolation measured on-host (including failure injection), a lease-fenced host-owned source handle and candidate provenance, general tested source patch and bounded repair, plus a scoped authenticated GitHub PR/Issue writer and verified remote reconciliation. No additional observer wrappers or false uninterrupted-work claims.


## P00 verified failed GitHub Actions run → bot-owned sanitized issue dedup (2026-11-20 — UNRELEASED)

- Hardened `tools/github_issue_bridge.py` to GET-verify completed failed Governance v3.2 CI run ID/SHA/same-repo identity before any issue mutation, append only canonical links/commit hashes (max five), verify matching existing issue was created by `github-actions[bot]` and has canonical title/URL before a narrow PATCH, rebuild content without raw old issue body, and deny malformed/spoofed transport/credentials. Repeated same run does not mutate.
- `.github/workflows/developer-incident.yml` grants `actions:read` + `issues:write` on a *trusted default-branch only* `workflow_run` listener, forwards trusted run ID/head SHA; Governance PR tests remain read-only. Added mocked API negative suite and ADR-0023, operator guide, M26 Help/**unpublished Wiki** and policy gates.
- GitHub docs confirm `workflow_run` listener must exist on default branch. This draft PR is unmerged, so no actual automatic CI→Issue delivery can be claimed and P00-T22 remains BLOCKED. A manual live GitHub connector write (if separately performed) must not be mislabeled as CI automation. No deployed worker, app code patch or P01.


## P00-T22 failed GitHub Actions run verified Issue publisher — source CI + manual remote writeback verified (2026-11-20)

**Source implementation:** [`a9b2d7713998`](https://github.com/Vertex-Systems-Network/zynoa-2-local/commit/a9b2d771399865c0e76f3a5b8e3e65bbb50cc5d2) now hardens `tools/github_issue_bridge.py` to independently GET-read failed `Governance v3.2` workflow ID and full head SHA, require exact failure/completed/same-repo/allowed event **before** any Issues write, allow only safe developer CI P2 records, deny public P0/end-user telemetry, restrict bot-owned fingerprint/title/canonical URL issue update and max FIVE verified run/SHA links, with no raw logs/old issue text/private source. The existing privileged `.github/workflows/developer-incident.yml` gets only contents:read, actions:read and issues:write, and is a **trusted-default-branch-only** workflow_run listener; no untrusted PR checkout or generic repo/merge write. Tests use mocked GitHub HTTP, so code-level acceptance is source-only, not live Actions reporter activation.

**Verified source CI:** [GitHub Actions #44658827576](https://github.com/Vertex-Systems-Network/zynoa-2-local/actions/runs/44658827576) **SUCCESS** at exact `a9b2d771399865c0e76f3a5b8e3e65bbb50cc5d2`, both `governance-lint` and `workspace-windows` trusted Actions App ID 15368. **394 Linux Python tests PASS**, Windows new dedicated incident publisher suite **17 tests PASS**; CHG-PR-GATE 22 structured change records PASS, 31-task manifest PASS and guarded merge dry-run PASS with ZERO GitHub mutations. Source tests include independent run readback, matching SHA/status/workflow, safe create, same-run idempotency, second-run bot-owned update, capped five-link history, no raw strings, spoofed/foreign issue denial and ambiguous response refusal.

**Real remote API proof, carefully distinguished:** independently confirmed actual [failed Governance run #44652995831](https://github.com/Vertex-Systems-Network/zynoa-2-local/actions/runs/44652995831) was completed/failure with exact head commit `c8846cf24b9bd440753a3bb9435557ef4f954a0a` and same repository. The authenticated **ChatGPT GitHub connector**, not the GitHub Actions worker, created [sanitized audit Issue #5](https://github.com/Vertex-Systems-Network/zynoa-2-local/issues/5), independently read back its canonical `state=open`, source run link/SHA and creator `wpessential` (without private data or automatic bot-fingerprint marker). This is **manual live GitHub Issue API write evidence only**, NOT an actual `workflow_run` listener execution or CI GITHUB_TOKEN permissions test. The issue deliberately cannot impersonate a bot-owned deduplicated automatic Issue.

**Hard blocker still present:** `.github/workflows/developer-incident.yml` and `tools/github_issue_bridge.py` do **not** exist on current protected `main` yet. GitHub docs require the `workflow_run` listener to exist on default branch. P00 cannot merge just to enable the reporter while T17/T19/T20/T21/T23/T24 remain unresolved. Therefore **P00-T22 remains BLOCKED** pending a *real* postmerge failed-governance event → listener → bot-authored Issue write and independent remote readback. PR #1 is OPEN/DRAFT/UNMERGED; PHASE.worker_running=false; P01 NOT STARTED. Tracked P00 tasks stay **31 total / 22 DONE / 3 IN_PROGRESS / 6 BLOCKED = 70% floor**, without artificial completion inflation. Record `CHG-P00-M26-GITHUB-CI-FAILURE-ISSUE-DELIVERY-20261120` source SHA+CI is tests-passed but **implementing/unmerged/unreleased**.

**Next:** evidence checkpoint commit and exact HEAD CI, update PR and Issue #3 with truth-preserving links. Remaining product host/model/sandbox/PR write blockers unchanged. [Runbook](../operations/P00_VERIFIED_CI_ISSUE_DELIVERY.md) · [Manual proof Issue #5](https://github.com/Vertex-Systems-Network/zynoa-2-local/issues/5).
