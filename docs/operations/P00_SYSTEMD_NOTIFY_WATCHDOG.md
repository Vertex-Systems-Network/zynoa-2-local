# P00 Linux systemd Readiness and Watchdog — Operator Contract

**Scope:** M22 P00 supervised read-only GitHub phase observer, existing draft [PR #1](https://github.com/Vertex-Systems-Network/zynoa-2-local/pull/1). **Source/template implementation only — no service installed, no remote host attestation.**

## Why this is needed

The previous systemd template used `Type=simple`. This can report an active process even though no authenticated GitHub reconciliation ever succeeded. A valid SQLite lease can likewise be renewed during transient remote failures and does not prove GitHub is currently reachable. `worker_observation_health` already separates last successful observation from lease activity. This slice connects that success boundary to the **main process** systemd readiness and watchdog protocol, so the operator-owned supervisor can distinguish process existence from recent useful remote work.

## Opt-in contract

- `tools.systemd_watchdog.SystemdWatchdog` is the service-only AF_UNIX datagram adapter. No extra pip dependencies, subprocesses, filesystem/credential reads, GitHub writes, AI model code or external URLs. It sends only fixed `READY=1` and `WATCHDOG=1` markers.
- `tools.phase_worker --systemd-watchdog` is explicit **operator opt-in**. Without this flag no systemd notification is sent. `--once` and bounded `--cycles` are incompatible with watchdog mode.
- Enabling the flag requires **Linux**, valid systemd-supplied `NOTIFY_SOCKET` and `WATCHDOG_USEC` (180–600 s), and a matching `WATCHDOG_PID` if present. Malformed, missing or mismatched values deny before the worker starts. Notification socket errors exit the process with sanitized failure; no automatic fallback to fake readiness.
- After `PhaseObserver.run_once()` validates the remote authenticated response, the current lease renews and the successful remote SHA/time evidence **commits to SQLite**. Only then does the *main worker process* send `READY=1\nWATCHDOG=1` on the first such observation or `WATCHDOG=1` on later successful observations. A successful observation may legitimately have `checks_passed=false` and `transition_ready=false` because P00 remains blocked; this is **service health**, never a merge permit.
- On a GitHub outage, invalid phase snapshot, stale lease or failed readback, the loop **does not** notify systemd, even though it may renew the SQLite lease to protect ownership during bounded retries. No "watchdog success" is inferred from an API error. systemd can then terminate/restart after its deadline. Outage-induced restarts cannot fix unavailable GitHub; the unit caps restart attempts and requires operator investigation of sustained failures.

## Restricted Linux service template

`deploy/systemd/zynoa-phase-observer.service` is still **not installed**. It now uses `Type=notify`, `NotifyAccess=main`, `WatchdogSec=300`, `TimeoutStartSec=150`, `Restart=on-failure`, `RestartSec=30`, `StartLimitIntervalSec=30min` and `StartLimitBurst=4`, and passes `--systemd-watchdog`. Other user/OS/readonly database protections remain. Actual host must run patched systemd and a dedicated restricted `zynoa` user, install credentials outside repo and configure separate host DB backups. A five-minute watchdog means successful observation must continue often enough; a stuck call or extended outage intentionally ceases keepalives.

**Operator-only acceptance after deployment:**
1. From a safe current P00 checkout, separately provision `/var/lib/zynoa` and service account; verify ownership/permissions and actual GitHub scoped read access. Read [Host Bootstrap](P00_HOST_BOOTSTRAP.md) and [Worker Runbook](P00_WORKER_RUNBOOK.md).
2. Authorized operator installs the reviewed unit, runs `systemd-analyze verify` and `systemctl daemon-reload`, enables/starts it, then reads `systemctl show zynoa-phase-observer.service -p Type -p ActiveState -p SubState -p MainPID -p WatchdogUSec -p Result -p NRestarts`. Record actual host identity, PID/UID and relevant supervisor journal without secrets.
3. Compare real service active PID/state to the separate [read-only last-success probe](P00_OBSERVER_HEARTBEAT.md) and authenticated live GitHub PR/check/issue API readbacks. A passing CI mock or local SQLite receipt does **not** prove this independent correlation.
4. On an isolated authorized host only, fail GitHub connectivity while keeping the process alive: confirm no new `WATCHDOG=1` is sent, the supervisor takes the documented recovery action, and no extra repo/issue/merge writes occur. Restore access, verify restart/new lease owner, fresh remote observation and actual backup/restore integrity. Record denial/error receipts.
5. Never grant model-generated code access to `NOTIFY_SOCKET`, rootless Docker daemon, host/systemd admin API, GitHub write token or phase-controller configuration. A forged readiness datagram is not independent service attestation.

## Verified source vs external gates

The new unit and Python adapter are exercised by fixture tests, including actual AF_UNIX datagrams on Linux and Windows policy-deny tests. GitHub-hosted CI does not install a user-owned systemd service or reproduce a real service watchdog action. **P00-T17 actual supervised host deployment remains BLOCKED** until the operator reports real machine/service/identity/restart evidence. P00-T19 rootless isolation, P00-T20 autonomous model patch/fix, P00-T18 ruleset and T21–T24 write/merge gates remain unresolved.

Official references (researched 2026-11-19): [sd_notify(3)](https://www.freedesktop.org/software/systemd/man/latest/sd_notify.html), [systemd.service(5)](https://www.freedesktop.org/software/systemd/man/latest/systemd.service.html), [systemd Exec isolation](https://www.freedesktop.org/software/systemd/man/latest/systemd.exec.html).

No desktop UI/screenshots, published Wiki, release or P01 implementation is claimed.


## P00-T28 Linux systemd remote-success watchdog — exact source CI verified (2026-11-19)

A new code slice on the **same** `phase/00-governance` branch added opt-in Linux systemd `READY/WATCHDOG` datagrams exclusively after authenticated GitHub observation and committed same-owner last-success SQLite evidence, plus restricted `Type=notify`/watchdog systemd **template** and Windows/Linux tests. The initial [CI #44412517931](https://github.com/Vertex-Systems-Network/zynoa-2-local/actions/runs/44412517931) failed one security test on both OSes: it expected zero journal events after unauthenticated remote refusal, but the production worker correctly persisted one sanitized `observation_blocked` audit event. This was fixed **in the test expectation only**, retaining failure logging and zero readiness/keepalive. No security check was relaxed.

Exact source commit [`1f8d0b284826`](https://github.com/Vertex-Systems-Network/zynoa-2-local/commit/1f8d0b28482681525a8b67aa2384e40923f705f9) succeeded on authenticated GitHub Actions [#44412717005](https://github.com/Vertex-Systems-Network/zynoa-2-local/actions/runs/44412717005): Linux `governance-lint` **298 Python tests PASS**, Windows suites including **13 systemd policy tests PASS (2 Linux-only datagram tests skipped on Windows)**, CHG-PR-GATE PASS (15 change records), PR task-manifest and non-mutating guarded-merge dry-run PASS. Tests include actual AF_UNIX Linux datagrams, hostile/missing systemd environment, notification send failure, no READY on unauthenticated or failed remote observation, durable heartbeat ordering, recovery/lease release, bounded Linux unit configuration and Windows fail-closed policy.

P00-T28 DONE means only a **tested P00 service/notification source contract**; change record `CHG-P00-M22-SYSTEMD-REMOTE-WATCHDOG-20261119` remains `implementing`, unmerged and unreleased, source SHA/run stored. Canonical task board is **28 total / 18 DONE / 3 IN_PROGRESS / 0 TODO / 7 BLOCKED = 64% scoped task count**, not evidence of P00 completion. The evidence-only checkpoint commit itself needs exact-HEAD CI verification. No real service/systemd, user-owned host, live model-backed edit/test/repair, OS sandbox, protected GitHub main, privileged PR writes, published Wiki/GUI, remote merge or P01 has been verified. Issue #3 remains OPEN; PR #1 DRAFT.

Next: exact HEAD evidence CI, maintain one phase/PR, and obtain independent operator-owned host/systemd/credential/remote API/restart proof, rootless sandbox and model repair, plus admin-installed protected main before closing Issue #3 or merging. Do not start P01 before independently verified P00 remote merge SHA.
