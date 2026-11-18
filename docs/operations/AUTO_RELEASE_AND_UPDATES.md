# M20 + M25 — Automatic Releases, Update Delivery and User-Controlled Installation

**Status: SPECIFICATION ONLY — no release pipeline, update endpoint, installer, or installed client currently exists.**

## 1. Product contract

When a phase PR is merged and *all release-specific gates pass*, an automated publisher MAY create a qualified release for the configured channel. Installed users running a compatible client should see a non-disruptive update notification when online. The user chooses **Update Now**, **Download for Later**, **Remind Me Later**, or **View Release Notes**. Stable app versions must not point at unfinished dev build channels. User data must survive installation, restart, failed update and rollback.

This is a client-side **pull/check** update notification on application startup, on foreground/resume, and at a user-configured interval with jitter/backoff. Do **not** imply push delivery to an app which is not running. An optional OS background service is separately scoped, explicitly enabled, and not needed for MVP.

## 2. Automation from PR merge to release

`verified phase PR merge → update release eligibility record → validate semver and changelog → choose channel → create signed tag → immutable CI checkout → run release gate → reproducible build → sign artifacts → checksum+SBOM+provenance → publish GitHub Release + latest.json → canary smoke test manifest/install → promote channel atomically → client detects update`

Publisher is a dedicated release workflow with restricted `contents: write` and no PR-supplied code execution under privileged tokens. PR workflows use read-only permissions. Tag signing and immutable release assets are separate trust roots. Release signing key stays in GitHub Actions secrets/protected environment or stronger signing service, **never in source/client**. Tauri update verification uses embedded *public* key; Windows code signing is optional in development but strongly preferred for production to reduce trust warnings. Updater package signing ≠ Windows Authenticode signing; document independently.

**Do not release on every merge by default:** each phase merge triggers release-eligibility review, not guaranteed stable publication. Before product GA: alpha/nightly canary only; after GA: stable release on passing qualification. GitHub protected branch rules and mandatory checks cannot be overridden.

### Release channels

- `internal`: engineering builds, no user updater endpoint.
- `nightly`: explicit opt-in, rolling build, migrations backward-compatible within declared window.
- `beta`: explicit opt-in, fully validated upgrade/recovery, clear preview banner.
- `stable`: default, full regression, migration, backup, package integrity and live update tests.
- `security`: prioritization of audited critical fixes, without skipping signature or data tests.

A channel change must verify version compatibility, avoid accidental downgrades, and maintain user data portability. Release metadata includes build SHA, semantic version, supported OS/arch, minimum previous version, channel, timestamp, notes, binary hash, updater signature, schema versions and manifest URL.

### Mandatory publisher gates

1. Merge SHA and protected branch authentic and verified; release tag refers to verified commit.
2. Clean repo, dependency locks, license/SBOM checks, no high security findings, reproducible build review.
3. Windows packaged installer + correctly configured updater artifacts + `.sig` + compatible `latest.json`.
4. Version numbers consistent across Cargo.toml, package.json, Tauri config, tag, manifest and release notes.
5. Signature check against trusted public key, hash check, URL domain policy and HTTPS enforced.
6. Verified clean install, 1 previous stable → new stable upgrade, cancelled download, interrupted download, retry, offline, insufficient disk and corrupted signature.
7. Verify local data before/after in controlled tests: messages/files/settings/backup manifest hashes; DB migrations with copy/restore safety.
8. Canary rollout, crash threshold and rollback routing; **app binary rollback ≠ DB schema rollback**.
9. Help pages, UI screenshots, source-backed release notes, error codes and issue automation.
10. Final manifest published only after artifacts successfully uploaded and validated; never display an unavailable update.

### CI permissions/security

Separate unprivileged test workflow from publisher; avoid `pull_request_target` build of arbitrary fork code. Use GitHub least-privilege token, protected signing environment, immutable dependencies/pinned action SHAs in production, build attestations where available. Release action template is located in `templates/github-workflows/release-windows.yml` and MUST NOT be activated until the app code, secrets, path names and signing have been verified.

## 3. In-app Update Center

