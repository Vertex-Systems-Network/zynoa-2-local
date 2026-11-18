# Engineering Specification Changelog (not product releases)

## [3.2.1] - 2026-11-18
### Added
- [DESIGN-IO](operations/DESIGN_INTEROPERABILITY.md): planned tool-neutral editable import/export with format adapters, fidelity reports, security tests and help/screenshots for Figma, Penpot, OpenPencil-A, OpenPencil-B and additional supported formats.
- ADR-0008 and deferred **P08I** implementation phase. P08 Designer core must be completed, tested, documented and remotely merged before P08I is started.
### Changed
- Phase contracts, agent constitution and designer documentation now explicitly prohibit premature cross-tool compatibility claims.
### Status
- Planning and P00 governance work; no working import/export or desktop application release.

## [3.2.0] - 2026-11-18
### Added
- M26 change intelligence, issue/PR/release traceability, user-facing What's New, version history and audit timeline requirements.
- Change schema, validation/rendering proof-of-concept, regression tests, release gates and automatic Help/Wiki sync requirements.
- 8 UI screen specifications, 20 option specifications and 28 pending real-application screenshots.
### Changed
- Universal agent rules and phase PR template require structured change records and synchronized documentation.
- Integration plan includes event persistence from P01, professional UI from P02 and release publication in P11.

## [3.1.0] - 2026-11-18
### Added
- Planned User Data Vault/backups (M23), Storage Relocation (M24) and Update Center (M25), with release publisher and recovery gates.

**These are changes to the specification package, not evidence that any desktop application feature is implemented.**


## P00 governance implementation log — 2026-11-18 (UNRELEASED)

- Added authenticated, repository-scoped read-only GitHub PR/CI/branch/issue observation and conservative phase-readiness policy.
- Added SQLite single-owner renewable lease, durable event journal and resumable bounded observation loop; no privileged actions or remote merges.
- Added sanitized developer-ci GitHub Issue bridge, explicit publishing guard and trusted default-branch workflow that activates only after its merge to main.
- Added operator runbook, service template, hosting alternatives ADR-0009 and checkpointed handoff; CI upgraded to Node24-compatible v6 actions and live authenticated observation.
- GitHub CI passing evidence recorded in P00_REMOTE_PREFLIGHT.md; change record `CHG-P00-M22-PHASE-OBSERVER-20261118` status IMPLEMENTING.
- This log records engineering development only. No application release or public changelog entry exists; M22 still partial, P00 draft PR remains open with host/ruleset blockers.
