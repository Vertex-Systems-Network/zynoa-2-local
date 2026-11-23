# P02 native Windows performance observations — not approved release budgets

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
