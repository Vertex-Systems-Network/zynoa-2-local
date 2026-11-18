# Quality Gates and PR State Machine

`DRAFT → PREFLIGHT_PASS → IMPLEMENTING → TESTING → FIXING (if needed) → DOCS_CAPTURED → SECURITY_PASS → PR_CHECKS_PASS → MERGE_READY → MERGED_VERIFIED → NEXT_PHASE`

| Gate | Pass evidence | Fail/block action |
|---|---|---|
| Phase integrity | Only permitted branch/paths; current main SHA tracked | Reject cross-phase commit |
| Build | Reproducible target build exit 0; binary stored | Issue+repair same branch |
| Static | Lint, format, typecheck clean; warnings ledger | Fix new warnings or dated waiver |
| Unit/contract | Required suite pass + report | Add regression tests |
| Integration/E2E | Real flows pass including offline/failure | Reproduce and repair |
| UI | Real captured screenshots, a11y and UX contracts | Screenshot/docs missing = fail |
| Security/privacy | No high-severity introduced; redaction tested | Security workflow/private issue |
| Performance | Baseline comparator and budget results | Optimize or scoped deviation ADR |
| User docs | Each option documented, images alt-captioned, help + wiki links | Fix docs before merge |
| Support | Error codes, diagnostic grouping, incident route tested | Issue/reporting repair |
| Release | Correct changelog, migration, rollback, license inventory | Build/release blocked |
| Remote truth | Required GitHub checks pass; merge SHA verified | Never claim merged from local state |

**Required human reviews configured on GitHub must be obeyed.** For autonomous auto-merge, choose compatible policy upfront: automated mandatory checks and bounded authorization, with no human-review requirement if organization policy allows. Never override platform restrictions.

**Warning policy:** New high-risk warnings fail. Baseline warnings tracked with fingerprint+owner+deadline. Expired waiver auto-blocks. Test skip must have ID and reason; test not executed ≠ passed. Error storms trigger dedupe rather than noisy tickets.

## v3.1 — data preservation and delivery gates (non-waivable)

- `DATA-01`: durable chat/message writes and managed artifact refs verified after abrupt process crash and reboot.
- `DATA-02`: DB online backup + encrypted archive verification + staged restore + broken/corrupt archive rejection tested.
- `DATA-03`: restore comparison of message IDs, file hashes, project manifests and settings; backups on another volume documented; reinstallation preserves data.
- `DATA-04`: pre-update verified snapshot, schema compatibility check and rollback/recovery plan; if snapshot fails, update is blocked.
- `STORAGE-01`: model and optional module location preferences persist; supported runtime-specific path migration and sample inference after relocation.
- `STORAGE-02`: source data remains intact if interrupted, checksum fails or runtime health check fails; no blind file deletion.
- `RELEASE-01`: verified merge SHA, signed build, valid manifest/signature, generated release notes, correct version + OS/arch routing.
- `RELEASE-02`: clean install, existing-version upgrade, offline defer, disk-full failure, corrupted signature and active-task checkpoint tests.
- `RELEASE-03`: stable channel rollout only after release qualification/canary. User selects when to install; updater never forces interrupted unsaved work.
- `DOCS-01`: screenshot-backed Help/Wiki for all added controls and error states. Documentation-only checks cannot claim product tests passed.

## v3.2 M26 mandatory changelog and documentation integrity gates

- `CHANGE-01` every user-impacting source PR has validated change-record(s); permitted no-user-impact exceptions are explicit and machine-checkable.
- `CHANGE-02` affected module docs + option catalog + Help/Wiki sources + real UI captures are synchronized before finalization.
- `CHANGE-03` no issue-open, PR-open, mere merged, reverted or unshipped change can appear in a published release changelog.
- `CHANGE-04` released records require verified merge SHA, passed tests, signed actual published manifest, correct channel/version and docs links.
- `CHANGE-05` workflow events and retries are deduplicated; public logs never leak private details.
- `CHANGE-06` root CHANGELOG, GitHub release, Help What's New, signed JSON feed and installed update UI pass change-ID parity.
- `CHANGE-07` tests cover release rollback, recovery, offline feed, broken link, version incompatibility, private security issue, schema mismatch and old client.


## DESIGN-IO — future Designer interoperability gates

- **DESIGN-IO-01:** P08 native Designer core must be **remotely verified merged** with M11/M12 evidence before any P08I branch/implementation.
- **DESIGN-IO-02..10:** Proven editable imports, target-verified exports, fidelity reports, undo/backup/recovery, safe parsing and permissions, illustrated Help/Wiki with real screenshots, truthful per-version compatibility matrix, verified artifact hashes and measured performance. Full normative contract: [DESIGN_INTEROPERABILITY](../operations/DESIGN_INTEROPERABILITY.md).
- P00–P08 are research/specification only for external-tool conversion. Native P08 basic raster/vector exports remain in scope. No premature claims of native .fig/.sketch support or all-format compatibility.
