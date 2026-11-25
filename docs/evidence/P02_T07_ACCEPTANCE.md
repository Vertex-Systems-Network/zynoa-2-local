# P02-T07 — Bundled offline article catalog and versioned search acceptance

**Official task:** P02-T07 · **Status:** DONE for its scoped offline-catalog/search contract only.
**Branch/PR:** `phase/02-shared-ui` / [Draft PR #12](https://github.com/Vertex-Systems-Network/zynoa-2-local/pull/12).
**Independent native source:** `da648baae21477cae44041ee0cbe99f8fc75f347`, [successful Windows run #45186464263](https://github.com/Vertex-Systems-Network/zynoa-2-local/actions/runs/45186464263), artifact `14824706339`.

## Delivered interface and boundaries

- Twelve bundled article objects and an offline-only typed search contract with schema `1`, catalog `2026.11-p02`, max 120-character query, category filter and bounded 1–50 results.
- Deterministic local ranking and safe empty/no-results state. Unknown schema, stale catalog and malformed requests fail closed with `M19-SCHEMA-001`, `M19-CATALOG-409` and `M19-QUERY-400`.
- Search and article selection render only the current filtered matches; contextual/related navigation clears incompatible filters. Browser storage, remote Help search, arbitrary script invocation and cloud telemetry remain absent.

## Verified evidence

1. Windows source/contract, TypeScript, Node UI algorithms, native Rust, production bundle and Tauri desktop cold boot passed in run #45186464263. A failed test would fail the Windows job, not be masked by later build steps.
2. Real Windows `M19-S01` and `M19-S02` native PNGs were downloaded and opened, hashes independently checked against immutable receipts. `M19-S02` visibly contains the typed query **theme**, two local results, an offline catalog label and the matching article view. SHA256 `fdb41c3e4e4bab499544e251480a550be3e3d7d6b55bd242a2fefd4446734b0f` (998×701).
3. Scoped [six-screen native review](../screenshots/M19/P02-M19-six-screen-review.json) ties actual PNGs to source SHA. Only real application captures, not synthetic graphics or browser previews, are accepted as evidence.

## Outstanding independent gates (not waived)

This task closure does **not** mark M19 or P02 complete. Final 14 M19 screen/option PNG assets, hosted Wiki publication, full assistive technology, performance gates, report workflow review and protected PR merge remain pending under T08/T09/T10/T11 as applicable. Current versioned search is not a guarantee of future module content; no release was published.
