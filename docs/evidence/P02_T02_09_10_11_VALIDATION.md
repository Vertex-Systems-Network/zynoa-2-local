# P02-T02.09 / T02.10 / T02.11 — scoped acceptance evidence

**Scope:** M02 accessible Windows CI integration, native visual foundation review, accurate Help/Wiki and change-record evidence. These IDs are child acceptance slices from the user-facing breakdown, **not** additional official P02 task-board entries. Parent `P02-T02` remains **IN_PROGRESS**; other P02 tasks and the full release gate are not done.

## Verified source and CI

- **Exact app/test/workflow/docs source SHA:** [`4cfa2af0bd61f0b7a393f9ffdce9834f55db635c`](https://github.com/Vertex-Systems-Network/zynoa-2-local/commit/4cfa2af0bd61f0b7a393f9ffdce9834f55db635c) (later review/handoff-only commits preserve the same application source).
- **Windows Tauri:** [Actions run #45149201009](https://github.com/Vertex-Systems-Network/zynoa-2-local/actions/runs/45149201009) **SUCCESS**, including accessibility source contracts, 12 native-integrity gate tests, 8 Help/Wiki accuracy tests, TypeScript, Node UI tests, production bundle, native Rust tests, Tauri binary/cold boot, 9 PNG capture pairs, source/build SHA/PNG geometry/provenance validation and upload.
- **Governance:** [run #45149201165](https://github.com/Vertex-Systems-Network/zynoa-2-local/actions/runs/45149201165) **SUCCESS** (Linux and Windows governance).
- **PR board:** [run #45149200935](https://github.com/Vertex-Systems-Network/zynoa-2-local/actions/runs/45149200935) **SUCCESS**.
- **Runner:** [run #45149200992](https://github.com/Vertex-Systems-Network/zynoa-2-local/actions/runs/45149200992) **SUCCESS**.
- No dependencies, privileged native capabilities, persistence or external network/reporting features were added by these tasks.

## T02.09 — Windows accessibility / fail-closed native evidence CI

**Scoped outcome: DONE.** The Windows job already had P02 focus/ARIA/contrast contracts. It now also executes `tests.test_p02_native_evidence` and `tests.test_p02_help_evidence` as distinct fail-closed steps, and checks real Tauri screenshot evidence after boot through `python -m tools.verify_p02_native_evidence`. Source + test changes are in the changed-path detector, so a test-only commit cannot silently skip Windows verification.

The verifier refuses incorrect/missing native PNG/JSON pairs; mismatched screenshot ID, source SHA, built SHA, trusted capture origin, PNG SHA256 or PNG IHDR geometry; false machine `capture_verified=true`; non-visible window; missing alt text/privacy assertion; false narrow viewport; and unchanged PageDown image. Negative fixtures are synthetic **test-only**, never accepted as UI screenshots. The resulting `P02-native-machine-review.json` report has `status=MACHINE_METADATA_HASH_VALIDATED_ONLY`, `independent_visual_review=false`, `manifest_completed=false`; the machine does not approve visual content.

## T02.10 — independent native visual foundation review

**Scoped outcome: DONE for listed visible native states.** The successful Windows run produced [artifact 14805158632](https://github.com/Vertex-Systems-Network/zynoa-2-local/actions/runs/45149201009). After the CI gate passed, all 9 actual PNG images were downloaded, opened in a contact sheet and visually inspected. Each image SHA256 matched the immutable capture JSON and the built/source SHA matched the exact CI commit.

[Scoped human-inspection record](../screenshots/M02/T02-visual-foundation.review.json) binds the screenshot IDs `M02-S03`, `M02-S04`, `M02-S05`, `M02-S06`, `M02-OPT-07`, `P02-T02-06`, `P02-T02-07`, `P02-T02-07-continued` and the cross-module `M19-S01` to their hashes and precise visual findings. The Workbench focus border is visible, command palette and Preferences are legible, gallery primary selection and disabled action remain differentiated, and the real 898×653 narrow window shows responsive one-column cards without visible horizontal clipping.

**Remaining visual coverage:** `M02-S05` initially clips lower cards at the viewport fold, so `P02-T02-06` and `P02-T02-07-continued` are necessary supplemental scrolled images. There is no separately reviewed dark-theme native screenshot, pointer hover / screen-reader E2E or typed-input preservation E2E. The images are GitHub CI **candidates**, whose original receipts still say `capture_verified=false`. This scope review does **not** imply every required final screenshot is saved/accepted in the central manifest.

## T02.11 — accurate Help/Wiki and change-record references

**Scoped outcome: DONE for the source-controlled P02 preview documentation.** [M02 Help](../help/articles/M02.md) and [Wiki source](../wiki/pages/M02.md) now document every one of the **8** M02 option IDs with real defaults, controls, keyboard steps, scope and status. Implemented options include session-only Comfortable/Compact density, Follow system/Dark/Light, local command search, 25–65% split slider and built-in focus / reduced-motion behavior. Unimplemented compact properties panel and user-configurable shortcut remapping are described plainly as unavailable, not "coming soon" settings.

`tests.test_p02_help_evidence` enforces truthful defaults, option IDs, source links and `PENDING` screenshot status. The online GitHub Wiki has **not** been published or independently synced, and the canonical Markdown is not a claim that the offline Help bundle includes every final option article.

**Manifest boundary:** `docs/screenshots/MANIFEST.json` still requires **15 M02** and **14 M19** final option/screen images, all PENDING. This review does not change the manifest to DONE or satisfy full M02/P02 task completion. The [P02 foundational evidence](P02_T02_FIRST_REAL_UI_SLICE.md) and [change record](../../.changes/records/CHG-P02-M02-UI-FOUNDATION-20261123.json) retain implementation (unmerged/unreleased) status.

**Rollback / handoff:** Revert this scoped verifier/tests/CI and source docs on the same PR if a conflict appears. Existing native user storage, P01 screenshot evidence, and protected main are untouched. Verify exact-branch lease and leave it `null` after handoff; continue unfinished P02-T02 and T03–T11 without changing evidence-gated task statuses prematurely.
