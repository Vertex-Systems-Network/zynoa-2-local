# AI Workspace 3.2 — Consolidated Master Plan

**Current spec revision:** 3.2.0 • 2026-11-18. **Status:** Documentation/agent-governance kit only; no actual desktop app/release/PR has been built by this artifact.

Current inventory: **26 module dossiers, 151 UI screens, 244 option specifications, 395 pending real-application screenshot obligations**. Older v3.0/v3.1 inventory counts inside the historical preserved text are superseded by these figures.

This file consolidates the retained full v3.1 master plan and the new M26 extension. Read the referenced detailed dossier and operation files for executable contracts.

[Current module index](modules/README.md) · [Phase Delivery](PHASE_SPECS.md) · [Change Intelligence](operations/CHANGE_INTELLIGENCE_CHANGELOG.md) · [Engineering Specification Changes](PLANNING_CHANGELOG.md) · [Product CHANGELOG](../CHANGELOG.md) · [AI Agent Rules](../AGENTS.md)

---

# AI Workspace 3.1 — Integrated Master Plan (v3 complete + release / backup / storage extension)

**Version:** 3.1.0 | **As of:** 2026-11-18 | **Artifact:** specification, governance and workflows only; app / remote worker / GitHub PR / published release not implemented.

# AI Workspace 3.0 — Autonomous Production Engineering Encyclopedia

**Spec version:** 3.0.0 • **Date:** 2026-11-18 • **Status:** Planning/specification only; no application or remote worker implied  
**Owner:** Project engineering team • **North star:** Speed × Quality × Intelligence × Trusted Autonomy × Professional UX  
**Canonical index:** [Module Specs](modules/README.md) · [Design Research](research/DESIGN_RESEARCH.md) · [UI Options](ui/OPTION_CATALOG.csv) · [Screens](ui/SCREEN_INVENTORY.csv) · [Help](help/README.md) · [Wiki](wiki/README.md) · [Quality](quality/PRE_DEVELOPMENT_CHECKLIST.md) · [Incidents](operations/ISSUE_AUTOMATION.md)

**Roadmap:**

| Phase | Name | Modules | Exit criterion |
|---|---|---|---|
| P00 | Governance, product research and AI controller | M22 | Constitution, PR policy, verified source bank, local controller contract and test harness |
| P01 | Desktop foundation and secure services | M01 M16 M17 M18 | Bootable client, IPC and storage, native security, diagnostic spine |
| P02 | Final shared UI and help foundation | M02 M19 | Polished shell/design system, all shared UI states, help framework and visual gate |
| P03 | Complete Chat module | M03 | Real local model inference, attachments, history, errors and streaming |
| P04 | Complete Coding module | M04 | Repository edit/test/verify workflow and scoped git operations |
| P05 | Intelligent model, hardware and download suite | M05 M06 | Benchmarked routing and verified resumable model management |
| P06 | Search + Research + Browser | M07 M08 M09 | Web research with citations, guarded browsing and verifiable evidence |
| P07 | Advanced knowledge and memory | M10 | Indexing, retrieval, context management, revalidation and recovery |
| P08 | Figma-like Design Studio and assets | M11 M12 | Editable node tree, real canvas, components, tokens, exports and QA |
| P09 | Media generation | M13 | Optional model worker, task scheduling, safe provenance and output gallery |
| P10 | Advanced autonomy and tool ecosystem | M14 M15 | Recoverable agents and policy-scoped MCP integrations |
| P11 | Production release and performance lab | M20 M21 | Signed delivery, regression budgets, observability and support readiness |
| P12 | Future expansion (separate scoped phases) | — | Native macOS/Linux maturity, collaboration, plugin SDK and innovation bank |

## 1. Contract, status, interpretation of “50× bigger”

This version expands the previous v2 blueprint into a **multi-document, machine-auditable engineering handbook**, with 22 module dossiers, screen inventories, configuration option catalog, pre-development gates, documentation and Wiki contracts, incident-to-GitHub workflows, and agent-specific instructions. The requested “50× bigger” is interpreted as a requirement for **greater decision and execution coverage rather than repetitive padding**. Every module has explicit acceptance evidence and paths to further documents. This is a plan and starter governance package; it does NOT assert the desktop product or autonomous server is already built.

**Priority order:** actual correctness and security boundaries; responsive professional GUI; fast and strong local inference; uninterrupted bounded autonomous work; source-backed research; maintainable modules; illustrated user guidance; sustainable releases. Maximize **Speed × Quality × Intelligence** jointly, not a fake single marketing number. Quality gates override speed optimization where they conflict.

**Environment:** Windows first, offline-first for installed models and local files; Internet required for research, GitHub and model downloads. Zero mandatory paid model APIs. Free license ≠ permissive commercial license; assess every third-party component/model and ship SPDX/license inventory. Local models cannot be assumed to match frontier cloud performance on small machines. Never advertise guaranteed tokens/sec or universal GPU compatibility.

**No-confirmation preference:** Developers may grant the controller a bounded, preconfigured authorization envelope for repository operations and safe task execution; no per-step prompts within that envelope. An out-of-scope or destructive step is denied and logged, not silently elevated. End-user telemetry requires an appropriate user-visible privacy choice. This is an engineering constraint, not a permission to exfiltrate logs.

**Status discipline:** Current documentation and any sample JSON are SPECIFICATION. GitHub remote status (branches/PR/checks) and running worker process MUST be checked before claiming implementation, automation or successful merge. A ChatGPT session alone is not an always-on developer worker.

