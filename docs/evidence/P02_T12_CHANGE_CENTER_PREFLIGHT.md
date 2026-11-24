# P02-T12 — M26 integrated shared UI first slice

**Issue:** [#16](https://github.com/Vertex-Systems-Network/zynoa-2-local/issues/16). Existing P02 v3.2 obligation; T12 IN_PROGRESS. **Scope:** shared UI foundation only, not P11 signed release publication. Source baseline `1abb1696f30086e015af15416f59f2d28fb94604`. Plan authority: MASTER_PLAN_V3_2, PHASE_SPECS v3.2, M26 dossier and existing append-only event-store contract. Existing six remappable navigation shortcuts preserved.

## Design choice and test plan

Alternatives: integrate within Help (less discoverable; mixes release state with support content), dedicated System navigation and fixed command-palette view (selected, independent semantic region, reuses native button/tab/focus design), or native data-backed live feed (requires unapproved query/release privileges and later services, rejected for this slice). Existing design-system tokens, responsive filter grid, standard keyboard tab behavior; no new dependencies, network, persisted preferences, or native IPC grant. Reuses read-only actual local runtime status and bundled allowlisted capability limitations, explicitly not live issue data.

| Existing obligation | Source slice | Acceptance still required |
|---|---|---|
| M26-S01 What's New | No verified releases / signed data unavailable; disabled check | Native capture, keyboard/speech, real future verified feed in P11 |
| M26-S02 Known Issues | Bounded search/module filter and selected bundled limitation, empty result | Native selection/capture and Help; no live issue inventory claim |
| M26-S03 Version History | Empty verified history, disabled comparison | Native capture and keyboard; actual version comparison after signed feed |
| M26-S04 / S05 Change detail and module history | Actual bundled notice detail and module filtered view | Native screenshot/option review; not actual released history |
| M26-S06/S07/S08 audit timeline/preferences/migration | Explicit service limitations only | Scope/controls design reconciliation and appropriate phase evidence pending; no completion claim |

T12 must still reconcile every applicable M26 screen/option obligation, add actual shared state rendering where missing, verify real Windows UIA, keyboard and spoken feedback, capture actual source-bound PNGs with independent review and reconcile Help/Wiki publication. No sample release data as proof. Existing M02/M19 29-image and Narrator gates remain intact. Test plan: TypeScript build and node UI-logic tests (filter/no-match, bounded allowlisted data, no false availability, navigation and Help), Python source regression, governance, actual Windows. No real new screenshots or test PASS asserted at this checkpoint.

## Prior CI failure triage

Previous plan-alignment Windows #45327284868 and governance #45327284903 failed obsolete test pin to actions/upload-artifact@v4. Corrected test to match approved v6, leaving read-only permissions and exact build/artifact checks in place. Isolated Narrator #45327285027 failed Preferences native focus readiness; one bounded clean app relaunch before speech only, genuine exact-head acceptance still required.

## Next deterministic action

Fresh exact-head CI, diagnose any actual failure. Add T12 native M26 screen and option captures and dedicated state/a11y checks; do not mark T12 done from source tests alone. T13 and T11 remain open. No P03.

## 2026-11-24 — exact-head CI readback and option reconciliation

Manual connector readback at `d3b7909aa24f3f322f700a58227df83ae332ab00`. All seven associated PR workflows completed successfully: [Windows](https://github.com/Vertex-Systems-Network/zynoa-2-local/actions/runs/45328365299), [Narrator diagnostic](https://github.com/Vertex-Systems-Network/zynoa-2-local/actions/runs/45328365368), [Wiki browser](https://github.com/Vertex-Systems-Network/zynoa-2-local/actions/runs/45328365313), [Governance](https://github.com/Vertex-Systems-Network/zynoa-2-local/actions/runs/45328365310), [Reviewdog](https://github.com/Vertex-Systems-Network/zynoa-2-local/actions/runs/45328365321), [task sync](https://github.com/Vertex-Systems-Network/zynoa-2-local/actions/runs/45328365437), [runner](https://github.com/Vertex-Systems-Network/zynoa-2-local/actions/runs/45328365418). Windows job 138223364250 reports successful TypeScript, UI algorithms, production bundle, native build, existing T10/NVDA and T11 Narrator checks. Artifact 14891705655 exists; its image bytes were not inspected in this slice. Existing successful tests do not independently establish M26 native acceptance. Local checkout, package versions and local tests were not available through this connector-only slice; no new runtime source changes.

### Exact option inventory (M26-OPT prefix)

| ID | Source truth at audited SHA | Next acceptance action |
|---|---|---|
| 01 | No release/channel filter; no verified versions | Design unavailable state, capture; live data after publisher |
| 02 | Module selector defaults All; M23–M26 allowlist; clears selected notice | Native select/filter/reset and capture |
| 03 | No category filter; notices are capability limitations only | Design unavailable state, no invented categories |
| 04 | No audience switch or authorized audit data | Explain privilege boundary; never expose private events |
| 05 | Notice-only search, 120-character bound, AND words, case-insensitive, empty/no-match | Native type/no-match/reset and capture; do not imply signed feed search |
| 06 | No verified issue link | Unavailable state; no unverified URL |
| 07 | No verified PR link or merge receipt | Unavailable state; no unverified URL |
| 08 | Contextual Help button/F1; no verified per-release documentation revision | Native Help journey and Wiki source/publication review |
| 09 | No release date/badge, feed absent | Capture truthful unavailable state |
| 10 | Known Issues tab lists bundled capability limitations, not actual open issue data | Native tab and detail capture; distinguish limitations |
| 11 | No verified fixed issues | Explain unavailable released fixes |
| 12 | Module Changes tab uses same limitation filter, not historical releases | Native module selection and detail capture |
| 13 | No notification setting or signed feed | UI boundary only; later persistence |
| 14 | No release migration data | Design unavailable state and contextual guidance |
| 15 | No audit query or scope authorization | UI boundary only; no private data |
| 16 | Export not enabled | UI boundary only; no sensitive export |
| 17 | Disabled Compare versions button | Native disabled semantics and explanation |
| 18 | No release-specific recovery data | Contextual safe guidance, no executable rollback |
| 19 | No unread marker persistence | UI boundary only; later verified feed |
| 20 | No report-from-change service | Explain unavailable operation; no remote write |

### Next native evidence design

Use actual System → Changelog navigation; assert app PID, named tab controls, focus and selected states, then capture S01/S02/S03/S04/S05. For implemented options, use real module selection, real query text, no-match, reset, notice detail, arrow/Home/End navigation and F1 contextual Help. Verify no fabricated data in each view. Test pending/connected/unavailable/preview transport labels without equating transport readiness with release readiness. Preserve existing native budget and screenshot provenance; if the existing suite cannot fit, use a separate bounded M26 capture job rather than weaken existing gates. S06–S08 and unavailable option surfaces require scope reconciliation and accessible state design; never mark them implemented on the basis of this inventory. Independently review original PNGs, UIA and actual spoken feedback, and verify hosted M26 Wiki before task completion.

Change record: `CHG-P02-M26-CHANGE-CENTER-20261124` (implementing, developer-only, no release). T12 IN_PROGRESS; #16 open. T13 TODO; #17 open. T11 IN_PROGRESS. No phase/merge/release claim.

## M26 service-boundary source slice

Baseline `0aad9772895b916f7ddc326d9a02bd7a12a93f97`: all seven associated workflows completed successfully; [Governance](https://github.com/Vertex-Systems-Network/zynoa-2-local/actions/runs/45329561800), [Windows](https://github.com/Vertex-Systems-Network/zynoa-2-local/actions/runs/45329561856). This is baseline only, not new implementation acceptance. Existing pinned React 19.2.0 / TypeScript 5.9.3 / Tauri 2.12.6 package inventory and ADR-0026 unchanged. Reuse the previously researched WAI-ARIA tabs pattern rather than placing unlabelled disabled actions in a single panel or introducing an external widget dependency. New audit/notification/migration panels remain readable without privileges; no fake loading, release, migration or persistence. Tab focus remains roving; inactive panels leave sequential focus. Disabled buttons have visible reasons. No new IPC, network, user files, dependency, schema or storage changes. Acceptance: node allowlist/absence of release-data tests, Python source contracts, existing governance and native suite, then dedicated native M26 keyboard/visual/speech and hosted Wiki evidence. This slice does not extend or weaken the existing screenshot budget. No local package install or tests executed via connector. Next: exact-head CI readback and dedicated M26 evidence suite; #16 stays open.

## M26 native candidate suite source implementation

Reuse existing native DWM capture and no-overwrite/hash safeguards in isolated M26Only mode on a fresh process; no enlargement of existing timed 69-frame suite. Exact source/build/run ID, foreground HWND, UIA root PID, named visible panel markers, real tab-arrow/Home/End focus, actual input ValuePattern, disabled controls and F1 Help journey. Ten candidates only (eight screens, search-empty and Help). Separate Python verifier denies missing, duplicate, wrong SHA/run, wrong geometry/hash and false visual/speech approval. No local Windows execution; previous head Windows run 45331186648 was still running at preflight. New exact-head CI and independent original PNG review, further option captures and real spoken feedback remain necessary. No new dependencies, privileges or runtime source changes.

## Exact-head NVDA regression and independent M26 execution

[Windows #45331538975](https://github.com/Vertex-Systems-Network/zynoa-2-local/actions/runs/45331538975) at `52945096de7b602c90e8b62840b55d48cd056009`: M26 source tests, TypeScript, native build, existing screenshot/UIA and performance gates succeeded; existing live NVDA failed `ZYN-NVDA-010` (named command search absent), before typing. M26 and subsequent acceptance stages skipped. [Issue #19](https://github.com/Vertex-Systems-Network/zynoa-2-local/issues/19) tracks the regression. The observed failure does not establish whether stale UIA, focus or shortcut delivery caused the absence. Candidate repair uses fresh PID-verified UIA roots, verified foreground, bounded search retries and actual named toolbar Invoke fallback. No change to three-stage speech verifier, real input ValuePattern or required labels. Independent M26 capture now executes after a successful native build even when an earlier verification step fails, while the job still fails on any failing gate. Cancelled runs never execute it. No permission change, fake receipts or release claims. Fresh exact-source CI required.

## Exact-head first M26 native frame and visual-driven repair

[Windows #45332866611](https://github.com/Vertex-Systems-Network/zynoa-2-local/actions/runs/45332866611) at `df0396056df10278b9505c968724c02e1f8f5b66`: six companion workflows passed; scoped NVDA and Narrator receipts independently read from original artifact 14892613992 (NVDA 6 events, Narrator 4 stages). M26 produced S01, then failed `ZYN-M26-004: required native control absent: Select a capability notice` after the keyboard transition to Known Issues. Downloaded original artifact, extracted S01 998x701 PNG, recomputed SHA-256 `155aee7c3f86361a5bb009c64a4d2ef60ec474fbcf96d98182e958be63a14971` matching its receipt. Visual inspection: oversized header/stacked Help action and wrapped tabs consume most of the native viewport; only top of release panel and heading visible; no final image approval. S02 not captured; offscreen detail is plausible, not proven cause. Compact M26-specific spacing, adaptive filter/detail grid and heading programmatic focus targets preserve 44px tabs, no new runtime privileges. Candidate harness uses bounded actual UIA ScrollItem or focus to reveal an offscreen marker and requires visible exact marker before and after capture; no self-approval or skipped gate. New exact-head CI required. T12 only, T13 untouched.

## Exact-head tab focus regression and repair

[Windows #45334807699](https://github.com/Vertex-Systems-Network/zynoa-2-local/actions/runs/45334807699) at `0a6c1c1d3e9b4f1d946ee8b5e093911916ce964c`: six companion workflows passed, native NVDA/Narrator passed, M26 S01 candidate generated; first Right Arrow failed `ZYN-M26-005` before Known Issues candidate. No S02–S08/Help image approval. The log proves failed focus observation, not exact cause. React roving tab focus now occurs after active/aria-selected commit using layout effect; same-tab Home/End focus remains immediate. Explicit accessible filter labels. Native harness requires real UIA TabItem SelectionItemPattern and HasKeyboardFocus at source and destination, waits boundedly for provider transitions, verifies previous selection clears, records seven exact real key transitions and rejects absent/mismatched evidence. No destination click, synthetic focus receipt or skipped gate. Only T12; new exact-head CI required.

## Exact-head module filter failure and independent image review

[Windows #45337382017](https://github.com/Vertex-Systems-Network/zynoa-2-local/actions/runs/45337382017) at `074b62e01b95b7505824aad7d9863ad9d5032dc4`: six companion workflows green; existing NVDA and Narrator passed; actual selected-focus keyboard transitions What's New → Known Issues → Version History → Module Changes passed. S01, S02, search-empty, S04 and S03 captured. S05 stopped at `ZYN-M26-004` exact status text after module selection; this does not prove whether selection or provider status text failed. Original artifact 14894612786 downloaded; five actual 998×701 images each recomputed SHA-256 matching individual metadata and exact source SHA. Visual review shows correct distinct release/no-match/detail/version states, but S01 fourth action, S02 last notice and S04 disabled actions require scroll evidence. No final image approval. New native filter gate reads actual UIA selector value (ValuePattern/SelectionPattern) and exact named notice button inventory before selection, after real keyboard selection and after Reset filters. Bounded alternate real keyboard dropdown interaction if collapsed selection fails; no direct JS state setter or fake count. Added strict receipt validation and negative tests. Remaining S06–S08/Help, full option/scroll and spoken evidence and hosted M26 Wiki still required. No T13 work. Fresh exact-head CI required.

## Exact-head independent duplicate and M26 detail regressions

[Windows #45341091895](https://github.com/Vertex-Systems-Network/zynoa-2-local/actions/runs/45341091895) at `b6b12b117fdd70a4e5800bbf5b2c21697ee60c72`: six companion workflows and M26 source tests passed; existing screenshot verifier rejected duplicate T10 actual-control frames (ZYN-SCREEN-030). Downloaded original artifact 14896007891: `P02-T10-CTRL-M19-OPT-04` and `P02-T10-CTRL-M19-OPT-08` share SHA-256 `e09883479992dfefefb23ee553189a40ec5e8db4e6ae92fa9af5ca030205e837`; inspected OPT-04 PNG shows Articles & search rather than glossary. Scoped repair invokes the actual native FAQ/glossary mode and requires real visible glossary heading before capture. Existing 69-image suite, duplicate detector and time budget unchanged. Independent M26 still ran: S01/S02/search-empty captured; S04 detail marker absent, S05 filter gate not reached. Original search-empty PNG correctly shows typed zzznomatch, zero notices and reset. New M26 focus checks re-read actual focus state, validate empty query after reset, require a genuine focused native button and Enter plus real detail marker; receipt rejects incorrect reset/activation. Exact-head CI required; no acceptance, no T13 work.

## Exact-head glossary activation and native foreground failure (manual connector repair)

[Windows #45342196065](https://github.com/Vertex-Systems-Network/zynoa-2-local/actions/runs/45342196065), source `f1b398dbf009ef7cca1110a643877545e9b15357`, job 138268355806: six companion workflows succeeded; Windows failed ZYN-SCREEN-045 (actual glossary mode activation), and independent M26 failed ZYN-M26-002 after three successful real tab transitions (through Module Changes). Logs do not prove the cause of foreground loss. Candidate repair uses real UIA focus and keyboard activation for aria-pressed Help workflow buttons rather than assuming InvokePattern, and submits one complete keyboard select gesture from the verified app foreground, then waits for exact foreground return before reading the actual selected module and notice inventory. Alternative: weaken foreground/duplicate checks (rejected); direct React/DOM state mutation (rejected). No dependency, permission, app runtime, data or storage changes; existing screenshot and performance checks unchanged. Source contract regression added; no local Windows execution or new passing result claimed. Fresh CI and independent M26 screenshots, option coverage, speech and hosted Wiki proof remain required; T12 IN_PROGRESS, T13 TODO. Manual connector-only lease, not an autonomous worker.
