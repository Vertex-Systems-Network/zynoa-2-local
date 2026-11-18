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
