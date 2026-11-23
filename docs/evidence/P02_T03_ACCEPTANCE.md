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

**Acceptance status:** NATIVE REVIEW ACCEPTED for the scoped T03 adaptive navigation/task requirements on exact-source Windows Tauri. This does not accept final 15 M02 or 14 M19 release PNGs or close P02.

**Rollback:** Revert App, Workbench, CSS, native capture, source tests, verifier, Help/Wiki and this evidence in same PR. No persistent user data migration was introduced.


## Windows-native blank-screen detector regression (investigated, not waived)

- [Windows run #45168992909](https://github.com/Vertex-Systems-Network/zynoa-2-local/actions/runs/45168992909) and [retry run #45170564930](https://github.com/Vertex-Systems-Network/zynoa-2-local/actions/runs/45170564930) both passed Python, TypeScript, Node UI, native Rust and Tauri build but **failed the M02-S03 screenshot step** with `ZYN-SCREEN-017`. These runs do **not** satisfy final T03 acceptance.
- The second run preserved a **diagnostic-only real WebView2 frame** `DEBUG-M02-S03.png` in artifact `14818210007`. The frame was opened and **shows a normal, legible Workbench** with the navigation correctly auto-collapsed, tab labels and runtime card visible. This is a sampling **false positive**, not a blank React render. The prior 12×10 evenly spaced grid saw **5 distinct sampled colors**; 24×16 points on the *same actual PNG* detect **21**.
- The screenshot script now samples **24×16** points for follow-up views, keeping the exact fail-closed **6-color threshold**, source/build SHA matching, PNG integrity check and bounded 3-frame retry. Persistent truly blank frames still trigger `ZYN-SCREEN-017` and upload a `DEBUG-` diagnostic for inspection; debug images **are not** part of any accepted screenshot manifest or machine-approved evidence.
- The new 24×16 test coverage is a safeguard against silently reinstating the coarse sampler. A **fresh exact-source native Windows run and independent visual review** are still required for all three T03 toggle images before T03 DONE.


## Exact-source Windows CI and independent acceptance (23 November 2026)

- **Source SHA:** `b8073122f07eb680f21c2ae42bed72207ef6a2ff`. All **5 of 5** workflow runs SUCCESS on that SHA: [Windows Tauri #45171909447](https://github.com/Vertex-Systems-Network/zynoa-2-local/actions/runs/45171909447); [Governance #45171909322](https://github.com/Vertex-Systems-Network/zynoa-2-local/actions/runs/45171909322); [Reviewdog #45171909235](https://github.com/Vertex-Systems-Network/zynoa-2-local/actions/runs/45171909235); [PR board sync #45171909094](https://github.com/Vertex-Systems-Network/zynoa-2-local/actions/runs/45171909094); [P00 runner #45171909104](https://github.com/Vertex-Systems-Network/zynoa-2-local/actions/runs/45171909104). Native Rust, TypeScript, Node UI, T03 Python regression tests (8), P02 source/help tests, actual Tauri executable build, cold boot and 21 screenshot integrity pairs PASS.
- **Artifact:** `14816693697`, actual GitHub Windows Tauri PNG and immutable metadata. Three T03 898×653 images were downloaded, **opened and independently inspected**. [Scoped visual review](../screenshots/M02/P02-T03-navigation.review.json) verifies PNG SHA256/source-build SHA against capture receipts:
  - `P02-T03-RAIL-COLLAPSED`: `6b44d38d60babbf91559f6df9d35432d3f5066fbcd6594afbeb1950579d79066`. Narrow icon rail and selected Workbench, no horizontal overflow.
  - `P02-T03-RAIL-EXPANDED`: `34db9764b4553f9284ba8d78cfad9062d37e4fe79a1fbdffab99ec3ba97831b2`. Alt+N expands labeled nav, grouped sections, current view retained; independent vertical sidebar scroll is visible.
  - `P02-T03-RAIL-RESTORED`: `b02bc29b0cd82b0b5dfff0492b011be51db6c6dafe74e639e6270a3761406931`. Second Alt+N returns to compact icon rail without leaving Workbench.
- **Visual verdict:** **PASS, scoped T03**, with accessible labels/shortcuts and pane roles additionally covered by source-level Python tests. The screenshots show visual behavior, not actual assistive technology/screen-reader-driven E2E; that remains a T10 release gate.
- **Preflight root cause resolution:** earlier `ZYN-SCREEN-017` blank false positives were due to sparse 12×10 samples on a legitimate minimal UI. Diagnostic real frame proved it rendered. Follow-up captures now take 24×16 samples without weakening the six-color minimum, and retain three bounded retries and fail-closed behavior. Earlier failed runs remain recorded as failures; only the source-aligned successful run above counts toward acceptance.
- **Task result:** Scoped requirements for T03 are implemented, checked and visually accepted. `P02-T03` may be marked **DONE** in the official PR task board. This does not claim P02-T02 final screenshot acceptance, complete T05–T11 implementation, P03 readiness, merge, or main-branch modification. Source machine captures retain `capture_verified=false` and `candidate_pending_visual_review`, with independent assessment in a separate record.

