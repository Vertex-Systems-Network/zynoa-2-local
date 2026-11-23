# P02-T02.12 — Final T02 acceptance and GitHub task closure preflight

**Task ID:** P02-T02 (M02 design tokens, accessible UI primitives and visual foundations).  
**Primary Draft PR:** [#12](https://github.com/Vertex-Systems-Network/zynoa-2-local/pull/12), branch `phase/02-shared-ui`.  
**Decision:** **IN_PROGRESS — NOT READY FOR FINAL CLOSURE.** No merge, P03, release or counterfeit DONE status.

This document captures the **T02.12 closure work** separately from the 11 officially tracked P02 task IDs. It is not a new official task row and must not move source-of-truth `docs/state/pr-tasks/P02.json` to DONE without real acceptance.

## Scoped component progress

| Internal acceptance slice | Evidence | Current assessment |
| --- | --- | --- |
| T02.01 Design tokens | Semantic dark/light CSS variables and M02 gallery | Implemented; broader state review pending |
| T02.02 Color contrast | Python WCAG small-label and focus contrast matrix in `tests.test_p02_ui_contract` | Verified for tested surfaces |
| T02.03 UI primitives | Buttons, inputs, native selector, state chips, gallery components | Implemented source |
| T02.04 Keyboard focus | Real Tauri focus ring, [Windows #45140383789](https://github.com/Vertex-Systems-Network/zynoa-2-local/actions/runs/45140383789) and [focus review](../screenshots/M02/M02-OPT-07.review.json) | Scoped DONE |
| T02.05 Reduced motion | `prefers-reduced-motion` CSS and source contract | Implemented; native OS-mode scenario pending |
| T02.06 Hover/disabled/selected/states | Real native selected/disabled gallery, [Windows #45145725506](https://github.com/Vertex-Systems-Network/zynoa-2-local/actions/runs/45145725506) | Scoped DONE; pointer-hover E2E pending |
| T02.07 Responsive foundations | 898×653 native gallery, independent review, [Windows #45145725506](https://github.com/Vertex-Systems-Network/zynoa-2-local/actions/runs/45145725506) | Scoped DONE |
| T02.08 TypeScript and UI regressions | TypeScript, Node UI and Rust tests on exact Windows CI source | Verified for tested algorithms |
| T02.09 Windows accessibility gate | [Windows #45149201009](https://github.com/Vertex-Systems-Network/zynoa-2-local/actions/runs/45149201009), 12 native integrity tests, ARIA/contrast source contracts | Scoped DONE |
| T02.10 Native foundation review | [9-image SHA-bound review](../screenshots/M02/T02-visual-foundation.review.json) and [scoped results](P02_T02_09_10_11_VALIDATION.md) | Scoped DONE; full M02 still pending |
| T02.11 Help/Wiki evidence | [M02 Help](../help/articles/M02.md), [Wiki source](../wiki/pages/M02.md), 8 option tests | Scoped DONE; publication and final Help integration pending |
| **T02.12 Final acceptance + official board closure** | This preflight + `tools.verify_p02_t02_acceptance`; remote CI and final acceptance still required | **IN_PROGRESS (cannot mark DONE)** |

## Non-waivable finalization blockers

1. **15 M02 final screenshot IDs** (`M02-S01..S07`, `M02-OPT-01..08`) in `docs/screenshots/MANIFEST.json` all remain `PENDING` at this preflight. Some real candidate PNGs exist only in a Windows Actions artifact namespace `docs/screenshots/_ci`. The final screenshots are not all in the required paths or independently accepted.
2. **M02-OPT-03 (compact properties panel) and M02-OPT-04 (user-defined shortcut mappings)** remain explicitly unimplemented; Help/Wiki must not advertise them as working controls. Their delivery is broader P02 functionality, separate from the first component slice.
3. Per-state native usability coverage for light/dark/system appearance, the keyboard guide, pointer hover, screen-reader navigation, inputs, reduced-motion Windows setting, overflow/error/offline and keyboard recovery is **not** established for all target screens. This slice adds **3 more native CI candidates**: `M02-S07`, `P02-T02-12-LIGHT`, `P02-T02-12-DARK`; they require exact-source CI, independent visual review and proper SHA receipts, and are **not yet final manifest proof**.
4. Full performance measurements and acceptance budget, option-by-option failure/undo rules, user-guide images, offline Help bundle coverage and optional remote Wiki publication remain release work.
5. P02-T03 through T11 remain separate official tasks. M19 has **14** further screenshot manifest entries pending (a separate module, not part of T02's 15-image count); the full phase cannot be considered complete from T02 alone.

## New T02.12 fail-closed guard

`python -m tools.verify_p02_t02_acceptance` reads the official `P02.json` task status, the M02 screenshot manifest, real final PNG paths, M02 Help/Wiki option IDs, planned/unimplemented controls and the existing scoped native review boundary. It reports `NOT_READY` with specific blockers and allows the official task to remain `IN_PROGRESS`. If anyone marks P02-T02 `DONE` while required proof is missing, the command **fails CI** with `ZYN-P02-T02-012`.

This gate is intentionally **local preflight only**, not evidence of verified remote CI, full human review or a completed release. The new P02 Windows step generates `docs/screenshots/_ci/M02/P02-T02-12-readiness.json` in its artifact. Source-level contracts and the verifier's rejection cases are covered by `tests.test_p02_t02_acceptance`.

## Next acceptance steps

- Review exact-source Windows artifact for `M02-S07`, Light and Dark screenshots; if PowerShell native keyboard capture fails, fix the same script and rerun full Windows CI. Keep immutable capture receipts with `capture_verified=false` until separate review.
- Complete all missing M02 features and 15 manifest screenshot assets through the appropriate official P02 tasks. Add final review/caption/alt-text/evidence and performance data; verify Help/Wiki links and accessibility end-to-end.
- Only then run the exact-head CI, full governance/Python regression suite, and remote GitHub proof; update the official `P02-T02` board from `IN_PROGRESS` to `DONE` *only after all conditions pass*, and synchronize the PR task-table block. Do not merge/advance phase as a substitute.

**Roll-back:** Revert T02.12's capture/guard/tests/docs changes on the same P02 branch; no user data, preferences or native storage migration was introduced. The source PR remains Draft until its own merger/phase gates pass.


## Exact-source Windows CI and independently inspected candidate closeout (2026-11-23)

- **Source SHA:** `e22d51d52d47ea08eba3594579f54104c78e392a`.
- [Windows CI #45153183376](https://github.com/Vertex-Systems-Network/zynoa-2-local/actions/runs/45153183376) **SUCCESS**: P02 focus/contrast, 13 fail-closed native evidence tests, 8 Help/Wiki accuracy tests, **8 final-readiness regression tests**, TypeScript/UI algorithms, Rust native tests, actual Tauri binary build/cold boot, 12 real native screenshot pairs and post-boot PNG/source SHA integrity report.
- [Real native visual review](../screenshots/M02/T02-12-appearance-keyboard.review.json): `M02-S07` (998×701) keyboard guide selected with visible gold focus outline; `P02-T02-12-LIGHT` (898×653) Appearance=Light with light palette; `P02-T02-12-DARK` (898×653) Appearance=Dark with charcoal palette. All three source/build SHA and PNG SHA256 values match original candidate receipts. The screenshot verifier asserts Light and Dark frames cannot have identical pixels.
- Machine receipt `P02-native-machine-review.json`: `MACHINE_METADATA_HASH_VALIDATED_ONLY`, `independent_visual_review=false`, `manifest_completed=false`. The human review is a *separate* scoped record, and the source receipts remain `capture_verified=false`. No final screenshots have been committed under mandatory `docs/screenshots/M02/M02-*.png` paths.
- CI-generated `P02-T02-12-readiness.json`: **`NOT_READY`**, `official_task_status=IN_PROGRESS`, `verified_manifest_screenshot_count=0`. It lists six blockers: 15 M02 final PNGs absent; 15 manifest entries not VERIFIED; scope-only visual review; M02-OPT-03/04 not implemented; M02 contract NOT YET VERIFIED.
- **Result:** T02.12 finalization protection and additional live visual coverage implemented/tested; **T02.12 full task closure remains IN_PROGRESS**, and the official parent `P02-T02` remains `IN_PROGRESS`. Full phase closure/PR merge is not implied. Future acceptance must close the documented blockers using the current main/branch and exact-source GitHub receipts.

