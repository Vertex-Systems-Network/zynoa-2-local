# P02 — First working M02/M19 desktop UI slice

**Status:** implementation proposed in Draft PR #12; **all CI and native screenshot outcomes pending** on this first source commit.

- Repo/branch: `Vertex-Systems-Network/zynoa-2-local` / `phase/02-shared-ui`; trusted prior P01 closeout protected main `f24c72eff1c4fec03a6687575ea19e9593b57a2c`, P01 11/11 verified.
- Modules: M02 shared design system/workbench, M19 offline help. Existing P01 native read-only `workspace_handshake`, user data vault, restrictions and CSP must not change.
- M02 implementation paths: `src/ui/theme.ts`, `src/ui/commands.ts`, `src/ui/CommandPalette.tsx`, `src/ui/Workbench.tsx`, `src/App.tsx`, `src/styles.css`. Provides theme/density from state (not persisted), semantic dark/light tokens, command search/keyboard, workbench tab roles and split slider, gallery interactive state examples and disabled non-backed controls.
- M19 implementation paths: `src/ui/help-catalog.ts`, `src/ui/HelpCenter.tsx`. Seven bundled curated help articles, search/category ranking, related navigation, glossary, FAQ, native/offline troubleshooting; intentionally no fetch, HTML injection, data upload, remote wiki write or reporting action.
- Tests: `apps/desktop/tests/ui-logic.test.mjs` pure TypeScript semantic search/token tests, `tests/test_p02_ui_contract.py` source/IPC/a11y tests, existing P01 regression suite, Windows native Tauri build. P02 native candidates will be captured via the existing SHA-pinned `scripts/capture_p01_desktop.ps1`, invoked by read-only `p01-desktop.yml` only for `phase/02-shared-ui`. New screenshots `M02-S03`, `M02-S05`, `M02-S06`, `M02-S04`, `M19-S01` are **candidate_pending_visual_review** with `capture_verified=false`. Additional M02/M19 option/state screenshots remain pending.
- T01 research: [ADR-0026](../adr/0026-p02-shared-ui-help-predev.md), official VS Code command palette, WAI-ARIA keyboard/focus, Figma and Penpot token systems. Alternative UI framework dependency rejected for no-supply-chain source slice.
- Rollback: revert these P02-only source/CI/docs files; no user data or native capabilities changed. No P03 or release.
- **Open risks and TODO:** native Windows compile may find TypeScript errors; actual visuals/keyboard automation must be inspected, preferences are not persisted, native Wiki external-link launch and issue feedback are not available, Help source mapping and full screenshot acceptance remain. Do not mark M02/M19 final based on this stage.

## Exact-source CI and screenshot failure analysis — 2026-11-22 UTC

Source commit [`6b0048e`](https://github.com/Vertex-Systems-Network/zynoa-2-local/commit/6b0048e9927e22ea0814b993b6e31fcf5bcaa656) has real [Governance #45068687082](https://github.com/Vertex-Systems-Network/zynoa-2-local/actions/runs/45068687082) **SUCCESS**, 528 Python unit tests and 21 governance tests PASS, with two validated structured records and trusted task-board sync. Windows workspace governance SUCCESS. Actual [native Windows job #45068687035](https://github.com/Vertex-Systems-Network/zynoa-2-local/actions/runs/45068687035) produced successful pinned `npm run check`, `npm run test:ui` (six Node pure-logic tests), `npm run build`, Rust `cargo test --lib --release` and full Tauri `build --no-bundle`. It then hit `ZYN-SCREEN-008: refuse replacing existing image` in `scripts/capture_p01_desktop.ps1:111` because P01's original `docs/screenshots/M01/M01-S01.png` **already exists in the version-controlled checkout**. This is a genuine and correct protection, not a native-build failure.

**Selected fix:** leave original P01 screenshot evidence untouched. For P02 source run, set actual native capture directory to `docs/screenshots/_ci/M01` with M02/M19 corresponding siblings and add them to artifact upload; no image overwritten. Source/build SHA and the native-window pixel/visibility contracts stay unchanged; file collisions still fail. Documented a Python regression for distinct CI paths and retained no-overwrite checks. First run's native screenshot capture was **not successful**. The next GitHub Windows job must produce original PNG + sha256/source metadata and candidates must be inspected before any capture can be accepted. The new WAI-ARIA improvements add stable tabpanel IDs and combobox focus target validation; TypeScript re-build pending.

**P02 progress:** T01 predevelopment source/CI verified; T02 semantic UI source in progress; other full module acceptance tasks remain outstanding. No fake completion of M02/M19 or later phases.


## M02-OPT-07 / P02-T02.04 keyboard-focus repair (2026-11-23)

- Source bug: each Workbench `role="tabpanel"` is keyboard-focusable, yet `:focus { outline:none; }` hid the visual indicator.
- Fix commit [4297822](https://github.com/Vertex-Systems-Network/zynoa-2-local/commit/4297822dac25a9a99a2d85e1218847e7d0fe77be): 2px `:focus-visible` ring with 3px offset using the existing light/dark `--outline` token.
- Regression [c6d3dcc](https://github.com/Vertex-Systems-Network/zynoa-2-local/commit/c6d3dcc0d9a9d85cb6377879d01d8aed1ab8b965): Python contracts for keyboard-focusable panels, ≥3:1 focus-token contrast on five semantic surfaces and fail-closed capture provenance.
- Windows gate [f005887](https://github.com/Vertex-Systems-Network/zynoa-2-local/commit/f005887a02675dea9f9873c9d0a3a4d07014e4cc) runs Python P02 UI contracts as a separate step and tracks test-only changes.
- Capture [d71ff6f](https://github.com/Vertex-Systems-Network/zynoa-2-local/commit/d71ff6fb9f0bb5d87e94163615de1b48c4cac058): real Tauri `M02-OPT-07` candidate after keyboard Tab traversal; metadata remains `candidate_pending_visual_review` and `capture_verified=false` until a separate visual inspection.
- Help and Wiki M02-OPT-07 instructions updated. No stored preferences, user data migrations, external services or new dependencies.
- **Checkpoint:** code and native evidence instrumentation committed. Windows CI and independent visible focus ring inspection determine acceptance. P02-T02 parent task remains IN_PROGRESS; no P02 merge/release claim.
