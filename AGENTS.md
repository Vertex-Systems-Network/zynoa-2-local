# AI WORKSPACE — UNIVERSAL AGENT CONSTITUTION v3

**Applies to Codex, ChatGPT coding agents, Claude, Cursor, Gemini, Copilot and other coding models.** The controlling authority is actual repository policy, CI and tools; this file alone does not enforce sandboxing.

**Strict mode:** [docs/agent/AI_STRICT_PROTOCOL.md](docs/agent/AI_STRICT_PROTOCOL.md) is binding (source precedence, phase lock, AI decision authority, token budget). The only operational plan is `docs/MASTER_PLAN_V3_2.md`.

## First action every session (DO NOT START CODING before this)

1. Read `docs/state/PHASE.json`, `docs/state/HANDOFF.md`, then only the needed sections of `docs/MASTER_PLAN_V3_2.md`, `docs/state/STATUS.md`, ADRs and in-scope `docs/modules/Mxx.md`.
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
