# P02-T11 — Protected Merge and Final Acceptance Preflight

**Latest 2026-11-24 evidence checkpoint:** All 29/29 genuine committed M02/M19 screen/option PNGs now have independent per-image SHA-bound visual review status VERIFIED. The 29th, M19-OPT-01, was re-captured on real Windows Tauri CI #45274014314 and its original binary replaced after read-only artifact-transport proof #45279976526. See [complete screenshot review record](P02_T10_FINAL_29_NATIVE_SCREENSHOTS_20261124.json). **These are screenshot proofs only.** Independent full NVDA/Narrator keyboard and live announcement testing, endorsed performance percentiles/budgets, hosted Wiki publication, owner/current-SHA review, security/issue adjudication and protected merge remain outstanding. T02/T10/T11 still IN_PROGRESS, PR #12 Draft, main unchanged.


**Latest 2026-11-24 checkpoint:** Authentic committed native screenshot assets total 29/29; scoped M02 image review 15 VERIFIED and scoped M19 review 13 VERIFIED, leaving **M19-OPT-01 final image 1 PENDING**. The corrected native M19 search control is source/hash validated on passing [Windows CI #45274014314](https://github.com/Vertex-Systems-Network/zynoa-2-local/actions/runs/45274014314) but not yet substituted into the versioned final path. Governance/Reviewdog/task-board checks passed on the same source head. Exact phase closeout **still blocked**: full NVDA/Narrator, approved performance budget, hosted Wiki publication, independent current-SHA owner review, all gates and protected merge. Main untouched, P03/release forbidden.


**New 2026-11-24 checkpoint:** 29 exact-original native Windows PNGs are now committed, matching SHA-256/Git blob source. M02 15/15 images have per-frame visual acceptance; M19 14 images still require final visual sign-off and refreshed search control screenshot. This removes the *missing M02 PNG* blocker only. Full NVDA/Narrator interaction testing, three-or-more exact-source performance runs with reviewed budgets, externally verified Wiki publication (or explicitly approved alternative), all-status docs parity, exact-head CI and independent owner PR approval/merge are **NOT COMPLETE**. This preflight stays NOT_READY_FOR_MERGE; do not bypass ruleset or merge just to change statuses.


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

## Exact source 69-frame evidence checkpoint (2026-11-23)

[Windows #45252195376](https://github.com/Vertex-Systems-Network/zynoa-2-local/actions/runs/45252195376) **SUCCESS** on `f2835a2a497ee0ad0f5a032f7bcd1069e9fd6ac9`. Original [GitHub artifact #14857775294](https://github.com/Vertex-Systems-Network/zynoa-2-local/actions/runs/45252195376/artifacts/14857775294) independently downloaded and validated: **69 PNG hash receipts matched, 15 unique native direct controls, all 29 final target IDs mapped to source-bound candidate images**, native UIA 9/9. Performance sample 7,168ms local metadata boot / 92,672ms complete 69-capture suite (one run, no budget). [Source-bound report](P02_T10_69_NATIVE_PROVENANCE_20261123.md). **No screenshot manifest entries promoted**; full visual/screen-reader, actual hosted Wiki, reviewer/owner-intent and protected merge gates still open. PR remains draft and T11 IN_PROGRESS.
