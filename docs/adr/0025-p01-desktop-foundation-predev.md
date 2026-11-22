# ADR-0025 — P01 desktop foundation pre-development gate

**Date:** 2026-11-22 UTC · **Task:** P01-T01 · **Decision:** ACCEPTED FOR IMPLEMENTATION PLANNING, not a shipped capability · **Scope:** P01 on `phase/01-foundation`, draft PR #10.

## 1. Remote and environment baseline (2026-11-22 UTC)

- Verified GitHub repository `Vertex-Systems-Network/zynoa-2-local`; remote `main` at `1697ea8488b2da089da22951de64f5254a48b71f`. Primary draft [PR #10](https://github.com/Vertex-Systems-Network/zynoa-2-local/pull/10) targets `main` from `phase/01-foundation`.
- The pre-edit P01 branch head `610de6784cf6f2cb79fd9f046511b7824ed3881b` had [passing Governance CI](https://github.com/Vertex-Systems-Network/zynoa-2-local/actions/runs/44967811108). Lease-only commit `b9c088421f8b7c055b57fa798ea2f7b97f6aa989` had [passing Governance CI](https://github.com/Vertex-Systems-Network/zynoa-2-local/actions/runs/44968410424). These are **baseline-only**, not P01 feature acceptance.
- Repository root currently has governance `tools/`, `scripts/`, `tests/`, `docs/` and `deploy/`; **no bootable P01 desktop application yet**. No desktop latency, install size, keychain, Rust build, Windows screenshot or data recovery metrics can be asserted. Record these as `NOT_MEASURED`; obtain first credible baseline when T03–T09 provide working artifacts.
- Remote GitHub Actions can run the existing Python checks on Ubuntu, plus scoped Windows jobs. No owner-supplied development hardware or credentials are assumed; no local Windows/Ollama runtime or release-signing capability has been verified. Use GitHub-hosted Windows runners for build and smoke tests, not CI results as proof of a user's installed application.
- Existing stored user-vault data format/schema: **NONE** (unimplemented); no migration, backup or recovery test has actually run against a P01 user vault. Prior P00 SQLite fixtures do not satisfy this gate. Registry roots/model inventories and third-party runtime ownership remain unknown until implementation. No user data deletion is authorized.
- Latest issue/CI authority must be rechecked before each implementation slice. No new blocking P01 regression established by the pre-edit passing governance run. Existing P00 infrastructure/incident issues are not automatically reclassified as P01 product failures.

## 2. Desktop stack research and alternatives

Official sources checked 2026-11-22 UTC. License statements concern the upstream framework only; audit all transitive licenses and pinned versions before adding a dependency.

| Candidate | Official evidence and upstream license | Security/Windows/offline tradeoff | Decision |
| --- | --- | --- | --- |
| **Tauri 2 / Rust + React + TypeScript + Vite** | [Tauri capabilities](https://v2.tauri.app/security/capabilities/), [Windows prerequisites](https://v2.tauri.app/start/prerequisites/), [Tauri license](https://github.com/tauri-apps/tauri); MIT or Apache-2.0 | Native Rust policy boundary and per-window capability sets; depends on system WebView2; command scopes are not automatic validation of custom Rust handlers | **Select**, consistent with master plan; pin exact, security-supported versions only at T03 |
| **Electron + React/TypeScript** | [Electron security guide](https://www.electronjs.org/docs/latest/tutorial/security/), [license](https://www.electronjs.org/docs/latest/why-electron); MIT | Bundled Chromium simplifies rendering parity, increases runtime/update ownership and privileged IPC/preload audit surface; requires sandbox and context isolation | Reject for P01's default footprint/privilege boundary; retain as fallback if reproducible Windows Tauri blocker |
| **Wails 3 + Go/React** | [Wails project](https://github.com/wailsapp/wails), [Wails site](https://wails.io/); MIT | Native webview and Go bridge are viable; replacing Rust policy/data boundary would rewrite current contracts; verify v3 migration and Windows bridge security | Reject to avoid unplanned Go/Rust dual backend, not because the framework is unsafe |

Tauri 2.12 announcement [documents Windows 7 support removal](https://v2.tauri.app/blog/tauri-2.12/); **Windows 10/11 is the provisional validation target**, subject to actual runner validation and a stated support policy. No silent support claim for Windows 7. WebView2 readiness must be tested rather than inferred. Offline app bootstrap must not depend on Ollama, GitHub or an external API.

**UX comparators (patterns only):** [VS Code workbench UX](https://code.visualstudio.com/docs/getstarted/userinterface) (workspace recovery, status strip, keyboard); [Windows Terminal](https://learn.microsoft.com/en-us/windows/terminal/) (tabs, discoverable actions, accessibility). Do not copy branded visuals or claim full feature parity. T03 targets a minimal truthful first-boot/recovery/error shell; P02 owns polished shared design system.

## 3. In-scope data, boundaries and decisions

- T03 M01: native Tauri shell starts offline; display startup, permission and recovery states; frontend is unprivileged.
- T04 M16: **contract discrepancy**: task board calls M16 `typed IPC`, while `docs/modules/M16.md` describes Project & Workspace Manager. Implement typed IPC as the *transport required by M01/M16 workspace operations*; do not relabel M16, invent an extra module or expand workspace features. Reconcile at T04 with contract tests. `docs/PHASE_SPECS.md` names M01/M16/M17/M18; the P01 task board and M23/M24/M26 dossiers explicitly assign **foundation sub-scopes** to P01. Defer other-phase UI and advanced relocation/update capabilities.
- T05 M17: Rust/native capability broker denies by default; explicit path and outbound-domain grants; OS keychain for secrets; no backend authority inferred from arbitrary WebView payloads.
- T06 M18: local structured diagnostics using stable trace/correlation IDs, bounded records and secret/path/user-content redaction; developer CI incident flow is distinct from consent-gated end-user telemetry.
- T07 M23: user-owned SQLite WAL vault and managed files live outside executable/update folders. A success acknowledgment occurs only after transaction commit. Real backup is SQLite online backup plus content manifest; never raw-copy only the WAL database or overwrite the last good copy.
- T08 M24: location registry distinguishes app/user data, backups, model stores, caches, staging and external references. Foreign runtimes are not silently moved; migration requires inventory → quiesce → stage → checksum → activate → probe → rollback.
- T09 M26: append-only, privacy-scoped idempotent event stream; user-facing released change state must derive from verified signed release, not PR completion.
- No new external service, paid API, telemetry default-on, execution permission or dependency is approved by this document. No repository/OS sandbox is implied by Tauri capabilities.

**Transport sketch** (to validate at T04): `{schema_version, command_id, correlation_id, idempotency_key, workspace_scope, payload}` → Rust validates shape + capability and dispatches → transaction/event store → versioned `{status, event_seq?, error_code?, recovery_action?}`; reject untrusted origin, oversized payload, unknown schema, stale/replayed writes and revoked grants.

Reference for WAL semantics: [SQLite WAL](https://www.sqlite.org/wal.html) and [SQLite online backup API](https://www.sqlite.org/backup.html).

**Persistence sketch** (T07–T09): managed data root under per-user OS application data (not install tree); SQLite foreign keys and transactional writes with WAL; versioned migration journal; backups to independently chosen destination with verified restore *into a new profile*; external paths are references unless specifically opted into an archive. State isn't committed merely because a UI event was emitted.

## 4. Threat-model delta and rollback

| Trust boundary / threat | Required mitigation and failure-injection proof |
| --- | --- |
| Compromised or remote WebView invokes privileged commands | Explicit per-window Tauri capability + per-command Rust authorization; reject forged scope, disallowed commands and origins, and remote navigation |
| IPC deserialization, schema downgrade, replay, file traversal or symlink escape | Versioned type checks, bounded inputs, canonical owned scopes, idempotency and negative integration tests; do not make frontend-provided paths authority |
| Secrets/telemetry leak through crash and audit logs | OS credential store; deny plaintext secrets; structured redaction and opt-in end-user upload; hostile-content and log-redaction tests |
| Interrupted vault commit/migration, WAL corruption, disk full, half backup | Transaction acknowledgement, migration checkpoint, online backup, disposable restore drill, original preservation and crash/reopen probes |
| Malicious model path/relocation, external runtime ownership | Discover owner first; stage with checksum, never delete sole copy; pause/retry/rollback and adversarial path tests |
| Forged change event or released status | Enforced scoped append stream, dedupe/sequence, payload privacy classes, independently verified release identity |
| Compromised dependencies/build artifacts | Pin lockfiles and known actions, provenance/license review, build on GitHub-hosted Windows/Ubuntu CI, signed artifact validation before release |

**Failure path:** on gate failure, record exact sanitized signal and owner action, leave current task IN_PROGRESS or supported BLOCKED, keep PR draft and phase fixed, revert only the affected non-user-data change, rerun new regression and full suite. No auto-merge permission exists in the current strict protocol. Later migrations require both backup and proven restore; no destructive cleanup on test ambiguity.

## 5. Tests-first acceptance map (to implement with each task)

| Task | Before implementation, define these failing/negative and recovery checks | Evidence gate |
| --- | --- | --- |
| P01-T02 | P00-only controller/worker references reject wrong active phase; resume observes P01; branch/PR spoof and lease mismatch denied | Python unit + governance/CI |
| P01-T03 | Windows Tauri cold/offline boot, WebView2 missing, invalid settings, keyboard/first boot/error/restore; Rust cargo check and TypeScript build | Windows hosted smoke, real screenshot once app runs |
| P01-T04 | Rust/TypeScript schema parity; unknown command, payload size, revocation, replay, timeout, state recovery | Unit + IPC contract integration |
| P01-T05 | Permission grant/revoke and secret denial; symlink escape, untrusted window and redacted error | Native policy and Windows security tests |
| P01-T06 | No secret/PII in logs, rate-bound error bursts, crash/resume, opt-in outbound guard | Negative/diagnostic tests |
| P01-T07 | SQLite commit-before-ack, abrupt exit, broken WAL, disk full, backup/restore to new profile, lossless data migration | DB integration + recovery drill |
| P01-T08 | Shared/external path refusal; free-space check, mixed-case/Unicode and symlink path, failed checksum/relocation/rollback | Native filesystem integration |
| P01-T09 | Same key retry dedupes, sequence monotonicity, privacy isolation, malicious payload refusal, no false released status | Event-store unit/integration |
| P01-T10 | Actual app screenshot provenance and every implemented option mapped to Help/Wiki; missing images stay PENDING | Docs/visual checks |
| P01-T11 | Re-run all checks on final SHA; verify Windows UX/data/security and PR table; no merge absent explicit owner message | CI+remote evidence, draft stays open |

**T01 gate itself:** document upstream alternatives and dates; review threat and data/UX contracts; validate every acceptance row above in a new unittest before feature development. The existing CI workflow runs `python scripts/check_governance.py`, `python scripts/verify_v3_kit.py`, `python scripts/verify_v31_kit.py`, `python scripts/verify_v32_kit.py`, `python -m unittest discover -s tests -v`, and `python -m scripts.check_pr_task_board`. New P01 functional build/Windows/visual/performance gates remain **PENDING** until relevant code exists; governance passing is not their substitute.

**Exit status for T01:** `PENDING_CI` until this ADR and its gate tests receive a real passing run linked in the P01 task manifest. No UI screenshot, release, merge, restored user vault, environment performance or version pin claimed.
