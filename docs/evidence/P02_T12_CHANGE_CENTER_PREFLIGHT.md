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
