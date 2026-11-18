# P00 Operator Runbook — Authenticated Phase Observer

**Status: IMPLEMENTED CODE, NOT DEPLOYED.** This document covers the read-only observation worker currently in `tools/github_gateway.py` and `tools/phase_worker.py`. It is **not** an unattended AI coding agent, automatic GitHub issue reporter, PR merger, or deployed 24/7 service.

## Components and ownership

| Component | Ownership | Verified behavior |
|---|---|---|
| `tools/phase_controller.py` | Phase policy, pure transition guard, SQLite audit journal | Unit tests, policy only |
| `tools/github_gateway.py` | Authenticated GitHub API readback, scoped to one configured repository | Mock tests + PR CI live API smoke |
| `tools/phase_worker.py` | Repeated authenticated snapshots, one renewable SQLite lease, safe event ledger | Unit tests; runner-host deployment not verified |
| `.github/workflows/governance.yml` | Read-only PR smoke, source syntax, existing governance/unit suites | CI checks current commit |

The observer uses GitHub's live PR, branch, checks, repository metadata and tracked blocker-issue endpoints. It must never treat a written PHASE.json value or generated AI text as verified merge evidence. It **never performs a GitHub write**.

## Operator prerequisites

1. Dedicated, patched host with Python 3.12+, secure storage outside the checkout and network access to `https://api.github.com`.
2. Checked-out repository in the correct active phase branch; verify branch SHA against GitHub.
3. **Repository-scoped GitHub App installation token** (preferable) or short-lived fine-grained token with Metadata/Contents(read), Pull requests(read), Checks(read) and Issues(read). Never ship token in the desktop application, record it in the repository, or place it in command-line arguments.
4. Locked-down environment service and permission boundary. On Linux prefer systemd credentials/secret store or an appropriately restricted environment file. On Windows use DPAPI/Credential Manager or service secret store.
5. Persistent DB location outside binary/repository directory with restricted OS ownership and backup policy. Only sanitized event metadata is stored.

## One-shot diagnostic (safe)

```bash
# Set ZYNOA_GITHUB_TOKEN securely through your host's secret manager first.
python -m tools.phase_worker --once \
  --repo Vertex-Systems-Network/zynoa-2-local \
  --state docs/state/PHASE.json \
  --db /var/lib/zynoa/controller.db
```

Output includes the observed branch/PR SHA, checks passed, blocker issue numbers, main protection state and `action: OBSERVE_ONLY`. `transition_ready` remains false until real GitHub state, phase status, checks and blockers satisfy policy. No PR is merged or branch created by this command.

## Long-running mode on a dedicated host (requires deployment)

```bash
python -m tools.phase_worker \
  --repo Vertex-Systems-Network/zynoa-2-local \
  --state docs/state/PHASE.json \
  --db /var/lib/zynoa/controller.db \
  --interval 30
```

The worker acquires a single SQLite lease for the process lifetime, renews it on every observation, logs sanitized repeated failure classes, and waits with bounded backoff. SIGTERM/SIGINT stops it and releases its lease; after a process crash a new worker may take over after the lease expires. Starting a second instance while first lease active fails rather than silently running both. Scheduled GitHub Actions workflows are **not** a guaranteed always-on process; scheduling is subject to runner availability.

On Linux, see [systemd service example](../../deploy/systemd/zynoa-phase-observer.service). It is a template, not an installed service. Before activation edit paths, create dedicated restricted user + data directory, install credentials outside repo and test manual observation. Record service PID, host ID, health check and last successful snapshot; then update `docs/state/PHASE.json` only with verified deployment evidence.

## Safety of phase promotion

`authorize_next_phase` is a pure contract: it accepts normalized evidence but does not itself fetch GitHub. To build a future authenticated transition controller, require a trusted `GitHubGateway.observe()` result, independent signing/authority boundary and GitHub ruleset/protection validation. P00's observer intentionally does not auto-merge. No next phase begins until the previous phase PR's actual remote merge SHA is verified.

