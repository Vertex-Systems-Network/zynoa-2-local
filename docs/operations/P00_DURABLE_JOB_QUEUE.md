# P00 Durable Development Job Queue — Read-Only Foundation

**Implementation status:** working Python scheduler + deterministic governance-check runner; not a deployed autonomous AI developer. **Phase:** P00, module M22; [PR #1](https://github.com/Vertex-Systems-Network/zynoa-2-local/pull/1).

## Objective

A reliable non-stop AI development worker will ultimately need durable jobs, idempotency, exclusive claims, bounded retries, crash/restart recovery, phase isolation and verifiable results. This P00 slice implements those primitives ONLY for **replay-safe read-only governance checks**. It DOES NOT launch shell commands, run coding models, edit project source, create branches/PRs, install runtimes, auto-merge or start a background host.

## Implemented interfaces

- `tools/dev_job_queue.py`: SQLite WAL queue storing safe job metadata, phase/branch, immutable spec, state, priority, attempts, retry-after, lease owner, attempt token and SHA-256 result digest.
- `tools/dev_job_runner.py`: fixed built-in handlers; no dynamic imports, shell tool, network or code execution. The only permitted job types are `phase-policy`, `design-spec`, `docs-integrity`.
- `tests/test_dev_job_queue.py`: job identity, duplicate prevention, phase boundary, claims, lease fencing, expired-worker retry, bounded backoff, blocked state, privacy schema, and handler failure tests.
- GitHub Actions `governance-lint` performs a separate smoke run against a temporary SQLite database; it is NOT a permanently running worker.

## Exact state model

```text
PENDING -> RUNNING -> SUCCEEDED
                 \-> RETRY_WAIT -> RUNNING
                 \-> BLOCKED (attempt limit, unrecoverable)
RUNNING + expired lease -> RETRY_WAIT or BLOCKED
```

Every `claim` uses `BEGIN IMMEDIATE`, selecting a single ready job for the exact active phase and branch. Each attempt gets a random lease token. A previous worker that lost its lease cannot mark a job successful after a new worker claimed it. Results contain only `{check, passed}` and the queue persists only a digest, not raw model output or user files. IDs are idempotent: resubmitting the same ID and same immutable spec does nothing; a conflicting specification is rejected.

Retries are bounded by max attempts (1–5); `RETRY_WAIT` delays grow exponentially with a cap. Exhausted or expired unsuccessful jobs enter `BLOCKED`; there is no infinite tight loop. Because the job kinds are read-only and replay-safe, an interrupted job can be retried; mutable Git operations and external publishing must use a **separate** authorized tool transaction with stronger at-most-once and remote reconciling rules.

## CI usage / reproducible smoke

```sh
python -m unittest discover -s tests -v
python -m tools.dev_job_runner --smoke --repo-root . --db /tmp/zynoa-smoke.db
```

On Windows choose a temporary Windows-writable path for `--db`. The smoke job uses the repo's current `docs/state/PHASE.json` (must be `IN_PROGRESS`), enqueues exactly three allowlisted checks, claims each, verifies the real repository, persists completion and prints JSON. It never creates GitHub issues or commits.

**Expected result:** three `SUCCEEDED` checks; `commands_executed=0`, `github_writes=0`, `model_tasks_executed=0`, `worker_deployed=false`. These are declarations backed by this intentionally non-executing code path; not product capability claims.

## Data flow and ownership

```text
Verified PHASE.json + operator environment
           |
    Enqueue immutable safe job (SQLite WAL)
           |
    Claim exact phase/branch + lease token
           |
    Fixed read-only validator
           |
    SHA-256 result marker / retry / blocked
           |
    CI output + local DB checkpoint
```

The Python queue does not store prompts, file contents, private paths, raw traces, API tokens or GitHub credentials. Use a dedicated DB outside the source tree, restrictive OS permissions, tested backup and single-owner service configuration for actual host deployment. SQLite WAL supports multiple readers and one writer; `BEGIN IMMEDIATE` reserves a write transaction and may fail with SQLITE_BUSY under contention; host executor must implement bounded retry for lock contention in the future.

## Current security guarantees and limitations

- Allowed job kinds are enumerated constants; job payload is absent. Arbitrary subprocess invocation is not supported.
- Queue `claim` is phase- and branch-scoped. No next-phase code can execute while active phase is P00.
- Lease token and owner fence completions and heartbeats; expired attempts may be retried only because all current job kinds are read-only.
- Database `chmod 0600` is best-effort on POSIX, not an encrypted vault or independent credential store.
- SQLite is not a distributed lock across separate storage hosts. A future multi-node worker needs a stronger shared lease backend with fencing. Do not run multiple hosts on independent copies of the same DB.
- This is not a process sandbox. Actual untrusted model-generated code must be executed in a separately secured OS/container boundary with filesystem/network limits and approval broker.
- The queue does not yet capture performance metrics or map every failed job to a GitHub Issue automatically; that is P00 Issue #3 work.

## Research and decisions

Source documents reviewed for P00 (2026-11-18):

- [SQLite transaction BEGIN IMMEDIATE](https://www.sqlite.org/lang_transaction.html): explicit write transaction semantics; appropriate for atomic queue claim on one SQLite host.
- [SQLite isolation](https://www.sqlite.org/isolation.html): transaction isolation and WAL assumptions.
- [Git worktree](https://git-scm.com/docs/git-worktree): future isolated worktrees for coding jobs; worktree creation can involve checkout hooks/filters, and must not be mistaken for a security sandbox.
- [GitHub Rulesets](https://docs.github.com/en/repositories/configuring-branches-and-merges-in-your-repository/managing-rulesets): enforce protected main and required CI on actual GitHub.
- [P00 hosting research](../research/P00_WORKER_HOSTING_RESEARCH.md), [read-only observer runbook](P00_WORKER_RUNBOOK.md), [ADR-0009](../adr/0009-phase-observer-boundary.md).

## Remaining full autonomous development work

1. Safe worktree manager and controlled model/tool execution with genuine sandboxing, resource budgets and allowed paths.
2. Durable task planning/work dependencies and GitHub issue/PR linkage with strict remote idempotency.
3. Persistent host actually deployed with credential manager, heartbeat, crash recovery and backup verification.
4. Authenticated branch/ruleset policy and locked CI checks; no bypass of org review settings.
5. Reliable CI errors → sanitized Issues with no duplicate leaks (trusted source installation).
6. Tested PR auto-merge policy, post-merge verification and next-phase creation only after previous merge.

**Do not mark P00/M22 complete from the above read-only queue or unit tests.** The protected main rule, host provisioning and model-backed executor are still open blockers in [Issue #3](https://github.com/Vertex-Systems-Network/zynoa-2-local/issues/3).
