# P02-T10 Native Option Reference Matrix

**Branch:** phase/02-shared-ui, draft PR #12. **Status:** SOURCE IMPLEMENTED; exact-head Windows visual acceptance subject to CI and independent review.

## Delivery

The existing Windows Actions job starts the real Tauri executable and captures all 16 documented option HELP references, M02-OPT-01 through M02-OPT-08 and M19-OPT-01 through M19-OPT-08, after exact-ID palette keyboard navigation. This matrix complements 38 prior native candidates, for 54 expected PNG+receipt pairs.

Per-frame receipt records include screenshot ID, actual option ID, exact keyboard route, build/source SHA, measured native window geometry, raw PNG SHA256, alt text and candidate_pending_visual_review with capture_verified=false. Missing/duplicate/blank frames fail closed; a machine report cannot declare independent visual approval.

New script tools/verify_p02_t10_readiness.py checks all 29 final screenshot IDs and paths, source-tied machine metadata, the 16-option inventory and a single Windows native startup/capture-duration sample. It returns NOT_READY while final mandatory images are absent, and does not treat Help references as actual control screenshot evidence.

## Boundaries

No additional runtime dependencies, browser/local storage, telemetry, network calls, native permissions, project file mutations, or external Wiki publishing. This is P02 screenshot evidence and test infrastructure, not completed accessibility/performance acceptance. Actual control screenshots, screen-reader validation, final Help/Wiki review and guarded P02 merge remain pending.

## Exact-source native verification

Windows run #45202826399 succeeded on source 155227566aca19053a705048998ecd85f389ab82 including TypeScript, Node tests, Python provenance and readiness tests, Rust tests, native Tauri build/boot, 54 actual screenshot candidates and data-safety checks. 16 individual M02/M19 option Help reference PNGs were downloaded from artifact 14833152368; their original bytes matched immutable SHA256 receipts. A separate scoped visual review is in docs/screenshots/M19/P02-T10-option-matrix-independent-review.json. They are NOT 29 final actual screen/control images.

The initial Actions artifact did not include P02-native-performance.json or P02-T10-readiness.json despite the producing CI stages passing; the workflow upload list is now extended so the next Windows run exports both truthful machine reports. No duration or final performance-budget claim is made from missing artifact data.
