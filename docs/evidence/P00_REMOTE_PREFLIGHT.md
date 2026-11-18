# P00 Remote Pre-Development Audit — 2026-11-18

**Status:** PARTIAL / BLOCKED for full autonomous operation. No claim of production readiness.

## Verified repository facts

- Remote: https://github.com/Vertex-Systems-Network/zynoa-2-local
- Default branch: `main`; initial SHA: `8dcb546828a8fdeef40dfaa250ac8f6b8639025d`.
- Repo initially contained v3.2 specification kit only; no desktop source app or installed background worker verified.
- Original phase state: `P00 PLANNED_NOT_STARTED`. Branch, PR and Issues absent at start of audit.
- Created `phase/00-governance` and [draft PR #1](https://github.com/Vertex-Systems-Network/zynoa-2-local/pull/1).
- GitHub metadata at first audit reported `allow_auto_merge: false`. Never infer that a merge can happen without additional policy/config.
- No actual UI screenshots, signed release, installer, backup service or model runtimes have been tested.
- New DESIGN-IO future interoperability requirement is specified and tracked in [Issue #2](https://github.com/Vertex-Systems-Network/zynoa-2-local/issues/2), after full P08 merge as P08I.
- Deployment and merge-policy blockers tracked in [Issue #3](https://github.com/Vertex-Systems-Network/zynoa-2-local/issues/3).

## Actual P00 code slice

- `tools/phase_controller.py`: ordered P00-P08-P08I-P09-P12 transition contract, local state validation, SQLite WAL idempotent event journal.
- `tests/test_phase_controller.py`: transition denial and acceptance fixtures, restart-safe deduplication.
- `scripts/check_design_interop_policy.py`: specification-only P08I staging check integrated into existing governance CI.
- `tests/test_design_interop_policy.py`: static contract tests, not working Designer import/export.

**Security/authority note:** This slice takes normalized remote facts as input; it does NOT independently authenticate GitHub or run a persistent controller. Such evidence requires a separate trusted reader and worker, not AI-authored JSON.

## Research and alternatives backlog

- Official tool references to revalidate with pinned versions: Figma Plugin API; Penpot; open-pencil/open-pencil; ZSeven-W/openpencil. Licensing, capability matrix, private API limits and real fixtures are NOT yet independently benchmarked.
- Agent hosting candidates: persistent user-managed machine/service with SQLite lease vs managed runner with durable external state; compare security/latency/cost and record ADR before deployment.
- UI/OS baseline tests require actual Windows development/test environment and product build; current documentation-only repository cannot supply screenshots or measured FPS/inference performance.

## Current verification and evidence limits

Prior GitHub Action runs on intermediate P00 commits have reported success. Final PR HEAD CI must be checked again after every change; no PASS claim for an in-progress workflow. Test failures must be fixed on the same branch.

## Required before P00 exit

1. Authenticated repo PR/CI/merge evidence reader and guarded branch/PR operations.
2. Persistent worker/lease and restart/replay tested on a configured host.
3. Research bank with pinned verified source/license comparisons and security review.
4. Automated CI acceptance gate and reproducible logs; truthful screenshot/docs status.
5. Verified merge of PR #1 into main and durable state checkpoint. **Do not create P01 branch before this.**
