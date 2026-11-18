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

## P00 audit clarification — no circular premerge and future-phase gates (2026-11-18)

- **BOOTSTRAP-01 (required before P00 merge):** Real persistent developer host/service identity, live heartbeat and restarted durable state; deployed authorized model with independently controlled security broker, resource limits and narrow task scopes. CI mock/fixture tests alone are NOT PASS.
- **BOOTSTRAP-02 (required before P00 merge):** One safe test-repository end-to-end unattended task: plan, scoped patch, tests, bounded fix, docs/evidence, update same PR; independently verify GitHub head and checks. No live user data or untrusted code execution outside a validated OS sandbox.
- **BOOTSTRAP-03 (required before P00 merge):** Actual `main` protected ruleset and required trusted CI, non-bypass configured write identity and no unresolved *pre-merge* critical blocker; PR is non-draft. Do not close an unresolved issue as a gate workaround.
- **BOOTSTRAP-04 (post-merge transition):** GitHub confirms exact P00 PR merge and resulting main commit; persist real `MERGED_VERIFIED` state and only then create P01 branch/PR. This **cannot be used as a prerequisite for the pre-merge blocker issue closure**.
- **M22 UI screenshots:** Record current P00 headless controller as a partial backend; running-app GUI screenshot gates remain mandatory when M22 graphical surfaces are implemented on the shared UI platform, not before P02 exists. Do not mark entire M22 product feature DONE at P00.
- **Future product:** P04 product coding studio, P10 in-product advanced agent features, P08I external design interoperability and P11 signed release keep their own full gates. No P00 requirement is satisfied by simply relabeling them future work.

See [continuous-autonomy audit](../operations/P00_CONTINUOUS_AUTONOMY_AUDIT.md). Existing P00-Q04/Q05 still require actual deployment, guarded actions and safe integration; this amendment clarifies **timing**, not bypass.

## Mandatory TASK tracking gates for each phase PR (2026-11-18)

- **TASK-01:** One canonical `docs/state/pr-tasks/<PHASE>.json` matches the actual phase, branch and primary PR number. CI validates all stable task IDs and count (1–120).
- **TASK-02:** GitHub PR body contains exactly one managed table with every task/actual status and calculated totals. Source remains version-controlled JSON, not a hand-edited percent.
- **TASK-03:** DONE and BLOCKED statuses link to relevant real repository evidence/issues. No CI-only inference of task completion; if evidence is stale or a regression occurs, mark IN_PROGRESS/BLOCKED truthfully.
- **TASK-04:** Each newly discovered in-scope task is added to manifest and tracked on the SAME PR. Docs/help/wiki/screenshot and change records updated where the task actually affects them.
- **TASK-05:** Automatic PR body writers must run from trusted main/host only, with narrow `pull-requests:write`; untrusted PR HEAD is read as limited schema-validated JSON, **never executed** with write authority.
- **TASK-06:** PR table and active manifest agree before final merge; merge gate, real protected main, independent CI, deployment, issue blockers and verified remote SHA are checked separately. No task-board bypass of security.

Source: [PR Task Tables](../operations/PR_TASK_TABLES.md). The trusted workflow in current P00 draft remains INACTIVE until securely installed on default main. P00 cannot pass unrelated host/ruleset gates due solely to a passing task-board test.

## P00 Host Bootstrap vs Deployed Worker Gates (2026-11-18)

- **P00-HOST-01 (fixture):** Authorized `tools.host_bootstrap` creates non-overlapping host root, private POSIX dirs, external SQLite DB and sanitized role metadata; repeated initialization does not overwrite existing journal.
- **P00-HOST-02 (fixture):** SQLite online backup + SHA-256 digest + required-table/PRAGMA integrity validation + copy/restore drill must pass with active WAL state; a corrupt snapshot/digest blocks without overwriting live DB.
- **P00-HOST-03 (fixture):** Linux systemd observer/backup templates have scope guard; Windows Task Scheduler preview uses current-user limited token with *at-logon* trigger, not privileged SYSTEM and not an always-on service.
- **P00-HOST-04 (fixture):** Windows handles are explicitly closed (EventJournal and WorkerLease) so temporary DB fixtures can be removed without locked-file errors; Linux/Windows CI must show real test proof.
- **P00-HOST-05 (BLOCKED externally):** Actually installed supervised host/service identity, secure token store, measured heartbeat/restart proof, real ACL/OS sandbox and stable backup retention/off-host recovery are still required. Passing P00-HOST-01..04 does **not** permit P00 merge or phase advancement.

Source: [Host Bootstrap](../operations/P00_HOST_BOOTSTRAP.md). CI-hosted disposable fixtures do not mean that the user's computer was modified.

## P00 Model Proposal vs Execution acceptance (2026-11-18)

- **MODEL-PROP-01 (fixture):** Model planning request uses explicit loopback-only Ollama `POST /api/chat`, bounded body/output, JSON schema and `stream:false`; proxy/redirect/public endpoint denied.
- **MODEL-PROP-02 (fixture):** Untrusted response is revalidated independently against exact P00 phase/branch/task, safe 1–8 `DRAFT_ONLY` paths and only fixed read-only checks; extra fields, tool calls, truncated JSON, governance/symlink escapes and duplicates deny.
- **MODEL-PROP-03 (fixture):** Planner must perform **zero** shell commands, file writes, GitHub writes and phase switches; policy files protecting the planner/host/PR task updater cannot be model-written. Linux and Windows unit tests required.
- **MODEL-EXEC-01 (still BLOCKED):** An actual deployed local model with measured capability, OS-supervised sandbox, independent restricted file/command broker and bounded CI/debug/fix feedback loop must pass on safe fixture repo. MODEL-PROP-01..03 cannot satisfy this gate, declare T20 DONE, merge P00 or create P01.

