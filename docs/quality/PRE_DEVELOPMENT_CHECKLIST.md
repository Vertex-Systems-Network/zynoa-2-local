# PRE-DEV Gate (mandatory before every code change)

1. Verify repository exact origin, clean/understood worktree and GitHub remote current `main` SHA.
2. Verify active phase lease, scope path allowlist, current PR, CI state and unresolved critical issues.
3. Read `AGENTS.md`, the agent wrapper, `docs/agent/AI_STRICT_PROTOCOL.md`, canonical `docs/MASTER_PLAN_V3_2.md`, phase delivery including all cross-cutting addenda, module dossiers, design ADR, decisions and latest handoff. Reconcile the task manifest against these requirements before implementation or completion.
4. Verify local environment, package versions, Windows target, Ollama and optional engine health; capture baseline warnings/errors and performance.
5. Search/revalidate official dependencies and UX options; record URLs/date/license and ≥2 feasible alternatives, or justify why only one.
6. Define user stories, IDs, each UI control type/default/validation/state/keyboard behavior/help/screenshot target and real backend link.
7. Threat model delta, privacy/telemetry impact, permissions, data flow, migration and rollback plan; sensitive changes reviewed by policy.
8. Set acceptance tests *before implementation*: unit/contract/integration/E2E/a11y/visual/security/performance/docs/Wiki.
9. Specify bounded autonomous retry budget, failure grouping and recovery route; reserve output paths and artifact hashes.
10. Record preflight report, baseline metrics and decision log; only then start source edits on active phase branch.

**Gate outcomes:** PASS, FAIL, BLOCKED with evidence. No automatic 'pass' from absence of checks. Existing failures require baseline labeling and linked issue; new warnings are never silently ignored. During implementation run short checks per slice; full checks before PR.

## v3.1 pre-development checklist additions

1. Identify durable chat/project/files data owner and confirm path outside app bundle; distinguish managed files vs mere external references.
2. Record pre-change data format/schema version; run a backup and corruption/recovery probe prior to any migration.
3. Enumerate downloaded artifacts, existing model folders, runtime ownership, disk and network volumes before installer or storage changes.
4. Verify current Tauri updater and action versions, packaging output names, signing secrets availability, version alignment and release channel policies.
5. Provide unit/integration/E2E fixtures for interrupted download, failed relocation, backup/restore and failed update.
6. Ensure release and backup documentation have real screenshot obligations and fresh Help/Wiki links; do not mark actual capture while app is unimplemented.

## v3.2 PRE-DEV changelog requirements

- Query most recent event IDs and source issues; identify duplicate issue fingerprints and existing planned work.
- Identify changes' category (bugfix/enhancement/feature/security/docs), product version impact and affected modules/options/screens.
- Before source edit, reserve a change ID and define acceptance tests, docs/Help/Wiki revisions and screenshots (if UI affected).
- Confirm release/issue privacy audience, known migration needs and how the change maps into upcoming release notes.


## DESIGN-IO (P00 research-only gate; P08I implementation)

- Research supported UI design tool formats, legal APIs, permitted plugin pathways, tested official release/version and interoperability fixtures. Compare Figma/Penpot/each OpenPencil independently.
- Before P08I, disallow unverified conversion code/dependency or UI labels claiming all-format compatibility. P08 may still implement native save and standards-based raster/vector export.
- At P08I start, fetch and verify P08 **remote merged SHA** and all M11/M12 native core acceptance evidence, real screenshots, help/Wiki and data migration/undo tests.
- Define target-tool reopen/round-trip tests, fidelity warnings, unsupported-feature labels, malicious file fuzz/security tests, user-selected storage and crash rollback scenarios before implementation.

## P00 durable-task preflight additions

- Re-read actual GitHub `main`, active phase PR, rule checks and open blocker issues; do not treat local JSON or check names as authenticated source.
- Confirm each queued job is allowlisted, replay-safe, immutable-ID, phase/branch-scoped, and not a privileged mutation.
- Verify SQLite queue database is on a single trusted host; reject independent replicated DB writers and stale lease tokens.
- Run real concurrent-claim, expired-lease, retry-budget, no-raw-secrets and job-result integrity tests.
- Confirm no worker, GUI, Wiki, release or auto-merge is claimed from an Actions smoke; mark unattested requirements BLOCKED.

## P00 DAG predevelopment and replay checks

- Verify every dependency target and predecessor already exists as an immutable queued job with matching phase and branch.
- Plan safe job order from prerequisites; priority may reorder independent jobs but never violate prerequisites.
- Reject graph cycles, unauthorized scope jumps, missing/corrupt prerequisites and dependency edits after a job starts.
- Exercise persistent reboot/reload, retries, terminal BLOCKED propagation, nondependent safe work and transaction rollback.
- Treat read-only SQLite job scheduling separately from potentially destructive model/Git/file operations; latter require independent authorization and OS sandbox.

