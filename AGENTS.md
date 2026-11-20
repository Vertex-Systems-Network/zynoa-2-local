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

## Continuous-autonomy audit / no prompt-only background claims (2026-11-18)

Before attempting another P00 "continue" slice, read [P00 Continuous-Autonomy Audit](docs/operations/P00_CONTINUOUS_AUTONOMY_AUDIT.md). Distinguish ChatGPT's bounded user-initiated run from a **real deployed developer host**. The existing observer, SQLite queue and GitHub Actions tests do not themselves implement continuous model-driven development. Prioritize safe host provisioning, OS sandbox, model-backed developer execution, real PR update/CI repair and protected-merge lifecycle over writing additional observer-only wrappers. Do not promise a non-stop background process unless heartbeat and live deployment are independently verified.

Use clear pre-merge vs post-merge gates: close Issue #3 only after all its *actual pre-merge* infrastructure and security requirements pass; the resulting merge SHA is verified **after** the permitted merge before starting P01. Do not relax the protected-main, CI, permissions or phase gate to claim progress. M22 desktop GUI/screenshots are future actual-UI obligations, not evidence that P00 headless bootstrap is complete.

## Mandatory task table on every phase PR (2026-11-18)

Before creating or continuing a phase PR, read [PR Task Tables](docs/operations/PR_TASK_TABLES.md). Each primary PR MUST have a versioned `docs/state/pr-tasks/<PHASE>.json` listing **all known tasks**, stable IDs, literal `DONE / IN_PROGRESS / TODO / BLOCKED` statuses, relevant evidence/blocker URLs and an auto-calculated total/progress. The PR description MUST include one managed table between `<!-- ZYNOA_PR_TASK_BOARD_START v1 -->` and `<!-- ZYNOA_PR_TASK_BOARD_END -->`. Update task status on the **same phase branch** with source/tests/help/wiki/changelog as progress occurs; newly discovered tasks require new IDs and total recalculation. A test passing does NOT by itself mark a broad task or entire phase DONE.

Run `python -m scripts.check_pr_task_board` and `python -m tools.pr_task_board --manifest docs/state/pr-tasks/<PHASE>.json --validate`. The task board only writes PR body when an independently trusted, explicitly authorized updater is operational; never grant `pull-requests:write` to untrusted PR code. The default-branch workflow is not operational before its merge. Preserve all human-written PR sections and never fabricate a sync. PR task table must be truthful and current before merge; post-merge SHA verification and next-phase sequencing remain mandatory.

## P00 host bootstrap and recovery proof (2026-11-18)

Before touching the external developer host, read [P00 Host Bootstrap](docs/operations/P00_HOST_BOOTSTRAP.md) and module M22. The `tools.host_bootstrap` utility initializes a **separate, operator-owned** data root (only with explicit provision authorization), validates P00/PR/branch, runs a consistent SQLite online backup and **disposable restore drill**; it never restores over the live DB, runs Ollama, installs a service or merges GitHub PRs. The older `EventJournal` and `WorkerLease` connections now close explicitly to prevent Windows locked-file failures.

Linux systemd observer + backup timer and Windows *at-logon current-user* task are templates; a Windows logon task is NOT a 24/7 service. Do not set `PHASE.json.worker_running=true` or task P00-T17 DONE from CI fixture deployment. First independently prove a persistent operator-hosted supervisor, secure credentials, real remote heartbeat/restart, and OS sandbox before enabling model-written code. P00-T16 may be accepted as **tested installer/host data package**, separately from the unfulfilled actual deployment gate.

## P00 local model proposal contract — no inherited execution rights (2026-11-18)

Before any local AI planning experiment, read [P00 Local Model Planning](docs/operations/P00_LOCAL_MODEL_PLANNING.md). `tools.dev_model_planner` accepts a host-defined `WorkspaceScope`, short non-sensitive P00 task brief and a local model ID. It uses explicit loopback Ollama `POST /api/chat` with schema-constrained structured output, and independently validates each proposed `DRAFT_ONLY` file path against trusted scope. The model receives **no shell, file write, GitHub, merge, download or network tool**. This is a proposal-only subcomponent; P00-T20 remains unfinished until OS-brokered edits, bounded tests/repair and remote receipts actually work.

Do not transmit secrets, source documents, chats, private paths or user data to the local planner in an unreviewed task brief. A prompt/schema is not a sandbox or authorization; real code changes must run through future host-scoped OS execution. The protected files list includes `tools/dev_model_planner.py`, `tools/local_model_probe.py`, `tools/host_bootstrap.py`, `tools/pr_task_board.py` and `tools/pr_task_trusted_sync.py`. Preserve existing P00 branch, draft PR and release gates.

