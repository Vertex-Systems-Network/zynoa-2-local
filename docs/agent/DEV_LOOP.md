# Persistent Development Controller — State Machine

This is the specification of a future **separately deployed resident worker**. The ChatGPT conversation does not execute it continuously. No controller is running in this starter.

## One-phase-at-a-time invariant
`active_phase` is a single-writer lease acquired transactionally. Only one owner has an open phase delivery branch/PR. Independent issue analysis may run concurrently, but code merges for the next phase cannot begin until the previous phase PR merge SHA is confirmed on `main`.

## State transitions

```
BOOTSTRAP -> RECONCILE -> ACQUIRE_PHASE_LOCK
    -> RESEARCH -> OPTION_BANK -> ADR -> ACCEPTANCE_TESTS
    -> IMPLEMENT_INCREMENT -> LOCAL_TESTS -> UI_VISUAL_QA
    -> SECURITY_REVIEW -> PR_OPEN_OR_UPDATE -> CI_WAIT
    -> PASS? -> AUTO_MERGE_REQUEST -> VERIFY_MERGE_SHA
    -> SNAPSHOT_STATUS -> RELEASE_LOCK -> NEXT_PHASE -> RECONCILE
               | FAIL
               v
         COLLECT_EVIDENCE -> ROOT_CAUSE -> SMALLEST_FIX -> RETEST
               | retry_budget_exhausted / unsafe / unavailable
               v
         MARK_BLOCKED -> WORK_SAFE_INDEPENDENT_ITEMS / BACKOFF
```

## Deterministic controller logic

```text
while controller_is_enabled:
  reconcile(local_db, git_remote, github_pr, required_checks, worktree)
  phase = lock_current_unmerged_phase()
  if blocked(phase):
     run_safe_non_dependent_tasks_or_backoff(); continue
  item = select_smallest_testable_item(phase)
  ensure_option_research_and_adrs(item)
  ensure_acceptance_tests(item)
  checkpoint(item)
  implement_with_task_model(item)
  result = run_allowed_checks(item)
  if failed(result):
     diagnose_and_fix_with_bounded_retries(item)
     persist_failure_if_unresolved(); continue
  commit_branch_and_update_pr(phase)
  await_ci_events_or_poll_with_limits()
  if every_required_gate_passes_and_protection_allows_merge():
     request_auto_merge_and_verify_remote_merge_commit()
     write_phase_completion_evidence()
     move_to_next_phase()
  else:
     reconcile_and_fix_or_block()
```

## Persistence and resume
- SQLite tables: `controller_runs`, `phase_locks`, `jobs`, `steps`, `checkpoints`, `tool_actions`, `artifacts`, `decisions`, `option_evaluations`, `tests`, `incidents`, `pr_snapshots`, `memory_items`.
- Job states: QUEUED, PLANNING, RESEARCHING, IMPLEMENTING, TESTING, FIXING, CI_WAIT, MERGE_WAIT, COMPLETE, BLOCKED, CANCELLED.
- Every step gets an idempotency key and input/output hashes. Never repeat destructive/non-idempotent actions on restart until remote state is rechecked.
- On startup, verify remote commit/PR/check states first, then compare local phase file. `STATUS.md` is human-readable projection, NOT an authority for verified PR facts.
- Save after each step: what changed, why, source facts, tests, open blockers, next smallest action, context links and recovery token.
- Long-running `CI_WAIT` is event-driven with bounded polling and backoff, not token-burning busy waiting.
- `RUNAWAY_GUARD`: stop repeating same failing command with identical input + environment; pivot to diagnosis or block.

## Multi-agent roles
- Coordinator: task graph, scope and phase lease.
- Researcher: competitive options, source citations and license checks.
- UX Designer: screens, components, accessibility and visual reviews.
- Architect: ADR, API boundaries, data flow and migration impact.
- Builder: code implementation in scope.
- Tester: unit/integration/E2E/performance evaluations.
- Security Reviewer: policy and dependency checks.
- Independent QA: adversarial review of claims and actual results.
- Release Controller: validates gates and performs authorized merge.

Roles can share model inference to save memory; the system should not assume one model is equally good at all tasks. Reviewer must use independent evidence, not only the Builder's summary.