## P00 worktree execution-broker preflight

- Verify actual GitHub active P00 PR/branch/CI and separately authenticated SHA; agent-supplied phase/branch or SHA is not authoritative.
- Validate trusted repository metadata, non-overlapping operator-managed worktree root and independent empty hooks directory; never auto-run Git commands on untrusted .git directories.
- Deny model access to protected governance/CI/state/secrets; deny traversal, symlink/junction escapes, Windows path ambiguity and invisible Unicode. Record permission denials with sanitized codes.
- Plan detached no-checkout worktree using exact commit and immutable job ID; validate only via disposable trusted fixture until host authorization broker and OS sandbox are deployed.
- Require real Windows/Linux executor, file handle/race, network/process, quota, credential separation, failure cleanup/receipt and restart testing before claiming automated coding works.

## Per-PR total task status and host model preflight (2026-11-18)

- Reconcile actual GitHub active phase, branch, primary PR, HEAD, CI and Issues.
- Open/create **one** `docs/state/pr-tasks/<PHASE>.json` with all known phase tasks, stable IDs, 4 allowed statuses and relevant evidence/blocker links; update PR body managed section with derived task count.
- Before each patch/checkpoint, record task status changes in manifest alongside tests, incidents, Help/Wiki and unreleased change records; never hardcode percentage or mark task DONE from unrelated CI.
- Validate `python -m scripts.check_pr_task_board` before claiming healthy PR state; remember trusted PR-body write workflow only exists after default-main installation.
- On actual developer host, run localhost-only Ollama preflight; no model inventory/probe on an ephemeral CI runner proves user's host has a working local model.

## P00 observer host pre-development and recovery acceptance

- Confirm dedicated host scope outside repo, current user/service identity and secure credential mechanism; never initialize a folder that contains unrelated user data.
- Refuse provisioning without explicit host capability; reject invalid P00 state, symlink/junction path and reinitialization of existing state.
- Validate SQLite WAL state, required event/lease schema and file permissions; test online snapshot, checksum and non-destructive restore drill before enabling a persistent worker.
- Exercise Windows database handle close and temporary-file cleanup in CI; never suppress locked-file warnings.
- Verify Linux systemd unit and backup timer only after operator install; a Windows at-logon task is not an unattended service.
- Record actual host heartbeat/restart/service status and model+OS sandbox only if independently observed; CI fixture proof is not deployment.

## Model-backed P00 task proposal preflight (2026-11-18)

- Confirm exact active P00 task ID and trusted host-origin `WorkspaceScope`; never derive the writable prefixes or phase identity from model output.
- Send only a short sanitized task brief to explicit local Ollama; no source contents, secrets, private files or user chats. Do not enable model tools or generic shell.
- Require completed model JSON schema response, independent path/check validation and no execution permissions. Record digest/evidence without dumping raw untrusted text.
- Keep `P00-T20` IN_PROGRESS until actual model/OS broker/patch/test/fix loop and remote receipts pass; mocked inference is not end-to-end proof.

## Host preflight for disposable model draft staging (2026-11-18)

- Verify active P00 task and actual GitHub branch/PR; create `WorkspaceScope` only from separately trusted host configuration and pass the **expected** task ID independent of model output.
- Validate model plan's paths/actions before any temp staging; accept only single-level `tests/fixtures`, bounded UTF-8 candidate text, no control/bidi/traversal, no oversized fixture.
- Stage candidate bytes solely in a newly allocated private temporary folder and verify hash; ensure cleanup and no actual source/user file writes.
- Do not AST parse, compile, import or run untrusted Python in privileged process; defer syntax/tests to independently verified OS sandbox. A passing preview does not make T19/T20 done.
- Update same PR task table and structured changelog with exact CI/Linux/Windows evidence; missing security and host gates stay blocked.

## P00 rootless Docker syntax broker preflight (2026-11-18)

- Read official rootless Docker and cgroup v2/systemd limits; never confuse `--memory/--cpus` flags with independently attested enforcement.
- Only an operator may install/cache/scan an image, configure a dedicated nonroot runtime and protect its rootless Unix socket. Never give Docker daemon/API access to an LLM or untrusted PR code.
- Validate exact host P00 task, approved scope, 1 Python fixture, digest-pinned image, no mounts/network/credentials, immutable fixed compiler, and disabled-by-default mode.
- In mocked CI require Linux and Windows positive/negative cases including no Docker call without enable, rootful/cgroup deny, unsafe paths, resource and output bounds, targeted cleanup, no candidate code execution.
- Mark standalone broker contract scoped task only after passing CI evidence. Keep T19 real sandbox and T20 full autonomous repair unfinished until actual host/isolation/merge proof.

