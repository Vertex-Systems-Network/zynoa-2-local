# AI WORKSPACE — UNIVERSAL AGENT CONSTITUTION v3

**Applies to Codex, ChatGPT coding agents, Claude, Cursor, Gemini, Copilot and other coding models.** The controlling authority is actual repository policy, CI and tools; this file alone does not enforce sandboxing.

## First action every session (DO NOT START CODING before this)

1. Read `docs/MASTER_PLAN_V3.md`, `docs/state/PHASE.json`, `docs/state/STATUS.md`, `docs/state/HANDOFF.md`, ADRs and in-scope `docs/modules/Mxx.md`.
2. Run/inspect `git status`, current branch and real GitHub remote `main`, current phase PR and CI. If unavailable, report `REMOTE_UNVERIFIED` and only perform safe local tasks.
3. Validate current phase lease and allowed paths; reconcile persistent worker memory, issues, baseline tests and outstanding blockers.
4. Run `docs/quality/PRE_DEVELOPMENT_CHECKLIST.md` and record time/version/source research before code edits. No blind copying.

## Engineering workflow

- One active phase, one `phase/NN-name` branch, one primary PR, multiple incremental commits; no next-phase implementation until verified remote merge.
- First foundation → professional shared GUI → fully real Chat → fully real Coding → model hardware/downloads → research/browser → memory → Figma-like editor → media → advanced agents → release.
- Run tests and fix every new error/warning. Bounded repeat loop; record blocked status; don't suppress CI to advance.
- Every completed module has exact option explanations, **real screenshots**, offline Help, GitHub Wiki mapping, error remediation and evidence. Missing images/docs means NOT DONE.
- Speed/Quality/Intelligence measured jointly; prefer stable actual improvements over untested optimizations.
- Design research must compare Figma, Penpot, **both distinct OpenPencil projects**, alternatives and legal integration options.

## Autonomous behavior

Operate within up-front configured scopes with no per-step prompt. Never demand redundant confirmations for safe authorized repo edits, tests and CI. Outside scope, deny/log and continue other safe work; never silently bypass branch protection, secrets policy, user privacy, or GitHub review settings. A chat session is not a persistent worker.

## Issues and diagnostics

Development errors, warnings and failures become deduplicated incident records and scoped GitHub issues automatically when repo access exists. End-user incidents are stored locally; remote reporting only after reporting enabled. Redact everything sensitive, no public security details, no repository token in shipped application. Link fix PR and verify deploy before resolution.

## Required output after EVERY slice

`phase_id`, `branch`, `scope`, `plan`, `source_evidence`, `files_changed`, `test_commands`, `actual_results`, `warnings`, `screenshots`, `help/wiki_links`, `issues`, `performance`, `checkpoint`, `next_safe_step`. Never claim tests, screenshots, issue creation or PR merge that did not actually occur.

## Always obey

`docs/quality/RELEASE_GATES.md`; `docs/operations/AUTONOMOUS_LOOP.md`; `docs/operations/ISSUE_AUTOMATION.md`; `docs/operations/DOCUMENTATION_HELP_WIKI.md`; `docs/operations/SAFETY_AND_PRIVACY.md`.

## Mandatory data, release and downloads rules (v3.1)

Before writing storage, chat history, model-management or updater code, read: `docs/operations/DATA_VAULT_BACKUP_RECOVERY.md`, `docs/operations/STORAGE_DOWNLOADS_RELOCATION.md`, `docs/operations/AUTO_RELEASE_AND_UPDATES.md`, and module specs `M23`, `M24`, `M25`.

- **Data first:** P01 must create an external-to-binary persistent vault. P03 cannot finish until chat/attachments recover after crashes, pass backup/restore and uninstall/reinstall tests. Do not mark messages stored before the DB transaction succeeds.
- **Every downloadable class gets a location:** user-chosen model/runtime/download and backup paths, where technically supported. Existing downloads migrate only through inventory → quiesce → stage → checksum → activate → probe → rollback. Never delete original sole copy during migration.
- **Releases are qualified, not blind:** phase merge triggers release eligibility. P11 adds signed GitHub Action publishing plus client notification/install/recovery. Stable channel never receives unfinished binaries. Updates are user-controlled and require a successful data checkpoint.
- **No deceptive guarantees:** a lone local backup cannot survive total disk failure; silent app update cannot be promised while app is closed; external files and heavyweight models are not automatically in backup; GitHub release tags are not proof of a tested working installer.
- **Docs/screenshots:** real screens+options, Help and Wiki evidence for M23–M25; backups, updates and relocation must have failure/recovery screenshots as well as happy paths.

## Mandatory changelog / change intelligence rules (v3.2)

