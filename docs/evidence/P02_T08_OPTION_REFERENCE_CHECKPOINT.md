# P02-T08 — M19 contextual Help workflow progress / native option directory

**Overall task status:** IN_PROGRESS — the source implementation is substantial but **not** accepted as the complete M19 reader/FAQ/wizard/report task.

## Current verified state

- Twelve bundled searchable articles, contextual F1 entry, five-step guided onboarding, four troubleshooting issues (three steps each), five FAQ answers, six glossary terms, sixteen M02/M19 option references, and sanitized local reports with safe-copy fallback.
- Strict typed local article and option routes, version-pinned search, bounded request sizes; no network fallback, browser storage or unsafe dynamic execution.
- Windows [#45189322734](https://github.com/Vertex-Systems-Network/zynoa-2-local/actions/runs/45189322734) on code SHA `cf30107a969ad1c15de8bc62cd4928137891a65d` succeeded: Python/Node UI regressions, TypeScript, Rust IPC, Tauri build/boot, 30 PNG metadata/provenance checks.
- [Native M19 six-screen review](../screenshots/M19/P02-M19-six-screen-review.json) covers real search, article reader, guided tour, troubleshooter and Wiki. [Option directory review](../screenshots/M19/P02-M19-option-reference-native-review.json) additionally confirms the visible initial 16-option interface.

## Required before T08 DONE

- Real native independent FAQ/glossary and local report/clipboard denied UI coverage, keyboard focus, state recovery and reader interactions; a new FAQ candidate is being added and is not yet independently reviewed.
- All required 14 final M19 screen/option images, true alt text and versioned manifest approval, assistive-technology checks and performance. Hosted Wiki is not claimed published. No full module/phase release or protected merge.

**Decision:** Keep T08 IN_PROGRESS and preserve the current Draft PR #12. No synthetic screenshots or fake source verification used.
