# ADR-0011 — A Git Worktree Is Not a Sandbox: Split Planning From Execution

**Date:** 2026-11-18
**Status:** Accepted for the P00 path-capability + plan-only slice; full OS sandbox and model execution remain BLOCKED.
**Module:** M22. **Branch:** `phase/00-governance`, same primary PR #1.

## Context

Zynoa's autonomous coding capability needs concurrent tasks without affecting the protected main checkout, user's files or GitHub state. The P00 controller already contains a read-only durable task queue and DAG, but the next step needs a filesystem authority model and a Git worktree plan. Untrusted repository metadata/configuration and hooks may execute programs during Git operations; worktree isolation alone cannot prevent filesystem/network or credential access.

## Decision

1. Introduce `tools/workspace_policy.py`, a **pure validation** layer for host-managed grants. An agent may request READ/WRITE checks but cannot set the scope, execute commands, delete files, alter its own policy, edit `.git`, change `AGENTS.md`, CI/rulesets or phase control documents. No actual file modification in the P00 slice.
2. Exact P00 branch and declared phase are required. Default write scope is narrow: `docs/help`, `docs/wiki`, `docs/research`, `tests/fixtures`. Protected path and secret-name denylist overrides any proposed prefix; attempt to broaden into governance is rejected.
3. Use `tools/worktree_plan.py` to construct a deterministic detached, no-checkout worktree command from immutable SHA in pre-existing separately controlled roots, with host-owned empty hooks dir. It only **returns a plan**. No shell interpreter, Git fetch/push/merge, untrusted flags, or arbitrary repo selection by model.
4. Prove the exact command on a newly created, disposable **trusted Git fixture** in CI; verify git pointer and immutable HEAD. Do not run against arbitrary/remote/user repos in this phase slice.
5. The eventual actual executor is a separate **privileged host service** with OS-level isolation, credential segregation, disk quota, time/cpu/memory limits, network egress restrictions, system call/path checks and durable reconciled receipts. Python `Path.resolve()` and `git worktree` are NOT adequate containment.
6. Windows junction/reparse-point and case-insensitive path tests require a real Windows runner before sign-off. On Linux, symlink checks + no-checkout fixture are preliminary risk tests, not permission to execute downloaded source.
7. No current runtime process, application GUI, model session, installer, Wiki publication, real screenshots or remote PR merge is inferred.

## Options weighed

| Approach | Outcome |
|---|---|
| Direct model shell in main repository | Rejected: bypasses phase protection and exposes secrets |
| New Git worktree with mutable branch | Deferred: risks branch collisions and checkout filters |
| Detached no-checkout worktree plan | Chosen P00 primitive; does not run until independently authorized |
| Fresh disposable clone + isolated host | Future option for untrusted repos; clone itself is not OS sandbox |
| Filesystem copy | Rejected as primary authority: no verified SHA/remote and copy/symlink risks |
| OS-level sandbox (separate process/account, scoped filesystem/network) | Mandatory future execution gate |

## Verification and residual risks

Tests in `tests/test_workspace_policy.py` validate path traversal, Windows-style drive/UNC, privilege escalation, root or file symlinks, hidden secrets, wrong phase, invalid commit IDs and one real disposable no-checkout Git fixture. CI evidence is linked in the P00 PR. **No live repo worktree or automatic coding task has been executed.** Post-plan race prevention, Windows reparse points, trusted-host grant signing, process sandbox, and safe cleanup remain outstanding Issue #3 items.

**Read:** [worktree policy](../operations/P00_WORKTREE_POLICY.md), [threat model](../security/THREAT_MODEL.md), [Git worktree docs](https://git-scm.com/docs/git-worktree), [Git security notes](https://git-scm.com/docs/git#_security) and [Python subprocess](https://docs.python.org/3/library/subprocess.html).
