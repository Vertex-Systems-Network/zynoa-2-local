# ADR-0026 — P02 shared UI / Help Center pre-development gate

**Date:** 2026-11-22 UTC · **Task:** P02-T01 · **Scope:** M02 (GUI tokens, shell, command palette, keyboard accessibility) + M19 (bundled offline Help Center). **Decision:** accept incremental dependency-free design system over visual-only mockups. **State:** design proposal under evidence-gated draft PR, *not a shipped final UI*.

## Evidence / baseline
- Protected repository `Vertex-Systems-Network/zynoa-2-local`, prior P01 closeout merged to `main` at `f24c72eff1c4fec03a6687575ea19e9593b57a2c`, P01 11/11, `MERGED_VERIFIED`, lease clear before kickoff. P02 isolated branch `phase/02-shared-ui`; expected primary draft PR #12 (verify actual remote number).
- P01 application already has pinned React 19.2.0, Vite 7.2.2, TypeScript 5.9.3, Tauri CLI 2.12.6 and Rust app. No new dependency justified in P02 foundation. Exact dependency versions read from repository package.json; no assertion that a local Windows build was run by this agent.
- Existing App.tsx has overview/settings/recovery/diagnostics, read-only `workspace_handshake`, no account/workspace writing. Existing UI lacks true shared token sheet, command palette, view-role-based tabbed workbench, usable appearance settings, global offline article reader, and keyboard/focus tests. P01 Windows screenshot evidence proves only limited read-only foundation states; no P02 screenshots exist yet.
- Remote main Governance and Windows checks success at [P01 closeout #45066568376](https://github.com/Vertex-Systems-Network/zynoa-2-local/actions/runs/45066568376); separate receipt check failed closed on absent verified issue-inventory/other preconditions and remains independently unresolved. **Do not claim externally published phase receipt or installed UI.**
- New P02 issues: currently none with `phase:P02` blocker; historical P00 #3 open and unverified, P08I #2 future blocker. Refresh live issue inventory per merge.
- Performance baseline is **NOT MEASURED** for P02 UI startup, palette latency, search, contrast or actual native screenshots; use measurable Windows-hosted CI later rather than estimated claims. External dependencies/licenses: no new packages.

## Real UX comparison / sources (official, checked 2026-11-22)
| Comparator | Evidence | Pattern used | Tradeoff |
| --- | --- | --- | --- |
| VS Code Workbench | https://code.visualstudio.com/docs/editing/getting-started/userinterface ; https://code.visualstudio.com/docs/configure/accessibility/accessibility | Predictable navigation, Ctrl+Shift+P command palette, Ctrl+K shortcuts, focus restore, offline-first shell | Reuse keyboard/navigation semantics, do **not** mimic code editor feature claims |
| Figma variables/modes | https://help.figma.com/hc/en-us/articles/14506821864087-Overview-of-variables-collections-and-modes | Semantic color/spacing aliases, light/dark/system modes with reusable component states | P02 is app UI; Figma-like user design canvas belongs to P08 |
| Penpot token system | https://help.penpot.app/user-guide/design-systems/design-tokens/ ; https://help.penpot.app/user-guide/design-systems/components/ | Composable theme primitives, named states; CSS custom properties instead of hard-coded per-component values | Do not implement Penpot import/export or external license-dependent adapters |
| W3C APG Tabs/Focus | https://www.w3.org/WAI/ARIA/apg/patterns/tabs/ ; https://www.w3.org/WAI/ARIA/apg/practices/keyboard-interface/ | Native buttons and meaningful focus; arrow-key tablist and modal palette dialog focus restitution | Requires deterministic tests and real keyboard smoke; aria roles alone are insufficient |

**Alternatives considered:** A) install large UI/component framework + icon/fonts: faster scaffolding but new supply chain, version and bundle costs, and less reliable native keyboard semantics. B) hand-crafted semantically named CSS tokens and minimal typed React components: no new dependency, direct accessible state control, safe native IPC isolation, and matches existing layout; **select B**. For Help: A) fetch GitHub Wiki live: fails offline and makes external docs a runtime dependency; B) build a versioned, bundled, validated article/search index referencing local curated help sources: **select B**. Live wiki links must be an optional explicit user action with offline explanation, never silent telemetry.

## Contract and threat delta
- M02 local-only UI state: typechecked `Theme = dark|light|system`; `Density = comfortable|compact`; `View` enum; no fake persistence. Default follows system setting; user choices are **session-scoped until a verified native settings service exists**. No filesystem, account, network, or additional Tauri capability is granted.
- M19 indexed static `id/title/category/summary/keywords/body` entries curated in source, max query length, deterministic ranking, case-insensitive and no remote search, no untrusted HTML via `dangerouslySetInnerHTML`, no PII reporting. Links to GitHub Wiki require user activation and explicit online/no-warranty label; never claim remote Wiki publication.
- Navigation/commands only route between existing implemented/pending sections; actions for nonexistent features remain disabled. Modal command palette traps tab/focus appropriately, Escape closes, focus returns to prior control. Typing into editable inputs must not trigger global shortcuts.
- Error/empty/loading/offline/disabled styles need screen-reader feedback and real screenshot proof; escape/sanitize search text as plain React text. CSP of Tauri remains unchanged.
- Dependency inventory unchanged. No schema migration. Rollback revert P02 branch commits; prior P01 vault & stored user data untouched.

## Tests defined before implementation
1. Governance Python unit source policy: tokens, command palette focus restore, no network/persistence/API escalation, M02/M19 option IDs and no fabricated actions.
2. TypeScript compilation and Vite bundle on trusted Windows runner; cold-boot Tauri executable with actually captured screenshots for M02/M19 (P02 screenshot requirement still **pending** until CI outputs).
3. User paths: nav -> command palette -> Help -> article; keyboard Escape and Ctrl+Shift+P; theme/density switch, system mode fallback, no local writes; search exact/partial/empty/gibberish and recovery.
4. Native/security negative: blocked workspace write and remote telemetry; no additional capabilities. Docs/wiki link resolution and image screenshot manifest verified against exact CI commit.
5. Performance: record native cold boot and palette/search timings from real runs, then set acceptance budgets; avoid invented numbers.
6. Full governance + versioned verifiers + 522+ baseline Python tests; browser-level a11y + screenshot review before P02 module tasks can be declared DONE.

**Retries/rollback:** At most 2 bounded fixes for any new CI root cause before logging a clear blocker and continuing other safe tasks. Never make failing jobs optional merely to force green. Release and merge gates unchanged.
