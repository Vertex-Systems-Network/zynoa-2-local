# P02-T05/T06 — scoped Windows functional acceptance (2026-11-24)

**Disposition:** P02-T05 and P02-T06: DONE for their scoped feature implementations and native UI evidence; P02-T02/T08/T10/T11 remain IN_PROGRESS. No phase merge/release.

## Verified evidence

- Original Windows Tauri [successful run #45256580719](https://github.com/Vertex-Systems-Network/zynoa-2-local/actions/runs/45256580719), source SHA `b52c2800fc7bee3ed773755a1d93cc783a51ad44`, uploaded artifact `14857333496`.
- The artifact contains 69 source/build-SHA and SHA-256 bound native screenshot candidates and a staged 29-target ZIP with 29 distinct PNG hashes and exact original control/view capture IDs. All captures are correctly marked *candidate/pending final approval*, not automatically verified.
- Independently re-extracted and inspected real native PNGs `P02-T05-PREFERENCES-LIVE`, `P02-T02-12-LIGHT`, `P02-T02-12-DARK`, and `P02-T06-GALLERY-READY`, `LOADING`, `EMPTY`, `ERROR`, `OFFLINE` plus the full 15-target M02 contact sheet. Each displays a different applicable state/control with meaningful labels, recovery guidance, native window chrome and no apparent major clipping at the captured dimensions.
- Compared source `b52c2800` to branch head `ee64d67c` before this status change: only change records, docs, task board and evidence changed; **no UI source, style, dependency or native capture script diff**. Native screenshot and application evidence therefore remains directly applicable to these two scoped features.
- `tests/test_p02_m02_controls.py`, `tests/test_p02_ui_contract.py` and `apps/desktop/tests/ui-logic.test.mjs` cover theme/density/session boundaries, contrast/focus, gallery states, pane slider/responsive layout, negative side effects. Successful Windows run included TypeScript, Node UI, Rust/native build and actual cold boot.

## T05 — DONE, scoped feature

System/light/dark mode, follow-OS behavior, compact/comfortable density, labelled read-only Windows reduced-motion status and reset-to-default controls are implemented. Setting changes are session-only, not persisted to files/account, and no OS preference is modified. Actual native dark/light and live summary screenshots are distinct and readable.

## T06 — DONE, scoped feature

Component gallery has independently selectable button states, feedback and preserved sample input, a disabled control, responsive sizing, and an actual illustrative split-pane slider (25–65%, 40% reset) with accessible percentage feedback. Five states (Ready, Loading, Empty, Error, Offline) are real, distinct and keyboard-choosable illustrative examples with recovery copy—not actual network/service probes. All five real native images were examined.

## Explicit non-acceptance boundaries

- **T02 still not DONE:** 15 required M02 screenshot PNGs are not committed to final repository paths; all 15 manifest entries PENDING. `tools/verify_p02_t02_acceptance.py` must remain fail-closed until final evidence and review.
- **T10 pending:** all 29 final M02+M19 screenshot commits, a full NVDA/Narrator keyboard/a11y traversal, multi-run performance budget, Wiki publication verification and independent full visual approval.
- **T11 pending:** exact-head full CI, independent security/privacy review, appropriate owner intent, protected final merge.
- Later Windows run on `ee64d67c` failed `ZYN-SCREEN-019` in M19 FAQ interaction, beyond the T05/T06 captured scope; an attempt-2 rerun was requested and must be verified independently. No declaration that this failed run is green.
- **Lease checked:** current `docs/state/PHASE.json` reports `lease_holder=null`, `worker_running=false`. Kept unchanged; no active worker takeover.
