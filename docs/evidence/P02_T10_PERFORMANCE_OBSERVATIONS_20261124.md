
**Latest validated P02-T10 exact-source baseline (2026-11-24):** [Windows #45305110513](https://github.com/Vertex-Systems-Network/zynoa-2-local/actions/runs/45305110513) source `1831de8433f2649684971fafbd83193db529330b` passed the unchanged budget after native exact-property UIA lookup optimization: cold native metadata 11,662ms, 69 native screenshot suite 92,602ms, 3 warm IPC samples 651/757/723ms (median 723ms). Aggregate acceptance gate PASS. Previous failing [#45303604148](https://github.com/Vertex-Systems-Network/zynoa-2-local/actions/runs/45303604148) recorded 1,357/7,052/4,976ms with a full-descendant enumeration probe; those values remain unmodified historical evidence. Unapproved product cold-start SLA and Narrator/release certification remain separately open. 

# P02 native Windows performance observations — not approved release budgets

**New native repeat evidence — 2026-11-24:** [Windows CI #45286192929](https://github.com/Vertex-Systems-Network/zynoa-2-local/actions/runs/45286192929) **SUCCESS** on `d0a8a3a7a3a9c8b69cf3353b4c48cc5c8677bc85`: three distinct real Tauri process launches had **first OS-visible native HWND 250, 133 and 139 ms** (median **139 ms**; maximum **250 ms**). The original verified GitHub job log contains the executable SHA-256 and exact-source receipt; Windows native build/boot/screenshot and negative Python contracts passed. **These values are only first visible shell, not ready-to-interact or native IPC latency** and must not be called product startup SLA or an approved budget.

**Stronger follow-up now implemented:** [source commit `fffb510`](https://github.com/Vertex-Systems-Network/zynoa-2-local/commit/fffb5101473908ebc393841d98a4daa6cbbebe15) keeps both first-visible-window timings and a separate **native IPC connected UIA readiness** duration, by inspecting actual WebView2 accessibility-tree status text `Typed native handshake connected`. It rejects missing status, nonmatching HWND PID, inconsistent timings, fewer/duplicate native processes and fake approved budget; adds negative fixtures. Its exact-head Windows run remains **NOT YET VERIFIED** at this checkpoint and must be read from CI. These are **three warm process** observations, not statistically reliable P95 or repeatable cold-start. The earlier real 42,582 ms native metadata outlier below remains in the baseline; do not hide it.

**Policy:** `performance_budget_approved=false`, `full_screen_reader_verified=false`, T10 IN_PROGRESS until approved thresholds, repeated cold/warm measurements and NVDA/Narrator signoff.

**Status:** UNAPPROVED_OBSERVATION_ONLY. This is not a T10 performance acceptance certificate.

## Actual source-bound Windows measurements

| Real GitHub native Tauri run | Source / attempt | Native metadata readiness (ms) | Screenshot suite (ms) | Meaning |
| --- | --- | ---: | ---: | --- |
| [#45265826578](https://github.com/Vertex-Systems-Network/zynoa-2-local/actions/runs/45265826578) | `80bb8fde` attempt 1 | 9694 | 92729 | Exact-source native build, data and capture |
| [#45265826578](https://github.com/Vertex-Systems-Network/zynoa-2-local/actions/runs/45265826578) | `80bb8fde` attempt 2 | 6627 | 93609 | Same source fresh GitHub-hosted runner |
| [#45274014314](https://github.com/Vertex-Systems-Network/zynoa-2-local/actions/runs/45274014314) | `c9a874a9` attempt 1 | 42582 | 93794 | New exact-head full PASS, potential startup outlier |

The third observation took 42.6 seconds from process launch until required native startup metadata was available. Do **not** discard it or infer a passing 10-second budget. GitHub-hosted Windows runner cold-start, AV, IO and visual-capture overhead vary; measurements are neither controlled warm-launch benchmarks nor production SLA. Separate preflight startup time from screenshot-suite time. Runs combine app boot and whole 69-frame screenshot automation, not typical user interactive latency.

## Before release performance acceptance

1. Run repeatable exact-source Win2025 native executable startup and representative palette/help interaction journeys with captured runner environment, cold/warm split, median and P95.
2. Propose explicit product UX and CI capture budgets from measured percentiles and resource context, with independent reviewer approval recorded in versioned evidence.
3. Put non-bypassable budget checks into the Windows native CI, include bad-budget fixtures and verify a real failing-run negative sample before certifying performance.
4. Investigate native startup variance (6.6–42.6s in this small unbalanced sample); **performance_budget_approved remains false**.

No additional binaries, user data, telemetry, secrets or CI skip has been introduced by this documentation.

## Explicit CI preview performance budget (2026-11-24)
The versioned [P02 CI budget](../quality/P02_T10_PERFORMANCE_BUDGET.json) adds non-bypassable Windows policy checks to the same source-bound real Tauri run. Thresholds: first CI native metadata readiness ≤45,000 ms; complete 69-real-PNG capture ≤120,000 ms; each of three warm native OS-visible windows ≤1,000 ms; each IPC-connected UIA interaction-ready ≤3,000 ms and median ≤2,000 ms. These are **P02 GitHub-hosted preview budgets, not a production startup SLA**. The historically measured 42,582ms outlier remains explicitly in the policy and cannot be deleted. Full end-user cold-start percentile and P11 product performance approval still require more controlled evidence. The CI step fails if source SHA, provenance, privacy, metrics or limits mismatch; successful verification doesn't grant NVDA/Narrator or release approval.