## Operator-only Docker syntax smoke preflight (P00, 2026-11-18)

- Require separately owned Linux non-admin host, approved pre-cached Python digest, rootless Unix socket, audited image provenance, delegated cgroup controllers, kernel patching and secrets kept outside model reach.
- Run `python -m tools.docker_host_smoke` only after BOTH explicit operator flags are given. Default/Windows/root execution must deny before Docker; fixed host-owned valid/invalid Python cannot mutate checkout or GitHub.
- Require both correct syntax marker receipts, exact hash/image/task identity and zero writes. A positive operator smoke is **not** independent sandbox attestation, model-based repair, persistent worker, or evidence of protected GitHub merge.
- Capture separate real-host network/filesystem/resource negative probes, supervisor restart, signed/traceable independent evidence and latest CI before T19/T20 or Issue #3 may advance.


## P00 persisted observer-success freshness preflight (2026-11-19)

- Distinguish an active SQLite lease from completed GitHub reconciliation; a lease renewed during network failure cannot certify freshness.
- Verify additive `worker_observation_health` schema, same-owner unexpired lease, valid remote SHA format, and bounded last-success age in a separate read-only host probe.
- Test successful loop recording, failed observation non-refresh, stale/replaced owner, expired lease, one-shot released lease, corrupted/missing schema, Windows disposable SQLite cleanup and no source/GitHub writes.
- Treat all local DB/supervisor reports as **host-local diagnostic hints** until an authorized operator independently verifies real systemd status, remote GitHub API and restart behavior. Do not mark T17/T19/T20 or Issue #3 done based on CI mocks.


## P00 systemd notify/remote-success preflight (2026-11-19)

- Require Linux and operator opt-in before reading `NOTIFY_SOCKET`, `WATCHDOG_USEC`, and optional matching `WATCHDOG_PID`. Refuse malformed/foreign PID, absent environment, Windows and one-shot service mode.
- Emit no readiness until authenticated GitHub response, durable owner-fenced success timestamp, and valid Git SHAs. During GitHub/API/state/lease failure, never send watchdog keepalive merely for process liveness.
- Exercise notification failures, repeated success, outage after readiness, unauthenticated remote result, Windows policy mocks and actual fixed AF_UNIX datagram on Linux.
- Real host/operator must separately verify systemd `MainPID`, restricted UID, service state/restart/WatchdogUSec, GitHub remote readback, backup/restore, no write token/model exposure, and outage-induced stop/restart. CI is not deployment evidence.


## P00 local model-authored fixture preflight (2026-11-20)

- Confirm current GitHub P00 branch, draft PR #1, latest-HEAD CI and independently verified protected main; keep Issue #3 open while external worker/runtime/sandbox is unavailable.
- Only P00-T20 host-approved plan with one flat `tests/fixtures/*.py` DRAFT_ONLY path may enter fixture-content generation; independently hash canonical validated plan and enforce matching response identity/plan SHA.
- Reuse only explicit loopback Ollama with proxies/redirects disabled, structured bounded response and no model tools; refuse model drift, duplicate keys, text/UTF-8/NFC controls, extra fields and truncation.
- Never host-parse/import/execute the generated Python, write the actual checkout, expose raw source in safe receipts/logs or treat disposable staging as isolation proof.
- Require Linux+Windows mock negative tests and real disposable receipt-integrity tests; real model inference and rootless execution remain distinct external gates. P00-T20/Issue #3 cannot be closed from mocked model output.


## P00 bounded local-model syntax correction (2026-11-20)

- Confirm exact HEAD CI, active P00/PR #1, protected main and Issue #3 before changing model-execution code; validate existing P00-T20 draft-only fixture plan.
- Require all three independent trusted host opt-ins and a current-user-owned rootless Docker socket before real inference. No model-selected image, broker callable, code execution, shell arguments, task identity or GitHub write token.
- Limit candidate attempts to two. Syntax-invalid may trigger a repair request to the same loopback model with only the model's prior candidate and a **fixed generic** invalid-syntax marker; any other broker/transport failure stops. Reject identical candidate digest.
- Check independent plan/source/preview SHA and validated syntax-broker receipt for *each* attempt. Never host-parse/execute generated Python, patch real workspace files or report mock inference as deployed. Linux/Windows mock suites required.


## P00 experimental functional execution preflight (2026-11-20)

