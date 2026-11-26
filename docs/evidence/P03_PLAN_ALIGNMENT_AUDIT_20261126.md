# P03 plan alignment — 2026-11-26

## Remote baseline and evidence

- PR #25 is draft, branch `phase/03-chat`, reviewed exact head `0d75fb7b91c2dccb6612a2b6ddb478ea3fce199b`. Remote main `2520271026a22053a9f11e47259f28f5249b5373` retains P02 MERGED_VERIFIED and last verified P02 merge `115b6c79fece26b5e4ec58ef8ad2364d7a77d244`. Comparison: 72 ahead, 0 behind. P04 not authorized.
- Six successful exact-head workflows, two skipped: [Windows](https://github.com/Vertex-Systems-Network/zynoa-2-local/actions/runs/45751187245), [local model](https://github.com/Vertex-Systems-Network/zynoa-2-local/actions/runs/45751187276), [governance](https://github.com/Vertex-Systems-Network/zynoa-2-local/actions/runs/45751187271), [foundation](https://github.com/Vertex-Systems-Network/zynoa-2-local/actions/runs/45751187291), [runner](https://github.com/Vertex-Systems-Network/zynoa-2-local/actions/runs/45751187267), [task sync](https://github.com/Vertex-Systems-Network/zynoa-2-local/actions/runs/45751187258). Windows job 139679084868 reports actual model UI candidate step success; artifacts 15086470939 and 15086406324 listed, not independently inspected. Issue #29 remains open until scoped proof review. Preserve task manifest 4 DONE / 10 IN_PROGRESS / 2 TODO.
- Source audit: M03 transport/SQLite/UI work exists; T08–T11 and T12–T14 contain pure source validators, not complete native product workflows. Backup hash validation is not authenticated encryption, lexical staging is not safe restore, and an allowlist is not scoped authorization. No full-phase or release claim.
- P00 persistent worker issue #3 and inherited warning issue #18 remain open; their historical merge or green unrelated tests are not completion. No cross-phase implementation.

## Acceptance-driven execution order (existing tasks, no added scope)

| Task | Prerequisite / next acceptance |
|---|---|
| T05–T07 | Independently inspect original current model UI artifact, verify dropdown DB acknowledgement, Stop/retry, model switch, context/draft parity and exact model calibration. Resolve #29 only with matching proof. |
| T08 | Native managed attachment import, safe open/size bounds, immutable hashes and transactional message links; recover from interrupted staging; real UI attach/read and restart. |
| T09 | Reuse managed storage for artifact ownership, provenance and recovery; safe scoped create/read; test interruption and user-visible result. |
| T10 | Fail-closed review/deny and scoped local tool execution with durable trace; allowlist alone does not grant authority. No shell/network tool expansion. |
| T11 | Snapshot-consistent full conversation export with linked artifacts, ordering, explicit destination and privacy/integrity verification. |
| T12 | Reviewed AEAD/KDF implementation per M23 specification, online SQLite snapshot, manifest plus managed hashes, wrong-key/tamper rejection and independently staged restore. |
| T13 | Inject process termination, disk/write failure and restart; compare acknowledged IDs and managed hashes; actual uninstall/reinstall acceptance; no sole-copy destruction. |
| T14 | Real performance measurements, native keyboard/a11y, security and previous-phase regressions; triage inherited/new warnings separately. |
| T15 | Original native screen/option/state evidence, Help and hosted Wiki readback; no synthetic substitute. |
| T16 | Final exact-head checks, issue review and owner-approved protected merge, then independent checkpoint; release qualification remains separate. |

Dependencies: T08 is foundation for T09/T10/T11; T11 and managed-data persistence inform T12; T12 feeds T13; T14 runs throughout and closes after native journeys; T15/T16 are final gates. Parallel contract tests are permitted but completion follows dependencies. Do not promote T08–T14 merely from pure tests. M23 is only its P03 chat-data scope; P05 model management, P04 coding and P11 release work remain deferred.

## First development slice: portable managed names

Scope: T08/T12 native pure validation. Reuse one bounded filename policy for both attachment receipts and restore staging candidates; tests cover unsafe names and ordinary Unicode. Existing hash, size and path ownership boundaries stay intact. No new dependency, IPC authority, real file write or crypto claim. This is a small reversible repair before actual managed storage. Reviewed existing M23 storage, backup and native contracts; no third-party dependency or external research needed for this slice. The alternative (separate divergent validators) was rejected to prevent drift. Future actual storage must independently verify filesystem handles, reparse points, quotas and staging ownership.

Tests added in the two Rust modules. Required checks: `cargo test --locked` in apps/desktop/src-tauri, `python -m unittest discover -s tests`, `python scripts/check_governance.py`, applicable verify scripts, and PR task board validation. Local environment has no Rust toolchain and cannot resolve github.com; remote connector access works. No new test execution, native screenshots, performance result or hosted Wiki publication is claimed. Await exact-source CI and independent artifacts; preserve lease/merge policy. No release.

## CI repair checkpoint

Exact `b6966b2` Governance run 45843464371: 770 tests, one M23 Wiki inventory failure. Windows run 45843464315: 770 tests, one Wiki failure, two CP1252 decode errors, 46 skips. [Issue #30](https://github.com/Vertex-Systems-Network/zynoa-2-local/issues/30) tracks both regressions. Candidate preserves the exact 27 M23 illustrated links, uses the full-guide link for the P03 note, and explicitly reads both Rust source files as UTF-8. No local full suite or new native acceptance is claimed; verify fresh CI and retain all gates.

## Verified repair and next T08 slice

Exact a4c757f six applicable workflows passed. See [managed blob candidate and original model artifact review](P03_T08_MANAGED_BLOB_CANDIDATE_20261126.md). No broad task status promotion.
