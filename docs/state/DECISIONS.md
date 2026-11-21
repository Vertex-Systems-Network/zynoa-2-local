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
