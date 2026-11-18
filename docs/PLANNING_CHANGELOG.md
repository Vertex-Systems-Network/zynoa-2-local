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
