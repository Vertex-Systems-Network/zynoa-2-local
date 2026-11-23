# P02-T04 — Command palette, shortcuts, keyboard navigation and focus recovery

**Official task decision:** **DONE (T04 functional acceptance)**. This is the complete scope of the official P02-T04 row, not the final M02/M19 screenshot-manifest or phase release. All changes remain on primary Draft [PR #12](https://github.com/Vertex-Systems-Network/zynoa-2-local/pull/12), `phase/02-shared-ui`, protected main unchanged.

## Acceptance matrix

| Required capability | Actual implementation and validated result | Proof |
| --- | --- | --- |
| Allowlisted command palette | Ctrl+Shift+P opens real ARIA dialog, focuses bounded 100-character local search; Up/Down selects, Enter navigates, Esc/Close/backdrop dismiss | Python focus contracts, Node UI command search, native `M02-S04` |
| Empty search and recovery | No-match query shows 0/7 and “No matching commands”; Esc closes without changing background view | Native `P02-T04-NO-MATCH` and `P02-T04-ESCAPE` |
| Navigation with focus handoff | Enter from palette navigates to the selected Workbench view; dialog owns focus, active view's main content receives focus by source effect | Native `P02-T04-ENTER-NAV`; React focus lifecycle contracts |
| Modal isolation | Main and sidebar are inert when palette is open; F1 and Ctrl+1..6 cannot navigate background; Escape closes. Both connected-opener and disconnected-opener focus fallbacks exist | `tests.test_p02_ui_contract`, code inspection, native modal/close |
| Keyboard tabs + focus visibility | Workbench tabs use roving tabindex and ArrowLeft/ArrowRight/Home/End; visible `:focus-visible` 2px token outline with 3px offset; contrast checks run | Native `M02-OPT-07`, `M02-S07` and WCAG source tests |
| Remappable navigation shortcuts | Ctrl+1..6 are strictly allowlisted; occupied key swaps both destinations. Sidebar, actual global handler and palette labels/search agree. F1 and Ctrl+Shift+P remain reserved | Node remap/search tests, source contracts, native `M02-OPT-04` and `P02-T02-OPT-04-swapped` |
| Accessible remapping feedback | Live assigned shortcut list is announced on change, and each sidebar control exposes its current `aria-keyshortcuts` | Source commit `cec58d5`, Python contract tests |
| Safe state boundaries | Session-only mapping and no network, OS-wide hotkeys, persistent preference store, arbitrary command execution or new native IPC permission | Source-only state, read-only UI reviewer, safe runtime design |

## Exact source CI and visual evidence

**Tested application/CI source SHA:** [`cec58d5e6131fff16245da6b888fb3fa4e5a043d`](https://github.com/Vertex-Systems-Network/zynoa-2-local/commit/cec58d5e6131fff16245da6b888fb3fa4e5a043d).

**Five workflows, all SUCCESS on that exact source:**
- [Windows Tauri #45165103677](https://github.com/Vertex-Systems-Network/zynoa-2-local/actions/runs/45165103677) — `tests.test_p02_ui_contract`, `tests.test_p02_native_evidence`, Help/acceptance tests, TypeScript, Node UI algorithms, native Rust, Tauri executable/cold boot, full 18 screenshot capture/hash gate.
- [Governance v3.2 #45165103669](https://github.com/Vertex-Systems-Network/zynoa-2-local/actions/runs/45165103669) — `python scripts/check_governance.py`, `verify_v3_kit.py`, `verify_v31_kit.py`, `verify_v32_kit.py`, **`python -m unittest discover -s tests -v`**, change record and PR board policies.
- [Reviewdog #45165103789](https://github.com/Vertex-Systems-Network/zynoa-2-local/actions/runs/45165103789) — scoped deterministic static review.
- [PR task-board sync #45165104083](https://github.com/Vertex-Systems-Network/zynoa-2-local/actions/runs/45165104083) and [runner #45165103555](https://github.com/Vertex-Systems-Network/zynoa-2-local/actions/runs/45165103555).

**Real Windows artifact:** `14814263091`, 18 source/build SHA-bound native screenshot + JSON pairs. The screenshot integrity gate emitted `MACHINE_METADATA_HASH_VALIDATED_ONLY`, `independent_visual_review=false`, `manifest_completed=false`. A separate [nine-image scoped visual review](../screenshots/M02/P02-T04-navigation.review.json) was created after opening the actual PNGs, verifying every listed SHA256, viewing keyboard focus and the default/swapped remapping screens. No fabricated browser screenshots or modified candidate flags.

## Remaining work assigned elsewhere — not T04 functionality

The central `docs/screenshots/MANIFEST.json` still has **15 M02** and **14 M19** final screenshot entries PENDING. Final approved option PNG paths, all-state screen-reader and pointer E2E, pixel-level focus target measurement, responsive/performance audits and full Help/Wiki release mapping belong to **P02-T10**, with broader M02/M19 acceptance under other official P02 tasks. A screenshot confirms Escape dismissed the palette, while the exact connected focused DOM node is verified by the source contract rather than independently captured pixel evidence; do not claim a full screen-reader certification.

**Source-of-truth status:** Set `P02-T04=DONE` with this exact source CI link. Keep `P02-T02=IN_PROGRESS`, the rest of P02 unchanged, and `PHASE.json.phase_status=IN_PROGRESS`. T04 closure does not authorize P03 implementation, P02 merge or release.

**Rollback:** Revert only the bounded T04 UI/accessibility/capture/tests and status changes on this same primary PR if a regression is found; session-only mapping and keyboard changes have no user-data migration.
