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
