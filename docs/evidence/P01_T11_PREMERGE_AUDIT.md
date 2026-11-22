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

## T11 ruleset fallback hardening (same phase, no merge)

The classic authenticated `/rules/branches/main` endpoint can be unavailable while the active repository ruleset API is readable. The P01 merge evidence gateway now falls back **only** to an authenticated repository-owned, active branch ruleset targeting exactly `refs/heads/main`, with no bypass actors or bypass permission and a complete rule set. Ambiguous/inherited/wildcard policies, inaccessible APIs and incomplete pagination all fail closed. The existing PR requirement, strict `governance-lint` and trusted GitHub Actions App ID 15368 checks remain mandatory. **This does not resolve the separately required P01 independent blocker scope, owner authorization or actual merge.** CI regression evidence for this change must be checked before saying the fallback passed.

### Verified final CI for ruleset fallback — 2026-11-22

The [source commit `58ae70e`](https://github.com/Vertex-Systems-Network/zynoa-2-local/commit/58ae70e2b39296e7e2a767e4b98764b69b596923) was independently validated on GitHub: [Governance v3.2 #45008926254](https://github.com/Vertex-Systems-Network/zynoa-2-local/actions/runs/45008926254) **SUCCESS** (476 Python tests OK, including exact-rule fallback and fail-closed regression coverage), [PR Task Board Sync #45008926308](https://github.com/Vertex-Systems-Network/zynoa-2-local/actions/runs/45008926308) SUCCESS, [P00 Runner #45008926231](https://github.com/Vertex-Systems-Network/zynoa-2-local/actions/runs/45008926231) SUCCESS, and [P01 Desktop #45008926179](https://github.com/Vertex-Systems-Network/zynoa-2-local/actions/runs/45008926179) SUCCESS (properly skipped heavy executable build for unrelated code). Legacy ruleset fallback now has a passing test baseline, but **independent P01 blocker scope remains incomplete** and the owner's **do-not-merge** instruction remains binding. The PR stays Draft and T11 IN_PROGRESS. No merge or main mutation.

### Guarded premerge hardening: independent blocker-scope + Actions provenance

A T11 security review identified that the guarded merge preflight previously evaluated only `open_critical_blockers != 0` and `checks_passed`; a fabricated `0` count paired with `blocker_policy_complete=false`, or `checks_passed=true` without trusted Actions run/job provenance, could reach the eligibility check in isolation. The guarded merger now explicitly requires `blocker_policy_complete is True`, **`type(open_critical_blockers) is int` and value 0**, and `workflow_provenance_verified is True`. Invalid/missing/boolean counts fail closed; regression tests prohibit calling the merge transport for those states. This tightens security; **no independent P01 issue policy was created** and `GitHubGateway.observe(P01)` without such a policy remains incomplete. PR #10 remains Draft/unmerged. Latest regression CI run must be verified before claiming this change passed.

### Final T11 safety hardening check — independent open issue census

At GitHub remote audit, open issue entries were [#2](https://github.com/Vertex-Systems-Network/zynoa-2-local/issues/2) (P08I enhancement), [#3](https://github.com/Vertex-Systems-Network/zynoa-2-local/issues/3) (P00 infrastructure), [#4](https://github.com/Vertex-Systems-Network/zynoa-2-local/issues/4) (P00 checkpoint), [#5](https://github.com/Vertex-Systems-Network/zynoa-2-local/issues/5) (P00 CI audit), and [#7](https://github.com/Vertex-Systems-Network/zynoa-2-local/issues/7) (M22 P2 governance incident). None had scope or severity labels. Their titles suggest different phases, **but titles/absence of labels are not an independently configured P01 issue-scope policy**; no evidence supports an unrestricted zero-blockers declaration. This prevents final merge-readiness certification today.

[Fail-closed merge-guard commit `77b5207`](https://github.com/Vertex-Systems-Network/zynoa-2-local/commit/77b520791b229815f4016f2e951ecd16fb4f2c3e) requires `blocker_policy_complete is True`, exact integer zero open blockers, and trusted CI provenance before enabling a merge. [Governance #45010064639](https://github.com/Vertex-Systems-Network/zynoa-2-local/actions/runs/45010064639) passed **479 tests**, including new blocker-scope/zero-count/Actions-provenance tests, with a merge dry run reporting zero mutations. [P00 Runner](https://github.com/Vertex-Systems-Network/zynoa-2-local/actions/runs/45010064770), [Task Board](https://github.com/Vertex-Systems-Network/zynoa-2-local/actions/runs/45010064642) and [P01 Desktop](https://github.com/Vertex-Systems-Network/zynoa-2-local/actions/runs/45010064658) were also successful. This is a verified **guard implementation**, **not** blocker-scope authorization. Owner's do-not-merge instruction remains binding, and T11 stays IN_PROGRESS.
