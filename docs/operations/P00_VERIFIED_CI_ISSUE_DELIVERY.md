# P00 — Authorized CI failure → deduplicated sanitized GitHub Issue

**Phase:** P00 · **PR:** #1 DRAFT, unmerged · **T22:** BLOCKED until live default-branch workflow delivery is independently observed.

## Problem and design

The existing `developer-incident.yml` is a **trusted-default-branch-only** `workflow_run` publisher. It cannot trigger from the unmerged `phase/00-governance` branch; Github requires a `workflow_run` listener to exist on the **default branch**. That is an intentional security gate, not a reason to merge an unfinished P00 PR. See [GitHub event semantics](https://docs.github.com/en/actions/reference/workflows-and-actions/events-that-trigger-workflows#workflow_run) and [privileged workflow security](https://docs.github.com/en/actions/reference/security/secure-use).

This source change strengthens the existing `tools.github_issue_bridge.DeveloperIssueBridge` for future *actual* delivery:

1. A **trusted GitHub Actions `workflow_run`** failure event, rather than an untrusted PR title, supplies the numeric run ID and full lowercase Git SHA. The reporter uses its own scoped default-branch `GITHUB_TOKEN` (`actions: read`, `issues: write`; `contents: read` for checkout) and **independently** reads `GET /repos/{repo}/actions/runs/{id}` before touching Issues. It requires identical ID and SHA, `status=completed`, `conclusion=failure`, exact `name=Governance v3.2`, event `pull_request` or `push`, and `head_repository.full_name` equal to this repository. Invalid/missing identity stops with zero Issues operations.
2. Only fixed developer-ci P2 metadata is accepted by `tools/incident_router.sanitize`. End-user reports, P0 security incidents, raw exception stacks, prompts, source code, paths, tokens, personal identifiers and job logs cannot enter public issue payloads.
3. The deterministic redacted fingerprint marker deduplicates **open and closed** Issues (bounded four 100-item pages). If the marker matches, verify the issue's canonical URL/number/title AND author `github-actions[bot]` before any update; never overwrite a user-created marker spoof. Same run ⇒ no mutation. A *new* failed run ⇒ update that one bot-owned issue via restricted `PATCH /issues/<number>`, rebuilding its content from the fixed sanitized envelope and at most **five** canonical run-id/commit links; never re-emit arbitrary existing issue body text. No generic PATCH or PR write routes.
4. A new incident ⇒ restricted `POST /issues` and check canonical returned issue URL/number and echoed safe body. An error or ambiguous response means **NOT VERIFIED** and requires remote reconciliation before retry; never claim success on HTTP errors or dedup scan exhaustion.
5. `workflow_run` uses trusted default branch code and does NOT checkout or execute the failing PR's code or download its artifacts. Workflow concurrency serializes issue writes; it never gets `contents:write` or `pull-requests:write` and cannot merge, label a PR or close a security issue.

**Rejected alternatives:** (A) `pull_request` job with `issues:write` and PR source checkout — unsafe privileged PR execution; (B) unverified `workflow_run` payload or build logs in the public issue — forged run/source/secret exposure; (C) automatic merge of incomplete P00 just to activate reporting — violates the P00 exit gates. Chosen: trusted default branch publisher + independent run API readback, narrow issue-only writes and a safe bounded history.

## Acceptance and rollout

```sh
python -m unittest tests.test_github_issue_bridge tests.test_ci_incident_delivery -v
python -m unittest discover -s tests -v
```

Tests use **mock GitHub HTTP** for failed run GET, new issue POST, same-run dedup, second-run PATCH, spoofed repository/SHA/conclusion/owner, invalid identities, redaction, four-page limit and failed update. CI remains **read-only** on the primary Governance workflow; incident publisher remains **inactive until P00 approved protected merge**. This source test cannot close T22.

A connector-authorized maintainer can separately create and read back a sanitized Issue for a *real historical failure*, but that proves only **manual live Issue API access**, not automatic `workflow_run` delivery or CI's `GITHUB_TOKEN` grants. Record those as separate evidence categories and avoid calling either an unattended worker or a release. A genuine postmerge failed governance run, trusted listener completion, new/existing Issue readback, repeat-run no-duplicate test and tight repo token permissions must all be independently verified to mark T22 DONE.

**Truth:** P00-T22 BLOCKED (no default-branch activation), T17/T19/T21/T23/T24 other host and merge blockers still apply. PR #1 DRAFT/UNMERGED, `worker_running=false`, P01 NOT STARTED, no user-facing UI or published Wiki. [Issue #3](https://github.com/Vertex-Systems-Network/zynoa-2-local/issues/3). [ADR-0023](../adr/0023-ci-run-verified-sanitized-issue-delivery.md).


## CI source and manual-connector proof (2026-11-20)

[Source Actions #44658827576](https://github.com/Vertex-Systems-Network/zynoa-2-local/actions/runs/44658827576) passed 394 Linux tests and Windows policy including 17 new simulated incident publisher checks. Independently verified historical failed [run #44652995831](https://github.com/Vertex-Systems-Network/zynoa-2-local/actions/runs/44652995831) and manually opened/read back [sanitized audit Issue #5](https://github.com/Vertex-Systems-Network/zynoa-2-local/issues/5) using an authorized GitHub connector. This is real **manual** GitHub Issues create/readback but cannot be confused with future automatic GitHub Actions `workflow_run` publisher: that listener is still absent from default branch, the test runner has read-only permissions, and T22 remains BLOCKED pending actual postmerge incident delivery. No generic PR/repository writes granted.
