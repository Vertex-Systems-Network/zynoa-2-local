# PRE-DEV Gate (mandatory before every code change)

1. Verify repository exact origin, clean/understood worktree and GitHub remote current `main` SHA.
2. Verify active phase lease, scope path allowlist, current PR, CI state and unresolved critical issues.
3. Read `AGENTS.md`, appropriate agent wrapper, MASTER_PLAN_V3, module dossier, design ADR, memory/decisions and latest handoff.
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
