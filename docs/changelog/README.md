# Change Records — specification only

These JSON records are PR metadata. At present there are **no actual product changes/releases** and `records/` is empty. Test fixtures are kept under `tests/fixtures` and MUST NOT be published as actual release entries.

## Per-phase routine

1. New issue/enhancement → audit event; not a shipped changelog entry.
2. AI agent creates or updates a `.changes/records/CHG-....json` within the currently authorized phase PR when code/behavior changes.
3. Update `docs/modules`, `docs/help/articles`, `docs/wiki/pages` and any affected UI/option specifications. Capture actual screenshots when module done.
4. CI validates record schema, issue/PR proof, docs references, duplicate IDs, risk/migration flags, and phase status.
5. Verified merge creates an unreleased release candidate only.
6. Signed release publishes a verified release manifest; root `CHANGELOG.md` and in-app feed are then generated from that manifest; never list merely reported/merged issues as shipped.

Template schema: [change-record.schema.json](schema/change-record.schema.json). 

Local demo validation (not real GitHub workflow):
```sh
python tools/changelog.py validate --records tests/fixtures/change_records.json
python tools/changelog.py render --records tests/fixtures/change_records.json --version 0.1.0 --channel stable --date 2026-11-18
```

All fixture records are artificial samples. Rendering is stdout-only unless intentionally redirected.

Additional event-envelope contract: [change-event.schema.json](schema/change-event.schema.json). UI/release tool alternatives: [Changelog tools comparison](../research/CHANGELOG_TOOL_COMPARISON.csv).