## 2. Canonical authority and five layers of governance

| Authority tier | Location | What it controls | Reconciliation rule |
|---|---|---|---|
| Repository policy | `AGENTS.md`, ADRs, threat model | Design/engineering invariants | Version controlled and verified |
| GitHub authority | Protected `main`, phase PR and CI | Actual commit and merge facts | Remote status always checked |
| Durable worker store | SQLite event log, leases, snapshots | Exact resume step, retries, artifacts | Compare with GitHub and filesystem |
| Module contracts | `docs/modules/Mxx-*.md`, schemas | Acceptance and API compatibility | PR gate checks modules in scope |
| Research + help | Options bank, wiki source, screenshots | Decision context and user guidance | Evidence linked to versions |

Instruction files for Claude/Cursor/Codex/Gemini/Copilot must point to canonical policy rather than evolve incompatible copies. A prompt file is not a security control. The independent worker checks branch, grants tool scopes and refuses cross-phase changes. The build system checks required artifacts and tests.

In an incomplete or contradictory state: **stop only the unsafe action**, record a blocker, reconcile facts, attempt permitted recovery and continue unrelated authorized tasks. Never fabricate a passing result. The user can inspect status rather than approve each mundane step.

## 3. Product surfaces and major screen system

The app is a desktop operating environment, not separate mini-websites. Shared shell: resizable left rail; global search/command palette; multiple workbench tabs; contextual right inspector; optional bottom terminal/event panel; status strip for active model, resources and jobs. Every module adheres to the same spacing, typography, empty/loading/offline/error/success patterns and keyboard map.

Primary navigation: Home; Chat; Code; Models; Search; Research; Browser; Knowledge; Design; Media; Agents; Projects; Tools; Diagnostics; Help; Settings. Advanced entries can be grouped under workspaces while keeping direct command-palette access. Screen registry CSV defines all screens and their states; GUI phase P02 finalizes shared UX contracts and doesn't pretend every module already works.

**Professional interface:** neutral dark/light themes; dense yet readable developer surface; hierarchical typography; sensible 8px grid with 4px substeps; resizable panes with persisted geometry; stable tab reopening; virtualized long lists; reduced-motion option; user-configurable density; high contrast; no decorative glows substituting for clarity. Explicit display/interaction tests for compact laptops, 1080p, 1440p and high-DPI monitors. Use real UI performance data and screenshot snapshots, not generated image comparisons pretending to show a working app.

**Global interaction grammar:** New task; search; attach; undo; save; switch model; inspect plan; view evidence; open help; report problem; stop/pause job. Shared component catalog includes segmented controls, model cards, approval views, progress/status, issue links, multi-select trees and command palette. All actions have deterministic IDs and accessible names. Screen inventory and module docs specify each option individually.

## 4. Design research bank: Figma, Penpot, two OpenPencil projects

There are **two independent projects named OpenPencil**, to be evaluated separately:

1. `open-pencil/open-pencil` — https://github.com/open-pencil/open-pencil — MIT-oriented local editor, `.fig`/`.pen` import/export, scriptable document nodes, CLI/MCP, design lint and web/desktop model. Docs https://openpencil.dev/overview/features and engine docs https://openpencil.dev/development/architecture.
2. `ZSeven-W/openpencil` — https://github.com/ZSeven-W/openpencil — Rust design-as-code, Git-diffable `.op` JSON, agent team orchestration, MCP and code exports. Product site https://op.zseven.tech/. This is **not the same repository or architecture** as #1.
3. Penpot — https://github.com/penpot/penpot — open platform with design tokens, components/variants, CSS Grid/Flex alignment, plugins, inspect and MCP. Check MPL 2.0 license obligations for integration/forking.
4. Figma — https://www.figma.com/ — proprietary UX benchmark for professional layer inspector, canvas, components, prototyping and handoff. APIs/terms apply; do not copy code or protected assets.

For each reference: gather official docs and permission-compatible screenshots; identify features and user jobs; record interaction steps, keyboard behavior, empty/error states, technical approach, license, feasibility, estimated maintenance cost and distinct improvement hypothesis. No blind copy or claim of feature parity.

**Selection method:** implement separate isolated spikes for OpenPencil core embed, ZSeven Rust/view integration, Penpot workflow interoperability and standalone custom rendering. Compare: embed API maturity, performance at 1k/10k nodes, fonts, vectors, auto-layout fidelity, text editing, undo determinism, import/export, AI editability, testability, offline behavior, binary size, license obligations and project stability. Use weighted decision record; select architecture based on reproducible demonstrations, not stars or promotional claims.

Build `docs/research/DESIGN_COMPETITOR_MATRIX.csv` and `docs/research/OPTIONS_BANK.csv`. A selected feature must have owner, ADR, user benefit, implementation plan, test and linked help topic. The eventual studio targets editable source documents, not flat PNG mockups.

## 5. Technology layering and documented alternatives

**Desktop:** Tauri 2/Rust + React/TypeScript + Vite, with strong native IPC capability isolation. **UI:** design-token-driven component kit (Radix-style primitives, Tailwind-compatible styling if chosen), Monaco, xterm.js, virtualization. **State:** TanStack Query/Zustand for front-end; SQLite WAL for durable event state. **Agent:** supervised TS/Rust worker process, typed JSON schema messages and tool broker; not a monolithic React effect. **Models:** Ollama primary; llama.cpp optional adapter; HF Hub discovery/download. **Browser:** Playwright isolated browser worker. **Search:** local/self-hosted SearXNG adapter, provider-fallback and user-visible limitations. **Design:** selected post-spike rendering/document engine, custom adapters. **Images:** optional ComfyUI sandbox and optional downloads. **GitHub:** GitHub App with least-privileged per-repo scopes for controller, CI GITHUB_TOKEN for repo-local operations, never ship tokens in desktop app.

