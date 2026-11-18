# P00 Host Bootstrap, Durable Observer Storage, Backup & Recovery

**Module:** M22 · **Phase:** P00 · **Owner:** trusted operator / external developer host.
**Status:** Implemented bootstrap/backup/drill utilities and OS service **templates** on draft [PR #1](https://github.com/Vertex-Systems-Network/zynoa-2-local/pull/1). **NOT INSTALLED on a persistent user-owned host.** No model-backed coding service or automatic merge is running.

## Why this slice matters

The existing P00 `tools.phase_worker` is a **read-only GitHub observer**. Without a host data directory separate from Git/source, SQLite WAL-safe backup/restore, OS-specific startup configuration and trusted credentials, it cannot reliably survive interruption. This implementation supports deterministic host provisioning and recovery checks; it does **not** give models shell access, turn ChatGPT into a background service or permit P00 to merge without actual GitHub protection.

## Files and trust boundary

| Item | Purpose | Current permission |
|---|---|---|
| `tools/host_bootstrap.py` | Validate exact P00 scope; explicitly initialize persistent host folders; inspect SQLite consistency; online backup + verified restore drill | Does not execute model/worker or GitHub write |
| `tools/phase_controller.py`, `tools/phase_worker.py` | Event journal and renewable single-owner worker lease | SQLite connections now explicitly close; Windows locked-file tests |
| `deploy/systemd/zynoa-phase-observer.service` | Linux read-only observer unit with ExecStartPre verified DB | Template; no service installed |
| `deploy/systemd/zynoa-phase-observer-backup.service` and `.timer` | Linux on-disk SQLite consistency snapshot and restore drill | Template; not enabled |
| `deploy/windows/Install-ZynoaObserverTask.ps1` | Optional current-user Task Scheduler **at-logon** observer; preview is default, registration requires `-Install` | Not a 24/7 Windows service |
| `tests/test_host_bootstrap.py` | Trusted temporary data directory, no-auth failure, WAL snapshot, integrity, stale/corrupt backup, schema corruption, scope denial, Windows teardown | Disposable fixture only |

The host path **must be absolute and outside** the source checkout, not symlink/junction redirected. The P00 phase/PR/branch must match tracked state. Initializing does not modify `AGENTS.md`, `PHASE.json`, `main`, GitHub PRs or worktrees.

## Storage data flow

```text
Trusted operator selects absolute host root (outside source)
    |
    +-> state/controller.db + WAL
    |     - phase_events append-only event journal
    |     - worker_leases single owner records
    |     - no GitHub tokens or raw model prompts stored here
    |
    +-> backups/controller-YYYYMMDDTHHMMSSZ-<random>.sqlite
    |     + .sha256 sidecar
    |     - SQLite Connection.backup() produces consistent snapshot
    |     - PRAGMA integrity_check / required table checks
    |     - separate disposable restore drill and count verification
    |     - live DB is NEVER overwritten by drill
    |
    +-> host.json (schema, phase, read-only role, no secrets)
```

On POSIX, directories are created mode 0700 and database/metadata 0600; Windows mode bits **do not prove ACL isolation**. Real Windows account ACL, service-identity restrictions, DPAPI/Credential Manager and Windows reparse-point handling still require host integration testing before turning on model-written code. No filesystem path is returned in user-visible JSON status by default.

## Local CLI: initialize then inspect and backup

Choose a secure writable root already owned by the dedicated observer identity. These commands are illustrative; adjust paths and confirm actual checkout, OS identity and disk space first.

```bash
# Linux, run inside trusted checked-out P00 source
# Do not put the DB under the Git repository or application's binary folder.
ZYNOA_HOST_INIT_ALLOWED=1 python -m tools.host_bootstrap \
  --repo-root "$PWD" --host-root /var/lib/zynoa initialize

python -m tools.host_bootstrap \
  --repo-root "$PWD" --host-root /var/lib/zynoa inspect

python -m tools.host_bootstrap \
  --repo-root "$PWD" --host-root /var/lib/zynoa backup
```

An initialization repeat **refuses to overwrite** an existing DB or host identity; run `inspect` instead. A failed or partial backup never deletes the sole live DB. To verify a particular backup snapshot without replacing any live state:

```bash
python -m tools.host_bootstrap --repo-root "$PWD" \
  --host-root /var/lib/zynoa verify-backup \
  --name controller-20261118T120000Z-aaaaaaaaaaaa.sqlite
```

Replace the sample filename with the actual verified output. Missing checksum, mismatched digest, missing required SQLite tables, invalid path, filesystem permission failure and corrupted database are BLOCKED, not auto-repaired. The command prints sanitized status/error classes without credential values or private host directory paths.

A single-device local snapshot does **not** protect against total device failure or ransomware. Configure independently encrypted, access-controlled, off-host copies, retention/disk space policy and tested cross-device restore at a later verified operator stage. **Do not** copy a live SQLite DB without the online backup API. Snapshot creation itself does not implement the product's P01/P03 user vault/chat history backup requirements; those remain separate.

## Linux service and backup timer (templates, not installed)

The versioned systemd unit:
- Runs as a dedicated `zynoa` non-root account, not an administrator.
- Uses `ExecStartPre` `tools.host_bootstrap ... inspect` to refuse a broken/missing host DB.
- Starts only `tools.phase_worker` observer with DB `/var/lib/zynoa/state/controller.db`.
- Restarts on failure and applies baseline systemd security restrictions.
- A separate timer triggers `tools.host_bootstrap ... backup` daily, using SQLite's consistent online backup while observer may be active.

An authorized server operator must explicitly install and validate unit files, create the restricted user, protected `/etc/zynoa/observer.env` credential configuration and host state, set ownership/ACLs, then test `systemctl status`, live heartbeat, SIGTERM restart, lease recovery, backup timer and verified remote GitHub readback. **The GitHub connector did not install systemd or create a live service.**

Environment files with tokens are still sensitive and may propagate secrets to child processes; a dedicated credential store / `LoadCredential` identity is preferable. The read-only observer's token must never be passed to a model, PR CI or distributable client binary.

## Windows preliminary option (not headless 24/7)

```powershell
$env:ZYNOA_HOST_INIT_ALLOWED = '1'
python -m tools.host_bootstrap --repo-root 'C:\path\to\zynoa-2-local' --host-root 'C:\ZynoaObserverData' initialize
Remove-Item Env:\ZYNOA_HOST_INIT_ALLOWED

# Preview only: validates local host DB and shows task metadata.
& 'C:\path\to\zynoa-2-local\deploy\windows\Install-ZynoaObserverTask.ps1' -RepoRoot 'C:\path\to\zynoa-2-local' -HostRoot 'C:\ZynoaObserverData'

# Requires separately approved local installation and valid stored identity.
# Add -Install only on the owned Windows machine once identity/ACLs are checked.
```

The Windows task uses current-user, low privileges, logon trigger, a fixed P00 observer command, no implicit overwrite of an existing task, and a bounded restart configuration. It runs only when the user is logged on; it **cannot satisfy the project's unattended 24/7 requirement**. For truly unattended Windows service execution a dedicated service account, real Windows service wrapper, secure credential retrieval, ACL/mount containment and real restart/heartbeat tests are still necessary. No user-host install is verified.

## CI evidence, error/warning resolution

The GitHub workflow runs:
1. Complete Python unit tests for both controller and host storage, including Windows locked-file regression.
2. Linux ephemeral `initialize → inspect → online backup → restore drill`.
3. Windows ephemeral `initialize → online backup → logon-task PREVIEW_ONLY` plus isolated host recovery tests.
4. Read-only GitHub phase observer, PR task manifest validator, guarded merge dry-run, change-record gate.
5. No tests install a persistent service, run model inference, set GitHub write tokens or publish a release.

The Windows path/SQLite backup failures found during development were **not hidden**; production connection close and file fsync handling were corrected and rerun. The latest exact CI HEAD, not this document alone, is the acceptance evidence.

## Distinct incomplete acceptance gates

**Storage bootstrap may be marked implemented** only after actual Linux+Windows CI succeeds and reliable backups/restore drills pass. But the wider P00 criteria remain BLOCKED:
- Actual *user-owned host* deployment, supervisor status, heartbeat and restart proof.
- Genuine local Ollama runtime + coding model capability measurements.
- Independent OS sandbox, process/network/file-handle broker and safe AI code execution.
- Protected GitHub `main` with a trusted required check and scoped write identity.
- One unattended safe test-repo plan → patch → test → error fix → existing PR CI → guarded transition proof.
- No fabricated graphical screenshots, user-facing release, Wiki publication or next P01 phase.

[Issue #3](https://github.com/Vertex-Systems-Network/zynoa-2-local/issues/3) remains the real P00 infrastructure blocker. [Post-merge Issue #4](https://github.com/Vertex-Systems-Network/zynoa-2-local/issues/4) applies **after** actual merge verification. Preserve [PR task manifest](../state/pr-tasks/P00.json) and existing [one-phase-one-PR policy](PR_TASK_TABLES.md).

## Source research (official)

- [SQLite online backup API](https://www.sqlite.org/backup.html) — consistent snapshots with active writes.
- [Python sqlite3 backup + connection closing semantics](https://docs.python.org/3.12/library/sqlite3.html) — context manager does not implicitly close.
- [systemd credentials](https://systemd.io/CREDENTIALS/) and [systemd.exec](https://www.freedesktop.org/software/systemd/man/latest/systemd.exec) — credentials and process isolation.
- [Windows Task Scheduler security contexts](https://learn.microsoft.com/en-us/windows/win32/taskschd/security-contexts-for-running-tasks) — least-privileged principals.
- [Windows logon trigger](https://learn.microsoft.com/en-us/windows/win32/taskschd/logontrigger) — requires user logon; not a persistent system service.


## P00 systemd watchdog deployment supplement (2026-11-19, template only)

The service template now uses `Type=notify` instead of `Type=simple`, `NotifyAccess=main` and `WatchdogSec=300`. It starts the read-only observer with `--systemd-watchdog`. Readiness is sent only after an independently authenticated GitHub observation and durable owner-fenced last-success commit. The host operator must validate real service `MainPID`/UID, active state, credential permissions, watchdog expiry and restart behavior; SQLite/CI evidence alone does not satisfy P00-T17. On GitHub outage no keepalive is sent, so the supervisor may rate-limit restart attempts; that is a visible blocker, not an auto-repair success. [Exact operator runbook](P00_SYSTEMD_NOTIFY_WATCHDOG.md).
