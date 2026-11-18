# ADR-0017 — systemd Readiness/Watchdog Tied to Verified Remote Work

**Date:** 2026-11-19 · **Status:** P00 source-level implementation; no installed service verified.

## Decision context
A background process may be alive (systemd `Type=simple`, SQLite lease active) while GitHub readback is unavailable. [ADR-0016](0016-success-heartbeat-not-lease.md) added last-success evidence, but the old unit still reported merely process liveness.

## Considered alternatives
1. Keep `Type=simple` and trust restart-on-crash: rejected because it does not detect broken remote reconciliation.
2. Periodic `WATCHDOG=1` independent of GitHub: rejected because it validates a local timer, not the useful work being supervised.
3. **Selected:** owner-verified GitHub remote observation + committed last-success SQLite record → main-process `READY/WATCHDOG` datagram; only successful cycles refresh watchdog.

## Effects and tradeoffs
- Restricted opt-in Linux adapter and `Type=notify` service unit with bounded watchdog/restarts. No write tokens or model tasks exposed.
- During external GitHub outages, systemd intentionally restarts or rate-limits the observer instead of showing a permanently healthy service; this can require operator diagnosis and does not guarantee availability.
- Short `--once` CI observations never send readiness. Missing `NOTIFY_SOCKET`, invalid/mismatched `WATCHDOG_PID` or notification errors are denied.
- This is a **source contract**, not attested production systemd/host or proof of any autonomous coding/merge. Independent real service deployment, permissions and restart/receipt tests remain mandatory for P00-T17.

[Operator contract](../operations/P00_SYSTEMD_NOTIFY_WATCHDOG.md) · [Infrastructure Issue #3](https://github.com/Vertex-Systems-Network/zynoa-2-local/issues/3).