See [P00 local model planning](../operations/P00_LOCAL_MODEL_PLANNING.md) and [Infrastructure Issue #3](https://github.com/Vertex-Systems-Network/zynoa-2-local/issues/3).

## P00-T25 ephemeral fixture staging gate (2026-11-18)

- **FIXTURE-01:** Require trusted host-supplied `expected_task_id`, exact P00 phase/branch and `WorkspaceScope`; never accept model-provided task ID as independent authority.
- **FIXTURE-02:** Only bounded exact-inventory, one-level `tests/fixtures` draft targets; deny traversal, symlinks, governance paths, malformed or Unicode control text and content > 8 KiB/file, > 32 KiB total or > 200 lines/file.
- **FIXTURE-03:** Fresh disposable temp directory only; verify bytes/hash and cleanup; existing repository/user files unchanged. No arbitrary file patch, shell, tool calls, GitHub mutation or model code execution. Do NOT use host AST parsing for untrusted Python.
- **FIXTURE-04:** Tests pass on Linux and Windows for cleanup, safe receipt, wrong task identity, malformed JSON, source preservation, path denial and no-command behavior; record exact CI SHA and run.
- **FIXTURE-05:** T25 completing proves *only* fixture preview; independent real OS sandbox/process/file-handle/network protection, live host/model, bounded coding repair loop, protected GitHub main and verified merge gates remain UNMET. PR may not advance to P01 based on this helper.

[Fixture operator contract](../operations/P00_FIXTURE_DRAFT_STAGING.md) · [ADR-0014](../adr/0014-staging-not-sandbox.md).

## P00 rootless syntax broker contract gates (2026-11-18)

- **DOCKER-SYN-01:** Only operator-supplied P00 task identity and `WorkspaceScope`; one flat bounded Python fixture; exact digest-pinned official image; candidate never chooses Docker image/socket/command/args or run permission.
- **DOCKER-SYN-02:** `enabled=False` is default and must issue **zero** Docker calls. Real invocation requires nonroot POSIX user, owned nonlinked rootless Unix socket and executable Docker binary. Reject rootful/remote daemon and unsigned/mutable image input.
- **DOCKER-SYN-03:** Require daemon to report exact rootless status, cgroup version 2 and driver systemd. The fixed container-side compiler must read effective cgroup-v2 `memory.max`, `pids.max`, `cpu.max`, reject unbounded/ignored controllers before model-source parsing, and check loopback-only interfaces and read-only root. Confirm actual delegated controllers/resource ceilings independently on the provisioned host; mocked results and script flags alone are not proof.
- **DOCKER-SYN-04:** Only `--network none`, read-only filesystem, no mounts or Docker socket, all capabilities dropped, no-new-privileges, fixed nonroot user, constrained memory/CPU/PIDs and private tmpfs. `--pull never`; fixed trusted `python -I -S -B -c` syntax compilation only. No candidate bytecode execution.
- **DOCKER-SYN-05:** Exact success/invalid markers, bounded output/no stderr leak, timeout targets only its own randomly named container and fails closed if cleanup uncertain; zero GitHub/workspace writes. Linux + Windows policy suites must pass.
- **DOCKER-SYN-06 (UNMET):** Real host rootless Docker, image provenance/vulnerability audit, delegated cgroup resource enforcement, no-network/no-mount escape probes, process supervision, cleanup after hard crash and actual CI receipts must pass BEFORE T19/T20 or P00 exit. Mock tests are not deployment evidence.

[Operator manual](../operations/P00_DOCKER_SYNTAX_BROKER.md) · [ADR-0015](../adr/0015-rootless-syntax-gate.md) · [Issue #3](https://github.com/Vertex-Systems-Network/zynoa-2-local/issues/3).

## Operator rootless syntax smoke — non-exit contract (2026-11-18)

- **DOCKER-SYN-07:** `tools.docker_host_smoke` refuses by default, requires two explicit operator authorization flags and nonroot Linux identity, exact P00/PR state, fixed valid/invalid harmless syntax fixtures and strict sanitized result/hash/zero-write verification. Linux and Windows CI exercise mocked success/denial only.
- **DOCKER-SYN-08 (BLOCKED):** The actual operator-owned Linux execution, delegated cgroup negative tests, independent network/filesystem/credential containment, supervisor recovery, verified image provenance and protected-main GitHub identity remain unverified. A successful smoke alone cannot mark T19/T20 complete or approve PR merge.


### P00 required check workflow provenance gate (2026-11-19)

P00-Q02 requires GitHub required check name, pinned Actions App and authenticated Actions run/job identity bound to current PR, SHA, check suite and expected workflow path. Same-name successful checks from another workflow fail closed. Passing code-level provenance does not attest hosted worker, GitHub ruleset installation, rootless isolation, CI workflow integrity or actual merge; Issue #3 remains open.
