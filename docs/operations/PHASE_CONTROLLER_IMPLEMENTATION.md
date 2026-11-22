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

## P01-T11: verified transition journal contract (2026-11-22 UTC)

For a **future** phase handoff, `EventJournal.record_verified_transition(state, target, evidence)` validates the pure `authorize_next_phase` contract and additionally requires exact booleans for independent main merge ancestry, protected main rules, trusted workflow provenance/source and the phase-specific issue inventory. It writes only the phase identifiers, primary PR number, exact merge SHA and issue-inventory fingerprint to the host-owned SQLite WAL event store. The same deterministic event ID is idempotent only if persisted bytes match; a conflicting existing record fails closed. A fresh database connection checks commit/readback after write. The return value **explicitly** reports `external_checkpoint_published=false` and `next_phase_started=false`.

**Operational boundary:** This is a durable **host-local** SQLite journal entry, not a repository-hosted immutable audit artifact, a deployed postmerge automation, or independent GitHub authentication. The trusted operator/controller must first acquire fresh authenticated `GitHubGateway` evidence, invoke the journal on a persistent secured storage volume, verify readback, and then independently commit or publish a sanitized checkpoint artifact with exact GitHub readback. Ephemeral GitHub-hosted CI containers do not guarantee the local database survives between runs; publish to versioned GitHub or retained CI storage before reporting external persistence. Never claim that merely adding this API backfills any historical record.

**Issue #4 historical P00→P01 gap:** PR #1, closeout PR #8 and P01 kickoff PR #9 have independent remote commit/phase-state evidence; however repository code search shows no production call writing a `phase_transition_verified` event for that transition, and no original SQLite transition row has been retrieved. This new API must not be used to impersonate an original 2026-11-21 event. Issue #4 remains OPEN for explicit independent maintainer acceptance or a genuine source-backed journal receipt. Existing strict `P01` issue-classification and owner's **do not merge** directives remain unchanged.


## P01-T11: external GitHub-backed receipt on a previously merged primary PR (future only)

After a P01+ primary PR has been merged **and** a separate protected-main closeout has persisted its MERGED_VERIFIED state, the trusted default-branch workflow at .github/workflows/verified-phase-transition.yml can publish a sanitized event to the already-merged primary PR's issue comments using only the built-in GitHub Actions token. It is triggered by the versioned PHASE.json push on main and supports trusted manual workflow_dispatch. It is never triggered from a PR branch or from untrusted model code, never runs a general model, and requires an exact main SHA and repository identity.

The tools/phase_transition_publisher.py workflow does the following in order:

1. Require P01+ (not historical P00), verified merged snapshot, no worker/lease claim, and an exact trusted main workflow ref/SHA. Read live authenticated GitHubGateway observations, requiring passed CI, original workflow source, branch protection/rules, and independently complete zero-blocker issue classification. If the protected main advanced via an approved closeout, compare the exact primary merge SHA to current main and require independently verified ancestry (not merely a matching PR title).
2. Invoke EventJournal.record_verified_transition, which inserts a sanitized local SQLite WAL entry with collision denial and reopened-database readback. Use only phase identifiers, the primary PR number, remote merge SHA and issue inventory digest. There are no secrets, raw code, end-user events, model text or mutable workflow inputs in the receipt.
3. Enumerate the exact primary PR's comment pages, reject duplicate IDs, altered event markers or non-bot authors. If the matching bot comment exists and is byte-for-byte intact, reuse it without a second write. Otherwise re-fetch the merged PR and protected main SHA and POST only one sanitized issue comment to the existing primary PR. Perform a separate GitHub API readback of the exact new comment ID, body, bot author and parent PR.
4. Report external_checkpoint_published=true only after that remote readback, along with the primary merge SHA and comment URL. Never update PHASE.json, start P02, merge another PR, create a new issue, or create an archival branch.

The matching comment is **remotely persisted and independently API-readable after the ephemeral runner terminates**. It is nevertheless mutable/deletable by principals with sufficient GitHub permissions, **not** an immutable cryptographic or append-only journal. The main repository's commit ancestry, existing PR merge receipt and default-branch Actions job are separate forensic anchors. This is a limited, accurate improvement over ephemeral-only SQLite. If stronger tamper resistance is contractually required later, protect an actual append-only archive/ref and independently verify its rules before making that claim.

**Deployment boundary:** The new workflow is only proposed in draft P01 PR #10 and is **not yet active on protected main**. GitHub requires workflow_dispatch workflows to exist on the default branch. The closeout must occur *after* an owner-approved protected primary merge; no such authorization exists at present. GitHub Actions using GITHUB_TOKEN may not trigger follow-on push workflows; the explicit main-only workflow_dispatch is the replay path. The workflow refuses all unmerged or unlabelled issue inventories; present P01 state is IN_PROGRESS with five open unlabelled issues, so no remote receipt may be written today. The missing **original 2026-11-21 P00-to-P01 journal event is not backfilled**, and Issue #4 remains open until an independent maintainer documents an accepted historical disposition. Links: https://docs.github.com/en/rest/issues/comments and https://docs.github.com/en/actions/how-tos/manage-workflow-runs/manually-run-a-workflow.

