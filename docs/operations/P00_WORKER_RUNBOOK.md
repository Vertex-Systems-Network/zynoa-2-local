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
