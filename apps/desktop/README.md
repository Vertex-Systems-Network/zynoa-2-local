# Zynoa desktop foundation (P01-T03)

A Tauri 2 / Rust + React / TypeScript / Vite scaffold. This build has **no custom Tauri commands, filesystem access, user data vault, networking plugin or telemetry**. Its UI is a truthful pending-state shell, not a functional workspace or backup utility.

From apps/desktop: `npm ci`, `npm run check`, `npm run build`, `npm run tauri -- dev`. On Windows: `npm run tauri -- build --no-bundle`.

The frontend is locally bundled and the Vite dev server binds to loopback. Windows 10/11 WebView2 is required. Native runtime smoke, dependency lock files, screenshots, signing and recoverable user storage require their own verified evidence; no user data should be entered into the shell.
