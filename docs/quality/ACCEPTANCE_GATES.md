# Non-negotiable Quality Gates

## Every phase
- Every deliverable listed in phase manifest has acceptance evidence (file paths, CI run IDs, test output or screenshots).
- Fresh dependency lockfiles, reproducible builds and version-checked toolchain.
- Formatting + lint + strict typecheck + unit tests pass where code exists.
- Integration and E2E tests for modified interfaces; relevant smoke tests run on Windows.
- Dependency license inventory, SCA/secret scan, CodeQL or equivalent where applicable.
- No critical/high severity unresolved findings, unowned privileged capability or unverified data flow.
- `STATUS.md`, `PHASE.json`, `HANDOFF.md`, ADR and PR record updated with factual results.
- PR meets branch protection; auto-merger verifies commit and status on GitHub before advancing.

## UI-focused P02 and later
- No dead buttons, placeholder metrics shown as real, unexplained errors or missing empty/loading/offline states.
- Keyboard navigable; WCAG 2.2 AA-oriented review (actual applicable checks recorded); adequate contrast, visible focus, semantic labels.
- Visual regression screenshots at 1280x800, 1440x900, 1920x1080 and 2560x1440; Windows scaling 100% and 125% where environment supports it.
- Navigation, splitter panels, sidebars, dialogs, forms, inspector, status bar and theme tokens use common components.
- Performance measures captured on target low/medium/high hardware profile; avoid inventing target achievement.

## Chat P03
- Real model response streaming, stop/regenerate, retry after crash, persisted conversations, attachments with provenance, measured time-to-first-token, fallback disclosure.
- Structured tool calls validated against schema; no unrestricted OS commands from chat.

## Coding P04
- Fresh checkout -> file diff -> sandbox test -> checkpoint -> rollback -> scoped commit -> PR on test repository.
- Error loop has bounded retry, audit, failure-state persistence; passing CI is mandatory.

## Figma-like P08
- Save/reopen document roundtrip preserves node IDs/properties; layer hierarchy, frames, selection, transform, text, component instances, constraints/auto-layout (per accepted milestone).
- Undo/redo, autosave/recovery, SVG/PNG export, history and design-token bindings verified on representative documents.
- Visual QA on actual canvas renders; generated designs remain editable, not flattened images.

## Performance and quality metrics
- Record startup p50/p95, UI interaction p95, memory idle, model cold start, TTFT, decode tokens/sec, context accuracy, tool schema success, agent task success rate, crash-free sessions, download useful throughput and checksum failure rate.
- Measure against a published baseline for each hardware tier; choose SLOs after sample benchmark rather than using made-up universal thresholds.
