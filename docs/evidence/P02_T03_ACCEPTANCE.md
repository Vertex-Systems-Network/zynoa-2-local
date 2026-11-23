# P02-T03 — Adaptive navigation, workspace shell and pane layout

**Task board:** `P02-T03` is IN_PROGRESS until its exact-source Windows CI and independent native visual review are accepted. This is a **whole official task** acceptance record, not a separate phase or additional P02 child ID.

**Primary work location:** existing Draft [PR #12](https://github.com/Vertex-Systems-Network/zynoa-2-local/pull/12), `phase/02-shared-ui`. Source-only changes do not imply a real user workspace service or merge/release.

## Implementation and constraints

| Feature | Real implementation | Boundary |
| --- | --- | --- |
| Navigation rail | Sidebar auto-collapses to a 78px rail at <=1000px viewport, including 900px native minimum; expands on wider windows | Browser and Tauri use a CSS media query match; no saved preference |
| Keyboard and pointer control | Accessible toggle button with `aria-expanded`, `aria-controls`, dynamic label and Alt+N shortcut | Keyboard shortcut is suppressed in text/select controls and modal palette; no OS-global hook |
| Active page and shortcuts | `aria-current=page` retained, fully named icon buttons, explicit navigation sections, dynamic Ctrl+1–6 labels | No duplicate routing or privilege escalation |
| Workspace semantics | Primary navigation landmark, breadcrumb navigation landmark, main content and footer | Project creation and real canvas remain unavailable |
| Structured pane layout | Named Workbench tabpanels, two separate named preview regions, split slider bounded 25–65% | Demo layout only; no real files, persistence or backend service |
| Responsive sizing | Native window 900px minimum; manual expanded rail still scrollable; content and cards use bounded `minmax` columns | Smaller browser preview is not native proof |

## Verification requirements

- Source tests `python -m unittest tests.test_p02_t03_navigation -v` must pass on Windows and in governance's test discovery. Existing T02, P01, TypeScript, Node UI, Rust, Help/Wiki and Reviewdog gates must remain green.
- Windows native capture script must produce actual *measured* ~898px-wide Tauri PNG and metadata pairs `P02-T03-RAIL-COLLAPSED`, `P02-T03-RAIL-EXPANDED` and `P02-T03-RAIL-RESTORED`. Machine verifier must reject missing pairs, incorrect source/build SHA, PNG SHA256 mismatch, wide/fake frames and identical toggled screenshots.
- An independent visual reviewer must confirm the first and last image have the icon rail and that the middle image has readable text labels, with the Workbench active and no horizontal clipping at narrow width. Original machine receipts remain `capture_verified=false`; review is a separate source-controlled record.
- Only after the exact-source CI and visual review, `P02-T03` may become DONE. `P02-T02`, screenshot manifest final M02/M19 option approvals and T05–T11 remain separate incomplete tasks. No P03 work is permitted without verified P02 merge.

**Manifest boundary:** All 15 final M02 manifest entries remain PENDING, and the M19 screenshots are separate T10 release requirements. T03 scoped candidate images never self-approve final asset paths.

**Status at authoring:** IMPLEMENTED IN SOURCE — NATIVE RUN AND REVIEW PENDING.

**Rollback:** Revert App, Workbench, CSS, native capture, source tests, verifier, Help/Wiki and this evidence in same PR. No persistent user data migration was introduced.


## Windows-native blank-screen detector regression (investigated, not waived)

- [Windows run #45168992909](https://github.com/Vertex-Systems-Network/zynoa-2-local/actions/runs/45168992909) and [retry run #45170564930](https://github.com/Vertex-Systems-Network/zynoa-2-local/actions/runs/45170564930) both passed Python, TypeScript, Node UI, native Rust and Tauri build but **failed the M02-S03 screenshot step** with `ZYN-SCREEN-017`. These runs do **not** satisfy final T03 acceptance.
- The second run preserved a **diagnostic-only real WebView2 frame** `DEBUG-M02-S03.png` in artifact `14818210007`. The frame was opened and **shows a normal, legible Workbench** with the navigation correctly auto-collapsed, tab labels and runtime card visible. This is a sampling **false positive**, not a blank React render. The prior 12×10 evenly spaced grid saw **5 distinct sampled colors**; 24×16 points on the *same actual PNG* detect **21**.
- The screenshot script now samples **24×16** points for follow-up views, keeping the exact fail-closed **6-color threshold**, source/build SHA matching, PNG integrity check and bounded 3-frame retry. Persistent truly blank frames still trigger `ZYN-SCREEN-017` and upload a `DEBUG-` diagnostic for inspection; debug images **are not** part of any accepted screenshot manifest or machine-approved evidence.
- The new 24×16 test coverage is a safeguard against silently reinstating the coarse sampler. A **fresh exact-source native Windows run and independent visual review** are still required for all three T03 toggle images before T03 DONE.
