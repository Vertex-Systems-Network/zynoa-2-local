# P02-T11 — Protected Merge and Final Acceptance Preflight

**Branch:** `phase/02-shared-ui`. **Primary:** [draft PR #12](https://github.com/Vertex-Systems-Network/zynoa-2-local/pull/12). **State:** IN_PROGRESS, not authorized for merge.

## Independently observed GitHub state (2026-11-23)

- Protected `main` remote SHA: `f24c72eff1c4fec03a6687575ea19e9593b57a2c`. Active branch ruleset ID **27593065** — "Zynoa Protected Main — Phase PR and Trusted Governance CI", enforcement **active**; main branch reported protected.
- PR #12 is **draft**, open, mergeable in Git object terms but `mergeable_state=blocked`. Existing review events were COMMENTED, not APPROVED. Review approval, owner-intent policy and exact-head trusted workflow checks must be separately proven before merge.
- Five open GitHub issues: #2 (`phase:P08I`, `merge:blocker`), #3 (`phase:P00`, `merge:blocker`), #4 and #5 (`phase:P00`, `merge:nonblocker`), #7 (`phase:P01`, `merge:nonblocker`). No open issue currently labelled `phase:P02`, but the scope of unrelated issues must be handled by protected policy, not silently waived or relabelled to merge.
- Previous exact-head run #45238907411 passed Windows, Governance, Reviewdog and task board checks for the earlier P02 54-frame UIA implementation. New 69-candidate capture and HTML review-pack implementation must pass its **own exact source SHA** and be inspected; do not inherit the earlier run's verdict.

## Acceptance blockers to close, without lying

1. M02 final 15 + M19 final 14 PNGs must exist in required paths and match exact native receipts, with independent visual/label/contrast/clipping/keyboard review. A source-bound CI artifact or a 29-target HTML candidate index does NOT satisfy committed final screenshot assets.
2. Actual full app keyboard and screen-reader tests (NVDA/Narrator), including focus trapping, labels, selection, error announcements and navigation; existing 9/9 Windows UIA is *scoped*, not full certification.
3. Multi-run Windows performance baseline and approved explicit budgets; one startup/capture duration sample does not establish acceptable regressions.
4. Help and Wiki source parity plus verified hosted GitHub Wiki publication or a separately approved docs-site substitute; local source map is not remote publication.
5. Security/privacy, accessibility and docs change records reviewed with all required exact-head GitHub checks; task board status/PR body parity, independent owner-intent authorization and effective branch rules evaluated before removing draft status.
6. Protected PR merge actually executed only after all premerge gates, and new `main` SHA independently verified. Only then can P02 be `MERGED_VERIFIED` and next-phase work begin.

## Completed preflight / rollback

Confirmed active GitHub branch/PR/main/ruleset, current phase lease, task inventory, source-compiled real Windows Tauri/9-of-9 scoped native UIA baseline and live issue inventory. No data schema, native permissions, remote telemetry, API secrets, production release or external publishing changed in this slice. Revert review/capture code on the existing PR to roll back; preserve real user data and original screenshots.

**Result: NOT_READY_FOR_MERGE.** T11 is IN_PROGRESS, other unfinished tasks remain truthful; no protected rule weakening, self-approval, issue closure, next phase or release.