Every binary/package/model needs supply chain checklist: version pin; hash/signature; provenance; license/SPDX; transitive dependencies; changelog; security review; uninstall path. Review runtime isolation and distribution obligations for GPL/AGPL/MPL dependencies. Optional sidecars may have independent licenses and cannot be treated as automatically permissive.

All services expose health checks, version negotiation, idempotent stop/start and backwards-compatibility policy. UI threads never synchronously wait for inference, HTTP fetch or filesystem crawling.

## 6. Speed × Quality × Intelligence measurable contract

**Speed dimensions:** desktop cold/warm start, first usable interaction, UI event P95, first token latency, tokens/sec, context indexing latency, download throughput/resume integrity, large canvas FPS, file tree scalability, test startup time. Record realistic per-tier baselines and define change budgets **after measuring hardware**. Refuse unsupported universal performance claims. Heavy worker concurrency is constrained by thermal, memory and GPU pressure to preserve UI.

**Quality dimensions:** regression pass rate, deterministic code checks, agent task-completion evals, design accessibility, error-free operations, source-citation accuracy, download checksum integrity, documentation completeness and recovery reliability. A quality score is evidence-linked and cannot be self-assigned by the generating model.

**Intelligence dimensions:** task classifier reliability; compatible model routing; capability-aware tool calls; plan quality; contradiction detection; retrieval relevance; bounded self-correction; specialist-agent independence and truthful report generation. Run eval sets for coding, chat, design edits and research on CPU/GPU tiers; model routing scores must incorporate *measured* results and confidence intervals. Strong reasoning models can handle plan/verification; fast small models do routing/classification if tested; deterministic tools verify code and citations.

**Optimization order:** avoid doing unnecessary work; retrieve only relevant context; reuse safe cache; stream output; keep warmed model only within memory budget; minimize UI blocking; pin efficient quantization; use concurrency where benchmarked. More parallel agents can be slower if they contend for one GPU or corrupt shared state. Design isolated queues and concurrency arbitration.

## 7. Automatic pre-development checks, warnings and test policy

**PRE-DEV** happens before a single source file is changed: reconcile repo/PR/phase, read instructions, inspect current failures and dependencies, check hardware/tooling, gather options-bank evidence, compare alternate approaches, confirm license/policy, plan data contracts and tests, capture baseline screenshot and quality metrics. Assign each requirement a traceable ID, failing test or measurable success condition, known risk, evidence path and help article path.

**During development:** small vertical slices; format/lint/typecheck; unit tests; integration tests; UI component tests; end-to-end on supported OS; accessibility/keyboard and high-DPI; security scan; resource/memory checks; docs/screenshots validation. Warnings are triaged by category (new, existing baseline, tolerated documented, tool false-positive). **New unwaived warnings fail the phase**. Exception requires dated justification with issue and expiry; no silent suppression.

**Fix loop:** classify failure; reproduce; identify root cause; add regression test; make minimal patch; rerun target test then dependent suites; compare baseline and UX; update docs. Set retry budgets per failure signature so a loop cannot waste compute forever repeating the same broken command. Persist evidence before each restart. If blocked, issue and safe queue fallback; no fabricated success.

**Post-implementation:** verify all UI options with screenshots, docs, Wiki/help links, offline/error states, data migration and rollback. Re-run prior phase regression suites on every subsequent PR. Before phase complete, generate immutable evidence manifest with commit SHA, executed commands, test results, screenshot paths, performance comparison, known issues and gate decision.

## 8. Phase branch PR auto-loop and independent gates

The delivery controller maintains exactly **one active development phase branch**, named `phase/NN-name`, based on verified latest `main`, with one primary PR for that phase. Multiple coding agents can cooperate in isolated worktrees **on the same phase scope**, coordinating through leases and conflict-aware integration; no parallel next-phase PR until previous phase merged and checked. Discovery/research may precompute future options but must not mutate future phase code.

`RESUME → verify state → PRE-DEV → options research → architecture/design → tests planned → implement smallest slice → lint/typecheck/test/a11y/visual/security → triage warnings → fix → update screenshot/help/wiki → docs validation → commit → PR/CI → repair same PR → passing evidence → auto-merge if branch policy permits → verify merge SHA → phase checkpoint → next branch`.

GitHub branch protection/rulesets are mandatory. Required reviews cannot be bypassed if configured. If truly zero per-phase human merge intervention is desired, configure permitted auto-merge with automated checks and no required human approval; high-risk changes can still be disallowed by an independent policy controller. Hotfixes are exceptions managed under their own guarded branch policy and linked issue.

PR gate requires: code and tests; licenses/SBOM updates; UI screenshots and explanatory help per completed module; no documentation link regressions; security and warnings triaged; impact on Speed/Quality/Intelligence measured; threat model updated; branch/phase integrity verified; issue status updated. GitHub API/CI state, not agent prose, determines success.

## 9. Persistent back memory, status and multi-agent handoffs

