# Prompt for the next AI agent (copy-paste as-is)

> You are working on `Vertex-Systems-Network/zynoa-2-local`. Read only these, in order: `docs/agent/AI_STRICT_PROTOCOL.md`, the `## CURRENT` block at the top of `docs/state/HANDOFF.md`, `docs/state/PHASE.json`, `docs/state/pr-tasks/P01.json`, and the P01 section of `docs/PHASE_SPECS.md`. Do not read anything else until a task needs it.
>
> Work only on phase P01, on branch `phase/01-foundation`, in draft PR #10. If your platform forces another branch name, open nothing new: push to `phase/01-foundation` if allowed, otherwise stop and report that in one line.
>
> Before editing, set `PHASE.json.lease_holder` to `<your-agent>@<UTC time>` and commit it. Clear it when you stop.
>
> Take the first task in `docs/state/pr-tasks/P01.json` that is not DONE (start: P01-T01, then P01-T02). For each slice: make the smallest complete change, add tests, run `python scripts/check_governance.py`, the three `python scripts/verify_v3*_kit.py`, `python -m unittest discover -s tests` and `python -m scripts.check_pr_task_board`; add a `.changes/records/*.json` change record when code changes; mark a task DONE only with a link to a passing CI run; update the `## CURRENT` block in `HANDOFF.md`; push and check PR #10 CI. Fix every red check at its root cause. Never skip or weaken a test.
>
> Do not merge PR #10 unless `docs/agent/AI_STRICT_PROTOCOL.md` contains an owner-written auto-merge rule or the owner says "merge" in chat. Do not start P02.
>
> Reply after each slice in this short form only: `phase | files_changed | tests (command -> result) | decisions | blockers | next_step`.

## Known facts for P01-T02

The P00 controller/worker code is hardcoded to P00 on purpose (security gate): `tools/workspace_policy.py` (`WorkspaceScope` accepts only P00 / `phase/00-governance`), `scripts/runner_worker.py` (P00 plan), task-ID constants like `P00-T20` in `tools/dev_fixture_*`, `tools/local_fixture_drafter.py`, and `IN_PROGRESS` checks in `tools/host_bootstrap.py`, `tools/dev_job_runner.py`, `tools/worktree_plan.py`, `tools/phase_merge_guard.py`, `tools/pr_task_trusted_sync.py`, `tools/docker_host_smoke.py`. Generalise them to "the active phase from `PHASE.json`" without loosening the checks, and keep CI smokes on `tests/fixtures/p00_active_root`.
