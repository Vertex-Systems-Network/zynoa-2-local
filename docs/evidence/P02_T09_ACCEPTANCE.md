# P02-T09 — Local Wiki source mappings, broken-link handling and offline assurance acceptance

**Official task:** P02-T09 · **Status:** DONE for strictly local, source-controlled mappings and offline link validation; no hosted Wiki publication is claimed.
**Branch/PR:** `phase/02-shared-ui` / [Draft PR #12](https://github.com/Vertex-Systems-Network/zynoa-2-local/pull/12).
**Independent native source:** `da648baae21477cae44041ee0cbe99f8fc75f347`, [successful Windows run #45186464263](https://github.com/Vertex-Systems-Network/zynoa-2-local/actions/runs/45186464263), artifact `14824706339`.

## Delivered functionality

- Two allowlisted source Markdown mappings `M02 → docs/wiki/pages/M02.md`, `M19 → docs/wiki/pages/M19.md`, explicitly `published:false`; a hosted GitHub Wiki is **not** in the offline bundle.
- Local `help://article/<known-id>` parser rejects traversal, unknown IDs, external URLs and query/fragment variants; the new local `help://option/M02-OPT-xx` and `M19-OPT-xx` option parser likewise resolves only the sixteen fixed IDs. Neither parser registers an OS-wide protocol handler.
- In-app Check bundled article and Wiki mappings validates article ID uniqueness, related links, FAQ/guide destinations, tour references and source map integrity, with user-visible invalid-route feedback rather than external fallback.
- No fetch, telemetry, browser storage, remote issue posting, credential read, or dynamic execution is introduced.

## Verified evidence

1. Windows native run #45186464263 passed the M19 source and negative-route regression tests plus Tauri binary/cold boot; system remained offline-capable.
2. Actual `M19-S06` screenshot (998×701, SHA256 `e13328637847640d906524d4da347848f917f86961300d165639a516d85d7afe`) visibly shows Wiki source rows, unpublished disclaimer and local route validator. Original PNG and JSON hash/provenance were reviewed in [six-screen review](../screenshots/M19/P02-M19-six-screen-review.json).
3. The separate option-route expansion has Node/Python contract tests and remains subject to its own exact-head Windows and native option-directory candidate verification; that later work is not falsely attributed to the earlier screenshot SHA.

## Out of scope of this scoped DONE

`M19-OPT-06` remains a **partial remote Wiki** feature until a controlled, authenticated and idempotent `.wiki.git` publish/sync is independently proven. Full final M19 screenshots, external opening, assistance technology E2E, and PR merge remain gates of T08/T10/T11 and overall M19. No claim that the GitHub-hosted Wiki is already live.