**Repo memory:** `AGENTS.md`, ADRs, `docs/state/`, research records and architecture contracts. **Transactional memory:** durable SQLite journal of each task, step, action, artifact SHA, model invocation, tool grant, recovery checkpoint, retries and phase lease. **Semantic memory:** local citations/embeddings of code, docs, issues, evaluated sources, always subordinate to repo/GitHub truth.

At startup, a developer agent must determine which repository, branch, commit, phase and PR are real; read failures and task lease; detect unmatched local modifications; reconcile CI and GitHub issue status; resume from an idempotency-aware step. Never rely solely on chat memory or a static ‘current phase’ line.

Handoff file records current objective, changed modules, evidence, tested commands, last successful checkpoint, unresolved blockers, known risky actions and next smallest safe action. On crash, durable step replay must avoid repeating writes, payouts, web submissions, issue creation or PR merges. Each external action has idempotency token where supported or pre-action remote-state verification.

Active development worker runs on a separately configured always-on developer PC/server or CI runner. Chat itself cannot continue development after its session ends; the master plan must never misrepresent this.

## 10. AI agent interoperability and deterministic work instructions

Every provider entrypoint (Codex/ChatGPT `AGENTS.md`, Claude `CLAUDE.md`, Cursor `.cursor/rules`, Gemini `GEMINI.md`, Copilot `.github/copilot-instructions.md`) loads the same constitution, current phase, test contract, memory and tool policy. Adapters format context and action requests but cannot change priority or permissions. A new agent starts with `BOOTSTRAP_STATUS` and must not pick a feature solely from its own preferences.

**Roles:** architect/researcher; UX designer; implementation worker; test engineer; security reviewer; documentation author; verifier/release controller. These may be separate models or guarded workflows, not inherently separate paid services. Never let the original implementation agent's unsupported self-judgment substitute for independent tests/review.

**Mandatory response/output contract:** machine-readable `work_item_id`, `phase_id`, `branch`, `scope_paths`, `source_evidence`, `candidate_options`, `decision_rationale`, `patches`, `test_commands`, `observed_results`, `regressions`, `screenshots`, `help_links`, `issues`, `next_safe_step`. Absence of required evidence marks task incomplete. AI may propose design alternatives but only selected options reach implementation.

## 11. Automatic development issues and user incident reporting

There are **two separate incident pipelines**:

**A. Developer/CI errors:** build/test/lint/type/UI warnings, worker crash and reproducible runtime defects are detected automatically. Normalize signature → redact → deduplicate → update existing issue or create issue with label/severity/module/phase/commit/reproduction/evidence. Use scoped GitHub App or CI token; no per-error human confirmation within repo-admin preauthorization. On fix PR, link issue; close only after passing regression evidence and verified deployment where appropriate.

**B. End-user errors:** app captures minimal local crash/error envelopes, shows local incident history; only with user-enabled reporting policy does it send sanitized diagnostic metadata to a relay. The relay uses server-side GitHub App credentials, global dedupe, rate controls, spam detection and private quarantine for sensitive findings. Never embed a GitHub write token inside an end-user app; never send raw prompts, code, uploaded files, home directories, personal data, credentials or browser history. Default mode can keep user incident local and still be user-friendly. No silent public upload under a 'no confirmations' development rule.

Fields: fingerprint; normalized event class; version and platform; module; error code; hashed stack frames; redaction version; build ID; sanitized occurrence count; affected version range; last seen; status; optional reproducible steps authored from safe local tests. Severity P0 security/data loss, P1 crash/core unavailable, P2 important broken feature, P3 warning or cosmetic. Routing: P0 security to private advisory or private security workflow; P1 public issue only if safe to disclose; transient provider/network events aggregate without issue spam.

Dedup by stable fingerprint + release range and confidence. An issue may be created when frequency/severity threshold is met, not one new issue for every repeated stacktrace. Offline spool, exponential retry, rate limits, GitHub outage handling and tenant separation are mandatory. Ticket creation failure must not crash app. GitHub API Issues write permission required. See `docs/operations/ISSUE_AUTOMATION.md` and runnable stdlib demo.

## 12. Illustrated documentation, Wiki pages and in-app Help Center

Every *completed functional module* must include **documentation as a deliverable**: (1) introduction and outcomes; (2) each screen and UI option explained by purpose/default/prerequisite/interaction/validation/errors/edge cases; (3) actual screenshots with annotated captions and alt text; (4) step-by-step workflows; (5) a concept diagram; (6) FAQ and troubleshooting tied to error codes; (7) permissions/privacy; (8) keyboard shortcuts and accessibility; (9) performance/storage impact; (10) applicable wiki URL and help route; (11) last validated app version and release notes.

**Screenshot truth:** actual screenshots are captured from a built running app by Playwright/native harness on real workflows and display states; images are checked by manifest/hash and visual snapshots. Architectural SVG diagrams are allowed as diagrams but **must not be substituted for product screenshots**. A module is NOT final if its screenshot checklist is pending. `docs/help/` and `docs/wiki/pages/` are the canonical text sources; generated Wiki pages are deployment mirrors. Wiki publication must be idempotent and update links once repository slug and Wiki permission are known. GitHub Wiki is a separate Git repository (`.wiki.git`) and can be mirrored by a controlled job. All new documentation pages link to support/issue information and adjacent modules.

**In-app Help:** `F1` or help icon; contextual 'What does this option do?' links; searchable offline index; glossary; guided tours; quick-fix troubleshooting; feedback/report issue; clear distinctions between offline help and online Wiki. Search local first; internet links are optional. Authors must document both beginner and advanced modes without hiding capability definitions.

