# Initial Threat Model

## Trust boundaries
Native Rust broker > trusted controller configured policy > sandboxed execution worker > agent model output > browser search/retrieved documents > arbitrary project files/custom plugins.

## Threats / mitigations
1. **Prompt injection in downloaded docs/HTML/repo:** ignore embedded behavioral instructions; retrieved material is data; every tool call passes broker policy.
2. **Agent destructive shell commands:** allowlisted tools, sandbox, worktree snapshots, no host secrets, process resource limits.
3. **Malicious dependency install scripts / MCP/ComfyUI plugins:** isolate, pin/scan, deny unapproved executable extensions and network egress.
4. **Local inference API exposed remotely:** loopback binding only, permissioned IPC/ephemeral authentication, firewall review.
5. **GitHub token leakage:** segregated merge identity, minimum scopes, OS credential store, redacted logs, ephemeral credentials.
6. **Poisoned or tampered models:** pinned revisions/files, checksums, licenses; no unreviewed `trust_remote_code`.
7. **Untrusted PR CI:** read-only token for test jobs, avoid elevated triggers with untrusted checkout.
8. **Cache exfiltration/private documents:** local encryption consideration, scoped document permissions, audit, default local processing.
9. **Inaccurate AI test summary:** use CI logs and deterministic verification, never model prose as pass evidence.
10. **Runaway autonomous loop:** bounded retries, watchdog, circuit breaker, state recovery and phase lock.

Document residual risks and platform-specific constraints before release. This document is not a completed security review.

## P00 queue and GitHub policy hardening (2026-11-18)

**Threat: duplicate/exhausted worker claims.** Queue claims use SQLite `BEGIN IMMEDIATE` and lease tokens to fence stale completion. Crash expiry safely retries only preapproved read-only checks, not irreversible Git changes. Multi-host copies of SQLite are explicitly unsupported. Concurrency and restart tests exist but are not real host deployment proof.

**Threat: fake green CI / hollow protection.** Merge gate must confirm authenticated effective branch rules include PR requirement and pinned required status check identity; `protected=true` or a matching check name alone is not sufficient. Any missing rules/permissions fail closed. Repository `main` is currently not protected, and merger must remain disabled.

**Threat: arbitrary execution via queue.** Only `phase-policy`, `design-spec` and `docs-integrity` handlers exist. No task payload, command string, dynamic tool import or external code execution is accepted. A future model-backed executor must use OS sandboxing and capability broker with separate GitHub write authority.

**Residual risks:** SQLite queue is not a distributed lease across independent machines; permissions on Windows must use OS ACLs; there is no deployed credential manager, permanent worker, worktree sandbox, E2E autonomous loop or completed security review. Reference [P00 queue spec](../operations/P00_DURABLE_JOB_QUEUE.md).

## P00 dependency graph threats and controls (2026-11-18)

- **Out-of-order execution:** Child jobs cannot claim while any prerequisite lacks committed SUCCESS, regardless of higher priority. Graph edges are phase/branch-scoped and change only before execution begins.
- **Cycles / stuck scheduler:** Atomic recursive-CTE cycle detection rejects direct and indirect cycles. Rejected multi-edge batch rolls back all inserted edges.
- **Corrupted graph or orphan prerequisite:** Claim uses a LEFT JOIN to treat missing parent as unsatisfied, and reconciliation marks the downstream job BLOCKED rather than silently running it.
- **Failure cascade:** Terminal BLOCKED prerequisites propagate to descendants; independent tasks remain eligible.
- **Scope boundary:** DAG coordinates only fixed read-only checks; it is NOT a sandbox, cannot authorize shell/models/Git writes, and should not store raw prompts, secrets or private paths. A separate broker and OS containment are still required.
- **SQLite limits:** BEGIN IMMEDIATE can encounter SQLITE_BUSY under writer contention; bounded retry/host deployment proof is pending. Independent multi-host SQLite copies are unsupported.

See [P00 DAG](../operations/P00_TASK_DEPENDENCY_GRAPH.md), [ADR-0010](../adr/0010-phase-task-dag.md) and [Issue #3](https://github.com/Vertex-Systems-Network/zynoa-2-local/issues/3).

## P00 model-facing worktree and path scope boundary (2026-11-18)

- **Git worktree is NOT an execution sandbox.** Git's local hooks/config/filters can invoke programs; only a new disposable trusted repo is used for the P00 Git command integration test. The application must never treat arbitrary downloaded/user-controlled .git metadata as trusted without separate isolated handling.
- **Path traversal and secret files:** model-facing path scope accepts only relative P00/phase branch paths, forbids Windows drive/UNC/backslash, traversal, invisible Unicode, reserved Windows device names, hidden credential variants, Git metadata and protected controller/security/CI/state files.
- **Symlink and Windows junction escape:** lexical ancestor checks and resolved-root comparisons reject common escapes. This is a policy *preflight*, not atomic secure file I/O: TOCTOU and reparse-point races must be addressed in OS broker. True Windows ACL/long path/reparse tests remain unverified.
- **No self-authorization:** policy objects and worktree roots are created by a trusted host, not retrieved content/model text. Git worktree plan is returned but not executed by current runtime. Actual untrusted model code needs OS isolation, restricted network/process identity and durable operation receipts.
- **No false green:** a disposable worktree fixture proves Git argv behavior, **not** safety of executing arbitrary repository code, actual worker deployment or product release.

See [worktree security contract](../operations/P00_WORKTREE_POLICY.md), [ADR-0011](../adr/0011-worktree-is-not-sandbox.md), and unresolved [Issue #3](https://github.com/Vertex-Systems-Network/zynoa-2-local/issues/3).

## P00 durable observer state / host bootstrap threats (2026-11-18)

- **Secrets & user data:** Host's SQLite `phase_events` and `worker_leases` contain sanitized operational records only; no GitHub token, chat history or user attachment copied. Host metadata records role/schema, not credentials. Product vault/backup belongs to P01+ and is **not** implemented by observer backups.
- **Path escape / symlink or junction:** `HostLayout` refuses relative/overlapping checkout roots, symlinks/junction-like components and mismatched P00 authority. Path validation is not race-free secure filesystem open; operator-owned ACL and no-follow broker remain mandatory for code execution.
- **SQLite WAL corruption:** Never raw-copy live `.db` without WAL; `Connection.backup()` creates an isolated consistent snapshot, SHA-256 receipt, integrity check and disposable restore drill. Interrupted backup may leave an orphan snapshot requiring independent reconciliation; it cannot be treated as complete without its sidecar.
- **Windows open handles:** Python sqlite3 context managers COMMIT but do not CLOSE. Changed EventJournal/WorkerLease to explicit `closing(...), db`; verified Windows temporary-file cleanup and recovery tests. A fake passing CI isn't sufficient for actual host deployment.
- **Windows scheduled task:** Current-user `Interactive` + limited runlevel; at-logon task requires user logged in, is not guaranteed 24/7 or secure service. Tokens must come from operator-managed OS secret store and never exposed to generated code.
- **Linux systemd:** Templates run dedicated non-root user and restricted write paths, but operator must secure EnvironmentFile credentials or move to encrypted service credential system. No service installed by GitHub CI.
- **Backup durability:** One local disk, unchecked retention or missing off-host encryption cannot guarantee data survival; actual operator off-host backup and restoration tests are still a release blocker.

Details: [P00 Host Bootstrap](../operations/P00_HOST_BOOTSTRAP.md) and [Issue #3](https://github.com/Vertex-Systems-Network/zynoa-2-local/issues/3).
