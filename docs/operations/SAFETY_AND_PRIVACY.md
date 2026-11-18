# Safe Autonomous Actions & Privacy

**Development autonomy:** one-time administrator configuration of repo scope, workflow scopes, allowed binaries, allowed network endpoints, resource limits and automatic PR merge policy. Within this envelope, no per-command confirmation. Outside it, broker denies, creates a blocker or private security incident, and continues safe tasks; it does not silently escalate.

**User autonomy:** end users opt in once to remote diagnostics or remain local-only. Product can recover, reopen or group errors automatically without transmitting private content. Do not infer that asking for automated development implies permission to upload every end user's private data to public GitHub.

**Threats:** prompt injection from repos/webpages, escaped filesystem scope, hostile custom nodes/plugins/MCP, RCE in downloaded artifacts, malicious model configs, secrets exposure via error report, SSRF and tokens bundled in client, CI tampering, PR policy bypass and model behavior confusion.

**Defenses:** native policy broker, isolated worktrees/low privilege, signed artifacts, security warnings, no raw logs in issues, minimal GitHub App permissions, rate limits and security quarantine. Test with intentionally hostile fixtures and prove denial. Separate policy authority from AI reasoning. Detailed threat model lives in `docs/security/THREAT_MODEL.md`.
