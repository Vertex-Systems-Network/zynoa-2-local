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
