## Phase task table (required for EVERY PR)

- **Manifest:** `docs/state/pr-tasks/<ACTIVE_PHASE>.json` (must match active `PHASE.json` and actual primary PR number).
- [ ] Every phase task is tracked with stable ID, status, evidence/blocker link and honest completion verification.
- [ ] Auto-generated table below matches manifest; preserve its markers when editing PR description.
- [ ] In-scope new tasks appended to the SAME phase manifest; phase merger still checks independent protected GitHub CI and release gates.

<!-- ZYNOA_PR_TASK_BOARD_START v1 -->
Task table not synchronized yet. The trusted controller must populate this block from the checked manifest; do not mark the PR complete while placeholder remains.
<!-- ZYNOA_PR_TASK_BOARD_END -->

---

## Phase and scope
- Phase ID / branch:
- Applicable module dossier(s) and requirement IDs:
- Exact reference and ADR(s):
- Research candidates compared (Figma / Penpot / both OpenPencils for design):

## PRE-DEV
- [ ] GitHub remote and branch lease verified
- [ ] Baseline errors and warnings captured
- [ ] Data flow / API contract / threat changes documented
- [ ] Tests defined before code

## Evidence
- [ ] Implementation functional, not mock only
- [ ] Unit + contracts + integration + desktop E2E pass
- [ ] New errors/warnings fixed or documented waiver with deadline
- [ ] Security and privacy checks pass
- [ ] Performance baseline and regression results attached
- [ ] Module options documented with **real** screenshots and alt text
- [ ] In-app Help index and versioned Wiki sources synchronized
- [ ] Incident/error codes and linked GitHub issues updated
- [ ] Change logs, licenses and migration/rollback notes included

## GitHub verification
- Required checks (links):
- Actual screenshots manifest:
- Issue links:
- Why safe to auto-merge:
- Post-merge verification SHA (controller fills after merge):

## v3.2 Change Log and Documentation Contract (required)
- Change ID(s) and type(s):
- Linked issue(s) and affected modules/options/screens:
- [ ] Structured change record in `.changes/records/` or documented machine-validated no-user-impact classification
- [ ] PR issue and change events deduplicated; no private data leaked
- [ ] Tests and actual verified results linked; warnings triaged
- [ ] Module dossier, UI option inventory, Help, Wiki and screenshots updated where behavior changed
- [ ] Breaking changes, data migration, rollback guidance included when relevant
- [ ] Release impact (major/minor/patch/none) and channel stated; not marked shipped before signed release
- [ ] Changelog/Wiki/Help parity gate ready for publishing
