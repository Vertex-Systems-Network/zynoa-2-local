# P01-T06 M18 native diagnostics foundation

**Status:** P01-T06 IN_PROGRESS; native spool source committed for Windows CI. **NOT connected to live runtime**. The module is not shipped, shown in the UI, or approved for end-user data capture.

The native Rust API accepts only compile-time allowlisted module, severity and error code plus a numeric timestamp. It never receives free-form crash text, stack traces, file paths, secrets, prompts or user content. JSONL spool is append/sync-before-acknowledgement, capped at 1 MiB, 512 bytes per line and 128 distinct groups; counters are bounded and replay refuses corrupt files without resetting their contents. There is **no automatic issue publishing**, no cloud calls, and no WebView diagnostic command.

A verified per-user directory outside the binary must come from the future M24 registry. This slice deliberately does not invent a default app-data path. Parent ownership, race-safe creation and rotation, safe crash capture/restart, privacy preview and consent, M18 end-user screens, and real screenshot/recovery evidence remain T06 acceptance work. Do not mark T06 DONE until those requirements are verified.

Verification is GitHub-hosted Windows Rust cargo tests and desktop build, Python contracts, Governance v3.2 and task-board CI.
