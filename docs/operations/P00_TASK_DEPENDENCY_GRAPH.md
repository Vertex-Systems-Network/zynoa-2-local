# P00 Task Dependency Graph — Durable Phase-Scoped DAG

**State:** Implemented SQLite dependency primitive and local tests on P00 draft PR #1. This is NOT a deployed coding agent, true OS sandbox or an autonomous GitHub merger. **Module:** M22.

## Purpose

Autonomous development tasks must respect pre-development, test, documentation and verification order even when asynchronous workers, priority changes, crashes and retries occur. A task's successful predecessor is a *database-enforced requirement*, not an instruction to a language model. Independent tasks may continue safely when unrelated tasks are blocked. All work remains within the active phase and branch.

## Architecture and data contracts

- Canonical database: `tools/dev_job_queue.py` creates SQLite WAL `development_jobs` and `job_dependencies` tables, indexed for claim and reverse lookup.
- `tools/dev_task_graph.py` adds immutable, **phase/branch-matched** dependency edges using `BEGIN IMMEDIATE` transactions. Duplicated same edges are idempotent.
- Each edge `(job_id, depends_on_job_id)` means child cannot claim until prerequisite has durable `SUCCEEDED` status.
- Cycle detection uses a recursive SQLite CTE inside the same transaction. Self-reference, multiple identical edges, missing parents, cross-phase/branch edges, more than 32 edges per call, and modifications after a job has started are rejected.
- `JobQueue.claim()` excludes tasks with any incomplete/missing prerequisite even if those tasks have the highest priority. Multiple eligible independent jobs still sort by priority then insertion time.
- A permanently BLOCKED parent causes its dependents to become BLOCKED with `DependencyBlocked` on reconciliation; propagation is transitive. A missing parent record in a damaged SQLite DB also blocks the child—never treats corruption as satisfied.
- Stale worker tokens cannot alter success, and only the queue's **three fixed read-only** job types can run in P00.

## Actual data flow

```text
P00 PHASE.json + authorized branch
              |
     Enqueue immutable safe jobs
              |
      Add dependency edges (DAG)
              |
 BEGIN IMMEDIATE + cycle/phase checks
              |
 Claim: all predecessors SUCCEEDED?
           /                    \
        NO                        YES
        |                          |
   Remain pending          Assign token + lease
        |                          |
 Failed prerequisite      Fixed read-only handler
        |                          |
   BLOCKED; log           Store digest + SUCCEEDED
```

## Real CI smoke order

The `python -m tools.dev_job_runner --smoke --repo-root . --db <writable-temp-db>` command enqueues these three allowlisted jobs with **inverse priorities** to prove dependency enforcement:

1. `p00-phase-policy` — validate actual local P00 phase state.
2. `p00-design-spec` — validate DESIGN-IO deferral / plan.
3. `p00-docs-integrity` — verify required agent and module handoff documentation.

The runner validates the exact order and all three `SUCCEEDED` statuses. Network/GitHub mutation, model inference and shell execution remain **zero** in this P00 smoke.

## Testing and recovery

`python -m unittest discover -s tests -v` covers: nested and direct cycles; same-branch and cross-phase rejection; multi-edge atomic rollback on failure; duplicate idempotency; restart persistence; high-priority dependent blocked; transient retry; terminal blocked cascade; independent task scheduling; missing/corrupt parent; illegal IDs; concurrent job claims and stale leases.

The DAG is persisted in the same SQLite DB as job queue state, enabling crash recovery. For actual use, database backups and restoration must be tested on a dedicated host. The current GitHub Actions runner uses a temporary DB and **is not the continuously running worker**.

## Limits and later execution phases

- The graph does not run a language model or apply file patches, and it does not record unrestricted prompts, private paths, secrets or raw error traces.
- Each dependency belongs to an already-enqueued job. Dynamic changes to an in-progress or completed job's dependency graph are prohibited; submit a new immutable job ID for modified work instead.
- This is a per-host SQLite transactional DAG, not a distributed scheduler shared between machines with independent databases.
- Do not encode irreversible operations (Git push, PR merge, deployment, filesystem write) as replay-safe queue job kinds. They require a separate policy broker and remote idempotency/receipt checks.
- P00 still requires supervised worker host deployment, sandboxed AI/coding tool execution, GitHub `main` ruleset activation and real end-to-end issue and merge verification (tracked in [Issue #3](https://github.com/Vertex-Systems-Network/zynoa-2-local/issues/3)).
- Module M22 GUI, actual option screenshots, published Wiki pages and installer are **not available yet**. No app feature is declared complete.

## Related project references

[P00 Durable Job Queue](P00_DURABLE_JOB_QUEUE.md) · [P00 Worker Runbook](P00_WORKER_RUNBOOK.md) · [Autonomous Loop](AUTONOMOUS_LOOP.md) · [M22 Module](../modules/M22.md) · [Threat Model](../security/THREAT_MODEL.md).

Upstream references: [SQLite WITH RECURSIVE](https://www.sqlite.org/lang_with.html), [SQLite transactions](https://www.sqlite.org/lang_transaction.html). These are interface references, not performance verification of the installed desktop client.