**Link/visual gates:** broken relative link; missing screenshot; unreadable image alt; stale option name; untested workflow; broken Wiki mapping or unversioned help content makes phase fail. Documentation remains maintained as UI evolves. `docs/operations/DOCUMENTATION_HELP_WIKI.md` is operational specification.

## 13. Data flow and stable event contracts

**Agent task:** UI intent → scoped project → durable job → classifier → capabilities check → model router → plan → tool request → Rust policy broker → sandboxed service → structured result → verification → artifact/checkpoint → UI event. Every transition carries trace ID, job ID, phase ID and monotonic sequence number; adapters cannot impersonate broker permissions.

**Design:** prompt/gesture → semantic design command → schema validation → node tree transaction → layout engine → renderer update → undo ledger/autosave → export artifacts → visual/test evidence → help screenshot capture. Preserve node IDs, component references and token dependencies. Layout should be deterministic; export integrity is measured separately from rendering fidelity.

**Research:** query and scope → provider search → fetch/parse → source record/provenance → evidence extraction → claim citation mapping → synthesis → independent citation validation → source-linked report → local cache with freshness policy.

**Downloads:** authorized model target/revision → license gate → disk reservation → provider download with resumable/retry strategy → temp content-addressed cache → integrity check → atomic manifest/install → runtime smoke test → benchmark/rank update. Never run arbitrary remote Python on model import.

**Incidents:** exception/event → local normalized envelope → sensitivity detection → redact → fingerprint → local durable spool → reporting policy → remote dedupe/triage (if authorized) → GitHub issue create/update → event link back to app → closing version verification.

All contracts versioned with explicit backwards compatibility, error envelopes and schema-validation tests. Use typed DTOs generated or shared across Rust/TypeScript; no loosely-typed magic payloads to privileged tools.

## 14. Security, privacy and OS boundary

Least privilege applies to desktop app and external development worker separately. Native host owns allowed project paths, allowed tool commands, outbound domain policy, process isolation, keychain, network logs, filesystem authorization and audit. Frontend renders UI, never holds arbitrary native execution rights. Browser pages, repositories, PDFs, plugin descriptions, AI output and model cards are all untrusted input subject to prompt-injection defenses.

Sandbox AI-generated code in workspace-specific worktrees; block symlink traversal/parent paths; constrain process environment; reserve destructive commands and publication for a preauthorized policy envelope. Credential store uses OS keychain; never include secrets in model context, incident payload, screenshots, Wiki or issue text. For Windows process sandboxing, evaluate restricted tokens/AppContainer/Job Objects and containers where suitable; do not label ordinary process isolation a strong security sandbox before testing.

Auto-release requires signed artifacts and verified update manifests. Supply chain lockfiles, licenses and model hashes tracked. Third-party MCP servers/custom image nodes treated as potentially executable code and not installed automatically. User reporting is locally observable and opt-in for remote diagnostics; deletion and retention settings honored.

## 15. Speed/Quality/Intelligence performance and UX test matrix

For each representative hardware tier, measure install, boot, navigation, model load, TTFT, tokens/sec, VRAM/RAM peak, download resume, indexing, canvas pan/zoom, editing, large-file/code indexing, export and task success. Define CPU-only, low VRAM, mid GPU and high GPU profiles; avoid arbitrary benchmark guarantees. Test Windows 10/11 baseline, driver incompatibility, offline mode, disk full, corrupted cache, update interrupted, missing model runtime and antivirus interference.

Test styles: type/static/lint + property-based document operations + unit + integration + API compatibility + full desktop E2E + accessibility + visual screenshot + chaos/fault injection + security + supply chain + benchmark + real user task evaluations. Include golden tests for `.fig`/`.pen`/`.op` conversion where legal and practical, with permission-compatible fixtures. Post-merge smoke tests ensure actual binary launch and first-run help paths work. New warnings must be fixed or independently waived with tracked expiry.

Quality evidence manifest must distinguish **not run**, **passed**, **failed**, **blocked** and **waived**; missing is not equal to passed. No skip of safety gate due to AI claims of confidence.

## 16. Phase order, ownership, dependencies and scope locks

Sequence is deliberately non-negotiable: P00 governance; P01 foundation; **P02 professional GUI**; **P03 fully functional chat**; **P04 fully functional coding**; P05 model intelligence and fast downloads; P06 search/research/browser; P07 knowledge/memory; **P08 Figma-like design engine**; P09 media; P10 advanced agents/MCP; P11 production release/benchmark; P12 future extensions. Infrastructure needed for a later module may be established earlier, but not claimed fully complete until its phase passes gates.

P02 freezes shared navigation, layout composition, visual tokens, keyboard behavior, documentation routes and screenshot IDs. **P01 installs a minimal runtime health/provisioning bridge, and P03 implements a minimal working Ollama-compatible inference adapter** so Chat can be completed before the advanced ranking/download features of P05. P03 completes real chat (not mock messages); P04 completes real Git/edit/test with safety; P08 only begins design engine integration after research spikes and interface/design document contract are verified. Each phase has one primary branch and PR. Feature flags hide unfinished behavior. Regressions against prior modules remain merge blockers.

Detailed module dossiers are at `docs/modules/`; screens at `docs/ui/SCREEN_INVENTORY.csv`; options at `docs/ui/OPTION_CATALOG.csv`; help and wiki pages at `docs/help/` and `docs/wiki/pages/`. Treat these as requirements, not proof of implementation.

