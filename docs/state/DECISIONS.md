# Architecture Decision Log

- ADR-0001: Windows-first local-first, modular Tauri/Rust + React/TypeScript, Rust policy broker, versioned agent sidecar. Status: proposed baseline; validate during P00.
- ADR-0002: Single active delivery phase branch and one primary PR; required checks, auto-merge subject to protection. Status: required policy.
- ADR-0003: Professional GUI shell/design system completed and tested before Chat implementation, while core interfaces remain extensible. Status: required policy.
- ADR-0004: Figma-like editor is a dedicated later module; do not conflate it with app design-system authoring. Status: required policy.
- ADR-0005: No recurring approvals for pre-authorized sandboxed tasks; all out-of-scope actions denied by broker. Status: required policy.

Record future decisions using ADR number, options considered, evidence, rationale, owner/agent, tradeoffs, tests and date.

## 2026-11-18 — v3.1 architecture additions (proposals until implemented)

- DEC-031A: Separate user vault, model binary stores, downloaded runtime payloads, caches and app executable.
- DEC-031B: Signed stable GitHub Releases; phase merge only triggers qualification, not unconditional end-user publication.
- DEC-031C: Client checks updates and notifies users; installation is their choice by default; no silent interruption of active agent work.
- DEC-031D: Mandatory verified backup before binary/schema migration; tested staged restore/rollback; OS reinstall and disk loss limitations documented.
- DEC-031E: Pluggable location adapters for Ollama/HF/ComfyUI and safe migration with checksums; do not rewrite independent third-party runtime settings silently.

## ADR-0007 — planned change intelligence architecture

M26 uses append-only event ledger, per-PR change records, verified-release manifest, product changelog projections and versioned Help/Wiki. Unreleased issue history stays separate from user-visible shipped releases. See `docs/adr/0007-change-intelligence-and-changelog.md`. No implementation yet.
2026-11-21 | P00 | Added AI_STRICT_PROTOCOL; V3_2 is sole operational plan | removes plan conflict and agent drift
2026-11-21 | P00 | Owner has no hardware/credentials: T17/T19/T21-T24 to be redesigned on GitHub-hosted runners + GITHUB_TOKEN | only AI-executable path; no user infrastructure
2026-11-21 | P00 | T22 live acceptance (workflow_run listener must be on main) moves to the first step after P00 merge; T24 merge no longer waits on it | breaks T22<->T24 circular dependency
2026-11-22 | P01 | ADR-0025 selects Tauri 2/Rust + React/TypeScript/Vite for native capability-scoped P01 foundation; Electron and Wails 3 retained as researched alternatives | matches master plan and keeps policy/vault in Rust; version pin and Windows proof deferred to T03
2026-11-22 | P01 | Interpret P01-T04 typed IPC as M01/M16 workspace transport while M16 remains Project & Workspace Manager; include M23/M24/M26 only for their explicit P01 foundation tasks | reconciles task-label discrepancy with module dossiers and preserves phase scope
2026-11-22 | P01 | T02 observer must bind phase/branch/PR and never journal invalid phase as P00 | prevents stale P00 identity from contaminating P01 evidence
2026-11-22 | P01 | P00 Issue #3 applies only to P00; P01 observer reports blocker policy UNKNOWN and cannot authorize phase transition/merge without separately configured blocker scope | prevents inheriting irrelevant P00 blocker and protects owner-only merge policy
2026-11-22 | P01 | Keep scripts/runner_worker.py and its heavy rootless/Ollama workflow phase-locked to the P00-T20 disposable fixture; use tools.phase_worker active-phase read-only observer for P01 | fixture model execution grants cannot be promoted to P01 source editing
2026-11-22 | P01 | T02 runner dispatch reads active phase plus trusted Actions branch/PR; P01 permits only read-only observer while P00 fixture Docker/Ollama and bot-branch publishing remain P00-only | prevents permission carryover and limits expensive jobs to relevant code changes
