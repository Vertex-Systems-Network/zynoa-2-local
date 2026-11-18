# AI Workspace 3.2 — Autonomous Engineering Master Kit

**State:** Specification, design/agent governance and local test scaffolding ONLY. Desktop application, GitHub branches/PRs, release publisher, backup, updater, end-user change tracking and published Wiki are **not** implemented.

## New in v3.2

- M26 **Change Intelligence / Changelog / Issue & PR Traceability**: every bug/enhancement/update produces a recorded event; verified released changes appear in user-facing changelog with issue/PR/documentation links, never merely planned issues.
- Structured change-record schema, local generator/validator prototype and targeted unit tests.
- 8 new UI screen contracts, 20 option contracts, 28 screenshot obligations (all pending).
- Updated cross-agent rules, PR template, module/help/wiki index, gate, phase and release requirements.
- `docs/PLANNING_CHANGELOG.md` records specification changes separately from root `CHANGELOG.md` (actual product releases only).

**Read first:** [Consolidated v3.2 Master Plan](docs/MASTER_PLAN_V3_2.md), [M26 Detailed Contract](docs/operations/CHANGE_INTELLIGENCE_CHANGELOG.md), [M26 Module](docs/modules/M26.md), [Agent Rules](AGENTS.md).

**Local validation:**
```bash
python scripts/verify_v32_kit.py
python tools/changelog.py validate --records tests/fixtures/change_records.json
python -m unittest discover -s tests -v
```

Sample change records live under tests/fixtures only and must never be represented as real app releases. No GitHub repository was modified by this package creation.


## P00 GitHub work and future Design Interoperability

Active P00 governance branch: `phase/00-governance`, [draft PR #1](https://github.com/Vertex-Systems-Network/zynoa-2-local/pull/1). **The application and persistent developer worker are not implemented.** New [DESIGN-IO specification](docs/operations/DESIGN_INTEROPERABILITY.md) establishes external designer import/export requirements for Figma, Penpot, both OpenPencils and extensible future formats, strictly **after** native Designer phase P08 passes testing/docs and is remotely merged. P08I is a separate phase/branch/PR. P00 static validation: `python scripts/check_design_interop_policy.py`. Do not mistake this for a functional design importer/exporter.


## Current P00 remote development (2026-11-18)

Repository governance is in progress on [draft PR #1](https://github.com/Vertex-Systems-Network/zynoa-2-local/pull/1), branch `phase/00-governance`. Real code now provides an authenticated **read-only** GitHub PR/CI/blocker observer, a SQLite-leased recovery loop, developer-only sanitized issue bridge, CI live API observation and unit tests. See [P00 runbook](docs/operations/P00_WORKER_RUNBOOK.md), [hosting study](docs/research/P00_WORKER_HOSTING_RESEARCH.md) and [ADR-0009](docs/adr/0009-phase-observer-boundary.md). These are NOT a deployed autonomous AI developer, a release, or a functional desktop GUI. `main` protection and a persistent host remain open in [Issue #3](https://github.com/Vertex-Systems-Network/zynoa-2-local/issues/3); P01 must not begin until P00 is verified merged. Future Designer import/export remains scoped to P08I after P08 per [Issue #2](https://github.com/Vertex-Systems-Network/zynoa-2-local/issues/2).

## P00 trusted worktree planning slice — 2026-11-18

Current work remains in [draft PR #1](https://github.com/Vertex-Systems-Network/zynoa-2-local/pull/1) on `phase/00-governance`; **P01 has not started**. Backend additions: `tools/workspace_policy.py` validates narrow host-supplied file scopes, `tools/worktree_plan.py` constructs a detached no-checkout SHA-pinned Git worktree plan, and `tests/test_workspace_policy.py` verifies a real temporary fixture Git worktree without touching the product source repo. Read [P00 Worktree Policy](docs/operations/P00_WORKTREE_POLICY.md) and [ADR-0011](docs/adr/0011-worktree-is-not-sandbox.md). This is NOT a sandbox, GUI, installed host, live AI coding agent or release. Remaining security/deployment blockers are tracked in [Issue #3](https://github.com/Vertex-Systems-Network/zynoa-2-local/issues/3).
