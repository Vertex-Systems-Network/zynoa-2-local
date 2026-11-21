# P00 — Durable Observer Success Heartbeat and Read-Only Local Probe

**Module:** M22 · **Active phase:** P00 · **Primary PR:** [#1](https://github.com/Vertex-Systems-Network/zynoa-2-local/pull/1) · **Status:** source / disposable CI tests only, not deployed.

## Purpose and boundary

The existing `worker_leases` table proves that a process recently renewed a SQLite lease, but a process could keep that lease while GitHub is unavailable. The `phase_events` journal intentionally deduplicates identical observations; its `created_at` does **not** advance on repeated successes. Consequently neither one is a trustworthy last-success freshness timestamp.

The P00 worker now writes a separate `worker_observation_health` row **only after** an authenticated `PhaseObserver.run_once()` call succeeds and the **same owner** still holds the unexpired lease. It stores exactly name, owner, observed-at timestamp and validated SHA-1-formatted 40-character Git IDs (PR HEAD and main). No GitHub response body, credential, model output or error message is stored. Failed observations may renew the lease for bounded retries but **do not refresh the last-success record**. An old owner or expired lease cannot update the row.

The new `tools.worker_health` CLI opens an **existing** operator-provisioned host DB in SQLite read-only mode. It validates `HostLayout` integrity, requires the active lease and success record to belong to the **same owner**, bounds the remaining lease lifetime to 180 seconds, requires a last-success age of 120 seconds or less by default (configurable 1–300), and rejects future timestamps, malformed SHAs, missing schema or links/invalid host roots. It never initializes a DB, runs a model, calls GitHub, creates a PR or changes the active phase.

## Actual operator workflow (no service installed by these commands)

1. Independently provision the dedicated operator host and `zynoa-phase-observer.service` per [Host Bootstrap](P00_HOST_BOOTSTRAP.md) and [Worker Runbook](P00_WORKER_RUNBOOK.md). Never share service secrets or rootless Docker privileges with the model.
2. In the trusted checked-out P00 code, validate the existing external host storage with `python -m tools.host_bootstrap --repo-root "$PWD" --host-root /var/lib/zynoa inspect`.
3. If and only if the observer service has separately been deployed and started by the operator, run:
   
   ```bash
   python -m tools.worker_health --repo-root "$PWD" --host-root /var/lib/zynoa
   ```
   
4. `RECENT_LOCAL_OBSERVER_EVIDENCE` means a matching lease and last successful remote-observation record were observed **locally**. This is not independent authentication of the currently running systemd process or remote GitHub state. Use `systemctl show zynoa-phase-observer.service`, checked PID/account/credential-store settings, remote Actions/PR readbacks and a real stop/restart test as **separate operator evidence**. Do not upgrade P00-T17 from this report alone.
5. `OBSERVER_NOT_FRESHLY_VERIFIED` or `BLOCKED` means missing/expired/mismatched/corrupt local evidence; inspect the service and remote connectivity without bypassing lease, privacy or merge controls. A one-shot `phase_worker --once` releases its lease and cannot yield a persistent-service success.

## Acceptance and limitations

- Tests create an isolated disposable checkout and external host root, exercise actual SQLite initialize/backup-compatible tables, crash/restart/stale/mismatched owner paths and run-loop heartbeat timing; Windows runs the same contract tests.
- No service is installed by GitHub CI, and self-reported SQLite data could be forged by a process with write access. Independently attested supervisor status, host identity, trusted GitHub readback and restart tests are still required.
- The new schema is additive. It is created when existing `WorkerLease` starts; existing data/journal is retained, not migrated destructively. Missing tables in a read-only probe fail closed rather than being created.
- A fresh observation means GitHub API reconciliation completed, **not that required CI passed, PR was merged, a coding model ran, or a sandbox is safe**. GitHub checks and open blocker issues remain separate.
- No application GUI/screenshot exists yet, and this source document is not a published GitHub Wiki page.

**External blockers:** [Issue #3](https://github.com/Vertex-Systems-Network/zynoa-2-local/issues/3) real host/service identity, managed credentials, approved sandbox/model worker, protected `main` and guarded PR writes. [Issue #4](https://github.com/Vertex-Systems-Network/zynoa-2-local/issues/4) is post-merge only. P00 PR #1 remains draft; no P01.


### SQLite WAL read-only nuance (CI regression corrected)

`mode=ro` protects application/database tables from mutation, **but it does not guarantee a byte-for-byte unchanged directory**. SQLite may create or maintain the `-shm` and `-wal` coordination sidecars for a WAL-mode DB while opening a read-only connection. This behavior is documented by [SQLite's WAL read-only rules](https://www.sqlite.org/wal.html#read_only_databases). Do **not** use `immutable=1` against a live worker DB merely to suppress sidecars: it can miss live uncheckpointed WAL changes and provide stale health status. The correct test compares actual database records and host metadata before/after, permits SQLite's own WAL sidecars, and explicitly closes connections to avoid Windows file locks. A deployment must ensure the observer identity can safely maintain private WAL sidecars without giving access to unrelated users.
