# M26 — Change Intelligence, Changelog, Audit and Documentation Sync

**Status: SPECIFICATION AND LOCAL TEST SCAFFOLD ONLY. No desktop changelog, CI-integrated release publisher or remote GitHub event bridge is deployed.**

## 1. Purpose and definition of done

Every meaningful bug, warning, incident, enhancement, feature, dependency/security update, UI adjustment and release obtains a traceable **event**. User-visible shipped changes are curated into versioned **release notes** and `CHANGELOG.md`. The same authoritative change IDs are connected to per-module technical docs, Help Center, Wiki source, screenshots (if UI affected), GitHub issues, PRs, tests and the signed release manifest.

**Never confuse four concepts:**

1. **Issue/ticket:** a problem or request exists; this DOES NOT mean fixed. Event `issue.reported` begins the record.
2. **Development change:** implementation is underway; the PR may fail or be reverted. Not shipped.
3. **Verified merge:** a PR merged into protected main, but no released binary necessarily exists.
4. **Published release:** signed installer/update successfully published and release manifested for the correct audience/channel. Only now can What's New say 'Available in version X'.

Issue-open events appear in the **In Progress / Known Issues** area; they do not enter the public released changelog. If a fix is reverted before release, keep the audit history; do not market it as delivered. Internal/audit-only events may appear in technical timeline under granted authorization without flooding public What's New. A security issue can have a private issue/advisory with a generic public summary until disclosure is safe.

## 2. Sources of truth (strongly separated)

| Layer | Source | Mutability | Consumers |
|---|---|---|---|
| 1. Live incident/audit feed | SQLite `change_events` / append-only durable event queue | Append-only; corrections are new events | Admin timeline, diagnostic router, job recovery |
| 2. Issue & PR truth | GitHub Issues, PR merge state, verified Git SHA | Refreshed from remote API; deduplicated | In Progress, development dashboard, change traceability |
| 3. PR change records | `.changes/records/<change_id>.json` in active phase branch | Reviewed with PR | CI, doc sync, version planning |
| 4. Merged release manifest | Signed/validated release CI manifest, released Git ref and artifact hashes | Immutable per release | `CHANGELOG.md`, release notes, in-app What's New |
| 5. Help & Wiki sources | `docs/help/...`, `docs/wiki/...` | Version controlled, published as separately verified step | Context help and support |
| 6. Client local cache | SQLite `release_feed_cache`, unread prefs | Rebuilt from signed embedded release data | Offline UI and update notifications |

**Invariant:** Changelog is a projection of verified data, not a writable source of release truth. No direct edits to an already released version's claims without a new signed correction/addendum; preserve historical integrity. PR change records should include a normalized version bump request and may integrate Changesets, but the desktop app version itself is centrally managed (do not let each package bump desktop version independently).

## 3. Events & schemas

Each event carries: `event_id` (unique), `stream_id` (change/issue), per-stream `sequence`, `event_type`, UTC time, origin (client/agent/CI/GitHub), correlation/causation ID, module, severity, payload (redacted), local/offline delivery state and retention class. JSON schema for the PR-facing change record is at `docs/changelog/schema/change-record.schema.json`; runtime event envelope is separate and specified at `docs/changelog/schema/change-event.schema.json`.

`ChangeRecord` mandatory fields:
- `change_id`: stable `CHG-...` UUID-like or unique sequence; never reuse.
- `module_id`, `kind`: `feature`, `enhancement`, `bugfix`, `performance`, `security`, `breaking`, `docs`, `dependency`, `maintenance`.
- `title` and user-oriented `summary` versus detailed internal technical notes.
- `status`: `reported`, `triaged`, `planned`, `implementing`, `merged`, `verified`, `released`, `reverted`.
- `source_issue_urls[]`, `source_pr_url`, `affected_option_ids[]`, `docs_paths[]`, `help_paths[]`, `wiki_paths[]`.
- `test_evidence[]` (test command + result link), verified `commit_sha`, `release.version/date/channel` if truly shipped.
- `audience`: `user`, `developer`, `private`; `breaking_change` and `migration_notes` when relevant.
- `created_at`, `updated_at`, `actor_kind`; additional `docs_impact` and `data_migration` flags.