## 17. Acceptance evidence and documentation gate schema

At phase completion the worker writes a gate manifest (immutable artifact tied to git commit) with keys: phase ID, source SHA, tested OS/hardware, implemented requirement IDs, full test suite results, warnings ledger, security scan state, performance metrics with baseline, screenshots manifest with image hashes, per-option help coverage, Wiki sync status or explicit pre-publication blocker, linked issues, license inventory, changelog, PR URL/check statuses, merge SHA and post-merge verification. A module's docs gate requires actual UI screenshots, not only SVG diagrams or sample mockups.

No PR auto-merge when critical severity issues remain, privacy leaks detected, cross-phase mutation observed, tests missing/failing, or versioned help mismatches the UI. Missing remote Wiki configuration may be deferred for **pre-implementation governance phase** only, but after the first final user module and repository Wiki enablement the publication check must be required; if Wiki unavailable, produce signed docs site alternative and clear non-compliance status rather than silently claiming a linked Wiki.

Read `docs/quality/PRE_DEVELOPMENT_CHECKLIST.md`, `docs/quality/RELEASE_GATES.md`, `docs/operations/DOCUMENTATION_HELP_WIKI.md` and each module's specific acceptance tests before writing phase code.

## 18. Future enhancement process, research refresh and deprecation policy

Add features by entering an enhancement proposal into the research/options bank with user problem, competitors, business value, evidence, dependency/upgrade risks, license, ADR, expected regression impact and compatibility path. Never replace a stable component because a new library looks newer. Use feature flags, typed adapters and migration compatibility. Plugin public API and design document schema must have explicit semver contract and deprecation window; dependencies pinned and upgrades exercised against golden fixtures.

Maintenance loops: daily development issue triage; automated dependency advisories on a scheduled cadence; periodic research reference revalidation; nightly full integration suites where infrastructure exists; pre-release accessible help screenshots; periodic user feedback clustering under privacy policy. Plan for optional collaboration, offline plugin packages, cross-platform rendering, task evaluation collections and multi-user identity only after core app is stable.

Future module branches adhere to same branch/PR/auto-merge protocol; there is no permanent unfettered writing to `main`.

## 19. Current factual state and transition to implementation

**As of this specification:** v3 documents, rules, diagrams, module contracts, helper templates and prototype local incident script exist in this downloadable kit only if accompanying validation says so. There is **no claim** that a native app, GitHub repository, GitHub issue reporting service, CI-runner, autonomous controller or Wiki publisher is installed, connected or operating. They need real implementation on a persistent machine/repository.

First production work item is P00: choose destination repository, verify access and policy, create guarded branch, install controller with persistent storage, implement and test governance checks, define research bank and first options, open PR, pass external CI and merge. Next create P01 only after remote merge verification. The desired zero-prompt execution requires up-front safe scope configuration; never invent permissions or bypass unavailable controls.

## Source references (official / first-party)

- OpenPencil editor: https://github.com/open-pencil/open-pencil and https://openpencil.dev/overview/features
- OpenPencil Rust design-as-code: https://github.com/ZSeven-W/openpencil
- Penpot: https://github.com/penpot/penpot
- Figma: https://developers.figma.com/docs/plugins/ ; https://www.figma.com/dev-mode/
- GitHub Issue REST API: https://docs.github.com/en/rest/issues/issues
- GitHub Wiki: https://docs.github.com/en/communities/documenting-your-project-with-wikis/adding-or-editing-wiki-pages
- GitHub branch protection: https://docs.github.com/en/repositories/configuring-branches-and-merges-in-your-repository/managing-protected-branches/about-protected-branches

**Research caution:** external capabilities and licenses are date-sensitive, so P00/P08 agents must recheck official docs and exact versions before dependency selection.



# v3.1 Core Extension — Non-negotiable Data and Delivery Requirements

This section supersedes older ambiguous statements regarding release qualification, persistent storage, backup and model locations. The 13-phase roadmap order remains unchanged.

## New module ownership

- **M20 (expanded):** CI release qualification, signed GitHub Actions artifact publishing and update manifests.
- **M23 (added):** Local user data vault, durable chat history and managed files, backup/export/import, encrypted archive and staged restore. [Full specification](operations/DATA_VAULT_BACKUP_RECOVERY.md).
- **M24 (added):** User-selectable storage and verified relocation of models, runtime sidecars, downloads, user vault and backups. [Full specification](operations/STORAGE_DOWNLOADS_RELOCATION.md).
- **M25 (added):** In-app update notification, user-controlled install, auto-check, version history and update recovery. [Full specification](operations/AUTO_RELEASE_AND_UPDATES.md).

## Hard data architecture invariants

1. User data is outside installation bundle; stable app identifier across updates; separate cache, model, user data and installer paths.
2. Chat save acknowledgment occurs only after durable persistence; large file artifacts are hashed and referenced transactionally.
3. Online SQLite backup, encryption/integrity manifest, schedule/retention, external-drive options and fully tested restore.
4. Original external folders are referenced, never silently included/copies; local backups on same disk cannot protect against disk loss.
5. Update requires a healthy persisted checkpoint and verified pre-upgrade backup, migrations have staged recovery and measurable no-loss test.
6. Every model/backend downloads into configurable storage adapter; moves use checksums, rollback and actual post-relocation model load.
7. App executable remains controlled by signed installer/updater; not arbitrarily movable from settings.
8. Release CI separate from user update UI. Phase merge triggers release eligibility; only publish stable if all gates passed.
9. Client polls secure update source when online/running; show notification and user chooses installation. No secret signing key or GitHub admin token in client.
10. All screens/options illustrated in Help/Wiki and verified by screenshots captured from real application before module status marked complete.