**Known deployment blockers (Issue #3):** No always-on host has been provisioned; no unattended coding executor installed; `main` was unprotected in the 2026-11-18 audit; current worker has no GitHub-write tools. Repository auto-merge setting being enabled does not waive branch protection or the PR completion policy.

## GitHub branch ruleset checklist

An administrator must use repository Settings → Rules → Rulesets (or equivalent authorized management API) to protect `main`:

- Require pull request before merging, no direct push/force push/deletion.
- Require `governance-lint` check from the trusted CI workflow and all required future security/release checks.
- Set up allowed merge policy and required reviews consistent with organization governance; never bypass configured reviews.
- Define trusted actors and prevent untrusted PR code from receiving GitHub write tokens.
- Validate actual ruleset through authenticated readback. A 403/404/empty policy is **NOT VERIFIED**, not proof protection exists.

## Privacy, recovery, and incident routing

- No user prompts, source files, passwords, secrets, raw stack traces or private paths enter the observer journal.
- API errors are reduced to safe error classes; transient failures retry with bounded exponential delay, not infinite tight loops.
- GH Issues #2 (future design interoperability) and #3 (P00 worker/protection) are tracked separately; issue creation for development events must use an independent scoped relay/CI workflow, not this read-only worker.
- Back up the SQLite database using a consistent snapshot and restore test; the GitHub repository remains the authority for branch/PR/merge state.
- A new host must re-read GitHub main, active PR, CI and open blockers before emitting any transition signal. It must never rely on the last local event as merge evidence.

## Limits and next tasks

P00 still needs authenticated GitHub write controller + guarded policy enforcement, supervised model-backed coding jobs/worktrees, safe issue reporter, actual host deployment/heartbeat proof, independent security review and full gate verification. **Do not mark P00 complete or move to P01 from this runbook.**

Official references:
- GitHub REST PRs: https://docs.github.com/en/rest/pulls/pulls
- GitHub Checks: https://docs.github.com/en/rest/checks/runs
- Branch protection: https://docs.github.com/en/rest/branches/branch-protection
- Actions scheduling: https://docs.github.com/en/actions/reference/workflows-and-actions/workflow-syntax


## Guarded PR merge executor — implemented but DISABLED by default

`tools/phase_merge_guard.py` now adds a separately secured merge entrypoint and independently testable fail-closed policy. It is NOT called by the read-only observer, does not bypass GitHub required review/protection, and does not start the next phase.

Dry-run (read-only, with scoped `ZYNOA_GITHUB_TOKEN`):

```bash
python -m tools.phase_merge_guard --state docs/state/PHASE.json
```

The current P00 PR must report BLOCKED because it is draft, main is unprotected and Issue #3 is open. The GitHub Actions governance workflow tests this dry-run with **zero write credentials** and asserts it never merges.

After a dedicated non-bypass GitHub App write identity is securely provisioned, an authorized worker may call `--apply` only with a separate `ZYNOA_GITHUB_WRITE_TOKEN` and `ZYNOA_ENABLE_MERGE=1`. This is an **administrator deployment configuration**, not a repeated per-task user dialog; never set these variables in PR CI or desktop binaries. The write gateway checks fresh PR/head/base SHA, protected main, successful required checks, mergeability, open critical blockers, draft status and readback; GitHub must still independently enforce branch policies. No such live merge has been attempted or verified in this repository. Its implementation needs an external security review and real test-repository integration before P00 exit.

## Queued governance checks and merge policy verification (P00 next slice)

```sh
python -m tools.dev_job_runner --smoke --repo-root . --db /tmp/zynoa-p00-job-smoke.db
```

Uses only `phase-policy`, `design-spec`, and `docs-integrity` handlers. Stores progress/digest in a temporary SQLite DB; no shell commands, GitHub writes or model tasks. For production host choose a restricted persistent database path rather than temporary file; this is not a deployed development worker. See [queue contract](P00_DURABLE_JOB_QUEUE.md).

**Effective rules requirement:** Before auto-merge can be allowed, remote `main` must report protected and the applied GitHub rules must include a PR requirement plus a required status check whose source GitHub App ID is pinned to and matches the observed successful check. An inaccessible or empty rules response means `rules_policy_verified=false`; do not treat a name-only status success or UI auto-merge toggle as permission. The current repository has no applied rules and therefore remains blocked. References: [GitHub effective rules REST](https://docs.github.com/en/rest/repos/rules), [Rulesets](https://docs.github.com/en/repositories/configuring-branches-and-merges-in-your-repository/managing-rulesets).

## P00 worktree planning smoke (trusted fixture only)

The phase branch contains `tools/workspace_policy.py` (file-capability decisions) and `tools/worktree_plan.py` (immutable detached/no-checkout command plan). Run `python -m unittest tests.test_workspace_policy -v` to validate the policy and execute a Git worktree **only in the test-created disposable repository**. No production repo Git worktree changes are performed by this test or by the planner. Never expose host scope-root paths, policy-grant objects, Git credentials or Git config to model-generated code. Worktree planning alone is **not a sandbox**; see [P00 Worktree Policy](P00_WORKTREE_POLICY.md) and the open host/deployment blocker Issue #3.

## Task status PR synchronization (P00 2026-11-18)

Current P00 task manifest: `docs/state/pr-tasks/P00.json`. Every phase PR must show total, Done/In progress/Pending/Blocked and per-row evidence links. Use `python -m scripts.check_pr_task_board` (read-only) and `python -m tools.pr_task_board --manifest docs/state/pr-tasks/P00.json --print` to preview. [Detailed PR task contract](PR_TASK_TABLES.md) explains the opt-in `--sync --expected-head <verified-SHA>` command and narrowly scoped PR-only credentials.

A trusted-main workflow `.github/workflows/pr-task-table-sync.yml` can auto-update later phase PRs after successful governance CI, without running PR code with write permissions; it does not activate until **actually merged to main**. The current P00 PR table was synchronized by authorized GitHub connector. Do not enable write credentials on pull_request test jobs.

Host model preflight before any model-backed worker: `python -m tools.local_model_probe`. This is a loopback Ollama health check, not a deployed AI coder, GitHub writer or validated OS sandbox. See [local preflight](P00_LOCAL_MODEL_PREFLIGHT.md), [Issue #3](https://github.com/Vertex-Systems-Network/zynoa-2-local/issues/3).

## P00 observer host storage provisioning & recovery (2026-11-18)

The observer now has an external data-root bootstrap and WAL backup+restore drill. Read [P00 Host Bootstrap](P00_HOST_BOOTSTRAP.md) before starting a service or selecting paths. The observer's original SQLite `EventJournal` and `WorkerLease` implementation now explicitly closes connections to avoid Windows file locks and failed restart/cleanup tests.

`tools.host_bootstrap` initializes `state/controller.db` (NOT the former `/var/lib/zynoa/controller.db` example) under the operator-owned host root. The Linux versioned systemd service now includes `ExecStartPre ... inspect` and uses `/var/lib/zynoa/state/controller.db`; a separate daily online-backup timer is available as an **uninstalled template**. Windows includes an explicit preview/opt-in *current-user at-logon* scheduled task, not an always-on service. Current P00 CI initializes only runner-temporary fixtures and verifies restore, it does not prove secure host credentials, model coding, worker heartbeat, installed service or actual GitHub write/merge. The true external deployment gate is [Issue #3](https://github.com/Vertex-Systems-Network/zynoa-2-local/issues/3).
