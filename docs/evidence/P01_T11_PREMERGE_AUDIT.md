# P01-T11 — Read-only final exit/merge readiness audit

**Date:** 2026-11-22 (UTC) · **Scope:** pre-merge evidence only · **Outcome:** `PREMERGE_GATES_PARTIAL`. No merge, branch protection bypass, release, or P02 action was performed. T11 remains **IN_PROGRESS** until independently authorized merge and exact remote merge verification.

## Remote source of truth

- Repository: `Vertex-Systems-Network/zynoa-2-local`, main target branch.
- [Draft PR #10](https://github.com/Vertex-Systems-Network/zynoa-2-local/pull/10) is **open, mergeable and unmerged**, at audit start PR head `84e3f5cd5ffa1d7f3d31d58e854ed7bffae25c58`.
- Independently fetched `main` HEAD: `1697ea8488b2da089da22951de64f5254a48b71f`; PR base SHA matches.
- `docs/state/PHASE.json` says P01 / IN_PROGRESS / `phase/01-foundation` / PR #10; no transition to P02 is authorized.
- Existing [P01 T01–T10 evidence](../state/pr-tasks/P01.json) is recorded as DONE. T11 covers final phase exit plus actual authorized merge, so it is not DONE.

## Tests and actual Windows proof

- [Governance CI #45008304983](https://github.com/Vertex-Systems-Network/zynoa-2-local/actions/runs/45008304983): **SUCCESS** at `84e3f5cd5ffa1d7f3d31d58e854ed7bffae25c58`; governance policy, V3/V3.1/V3.2 verification scripts, change-record checks, PR task-board gate, merge-guard **dry run with zero mutations**, and `python -m unittest discover -s tests -v` (**473 tests, OK**) verified from GitHub job logs.
- Same commit: [P01 Desktop workflow #45008305008](https://github.com/Vertex-Systems-Network/zynoa-2-local/actions/runs/45008305008) **SUCCESS**; heavy Windows build correctly skipped on a lease-only/no-source update.
- Earlier genuine desktop [Windows #45006477419](https://github.com/Vertex-Systems-Network/zynoa-2-local/actions/runs/45006477419) **SUCCESS**: compiled native Tauri executable, real cold boot, 32 Rust tests, and five visually reviewed SHA-pinned native screenshots published to GitHub, as indexed in [M01 screenshot evidence](../screenshots/M01/README.md). This is **only** proof for implemented read-only/disabled foundation states. Planned options, full M01/M16/M17/M18 feature surfaces, and live GitHub Wiki remain pending, not released.
- [Task board sync #45008304980](https://github.com/Vertex-Systems-Network/zynoa-2-local/actions/runs/45008304980): **SUCCESS**.

## Effective branch protection (GitHub ruleset)

- `main` branch is marked `protected=true`; the older `/branches/main/protection` endpoint returns **403 to this integration**, so it is **not** used to infer missing protection.
- **Effective active repository ruleset [#27593065](https://github.com/Vertex-Systems-Network/zynoa-2-local/rules/27593065)** was retrieved separately through GitHub: targets `refs/heads/main`; prohibits deletions and non-fast-forward pushes; requires a PR with review-thread resolution, enforces strict passing `governance-lint`, pinned to **GitHub Actions App ID 15368**. The observed successful governance check has the same App ID. Bypass actors are empty and `current_user_can_bypass=never`.
- Repository settings report `allow_auto_merge=true` and squash merge allowed; these facts alone never authorize a merge.

## Remaining T11 gates — deliberately not passed

1. **Owner authorization is absent.** The owner's latest explicit instruction was **not to merge PR #10**. PR therefore stays **Draft**, unmerged. No automatic/guarded merge is attempted.
2. **Critical blocker scope is not finalized for P01.** `tools.github_gateway.GitHubGateway.observe()` deliberately returns an incomplete blocker policy for phases other than P00 unless an **independently configured** issue scope is supplied. Do not silently treat the absence of a P01-labelled issue as explicit approval. A merge action must verify this scope and re-check all current GitHub data at execution time.
3. **Post-merge truth cannot exist yet.** Exact resulting `main` merge SHA, `MERGED_VERIFIED` checkpoint, and subsequent P02 permission are *post-merge* gates and must not be asserted before the actual authorized merge.
4. **Remote Wiki remains un-published**, and future-option screenshots are deliberately `PENDING_IMPLEMENTATION` rather than fabricated. These are deferred feature scopes, not proof of present functionality.

**Next authorized step:** finish independent blocker-scope/merge-guard policy under current phase and present a fully audited merge-ready PR; only upon an explicit owner **merge** instruction can the bot attempt protected merge, verify its actual SHA and update the phase checkpoint. Do not use task count or green CI as a merge substitute.