## New first-class end-user UI surfaces

`Settings → Data & Privacy → Data Vault` · `Settings → Backup & Restore` · `Settings → Storage Locations` · `Settings → Downloads & Quotas` · `Settings → Updates` · `Help → Recovery` · `Chat → History & Export`.

At startup show localized state if backup overdue, drive unavailable or update ready; do not interrupt working agents. Background scheduling while app is closed only exists if a separately opted-in service/scheduler is actually installed.

## New critical regressions

- `P01`: stable vault, DB transaction / managed artifact integrity and no data in binary path.
- `P03`: real chat/attachment persistence and independently verified encrypted backup/restore.
- `P05`: interrupted relocation and model load with Ollama/HF/ComfyUI custom destinations.
- `P11`: signed release, valid latest manifest, update notification, cancel/defer, pre-update backup, interrupted install and postboot preservation checks.

## Release pipeline and location matrix

See [Automatic releases](operations/AUTO_RELEASE_AND_UPDATES.md), [Backup/data vault](operations/DATA_VAULT_BACKUP_RECOVERY.md), [Storage relocation](operations/STORAGE_DOWNLOADS_RELOCATION.md), [new module dossiers](modules/README.md) and [v3.1 cross-phase matrix](PHASE_SPECS.md).

## v3.2 — M26 Automatic Changelog & Change Intelligence

**New module:** [M26 dossier](modules/M26.md). Every issue/warning/enhancement/bug/update creates a durable change/audit event. PRs contain machine-validated change records with relevant module IDs, test evidence and updated documentation. Unreleased/closed issues must not enter the public shipped changelog. Signed release publication atomically produces: root `CHANGELOG.md`, GitHub release notes, versioned in-app What's New, related Help indexes and Wiki source links from verified manifest; protect security/private data. See [M26 detailed contract](operations/CHANGE_INTELLIGENCE_CHANGELOG.md), [ADR-0007](adr/0007-change-intelligence-and-changelog.md) and [Planning Change History](PLANNING_CHANGELOG.md).

**Phase hooks:** P00 policy/schema; P01 append-only event persistence; P02 final shared changelog UI/help foundation; P03–P10 every changed module links change record/documentation; P11 verified release notes/changelog/update parity. All new features must preserve data, backup and release traceability standards from v3.1.


---

## Addendum 3.2.1: Cross-tool Designer import/export (deferred after P08)

The user requires external design files to be editable in Zynoa Designer and Zynoa documents to be exportable to other UI design tools. Research Figma, Penpot, `open-pencil/open-pencil` and `ZSeven-W/openpencil` separately, plus standards-based formats and future plugin adapters. Differentiate imported editable nodes from flat raster previews and an official API/plugin bridge from proprietary undocumented native writers. Never claim universal interchange fidelity.

**Mandatory sequence:** P00 research/RFC only → P02 global GUI system → **P08 Designer core fully implemented, tested, screenshot-documented and remotely merged** → **P08I** separate branch/primary PR for proven cross-tool import/export adapters → P09 next media phase. The M11/M12 core must independently pass its original completion gate before P08I begins; P08I is not part of P08's original exit criterion. Existing basic SVG/raster export remains P08 scope. No cross-tool import/export feature is implemented by this plan.

P08I provides versioned format capability matrices, import/export wizards, preflight preview, fonts/components/tokens/variants mappings, fidelity and unsupported warnings, safe worker execution, reproducible target-app round-trip tests, backup/undo, Help/Wiki and actual product screenshots. Each new format is independently tested; native `.fig` writer cannot be promised absent permitted official interfaces.

**Primary requirements:** [DESIGN-IO](operations/DESIGN_INTEROPERABILITY.md) · [P08I phase](PHASE_SPECS.md) · [Design research](research/DESIGN_RESEARCH.md).

## P00 execution boundary implementation note (2026-11-18)

The repository contains an early M22 **policy/plan-only** foundation for workspace file scope and Git worktree creation. It does not run generated code and does not replace the Windows-first OS sandbox or full autonomous agent requirements. Before enabling executable code tools, require host-controlled immutable scope grants, process and network isolation, safe file-handle operations, resource budgets, trusted Git source validation, crash reconciled worktrees and credentials segregated from model processes. See [P00 Worktree Policy](operations/P00_WORKTREE_POLICY.md), [ADR-0011](adr/0011-worktree-is-not-sandbox.md) and [active project status](state/STATUS.md). This addendum does not change the phase roadmap.

## Addendum 3.2.2: Continuous development autonomy audit (2026-11-18)

The original user goal includes uninterrupted, phase-by-phase AI software development without repeat "continue" prompts. An instruction file or GitHub Actions PR test cannot provide that by itself. [Repository audit](operations/P00_CONTINUOUS_AUTONOMY_AUDIT.md) verifies that `phase_worker.py` is an undeployed read-only observer, `dev_job_runner.py` is a three-check test harness, PR #1 is draft and `main` is not protected. **A separate live developer host** with model, safe OS-scoped code execution, durable queue, CI/error repair and guarded PR promotion must be installed and proven before claiming hands-free phase progression.

