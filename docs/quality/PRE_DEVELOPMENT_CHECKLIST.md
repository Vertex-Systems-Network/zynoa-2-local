# PRE-DEV Gate (mandatory before every code change)

1. Verify repository exact origin, clean/understood worktree and GitHub remote current `main` SHA.
2. Verify active phase lease, scope path allowlist, current PR, CI state and unresolved critical issues.
3. Read `AGENTS.md`, appropriate agent wrapper, MASTER_PLAN_V3, module dossier, design ADR, memory/decisions and latest handoff.
4. Verify local environment, package versions, Windows target, Ollama and optional engine health; capture baseline warnings/errors and performance.
5. Search/revalidate official dependencies and UX options; record URLs/date/license and ≥2 feasible alternatives, or justify why only one.
6. Define user stories, IDs, each UI control type/default/validation/state/keyboard behavior/help/screenshot target and real backend link.
7. Threat model delta, privacy/telemetry impact, permissions, data flow, migration and rollback plan; sensitive changes reviewed by policy.
8. Set acceptance tests *before implementation*: unit/contract/integration/E2E/a11y/visual/security/performance/docs/Wiki.
9. Specify bounded autonomous retry budget, failure grouping and recovery route; reserve output paths and artifact hashes.
10. Record preflight report, baseline metrics and decision log; only then start source edits on active phase branch.

**Gate outcomes:** PASS, FAIL, BLOCKED with evidence. No automatic 'pass' from absence of checks. Existing failures require baseline labeling and linked issue; new warnings are never silently ignored. During implementation run short checks per slice; full checks before PR.

## v3.1 pre-development checklist additions

1. Identify durable chat/project/files data owner and confirm path outside app bundle; distinguish managed files vs mere external references.
2. Record pre-change data format/schema version; run a backup and corruption/recovery probe prior to any migration.
3. Enumerate downloaded artifacts, existing model folders, runtime ownership, disk and network volumes before installer or storage changes.
4. Verify current Tauri updater and action versions, packaging output names, signing secrets availability, version alignment and release channel policies.
5. Provide unit/integration/E2E fixtures for interrupted download, failed relocation, backup/restore and failed update.
6. Ensure release and backup documentation have real screenshot obligations and fresh Help/Wiki links; do not mark actual capture while app is unimplemented.

## v3.2 PRE-DEV changelog requirements

- Query most recent event IDs and source issues; identify duplicate issue fingerprints and existing planned work.
- Identify changes' category (bugfix/enhancement/feature/security/docs), product version impact and affected modules/options/screens.
- Before source edit, reserve a change ID and define acceptance tests, docs/Help/Wiki revisions and screenshots (if UI affected).
- Confirm release/issue privacy audience, known migration needs and how the change maps into upcoming release notes.
