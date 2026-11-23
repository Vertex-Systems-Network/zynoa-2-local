# P02 M19 — Real functional offline knowledge workflow: exact-source validation

**Current PR:** [Draft #12](https://github.com/Vertex-Systems-Network/zynoa-2-local/pull/12), branch `phase/02-shared-ui`. **Status:** substantive application source implemented, test-verified; M19/T07–T09 final task gates remain **IN_PROGRESS**. No merge, release, P03 or hosted Wiki publication claim.

## Actual implemented user value

- **Offline corpus and versioned search:** `help-catalog.ts` contains **12** actionable bundled guides. `help-workflows.ts` exposes `requestOfflineHelp` (schema 1, catalog `2026.11-p02`), bounded query/category/limit, explicit `M19-SCHEMA-001`, `M19-CATALOG-409`, `M19-QUERY-400` rejections. HelpCenter uses that contract rather than a fabricated cloud search.
- **Usable recovery state machine:** Four deterministic issue selections, three linked recovery steps each, Previous/Next/Solved/Start over, exhausted state and linked articles. No native repair commands or hidden persistence.
- **FAQ and glossary:** Five expandable FAQs with real article routes, six glossary definitions.
- **Wiki/source link assurance:** Two trusted M02/M19 Markdown source mappings, strict `help://article/<id>` parser and link audit for article/related/FAQ/wizard/map references. No traversal, unknown route execution or remote publication.
- **Safe article reports:** Reason selector, locally generated JSON (schema/catalog/article/reason/`transmitted:false`), clipboard copy with selectable text fallback. No raw notes/files, storage, telemetry or automatic GitHub ticket.
- **Connected navigation:** In-app tabs route between article/search, wizard, FAQ and source mapping; related article controls return to real bundled articles. M19 Help and Wiki source docs updated to match existing vs unavailable features.

## Tested real code, not merely screenshots

Exact code SHA: [`0ae41bc493f4ef11e3c910c00622241be629f879`](https://github.com/Vertex-Systems-Network/zynoa-2-local/commit/0ae41bc493f4ef11e3c910c00622241be629f879). **5/5 source GitHub Actions successful**:

- [Windows Tauri run 45177798032](https://github.com/Vertex-Systems-Network/zynoa-2-local/actions/runs/45177798032): P01 safety, **9 M19 Python source contracts**, existing P02 tests, TypeScript, Node UI algorithms including seven new offline workflow tests, native Rust, actual Tauri executable/cold boot and 21 original screenshot SHA/geometry/provenance validations PASS.
- [Governance 45177797572](https://github.com/Vertex-Systems-Network/zynoa-2-local/actions/runs/45177797572) SUCCESS, [Reviewdog 45177797448](https://github.com/Vertex-Systems-Network/zynoa-2-local/actions/runs/45177797448) SUCCESS, [PR board 45177797727](https://github.com/Vertex-Systems-Network/zynoa-2-local/actions/runs/45177797727) SUCCESS, [Runner 45177797605](https://github.com/Vertex-Systems-Network/zynoa-2-local/actions/runs/45177797605) SUCCESS.
- Initial CI failure on an outdated P01 test asserting `HEAD^..HEAD` checking was **repaired, not waived**. The Windows workflow now compares the **full PR base-to-head diff** to prevent false green from docs-only handoff commits; the P01 regression test explicitly requires this stronger safety behavior.

Real M19-S01 native screenshot artifact `14819743736` was independently opened and [reviewed](../screenshots/M19/P02-M19-workflows.review.json). Image is 998×701 and SHA256 `c8e64c8033f7e551c5e0515bda868fa411feb69384d8de8b35ac96f32b861b27`, matching the source/build SHA receipt. The visible Help landing now shows **12** articles and the four functional workflow modes.

## Not-yet-accepted outcomes

The native screenshot shows **only the landing view**; it does **not** prove fully clicked-through wizard, FAQ, report or Wiki scenarios in a native E2E runner. All 14 final M19 manifest PNGs, screenshot tours, remote Wiki synchronization, actual screen-reader E2E and performance acceptance remain pending. The source candidate receipt retains `capture_verified=false`; this review is separate. T07/T08/T09 remain **IN_PROGRESS** until whole-task evidence gates are fulfilled.

**Next major development:** run real native interactive workflows (including search, wizard outcomes and Wiki invalid-link recovery), complete final M19 option/screens screenshots and integrate offline Help/Wiki publication policy, then close official T07–T09 individually. P03 is locked until P02 is `MERGED_VERIFIED`.
