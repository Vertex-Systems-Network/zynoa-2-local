# P02-T10 real Windows screenshot review bundle

This source-only CI utility builds one **self-contained offline HTML review** for the exact P02 real Tauri Windows build. It embeds original PNG bytes from the 29 direct screen/control candidate targets and places the 16 option *Help-reference* frames in a separately labelled section. It never generates synthetic screenshots, opens network URLs, or modifies app data.

The 29 final manifest targets are mapped to **14 already existing direct native screen/control candidates** and **15 newly captured native control journeys**. Original screenshot hashes, source/build SHA, native HWND provenance, unique frames, interaction identity and 69 PNG/receipt pairs must pass before the index is written. The review pack is exported in the Windows Actions artifact as `docs/screenshots/_ci/M02/P02-T10-69-native-review.html` plus machine index `P02-T10-29-review-index.json`.

**Do not confuse artifact preparation with acceptance:** `docs/screenshots/MANIFEST.json` retains all final M02/M19 targets `PENDING` until individual actual PNGs are committed to their required paths, reviewed for contrast/clipping/correct option/control and accompanied by source-bound review receipts. These images are candidates, not the 29 required final committed screenshots; native UIA's 9/9 scoped success does not certify a complete screen-reader trial. A single performance timing sample cannot approve budget. Hosted GitHub Wiki publication and protected merge must also be independently verified.

No new dependency, telemetry, binary package, user data access or native IPC permission. **Rollback:** remove the review pack generator/test and its two workflow invocations; the underlying running app and data are unchanged.
