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

## P00 M22 queue/governance security acceptance (not yet completed)

- P00-Q01: SQLite queue unique jobs, exact active phase/branch, concurrent single winner, fenced attempt token, crash replay of read-only work and bounded retries pass tests.
- P00-Q02: Actual GitHub required PR rules and required check pinned to trusted app are fetched and verified. A protected branch with no required checks must not authorize merge.
- P00-Q03: Queue does not accept or execute arbitrary shell/model/Git-write jobs. Future mutable task executor must have independent authorization and sandbox.
- P00-Q04: Repository `main` has externally verified active protection/ruleset; P00 host is actually deployed with durable state/credential store, live heartbeat and failover exercises.
- P00-Q05: End-to-end guarded GitHub write/merge, issue reporter, security and recovery proofs complete. Current smoke is read-only and **does not pass P00-Q04 or P00-Q05**.
- P00-Q06: All actual module Help/Wiki/screenshots validated when running UI exists; no documentation placeholder represented as real screenshot or published Wiki.

See [queue contract](../operations/P00_DURABLE_JOB_QUEUE.md) and [open infrastructure Issue #3](https://github.com/Vertex-Systems-Network/zynoa-2-local/issues/3). These non-waivable requirements block P00 finalization and next-phase creation.

## P00 dependency planner acceptance — current code slice

- P00-DAG-01: Every dependency must match active phase and branch; invalid/missing parent and self-edges are rejected.
- P00-DAG-02: Transactional cycle detection rejects direct and indirect loops; multi-edge batches roll back completely on error.
- P00-DAG-03: A higher-priority dependent cannot run before its predecessor commits success; unrelated eligible work remains runnable.
- P00-DAG-04: Restarted SQLite queue preserves dependency edges, and blocked prerequisites cascade transitively. Corrupt/orphan parent never counts as success.
- P00-DAG-05: CI smoke proves actual three-stage governance checks in dependency order with zero shell/model/GitHub writes.
- P00-DAG-06: Tests/Help/Wiki/ADR/changelog and remote CI are linked. This is a backend-only implementation; no GUI screenshots can be claimed.

Passing these DAG-specific checks **does not** waive P00-Q04/Q05, protected-main ruleset, permanent worker deployment, sandboxed coding execution or actual remote merge verification. Details: [DAG contract](../operations/P00_TASK_DEPENDENCY_GRAPH.md).

## P00 workspace guard/worktree acceptance

- **P00-WSP-01:** P00 phase/branch exactness, path containment, no privileged write scope and no agent-issued scope expansion verified.
- **P00-WSP-02:** Unit denial for traversal, Windows drive/UNC, symlink/junction, secret files, Git metadata, malicious Unicode and prohibited actions.
- **P00-WSP-03:** Worktree planner accepts only a trusted ordinary repo, separate controlled root, empty hooks dir, exact commit SHA and safe job ID; no shell, checkout, fetch, push or merge.
- **P00-WSP-04:** Real *disposable fixture* Git worktree creation and detached SHA readback, test evidence attached to phase PR. No user workspace Git mutation from CI.
- **P00-WSP-05:** Documentation, Help/Wiki source, security ADR/changelog and limitations are linked with truthful status.
- **P00-WSP-06 (BLOCKED):** OS sandbox/ACL or fd-based safe writes, isolated tool process, secrets separation, actual model worker, Windows reparse tests, deployment/backup and interrupt-recovery verified before code execution may be enabled.

Passing policy/fixture tests cannot waive branch protection, other P00-Q04/Q05 gates, real GUI screenshot obligations or verified merge. [Worktree contract](../operations/P00_WORKTREE_POLICY.md).
