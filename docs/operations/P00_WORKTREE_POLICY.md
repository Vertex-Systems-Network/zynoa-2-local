# P00 Trusted Worktree Planning & File Capability Boundary

**Status:** Implemented policy/planning code and disposable Git fixture tests only. **No model execution, live repository worktree mutation, OS sandbox or autonomous worker deployed.** Current phase: P00 / M22 / [draft PR #1](https://github.com/Vertex-Systems-Network/zynoa-2-local/pull/1).

## Why this boundary exists

A model-driven coding agent must be able to propose a file change and a task worktree **without gaining access** to user directories, tokens, Git admin metadata or repository security policy. Git worktrees themselves are NOT sandboxes: Git's local configuration, hooks and content filters can run programs, and untrusted Git metadata can be dangerous. In P00 the default is **deny all execution** until a separately controlled OS sandbox and real host identity are deployed.

## Implemented modules

### `tools/workspace_policy.py` — file capability *validation only*

`WorkspaceScope(root, phase, branch, writable_prefixes)` is a frozen host-created policy object. In P00 it accepts exact `phase=P00` and `branch=phase/00-governance`. The model **must not** set these values or extend its own scope; a future host-side broker provisions the object from preauthorized configuration.

- Default permitted WRITE directories: `docs/help/`, `docs/wiki/`, `docs/research/`, and `tests/fixtures/` **inside a trusted task worktree**. No actual files are written by this component.
- READ requires a regular existing file; WRITE allows a target file that may be created later, but only under its allowed directory.
- Security/authority paths are always protected: `AGENTS.md`, `.git/`, `.github/`, `docs/state/`, `docs/quality/`, `docs/adr/`, `deploy/github/`, credential/config directories and governing controller source files.
- Relative path parser denies absolute paths, Windows drive prefixes/UNC, backslashes, traversal (`..`), empty/dot components, reserved device filenames, control/invisible Unicode, hidden secret variants, unsafe Git metadata filenames and symlinks/junctions.
- Resolve-and-check enforces logical containment; decisions report only generic `APPROVED_SCOPE` or `WORKSPACE_SCOPE_DENIED`, not host absolute paths.
- `execute`, `delete`, `merge`, `chown` and all unknown operations are prohibited. This is **not** the future user-visible designer/editor file picker or a data vault implementation.

**Important limits:** Python path checks are susceptible to time-of-check/time-of-use races if another process can replace ancestors. A future privileged broker must use OS-level file descriptors / no-follow primitives or equivalent, restrictive worktree mounts and separate low-privilege identity. Python's best-effort `is_junction` and symlink checks are not substitutes for Windows ACLs/reparse point policy.

### `tools/worktree_plan.py` — immutable Git worktree *plan only*

The builder requires:
- Trusted existing ordinary Git checkout with an actual `.git` directory, not a symlink or untrusted Git repository.
- A separately controlled, non-overlapping, already-existing worktree root.
- An empty host-owned Git hooks directory outside both source and worktree root.
- Exact full 40-character SHA, safe job ID, active P00 branch and primary PR in local state; a trusted future broker must also fetch authoritative GitHub proof before it acts.

Generated argv (no user-defined flags):

```text
git -c core.hooksPath=<empty-trusted-hooks-dir> -C <trusted-repo> worktree add --detach --no-checkout -- <new-target> <full-commit-sha>
```

The plan uses `shell=False`, `--no-checkout` (no repository file checkout/smudge as part of this operation), an immutable SHA and a distinct target path. The module **does not execute** it or store raw private paths in its public decision summary. It does not fetch, push, checkout branches, merge PRs, delete a worktree or clean interrupted changes. A future privileged broker must reconcile any partial creation with live Git state before retrying.

### Actual isolated fixture integration test

`tests/test_workspace_policy.py` creates a **new disposable Git repository** under a temporary test directory, makes an empty fixture commit with isolated Git configuration, builds the approved plan and runs its fixed `git worktree add --detach --no-checkout` command only against that trusted fixture. It verifies the new `.git` pointer and exact HEAD SHA. The project worktree and real GitHub repository are untouched. Git executable availability is required for this fixture test; on environments without Git the integration test is skipped and **M22 must not be marked verified** from a skipped test.

Other tests cover scope enforcement, link escape attempts, Windows drive/UNC/traversal, secret and privileged paths, invalid branch/phase, existing targets, hooks-directory policy, counterfeit SHA and sanitized outputs.

## Agent-to-host data flow (planned, not deployed)

```text
Agent proposes file or worktree operation
                 |
Trusted controller checks current phase/PR (GitHub)
                 |
Host-issued immutable policy grant (outside model process)
                 |
Path/operation validator OR immutable worktree plan
                 |
Protected OS sandbox / separate low-privilege worker  <-- NOT IMPLEMENTED
                 |
Host verifies actual filesystem, Git HEAD, tests and receipts
                 |
A separately authorized GitHub policy broker controls PR actions
```

No AI model should be able to change `AGENTS.md`, alter the merge guard, overwrite the worker's policy object, or grant itself network/file permissions. No code/research from untrusted repositories can authorize higher privileges.

## Pre-development options research (verified 2026-11-18)

| Alternative | Benefits | Risk / decision |
|---|---|---|
| Git `worktree add --detach --no-checkout` | Quick metadata-light isolation between tasks; one shared Git object store | **Selected for trusted fixture planning**; not a security sandbox; untrusted repo Git config requires external controls |
| Fresh `git clone` / separate object database | Reduces reliance on an existing `.git` metadata directory; can support stronger repo boundary | More disk/network/time; still not an OS sandbox, content execution remains dangerous; evaluate for untrusted source |
| Copy directory to task folder | Minimal Git requirements | No verified commit identity, submodule and symlink hazards, expensive storage; rejected as trusted source-of-truth mechanism |
| OS sandbox/container (restricted process/identity/network/volume) | Actual execution boundary | **Mandatory future gate** before running generated code; needs Windows/Linux separate integration tests and host provisioning |

Authoritative sources:
- [Official Git worktree commands](https://git-scm.com/docs/git-worktree)
- [Git security boundary: local config and hooks](https://git-scm.com/docs/git#_security)
- [Git attributes and executable smudge/process filters](https://git-scm.com/docs/gitattributes)
- [Python subprocess management](https://docs.python.org/3/library/subprocess.html)
- [Windows path/junction behavior](https://docs.python.org/3/library/pathlib.html)

## Acceptance & genuine remaining blockers

P00-WSP-01 Path scopes prohibit traversal, symlink/junction and privileged credential/phase files.
P00-WSP-02 Scope cannot be widened to protected governance prefixes; model does not hold authority to issue grants.
P00-WSP-03 Worktree plan targets immutable SHA and exact P00/branch/PR; no arbitrary git flags.
P00-WSP-04 Real disposable Git fixture executes the no-checkout plan and verifies detached HEAD SHA; live repo untouched.
P00-WSP-05 Test negative cases (symlink root, overlapping roots, hooks dir nonempty, existing target, wrong phase).
P00-WSP-06 CI, threat model, Help/Wiki source, and unreleased change record link to genuine evidence.
P00-WSP-07 **NOT YET PASSED:** Actual OS sandbox, real Windows and Linux hardening, secure filesystem write system calls, host-issued grants, runnable AI test loop, terminated-process cleanup, token protection and deployment proof.

Full P00 release remains BLOCKED by [Issue #3](https://github.com/Vertex-Systems-Network/zynoa-2-local/issues/3); no P01 branch before P00 PR remote merge verified. Real app screenshots and published Wiki remain pending.
