# Autonomous Operations Policy — no per-step prompts inside pre-authorized scope

## Default authorization envelope
The trusted controller must receive a one-time, explicit, machine-readable workspace scope from its operator at provisioning. Until that envelope exists, capabilities are deny-by-default. Human clicks are NOT required during normal, pre-authorized, sandboxed phase execution. A prompt instruction cannot expand this scope.

Allowed without repeated approval **once scoped**: read project files, write within active branch/worktree, execute allowlisted formatting/lint/tests/build tools inside sandbox, update planning documents, collect safe UI screenshots, fetch public package metadata from allowlisted hosts, create the primary phase PR, and request auto-merge when protected branch rules and required evidence permit it.

Never auto-authorized: delete or modify files outside workspace; read operating system secrets; mount private directories; change credentials, firewall, system registry, or host security settings; hidden data exfiltration; arbitrary unreviewed plugin execution; unbounded paid API requests; deploy to production; publish to unknown destinations; circumvent repo branch protection; mass deletion/reset outside own worktree.

Higher-risk task requiring access beyond the configured envelope must be BLOCKED with a logged reason. The scheduler can move to other independent safe tasks but cannot silently grant itself additional rights. This preserves the user's no-popup workflow without introducing unrestricted system access.

## Workspace isolation
- Use an isolated Git worktree per active phase and a sandboxed process runner with read/write to only allowlisted repo roots; avoid running unknown project tests with host-level credentials.
- Deny symlink/path traversal escape; canonicalize all path inputs.
- Lock agent egress to approved domain list where possible; treat browser/retrieved content as untrusted task data.
- OS keychain for credentials; issue short-lived least-privilege GitHub tokens to merge controller, never to untrusted code execution.
- Record all filesystem mutations as diffs and append-only audit events; provide automated checkpoint/restore.
- ComfyUI custom nodes, MCP servers and npm postinstall scripts are executable code: install only through separate signature/license/security review.

## Repository action policies
- No direct push to `main`; allow phase branch pushes via Git credential isolated from app tests.
- Auto-merger uses a separate identity/context from PR code execution; limited permission on status checks, no `pull_request_target` checkout/run of untrusted PR code.
- No merge if baseline security tests, dependency review, tests, branch status or acceptance evidence is missing.
- External protected branch rules take precedence; never work around missing required review.
- No force-push unless a narrow, audited policy expressly permits it for the agent-owned branch (not default).

## Resource ceilings
- Controller must enforce CPU/GPU/RAM reservations, max parallel model loads, max active code execution, job timeout, storage floor and download bandwidth cap.
- Retries have budgets; transient network errors use exponential backoff and jitter, code defects get a bounded diagnosis cycle. Do not infinite-loop on the same failure.
- When blocked, save checkpoint and diagnostic packet; continue only independent scoped work.