- Confirm P00/PR #1 HEAD, actual GitHub rules and CI; do not use source-only mock results as deployed-worker evidence.
- Any functional execution needs FOUR independent trusted grants, a one-file P00-T20 fixture, exact plan hash and full rootless socket/daemon/cgroup-v2/systemd checks. Verify effective in-container cgroup ceilings, no-network/no-mount/read-only/nonroot settings.
- Execute candidate Python **only** inside a separately approved rootless container with fixed tests, never on the host and never with repo credentials. The trusted literal reference harness smoke does not attest production isolation.
- Repair at most once after exact invalid syntax or fixed functional failure; reject Docker transport errors, forged results, repeat candidate SHA, changed path/task and other statuses. No GitHub/checkout mutation is implied.
- Require Linux and Windows mocked Docker/model negative tests, and independently witnessed real Linux host containment and credential-leak failure-injection before authorizing real task execution. P00-T20 remains incomplete.


## P00 detached worktree file writer authorization (2026-11-20)

- Require three independent, explicitly true grants before any new-file write: enable, operator acknowledgment and scoped file-write permission. The model may not supply these nor the file descriptor, trusted repo path, worktree parent, pinned commit or expected candidate digest.
- Use a separately-created detached no-checkout worktree; verify `.git` points back to the *trusted source repo* and detached `HEAD` equals the operator-pinned full SHA. The real checkout must remain untouched. Never replace existing files.
- Non-root Linux only; require directory FD support, no-follow opens, same-owner non-group-writable parent directories, bounded UTF-8 source, temp inode fsync, hardlink no-replace publication and reread SHA. Windows must fail closed; a Path/ACL fallback is not approved.
- A partial crash or unusual filesystem error after hardlink requires trusted reconciliation, not automatic blind deletion or an assertion that no file was written. Same-UID attackers, lease fencing, sandbox resource proof and worktree cleanup remain outstanding host security gates.
- Linux test must **actually write** to an isolated fixture Git worktree and verify source checkout untouched, plus deny symlink escapes, existing files, forged SHA/task and malicious draft content; Windows test must deny.


## P00 tested-candidate no-replace Git write acceptance (2026-11-20)

- Before any model inference: check P00/T20 host task, fixed one-file `DRAFT_ONLY` plan, source repo pinned SHA, detached no-checkout worktree ownership, Linux nonroot fd/no-follow support, and FIVE exact opt-ins for model, syntax, runtime and file publication. The model/CI receipt cannot choose the trusted target or approve itself.
- For each of at most TWO candidates, verify SHA and plan/path identity from Ollama, disposable preview, syntax broker and functional broker independently, then pass **identical source and SHA** to the no-overwrite writer ONLY on exact functional PASS. No rehydrated source from untrusted receipts.
- Deny forged/mismatched candidate SHA, changed file/task or Git commit, repeat failed candidate, unsafe socket/host, bad Docker status/transport, existing target and all missing grants. Check a failed/denied test makes NO new file; check a single repair writes only corrected candidate.
- Linux CI must actually create a new file in its private detached Git worktree; Windows must fail closed. Both CI model and Docker responses are mocks, **not independent sandbox or production host attestation**. Never authorize GitHub write/merge or P01 on this proof alone.


## P00 T22 real CI failure → Issue authorization gate (2026-11-20)

- Verify remote default branch contains the reviewed `workflow_run` reporter before claiming it can trigger; source-only PR checks cannot prove listener activation. Never merge a blocked PR just to enable writeback.
- Keep Governance PR workflow token read-only. Privileged publisher has `actions:read`, `issues:write`, `contents:read` only and checks out **trusted default branch only**, never failed PR head/merge commit or build artifacts.
- Independent `GET /actions/runs/<id>` must confirm completed failed Governance workflow, identical full SHA/run ID/repo/event. Only allow safe P2 `developer-ci` fixed error class/version and fingerprint. P0/user telemetry goes private or denies.
- Reusing a fingerprint updates only a canonical existing bot-owned Issue, not spoofed user Issue. Preserve only max five strict run markers, no raw old issue text. Bound listing to four pages, restrict all HTTP methods/paths, reject uncertain POST/PATCH readback as failed delivery.
- CI negative tests may mock GET/POST/PATCH; only actual postmerge workflow run and verified GitHub Issue response establish real automatic delivery (T22). Keep T22 blocked until proof.


## P00 static GitHub PR new-file proof preflight (2026-11-20)

- Only a trusted human/operator-controlled literal fixture is permitted; model-authored source may NOT be given a remote Git permission before independent sandbox provenance and host separation.
- Explicit three host opt-ins and a separate scoped remote token; exact current open/draft/unmerged P00 PR #1 and trusted 40-hex HEAD. Prove fixed path absent and read Git parent tree; never overwrite existing sources.
- Verify Git blob object hash against literal bytes; tree has exactly one new 100644 fixture; commit has pinned original parent/tree; update only phase/00-governance ref with `force:false`. On remote ambiguity or moved head reconcile, do NOT retry blindly.
- Verify PR HEAD at new SHA plus fixed file contents from immutable SHA. CI mocks all network/remote writes; real manual connector proofs do not attest host security/token restriction/full autonomous source edits.
