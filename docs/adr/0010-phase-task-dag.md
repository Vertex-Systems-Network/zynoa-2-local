# ADR-0010 — Phase-Scoped Dependency DAG Before Autonomous Coding

**Status:** Accepted for P00 read-only scheduler foundation. **Date:** 2026-11-18. **Owners:** M22 Governance. **Not a shipped desktop feature.**

## Problem

An autonomous development controller cannot rely on prompts saying "do tests before docs before merge". Multiple agents, priorities and retries may cause out-of-order work; a failed prerequisite could allow downstream implementation or documentation to claim success incorrectly.

## Decision

Extend the durable SQLite JobQueue with a version-independent `job_dependencies` table and `tools/dev_task_graph.py`.

- Each dependency edge is an immutable parent prerequisite ID, on the SAME active phase and branch; cross-phase or cross-branch edges are prohibited.
- Register dependencies transactionally via `BEGIN IMMEDIATE`, check cycles with a recursive CTE and reject self loops.
- Enforce dependencies directly in `JobQueue.claim()`. A high-priority job with an unfinished prerequisite remains unclaimable; any independent task can still run.
- Failed prerequisites cause downstream jobs to enter terminal `BLOCKED` (transitive). Corrupt/missing dependency records fail closed.
- Every edge is idempotent; edge modifications are prohibited once the dependent job starts.
- Restrict this graph to existing read-only job kinds. No untrusted shell, model execution, GitHub mutation, deployment or filesystem change in the replay-safe DAG.
- Keep current SQLite schema transactionally updated in the same local DB. A separate host with a copied DB is unsupported.

## Why this architecture?

Pure prompt ordering is unverifiable. A queue with only priorities can execute documentation or release tasks before prerequisite checks. A graph without cycle detection can stall indefinitely. An external distributed orchestrator would introduce hosting/credentials complexity before P00 host provisioning and benchmarks. SQLite CTE + single-writer transactions already match the chosen P00 local-first queue.

## Alternatives and limits

- **Priority-only queue:** rejected, cannot enforce sequential dependencies.
- **Arbitrary agent-created executable DAG:** rejected until capability brokerage and OS sandbox are validated.
- **Multi-host distributed execution:** deferred; independent SQLite copies cannot guarantee a shared lease/phase lock.
- **Force unblocking after retries:** rejected; a permanently blocked prerequisite requires a new versioned recovery plan, not a fabricated SUCCESS.

## Test evidence and acceptance

`tests/test_dev_task_graph.py` covers direct/indirect cycles, batch rollback, stage ordering overriding priority, cross-phase/branch protection, restart durability, retry, independent tasks, corrupt/missing prerequisites and blocked cascades. The existing queue tests still cover concurrent claims and stale token fencing. `tools/dev_job_runner.py --smoke` proves the graph controls three real governance checks despite inverse priorities.

The PR's GitHub Actions logs, not this ADR, are authoritative for latest test results. No persistent worker or real code editing is implied.

## Source research

- [SQLite recursive queries](https://www.sqlite.org/lang_with.html): `WITH RECURSIVE`, cycle-safe `UNION`.
- [SQLite transactions](https://www.sqlite.org/lang_transaction.html): `BEGIN IMMEDIATE` can return SQLITE_BUSY under contention.
- [SQLite isolation](https://www.sqlite.org/isolation.html): transaction visibility and local SQLite writer constraints.
- [P00 task graph](../operations/P00_TASK_DEPENDENCY_GRAPH.md), [P00 durable queue](../operations/P00_DURABLE_JOB_QUEUE.md), [Issue #3](https://github.com/Vertex-Systems-Network/zynoa-2-local/issues/3).

**Unresolved P00 gates:** protected main ruleset activation, actual supervised host, genuinely sandboxed model-backed code worker, trusted GitHub write receipt verification and published Help/Wiki/screenshots.
