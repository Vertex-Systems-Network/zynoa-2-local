# P00 trusted static GitHub fixture — new-file, non-force PR branch proof

**Date:** 2026-11-20 · **Task:** P00-T21 partial source evidence; T21 remains **BLOCKED** until actual autonomously authenticated worker writer and independent sandbox acceptance.

## Need and explicit limitations

The repository already holds source-only model draft/test/isolated disposable Git file stages, but no separately secured user-owned host or authenticated model→PR code delivery. This narrowly bounded source module `tools/github_static_fixture_publisher.py` tests the **remote Git Data API lifecycle** for a fixed **operator-reviewed literal** Python fixture. It is intentionally NOT an interface for model-authored Python or an arbitrary path, branch, patch, commit message, shell command, file replacement, or user repository source edits.

**Only possible published file:** `tests/fixtures/p00_trusted_remote_probe.py` containing an inert, fixed two-times integer function. This literal cannot be changed through API parameters. A model cannot set the content, token, branch, file path, target PR, or the explicitly required three operator grants. It is placed ONLY on open DRAFT PR #1, branch `phase/00-governance`. Its role is remote-write plumbing evidence, NOT execution or AI coding.

## Actual source contract

1. Default-DENY until a separately trusted non-PR-code operator supplies `enabled=True`, `operator_ack=True`, `manual_review=True`, a nonblank scoped GitHub token, and exact prior 40-hex PR HEAD SHA. CI never supplies a write token; Windows CI runs **fake HTTP only**.
2. Independently `GET /pulls/1`: must be open, draft, unmerged, same repo/branch and exact HEAD, base `main`. Independently read parent Git commit tree. `GET /contents/tests/fixtures/p00_trusted_remote_probe.py?ref=<SHA>` must return verified 404; an existing path is never overwritten. Recheck PR SHA immediately before the first remote object write.
3. `POST /git/blobs` with **fixed literal** and UTF-8, verify Git SHA-1 blob object against literal bytes. `POST /git/trees` with exactly one new file, immutable base tree and 100644 blob mode. `POST /git/commits` with one parent equal to the preverified PR HEAD and the new tree, no other files included.
4. `PATCH /git/refs/heads/phase%2F00-governance` with `force:false` ONLY. A moved PR HEAD normally causes a non-fast-forward rejection; this is not an unconditional atomic compare-and-swap against a branch that an unauthorized actor can force rewrite. This code does not touch `main` or call PR merge.
5. **After remote ref update**, independently re-read PR HEAD at exact new commit, re-read file contents from that immutable commit and verify exact bytes. If any HTTP result, SHA, ref or readback is ambiguous, fail closed with no success claim; if the ref already advanced, reconcile remote state rather than blindly retrying.

No model code is executed; no Docker is run; no user secrets are ever attached to a commit, status or error. The dedicated repo token still has broader power than a source-level path allowlist can cryptographically constrain; the authority boundary requires host identity, secret isolation, GitHub App/repository scope, expiry and approval policy before deployment. A source-only allowlist is defense in depth, not an independent non-bypass credential guarantee.

## Evidence, tests and interpretation

```sh
python -m unittest tests.test_github_static_fixture_publisher -v
python -m unittest discover -s tests -v
```

Linux and Windows CI use mocked HTTP for successful nonforce Git lifecycle, existing target, bad candidate blob SHA, forged parent/tree, stale PR ref, denied force-update, transport conflicts and post-write readback corruption. They do **not** run a token-privileged write. A separately authorized ChatGPT GitHub connector may manually reproduce this protocol and verify the new remote file/commit on draft PR #1; this proves **manual connector Git write and readback**, not that this Python module was executed on the user's host or that an autonomous AI worker has a valid token.

**Still blocked:** P00-T17 host service/heartbeat, T19 independent OS sandbox/container containment, T20 real model-authored application source edit/test/repair, T21 time-bound non-bypass writer identity and complete unattended PR flow, T22 postmerge `workflow_run` Issue delivery, T23 end-to-end, T24 protected merge. T14 task board writer also inactive before approved merge. P00-T21 remains BLOCKED even after a successful static fixture proof; P01 not started; `PHASE.json.worker_running=false`. Do not merge PR #1 merely to activate privileged postmerge workflows.

**Rejected alternatives:** model-selected `git push`/shell, rewriting source checkout directly, full replacement `PUT /contents` with optional existing-file SHA, force-push, publishing an unverified model fixture or granting the PR workflow `contents:write`. Official: [GitHub Git database APIs](https://docs.github.com/en/rest/git), [Update reference](https://docs.github.com/en/rest/git/refs#update-a-reference), [Git blob object hashing](https://git-scm.com/book/en/v2/Git-Internals-Git-Objects). [ADR-0024](../adr/0024-static-only-remote-branch-write-probe.md).
