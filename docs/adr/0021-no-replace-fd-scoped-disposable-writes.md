# ADR-0021 — Create new draft fixture only in detached worktree through fd-scoped no-replace publication

**Date:** 2026-11-20 · **Status:** P00 scoped implementation, real developer host/OS sandbox still blocked.

## Context
P00 model planning, ephemeral previews, syntax compilation and fixed-function execution prototypes cannot alter a source file. Users need true file-editing progress, but a model must never write to a trusted checkout or override governance or credential files. Existing `worktree_plan` creates only the *plan* for detached no-checkout Git targets. `WorkspaceScope.check()` alone is subject to time-of-check/time-of-use races.

## Decision
Implement `tools.scoped_worktree_fixture_writer.apply_one_disposable_fixture` as a **separately operator-granted Linux-only nonroot** operation on a pinned detached, no-checkout Git worktree distinct from the trusted source checkout. Independently require exact phase task, source Git SHA, candidate SHA-256, workspace scope and triple opt-in. Restrict to one *new* flat `tests/fixtures/*.py`; deny replacement. Open owned parent directories via `O_DIRECTORY|O_NOFOLLOW` directory FDs, write a `0600` temp file, fsync, `linkat`-style publish without overwrite and SHA-verify the result. Fail closed, no rollback illusion after uncertain publication; don't execute Python, run Git or write GitHub.

## Rejected
1. `Path.write_text` or `os.replace` in source checkout: bypasses immutable-source and no-overwrite policy, leaves symlink races.
2. Arbitrary multi-file `git apply` patch controlled by model: unsafe parser/config/tool authority before separately attested sandbox and host lease.
3. Making Windows file writes available by path fallback: Windows ACL/reparse-point safe handle contract has not been designed or verified.

## Tradeoffs
Cross-platform CI can check the policy and Linux can really write **only its own disposable Git fixture**. An authorized operator could later inspect generated files with isolated tests but they are never production code changes here. Same-UID interference, process crashes, filesystem durability and host identity remain external security concerns; fsync and FDs don't replace OS sandbox or grant fencing. No host deployment/real Ollama/remote PR writer evidence; full P00-T20 remains IN_PROGRESS. [Operations](../operations/P00_SCOPED_WORKTREE_WRITER.md).
