# P02 pre-development gate — shared design system and offline Help

**Date:** 2026-11-22 (UTC) · **Baseline status:** in progress, NOT an acceptance or release receipt

## Authenticated remote source and phase lock

- Repository: https://github.com/Vertex-Systems-Network/zynoa-2-local; protected main exact SHA `f24c72eff1c4fec03a6687575ea19e9593b57a2c`.
- Prior foundation primary PR #10 verified merged at `c5fca7106942e96be2c6d07ff9938a61e7854780`; closeout PR #11 separately merged at `f24c72eff1c4fec03a6687575ea19e9593b57a2c`.
- Main committed PHASE P01/MERGED_VERIFIED with 11/11 P01 tasks DONE and empty lease. The new phase branch `phase/02-shared-ui-help` is based exclusively on that exact protected main commit.
- Last real P01 closeout CI: governed Python tests 522 PASS on reviewed closeout HEAD; main governance and Windows success, while the new independent transition-receipt job still returned BLOCKED and **no authenticated remote transition comment was published**. Do not treat that failure as a successful journal receipt.
- Existing M02/M19 dossiers explicitly say SPECIFICATION ONLY; existing M01 shell contains four views, a read-only native workspace.status handshake, and disabled workspace/recovery actions. None of the M02/M19 option surfaces are finished today. No actual performance number, new Windows screenshot or runtime accessibility pass should be claimed before respective CI.

## UX options and implementation decision

- **Option A (selected):** Extend the existing React 19 + TypeScript 5.9 + Tauri v2.12 shell using semantic CSS variables, focused components and static in-app help. Zero new runtime dependencies; preserves the P01 native Rust boundary and offline boot. Test with pinned Windows Actions.
- **Option B (rejected for now):** Introduce Fluent UI as a new React component library; attractive keyboard/a11y primitives but raises dependencies, migration effort and theme integration risk. Use Fluent 2 token principles, not its copyrighted look or assumed component behavior.
- **Option C (rejected):** Replace the shell with Electron/full code editor. Conflicts with scoped Tauri/Rust boundary and introduces unnecessary privilege/packaging exposure.
- Source references checked 2026-11-22: official [Tauri frontend docs](https://v2.tauri.app/start/frontend/), [Tauri security capabilities](https://v2.tauri.app/security/capabilities/), [Fluent 2 design tokens](https://fluent2.microsoft.design/design-tokens), [W3C APG keyboard guide](https://www.w3.org/WAI/ARIA/apg/practices/keyboard-interface/), [W3C modal dialog example](https://www.w3.org/WAI/ARIA/apg/patterns/dialog-modal/examples/dialog/). These provide patterns, **not proof of implemented accessibility**.

## Scoped flows and acceptance before code

1. **M02 tokens/themes/density:** reversible local-only UI preferences (no secrets), validated persisted values with corruption fallback, first-run dark default, theme contrast, density, large text/keyboard focus and reduced-motion support.
2. **M02 workbench:** Overview, Settings, Recovery and Diagnostics retain truthful P01 native status. Add Help, component gallery, and command palette for implemented navigation/actions only. Ctrl+K opens search; Escape closes; Tab stays in the dialog; Enter executes selected command. Existing Ctrl+1–4 behavior continues; shortcuts must not steal focus from editable controls.
3. **M19 offline Help:** versioned typed article entries rooted in audited packaged sources; safe plain text, no HTML/remote fetch and no untrusted execution, index search with normalized query/ranking and safe empty/error results. User can read Help without native transport, from browser preview or desktop window.
4. **M19 help linking:** control-level Help routes, Getting Started, keyboard shortcuts, offline capabilities and clear troubleshooting. Wiki source remains versioned documentation; **do not claim remote GitHub Wiki is published** until verified.
5. **Real verification:** Python contract tests of source structure and negative paths, TypeScript tsc/Vite bundle, native Windows Tauri cold boot, actual screenshot capture with SHA index, a11y/keyboard and error/recovery smoke. Only mark task DONE with actual CI evidence.
6. **Performance baseline and rollback:** record cold boot/shell UI/Help search performance via actual runner not fiction; no destructive migration, no download or user data overwrite. Revert scoped frontend/doc commit to restore P01 shell, preserving native vault and IPC.

## Security/privacy boundary

- Never add arbitrary WebView-to-Rust privileged commands, remote HTML injection, telemetry or write permissions while delivering a UI layer.
- Help is in bundle and must be safe for offline display; user queries remain local. No network authorization, GitHub writes or credential storage from frontend.
- Future workspace creation/recovery operations remain disabled until backed by native service and independently tested recovery contract.
- Issue #3 P00 permanent-host/autonomy remains OPEN and labelled phase:P00/merge:blocker; #2 is deferred P08I blocker; #4 original P00 transition receipt remains unverified. Do not reclassify merely to pass P02.