Route `settings://updates` and notification deep link `workspace://updates/available`. Screens: version overview, update notification, progress dialog, release notes, history/rollback eligibility, update failure recovery.

User preferences: startup/background-online checks, interval, channel, auto-download (OFF default), install policy (user-click default), bandwidth cap, metered-network policy, idle-window preference, skip/defer nonsecurity versions, check now, release notes and diagnostics.

**Critical contract:** app never silently interrupts an active job. Before updater install: pause agent workers, flush streams, checkpoint files, commit SQLite, create verified pre-upgrade recovery snapshot, freeze schema writes, close open handles, and display a clear restart/install action. If the last clean data checkpoint or backup fails, block automatic installation and offer diagnostics. If install succeeds, first-launch smoke-check schema, files, chat history, settings and workers, then mark success. If boot fails, offer recovery shell and previous compatible build when recoverable.

Error codes: `UPD-E001` network unavailable, `UPD-E002` signature invalid, `UPD-E003` incompatible platform, `UPD-E004` insufficient free disk, `UPD-E005` backup checkpoint failed, `UPD-E006` migration incompatible, `UPD-E007` installer launch failed, `UPD-E008` staged package inconsistent, `UPD-E009` forced rollback unavailable, `UPD-E010` manifest invalid.

## 4. Protocols, data and events

Contracts:

- `UpdateRelease {version, channel, commitSha, notes, supportedPlatforms, minimumVersion, artifactDigest, signerIdentity, schemaCompatibility}`.
- `UpdatePreference {channel, autoCheck, autoDownload, installPolicy, intervalHours, bandwidthLimit, meteredPolicy}`.
- `UpdateJob {jobId, idempotencyKey, desiredVersion, status, progress, downloadedBytes, totalBytes, signatureVerified, backupId, errorCode}`.
- `ReleaseQualification {phasePr, mergeSha, channel, gateResults, releaseDecision}`.

Events: `release.qualification.passed|failed`, `update.available`, `update.download.started|progress|completed|failed`, `update.signature.verified|rejected`, `update.preflight.passed|failed`, `update.installer.started`, `update.postboot.healthy|failed`, `update.deferred`.

Persistent states: `NO_UPDATE → AVAILABLE → DOWNLOADING → VERIFIED → PREFLIGHT → INSTALLING → RESTART_PENDING → POSTBOOT_VALIDATION → APPLIED`, with side states `DEFERRED`, `PAUSED`, `FAILED`, `RECOVERING`.

### Failure / tests

- Crash between download stages; app can resume without corrupting local profile.
- Invalid `latest.json` rejected; unsigned package rejected; wrong platform rejected.
- Network offline and metered network behavior; proxy/captive portal; safe retry.
- Signature valid but hash mismatch; manifest tampering; rollback protection.
- Disk full, power loss during preflight, antivirus holding executable, locked worker, abandoned model download.
- Open chat/coding editor not lost across successful or failed update.
- Stable client never offered beta/nightly artifact without channel opt-in.
- Rollout manifest failure does not make current valid installed version unusable.

## 5. Documentation obligations

Screenshots, annotated controls, keyboard access, update errors, offline UI, actual updater evidence, download/start/restart states, exact GitHub Release links, Wiki article and Help Center link are acceptance blockers. Until real app exists, mark all screenshots `PENDING`.

**Official reference sources (verified 2026-11-18):**
- https://v2.tauri.app/plugin/updater/
- https://v2.tauri.app/distribute/pipelines/github/
- https://github.com/tauri-apps/tauri-action
- https://docs.github.com/en/actions/reference/workflows-and-actions/workflow-syntax

## v3.2 release changelog synchronization

Release workflow must validate release-qualified `ChangeRecord`s and published artifact manifest before producing user-visible content. Generate `CHANGELOG.md` version section, GitHub release notes, signed update feed, local Help What's New and Wiki revision/index from the **same validated set of change IDs**. Reconcile release SHA, channel, version and published assets; unavailable artifacts must not trigger in-app announcement. On partial publication failure, retain last trusted feed, preserve original release history and create a deduplicated issue. See [M26](CHANGE_INTELLIGENCE_CHANGELOG.md).