Resolve P00 bootstrap vs product-feature scope ambiguity using [phase delivery addendum](PHASE_SPECS.md): host-side autonomous developer is P00 pre-merge infrastructure; GUI captures are required once actual UI exists (P02+), full end-user coding tools belong to P04, advanced in-app agent functionality to P10. No current security gate is waived. Separate pre-merge blocker closure from actual post-merge SHA verification to avoid a circular issue/merge dependency. Do not start P01 until real P00 merge verification.

## Addendum 3.2.3 — Every phase PR has a live task table (2026-11-18)

All P00–P12 primary Pull Requests (including P08I) must display **a complete, evidence-backed, automatically rendered Task Progress table** in their GitHub PR descriptions. The authoritative list is `docs/state/pr-tasks/<PHASE>.json`; the PR displays total, Done/In Progress/Pending/Blocked and percentage, one task per row, with issue/verification links. On discovery of new in-scope work, update the manifest and add the new task to the count; do not hide blockers to inflate percentage.

A trusted default-branch `workflow_run` syncs after successful governance CI, using only bounded PR-head JSON input and a scoped PR-body write identity. Before that workflow is truly merged and active, a separately provisioned host sync or explicitly authenticated repository update is required. **Do not claim a permanent task updater or local AI developer exists simply because scripts are in draft PR #1.** Independent phase release gates, actual screenshots once UI exists, post-merge verification and user data safety remain mandatory. Details: [PR Task Tables](operations/PR_TASK_TABLES.md), [P00 tracked tasks](state/pr-tasks/P00.json).

## Addendum 3.2.4 — P00 host bootstrap and WAL recovery implementation (2026-11-18)

A concrete headless M22 host bootstrap is available in `tools/host_bootstrap.py` with path-scope/phase checking, explicit isolated data initialization, SQLite backup and non-destructive restore verification. Linux systemd observer/backup templates and Windows current-user task preview are in `deploy/`; Windows at-logon is **not** continuous 24/7 execution. Actual provisioned host/identity, worker process, AI sandboxed patching and protected GitHub main remain **P00 blocking gates**. This addition does not waive the P01 user-data vault or later module backups, UI screenshots or release/update requirements. See [host operator runbook](operations/P00_HOST_BOOTSTRAP.md) and [P00 task board](state/pr-tasks/P00.json).

## Addendum 3.2.5 — Bounded local AI planning adapter (2026-11-18)

P00 now has a concrete **model proposal** component, `tools/dev_model_planner.py`, using official Ollama `/api/chat` structured JSON and independent host-side validation against the existing workspace policy. It is intentionally unable to execute generated commands, mutate files or the GitHub repository. Only known P00 task IDs, existing read-only checks and draft-only paths are accepted. Cross-platform tests mock inference; no actual user-host Ollama installation, secure OS executor, persistent worker or production model capability is proved. Full plan→edit→test→repair loop remains [P00-T20](state/pr-tasks/P00.json) **IN_PROGRESS**, blocked on actual host/execution/merge security. See [local model planning contract](operations/P00_LOCAL_MODEL_PLANNING.md).

## Addendum 3.2.6 — Disposable fixture-only draft stage (2026-11-18)

To bridge proposal-only Ollama planning and future safe execution, P00 includes `tools/fixture_draft_stager.py` with host-supplied task identity, strict `tests/fixtures` paths, bounded UTF-8 text, OS temporary-directory staging, SHA-256 receipts, Python text-only handling and automatic cleanup. The stager never writes into the actual repository, runs generated code or modifies GitHub state. The dedicated [staging contract](operations/P00_FIXTURE_DRAFT_STAGING.md) and [ADR-0014](adr/0014-staging-not-sandbox.md) separate this real tested preview from the **still-blocked** OS security broker and full model→edit→test→fix loop. Newly discovered task P00-T25 is tracked separately from incomplete umbrella task P00-T20; PR table counts are derived dynamically. Product user-data backup, GUI screenshots, M22 runtime and P01 remain unchanged.

## Addendum 3.2.7 — Rootless Docker syntax-only broker (2026-11-18)

Added `tools/docker_syntax_broker.py`, `tests/test_docker_syntax_broker.py` and Windows policy coverage as a **bounded OS isolation interface**: a model's prevalidated single Python fixture can be syntax-compiled (never run) only under operator-authorized, pre-cached digest-pinned Docker with current-user rootless socket, rootless daemon/cgroup v2/systemd checks, no network/mounts, nonroot UID, read-only filesystem and resource caps. Default mode denies all Docker calls. CI currently verifies policy using mocked Docker responses on Linux/Windows; a user-owned rootless host has **not** been deployed or independently probed. Full OS sandbox proof P00-T19 and actual model patch/test/repair P00-T20 remain unmet, as does protection of GitHub main. [Operator details](operations/P00_DOCKER_SYNTAX_BROKER.md) and [ADR-0015](adr/0015-rootless-syntax-gate.md).

## Addendum 3.2.8 — operator-only Docker syntax smoke interface (2026-11-18)

`tools/docker_host_smoke.py` provides a **default-denied** Linux operator command to exercise existing P00 rootless Docker syntax checking with two fixed harmless valid/invalid fixtures. Separate opt-in, checkout validation, receipt verification and zero GitHub/workspace writes are contract tested on mocked Linux/Windows CI. No developer host is provisioned, sandbox independently attested or PR merged. Full P00-T19/T20, subsequent GUI, user data, Wiki/screenshot and phase sequencing obligations remain unchanged. [Runbook](operations/P00_DOCKER_SYNTAX_BROKER.md) and Issue #3 remain authoritative.
