# Zynoa desktop foundation (P01-T03)

A Tauri 2 / Rust + React / TypeScript / Vite scaffold. This build has **no custom Tauri commands, filesystem access, user data vault, networking plugin or telemetry**. Its UI is a truthful pending-state shell, not a functional workspace or backup utility.

From apps/desktop: initially run `npm install` to resolve the pinned dependency manifest; thereafter use `npm ci`, `npm run check`, `npm run build`, `npm run tauri -- dev`. On Windows: `npm run tauri -- build --no-bundle`. Lockfiles must be committed from verified CI before treating a build as reproducible.

The frontend is locally bundled and the Vite dev server binds to loopback. Windows 10/11 WebView2 is required. Native runtime smoke, dependency lock files, screenshots, signing and recoverable user storage require their own verified evidence; no user data should be entered into the shell.

## P01-T04 read-only typed transport

The only native RPC is `workspace_handshake` for schema v1 `workspace.status`. The main-window capability explicitly permits this command through the Tauri AppManifest; unregistered commands, unknown schemas, external scopes and payload fields are denied. The handshake reports `not_configured`, and makes **no user-data, backup, filesystem or network claims**. The UI shows unavailable state if the native call errors or times out. All write/replay and user permission lifecycles are deferred to the evidence-gated security and vault tasks.

## P02 M02/M19 source implementation (ongoing, not release-ready)

The M02 workbench, reusable gallery, keyboard command palette, and M19 Help Center are bundled into the existing React/Tauri window. Global navigation shortcuts: Ctrl+1 Overview, Ctrl+2 Preferences, Ctrl+3 Recovery, Ctrl+4 Diagnostics, Ctrl+5 Workbench, Ctrl+6 Components; F1 Help Center; Ctrl+Shift+P command palette. Modal Escape returns keyboard focus. Theme system/dark/light and density comfortable/compact are **session-only** with no native preference persistence or network access. Split pane is a visual session preview only. The offline Help Center includes a bundled searchable article index, FAQ, glossary and recovery instructions; no GitHub Wiki publishing or issue reporting is implemented. Backend workspace creation, backup and restore remain disabled.

Run `npm run check`, `npm run test:ui` (pure TypeScript algorithms compiled and tested with Node), and `npm run build`. GitHub-hosted Windows CI performs the real source-bound native Tauri build, cold boot and candidate screenshots; these are not pre-certified without artifact inspection. Modules M02/M19 stay in progress until visual/a11y/documentation proof satisfies the phase gate.
