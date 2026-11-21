# ADR-0016 — Successful Remote Observation Heartbeat Is Separate from Worker Lease

**Date:** 2026-11-19 · **Status:** P00 source-level decision; deployed host not verified.

## Context
The SQLite worker lease measures ownership/liveness, not remote observation success; failed GitHub calls may refresh the lease. The journal deliberately deduplicates identical remote snapshots. A process can therefore have a fresh lease while the latest successful remote reconciliation is arbitrarily stale.

## Options
1. Reuse lease expiration as the success indicator — rejected because failures legitimately renew the lease during bounded backoff.
2. Use newest `phase_events.created_at` — rejected because deduplication intentionally prevents identical successful snapshots from creating events.
3. Persist a separate, owner-fenced last-success heartbeat — **chosen**. A transaction requires the caller still hold the unexpired active lease, recording only bounded time and validated remote Git SHAs.

## Implications
The read-only local probe compares the same owner across current lease and success row, with time limits and no credentials or raw responses. An earlier successful observation cannot be transferred to a new lease owner. The new table is additive. These values remain local evidence only; independent systemd/process, GitHub authority and real host restart tests are still required before T17 can pass. No GUI, model code execution, remote write, phase transition or GitHub merge is authorized.

See [P00 Observer Heartbeat](../operations/P00_OBSERVER_HEARTBEAT.md) and [Issue #3](https://github.com/Vertex-Systems-Network/zynoa-2-local/issues/3).