Every AI agent (Codex/ChatGPT, Claude, Cursor, Gemini, Copilot, autonomous workers) MUST read `docs/MASTER_PLAN_V3_2.md`, `docs/operations/CHANGE_INTELLIGENCE_CHANGELOG.md`, `docs/changelog/README.md`, `docs/modules/M26.md`, and `docs/PLANNING_CHANGELOG.md` during phase preflight, alongside earlier rules.

1. On issue/warning/enhancement/request, create or reconcile an append-only event record; sanitize and deduplicate. Never claim issue fixed by issue closure alone.
2. For every meaningful feature/fix/performance/security/behavior change: create/update structured change record in the active phase PR with module/option IDs, evidence, affected docs/help/wiki and migration notes. No cross-phase or extra PR.
3. Keep **issue lifecycle**, **merged PR**, **verified implementation** and **published release** as separate facts; user-facing What's New may show only actually released changes.
4. Pre-merge docs gate: update screenshot requirements, real captures when applicable, Help and Wiki source, module dossier and option inventory. Missing docs is a failure, not a completed feature.
5. Release publisher alone derives shipped CHANGELOG.md, GitHub release notes, feed and in-app changelog from verified manifest; check version/channel/SHA parity and privacy before posting. Security disclosure follows privacy policy.
6. After each development slice output `change_ids`, `issue_status`, `release_status`, `docs_links`, `help/wiki_revision`, `screenshot_evidence`, `test_results` and `checkpoint`. A local planning changelog is NOT the released product changelog.

See `docs/quality/RELEASE_GATES.md` CHANGE-01..07 and ADR-0007. These are specifications until actual CI/desktop components exist.

## Deferred Designer interoperability / cross-tool import-export (P00 policy addition)

All agents MUST read [DESIGN-IO specification](docs/operations/DESIGN_INTEROPERABILITY.md) when researching or working on the Designer. Figma, Penpot, both distinct OpenPencil projects, and future design tools use an extensible adapter strategy. **P00–P08 may research the adapters, but MUST NOT implement external-tool conversion or promise native editable interchange.** Complete M11/M12 Designer core in P08 with real tests, screenshots, Help/Wiki and verified merge. Only after the P08 remote merge and all core acceptance gates pass may a separate **P08I** phase branch and PR implement file import/export adapters. No unsupported proprietary-format compatibility claims. See DESIGN-IO-01..10.

## P00 durable job queue and trusted merge-policy attestation (2026-11-18)

All agents must follow [P00 Durable Job Queue](docs/operations/P00_DURABLE_JOB_QUEUE.md): fixed read-only checks only until sandboxed task execution is independently approved. Phase-scoped SQLite queue jobs have immutable IDs, lease ownership tokens, recovery and bounded retries; **never place Git pushes, deployment, filesystem writes, model tool calls or arbitrary shell commands in replay-safe read-only queues**. The job runner cannot begin another phase based on a plan or self-declared success. GitHub merge-readiness must verify effective applied branch rules and required CI check **trusted GitHub App identity** as well as passed CI. A branch merely marked `protected=true` is insufficient. If rules cannot be read, phase transition and automatic merge remain blocked. P00 remains unfinished until host deployment, guarded end-to-end task executor, ruleset and full PR acceptance proof exist.

## P00 phase-scoped job dependencies (2026-11-18)

For any queued P00 task, read [P00 Task Dependency Graph](docs/operations/P00_TASK_DEPENDENCY_GRAPH.md) and ADR-0010. Dependency readiness must be enforced by the SQLite queue, not by an agent's narrative order. Use immutable job IDs and phase/branch-matched edges. The graph rejects cycles; a missing/blocked prerequisite prevents children from executing. Independent safe checks can proceed, but no model-generated code, shell commands, GitHub writes or next-phase actions are authorized by the read-only DAG. Do not claim M22 complete or start P01 without verified P00 PR merge and all documented security gates.

## P00 trusted worktree and workspace capability boundary (2026-11-18)

Read [P00 Worktree Policy](docs/operations/P00_WORKTREE_POLICY.md) and ADR-0011 before planning any code-editing task. **A Git worktree is not an OS sandbox.** P00 includes a host-controlled path permission validator and immutable detached no-checkout worktree planner; the model cannot grant file scopes to itself or change protected `AGENTS.md`, Git metadata, state, security policies or merge guards. Default allowed write proposals cover only documented safe subfolders; no actual writes are performed by the planner. No AI-generated shell, dependency install, Git checkout, model tool invocation or live repo worktree mutation is authorized until a separately deployed low-privilege OS sandbox, trusted host-issued grants and receipt/recovery tests exist. All planning must remain in P00/PR #1; no P01 until verified merge.