**Event examples:** `issue.reported`, `issue.triaged`, `change.planned`, `change.started`, `test.failed`, `test.passed`, `docs.updated`, `pr.opened`, `pr.merged_verified`, `change.verified`, `release.qualified`, `release.published`, `client.update.detected`, `client.update.applied`, `change.reverted`. Rate-limit noisy diagnostics; unique fingerprint for recurring error. Repeated events must not cause duplicated change cards or GitHub issues.

### State machine

`REPORTED -> TRIAGED -> PLANNED -> IMPLEMENTING -> MERGED -> VERIFIED -> RELEASED`.

Allow an internal `BLOCKED` flag at every pre-release state. `REVERTED`, `CANCELLED` are terminal outcomes with retained history. No direct jump `REPORTED -> RELEASED`; release requires verified merge, CI checks, documentation and release manifest. `issue.closed` alone is insufficient evidence.

## 4. Autonomously produced change records and documentation

**On issue creation:** store a sanitized event and GitHub issue URL; show *Known Issues* (not What's New). On enhancement acceptance: record scope, intended user impact and affected module with `planned` state. On each significant implementation slice: attach PR, tests, screenshots and files; do not create user-facing release copy until merge evidence exists. On verified merge: add to internal `Unreleased` candidate queue, note document revisions and options changed; user-visible What's New stays unchanged. On release qualification: determine actual bundled commits and release channel, derive release version, diff prior release and attach only records present in published artifact. On release publication: atomically export `CHANGELOG.md`, release notes Markdown, JSON feed and docs index based on same canonical manifest; verify hash/revision parity. In app, cache signed feed and update unread state. For older clients, show only compatible release notes and migration notices.

**One PR MUST contain:**
1. One or more change records for user-impacting changes, or an explicit machine-validated `docs-only / no-user-impact` classification for purely internal changes.
2. Issue link (if any), exact module ID, support severity and public/private audiences.
3. Updated module dossier, option catalog and screen inventory where behavior or controls changed.
4. Updated Help/Wiki source for any affected user-visible behavior; screenshots of actual changed controls once implemented.
5. Test evidence and current issue statuses; migration and rollback instructions if data semantics changed.
6. Version impact (`major`, `minor`, `patch`, or `none`), breaking/compatibility flags, approved security-disclosure policy.

`PR -> docs changed -> docs screenshot tests -> CI quality gates -> merged SHA verified -> release candidate -> signed release -> release notes publication`. Documentation drift blocks phase finalization. Never allow a generator to silently overwrite editorial corrections without storing the reviewed source and rerunning parity checks.

## 5. Public changelog categories and release versions

Use Keep a Changelog style: `Added`, `Changed`, `Deprecated`, `Removed`, `Fixed`, `Security` in the user-facing file; optional `Performance` and `Breaking` badges in the app UI, mapped to appropriate headings. A semantic version bump is based on actual contract compatibility, not issue priority: `major` for incompatible breaking release, `minor` for backward-compatible user features, `patch` for backward-compatible fixes. Beta/nightly pre-releases are isolated by release channel. PR labels or conventional commits are useful categorization hints but never override verified change records.

**Example (illustrative only, not an actual release):**
```markdown
## [1.3.0] - 2026-11-18
### Added
- Added version-filtered change history in Settings. (CHG-001, PR #42)
### Fixed
- Fixed chat recovery after interrupted shutdown. (CHG-002, Issue #87)
```

**Special cases:**
- `docs` changes trigger their own planning/doc history; only public-visible when user benefit justifies a `Changed` release entry.
- `security` fixes: redact vulnerabilities and private issue URLs until coordinated disclosure; for critical client protections include urgency and update guidance, not exploit code.
- `revert`: event retained. If a release containing feature was revoked, publish a corrected update/advisory; don't silently rewrite downloaded notes.
- `duplicate issues`: one canonical issue fingerprint links to multiple occurrence events.
- `partial deployment`: wait until actual artifact is published for target OS/channel. Version number alone does not prove availability.
- `offline`: client uses last verified cached release notes; it cannot know about new releases while offline.
- `privacy`: don't put user prompts, absolute home paths, personal documents, secrets, token values or private stack traces in public changelog or GitHub Issues.

## 6. Desktop UI — UX and accessibility requirements

Routes: `workspace://whats-new`, `workspace://changes/in-progress`, `workspace://changes/history`, `workspace://changes/<change_id>`, `workspace://changes/module/<module_id>`, `settings://changes`.

Screens M26-S01 .. M26-S08 (see dossier), with readable chronological version cards; categories, filters and module selectors; deep links to relevant Help, GitHub Issue/PR, compare versions, migration warnings and follow-up fix status. Empty state says **No released changes yet**, not `v1.0.0` if no actual published release. Unknown remote links are plain text or hidden. Offline UI presents last-verified timestamp. Privacy-sensitive developer/audit timeline is behind permission scopes. Unread indicator clears only when a user views that version; do not reset across app restarts. Keyboard and screen-reader semantics; high-DPI, responsive widths, contrast compliance and locale labels. All API responses are paginated for scale.

## 7. Help Center + Wiki automatic sync contract

For any user-impacting record, include version-aware `docs_paths`, `help_paths`, `wiki_paths` and `affected_option_ids`. When an option changes, CI verifies: option ID exists; Help explanation updated; screenshot manifest has a real capture **when module is finalized**, with alt text, hash, build SHA; Wiki source article updates and version compatibility are correct. Release generator includes links to exact docs for the shipped version and checks local offline Help resources exist. Publish Wiki using a separate authenticated step; if GitHub Wiki is temporarily unavailable, keep versioned local Help and mark publication pending instead of inventing a link. Changelog cards link to installed app's matching Help version so they remain meaningful offline.

## 8. Quality gates and expected tests

`CHANGE-01` Every externally visible code PR has structured change record(s) or a validated no-user-visible classification.

`CHANGE-02` Each changed option/function has updated docs, Help + Wiki sources and screenshot/alt obligations; no stale links or wrong version.

`CHANGE-03` Every released record has verified merge SHA, actual published artifact, matching version/channel, CI tests passing and linked documentation.

`CHANGE-04` Known issues / enhancement requests are NEVER labeled shipped before published release.

`CHANGE-05` Idempotent GitHub callbacks and retries; deduped by `(provider,event_id)` and consistent stream sequence; repeated events create no duplicate entry.

`CHANGE-06` Release notes, root `CHANGELOG.md`, Help What's New page, updater notification and signed JSON change feed agree on versions, sections and change IDs.

`CHANGE-07` Security/privacy: sanitize payloads, restrict sensitive details, block private source links and system paths from public feed.

`CHANGE-08` Crash, offline, interrupted publish, pagination, missing GitHub API, duplicate issues, wrong channel, reverted change, old client, data migration and release rollback exercised.

`CHANGE-09` Update installer preserves unread notification state and cached history; backup/restore includes user settings but does not pretend to synchronize private GitHub issue data.

`CHANGE-10` Real screenshots and option-by-option Help for module M26 before it is final; test local Help link and GitHub Wiki sync.

**Automation and sample tooling:** `tools/changelog.py` validates PR change records and generates a preview from a verified released fixture; it is not the production event bus. `scripts/verify_v32_kit.py` validates the spec package. `tests/test_changelog.py` covers shipped-only filtering, privacy filtering, missing docs verification and duplicate entries. The guarded CI workflow is a *template/gate for governance*, not a deployed production release system.

## 9. Research and external standards (verified 2026-11-18)

- Keep a Changelog: https://keepachangelog.com/en/1.1.0/
- Semantic Versioning: https://semver.org/spec/v2.0.0.html
- GitHub auto-generated release notes: https://docs.github.com/en/repositories/releasing-projects-on-github/automatically-generated-release-notes
- Changesets monorepo changes: https://changesets.dev/guide/getting-started
- Changesets release and changelog flow: https://changesets.dev/guide/why

Record official docs' retrieval dates in research bank before relying on current APIs.
