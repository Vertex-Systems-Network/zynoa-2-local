# P00 Research Decision — Persistent Controller Hosting & GitHub Authority

**Recorded:** 2026-11-18. **Status:** Source-reviewed candidates; deployment/performance NOT measured. **Scope:** P00/M22. **Related blocker:** Issue #3.

## Options evaluated

| Option | Unattended execution | Durable state | Cost / limitations | Decision |
|---|---|---|---|---|
| GitHub-hosted Actions on PR or schedule | Only bounded jobs, not a daemon | External state required for cross-run memory | CI useful; scheduled triggers may be delayed, run on default branch at >=5-minute intervals | Use for CI, not core continuous worker |
| Dedicated Windows/Linux workstation service | While machine powered and service running | SQLite WAL + backup + lease | Free software but requires powered host and secure secrets | Preferred local-first host |
| Always-on managed VPS/container | While hosting active | Volume-backed DB/managed DB | Potential operating cost and backup obligation | Optional later |
| Chat session as daemon | No | Chat context not authoritative durable state | Cannot run independently after session ends | Rejected |

## Authority and safety

- GitHub REST API provides actual PR, branch, check-run, issue, and merge facts. Local files and AI prose never substitute for verified remote truth.
- Least privilege: read-only observation token for Pull requests, Checks, Issues and repository metadata; separate restricted Issues(write) identity for trusted reporting; any eventual PR/Contents(write) merger requires reviewed policy.
- Never use a privileged token in a shipped desktop application, logs, public issue descriptions or untrusted PR jobs.
- CI PR runs read-only. A failure-reporting workflow_run executes trusted default branch code only, never checks out or executes untrusted PR content.
- Protect main with actual GitHub ruleset requiring PR, trusted checks and blocking force-push/direct-push; existing repository auto-merge preference is not sufficient.

## P00 implementation decision and current scope

1. Pure controller policy and durable SQLite WAL journal (tools/phase_controller.py).
2. Authenticated read-only GitHub API gateway (tools/github_gateway.py).
3. Renewable lease and repeated observation (tools/phase_worker.py); no code generation, GitHub write or merge permission in observer.
4. Separate gated developer-ci incident bridge (tools/github_issue_bridge.py) using sanitized fingerprints and explicit Issues(write) authorization. Trusted failure workflow activates only after merge into main.
5. Future guarded transition executor and AI coding/model workflows are distinct services requiring separate security acceptance.

## Required P00 completion evidence

- Deployed supervised host with heartbeat, lease/crash restart, file+DB recovery tests.
- Verified GitHub authentication, branch/PR/checks/sha readback and proper policy enforcement.
- Protected main branch ruleset; independent review of auto-merge conditions and token scope.
- Live end-to-end fault exercises on safe test repo or scoped non-destructive integration.
- Verified source/licensing, threats, CI, documentation and P00 PR merge before P01 branch.

## Official sources reviewed 2026-11-18

- GitHub Actions schedule/default-branch constraints: https://docs.github.com/en/actions/reference/workflows-and-actions/workflow-syntax
- Scheduling delays: https://docs.github.com/en/actions/how-tos/troubleshoot-workflows
- GitHub REST PRs: https://docs.github.com/en/rest/pulls/pulls
- GitHub REST Issues and permissions: https://docs.github.com/en/rest/issues/issues
- Protected branches: https://docs.github.com/en/rest/branches/branch-protection
- GitHub repo rulesets: https://docs.github.com/en/rest/repos/rules
- Checkout Node24 runtime: https://github.com/actions/checkout
- Python setup Node24 runtime: https://github.com/actions/setup-python

These documentation sources do not prove a worker has been deployed or benchmarked.
