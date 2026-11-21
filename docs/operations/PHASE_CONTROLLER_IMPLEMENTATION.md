# P00 Phase Controller — Implementation Slice 1

**Implementation status:** PARTIAL (policy primitives and local SQLite journal). **No persistent worker/daemon deployed**, no live GitHub transition executor, no PR auto-merge. This is a development foundation, not completion of P00/M22.

## Scope delivered

`tools/phase_controller.py` provides a canonical ordered phase sequence with **P08 -> P08I -> P09**, validated local phase snapshots, pure `authorize_next_phase` transition policy and idempotent persistent event journaling (SQLite with WAL mode). `tests/test_phase_controller.py` exercises accepted and denied paths, incorrect/unauthenticated evidence, blocked phase jumps, and restart-safe deduplication.

The core policy requires a tracked active branch, PR number, `MERGED_VERIFIED` status, exact verified merge commit SHA, CI checks and no critical blockers. A P08I transition must be preceded by completed P08. This policy DOES NOT fetch or authenticate remote evidence by itself: upstream trusted GitHub reader must populate `authenticated_remote` and all other fields from live API, not AI-generated text.

## Operational command

```bash
python tools/phase_controller.py --state docs/state/PHASE.json
python -m unittest tests.test_phase_controller -v
python scripts/check_design_interop_policy.py
```

The CLI prints `remote_merge_verified_by_this_command: false` and `persistent_worker_deployed_by_this_command: false`. It never mutates the repo, creates a branch/PR, authenticates a user or claims CI success.

## Remaining P00 work / blockers

1. Add a real authenticated GitHub adapter with least-privilege credentials and readback of branch, PR, CI, merge SHAs, repository policy and blocker issues.
2. Add a supervised persistent worker with lease ownership, durable checkpoints, heartbeats, retry budget, event replay, queue priority and cancellation; test process crash recovery on a configured developer machine/runner.
3. Bind actual branch/PR mutation to verified policy; never circumvent configured reviews, secrets protection or CI.
4. Finalize P00 phase acceptance tests, source-backed research bank, full security threat evaluation, documentation with real product screenshots only when actual UI exists.
5. Correctly validate worker deployment and auto-merge repository settings before claiming "autonomous non-stop" development.

## New future requirement (tracked issue #2)

The [Designer interoperability specification](DESIGN_INTEROPERABILITY.md) and ADR-0008 defer **cross-tool editable import/export** to P08I, after native Designer core P08 is truly complete and remotely merged. This is a policy and planning addition only.

## Evidence and release classification

Tests and GitHub CI should be linked by the P00 PR; only completed jobs may be reported as passed. No user-facing release notes entry or CHANGELOG entry is appropriate for this incomplete internal implementation. The [planning changelog](../PLANNING_CHANGELOG.md) tracks the change.
