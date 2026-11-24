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