## P00 ephemeral model fixture staging — no sandbox claims (2026-11-18)

The [fixture staging contract](docs/operations/P00_FIXTURE_DRAFT_STAGING.md) adds `tools.fixture_draft_stager.preview_fixture_drafts` for small, **disposable** `tests/fixtures` model draft previews. The trusted host supplies a separate `expected_task_id` and `WorkspaceScope`; the model cannot self-authorize its own task. Candidates are strictly bounded, temporarily written only under a newly generated OS-owned directory, hashed, and deleted; ZERO user/repo files are changed, ZERO model code or shell commands executed, ZERO GitHub writes. Proposed Python is **never parsed/compiled** in the privileged host due to AST resource-exhaustion risk; real syntax and runtime tests require a separate OS sandbox and host broker. This stage is NOT the sandbox, daemon, patcher or autonomous coding loop. Full P00-T19 and P00-T20 remain incomplete and Issue #3 still blocks merge. P00-T25 records only the verified fixture-preview subtask; preserve its evidence in the current PR table.

## Rootless Docker syntax-only execution (2026-11-18)

Read [P00 Docker Syntax Broker](docs/operations/P00_DOCKER_SYNTAX_BROKER.md) and [ADR-0015](docs/adr/0015-rootless-syntax-gate.md) before attempting any container-based model check. `tools/docker_syntax_broker.py` accepts only host-bound P00 `WorkspaceScope` + separately expected task ID + one small `tests/fixtures/*.py` draft, then optionally performs **syntax compilation only** inside pre-cached digest-pinned rootless Docker. It **does not execute the model's program**, modify the project, run arbitrary shell, update GitHub, or automatically start a worker.

The runtime is disabled without explicit trusted host authorization; requires a current-user-owned rootless Unix Docker socket, valid Docker CLI, confirmed rootless status, cgroup v2 and systemd driver, and fixed network-none/read-only/no-mount/caps-dropped/limited-resource container flags. Only known success/invalid status markers are accepted. Docker's reported resource settings are not proof of actual CPU-controller delegation: real host attestation and failure-injection are mandatory before P00-T19 or P00-T20 can complete. Model-suggested Docker commands/image/host paths are never allowed. Windows native Docker syntax execution is not enabled. This code is **not** a deployed or independently attested OS sandbox.


## P00 fixed-function container evaluation boundary (2026-11-20)

Before invoking `tools/docker_fixture_runtime_broker.py` or `tools/dev_fixture_functional_repair_loop.py`, read [P00 functional fixture operations](docs/operations/P00_SANDBOXED_FUNCTIONAL_FIXTURE.md) and ADR-0020. This is a separately operator-gated, Linux rootless-Docker-only **fixed five-case Python fixture** experiment. Only the container may execute generated Python; host controller never does. Model cannot choose test commands, Docker argv, local token, repo mounts, file writes or GitHub lifecycle actions. A pass from CI mock Docker or a container still marked `ISOLATION_UNVERIFIED` is NOT actual safe sandbox attestation or authority to push/merge. Actual non-root host/service, resource containment failure injection, scoped repository patch/test/fix, secure GitHub write identity and independent merge SHA remain required before P00 ends or P01 begins.


## P00 detached worktree fd-scoped fixture writer — actual disposable file writes (2026-11-20)

`tools/scoped_worktree_fixture_writer.py` now has a deliberately restricted **Linux nonroot, host-authorized new-file writer**. Before using it read [operator contract](docs/operations/P00_SCOPED_WORKTREE_WRITER.md) and [ADR-0021](docs/adr/0021-no-replace-fd-scoped-disposable-writes.md). It requires an existing separate **detached no-checkout** Git worktree at a trusted source SHA, independently host-issued P00 task ID and exact candidate SHA-256, three independent opt-ins, and only one `tests/fixtures/*.py` new file. It opens owned directories with dir_fd/O_NOFOLLOW, fsyncs a temporary inode, hardlinks to a NEW destination without replacing prior files, and rereads hash. No host model source execution, no normal repo checkout edits, no GitHub writes, no untrusted commands, no Windows fallback; same-UID/host privilege isolation, leases and true model test attestations remain external. **NEVER feed source checkout, user files or model-generated grant/path/candidate authorization directly into this API.** P00-T20 stays IN_PROGRESS until real host-backed model plan→edit→test→repair and protected remote PR evidence.
