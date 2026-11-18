# ADR-0007 — Separate incident ledger, PR changeset and released changelog

**Status:** Proposed; not implemented. **Date:** 2026-11-18.

## Context

The user needs an auditable event history of every issue, enhancement and update, while ensuring end users do not see unfinished work as shipped. Changelog, GitHub release notes, Help and Wiki must remain synchronized.

## Decision

Adopt event ledger + machine-readable per-PR change records + one release manifest as canonical source for release projections. Issue-open and PR-merged events are not themselves release events. Publish signed/verifiable release notes and derived `CHANGELOG.md` only from actual shipped versions. Keep module Help, Wiki and screenshot evidence versioned. Use Keep a Changelog categories and Semantic Versioning at product boundary. Optional Changesets can manage package versions but cannot decide shipped desktop app state alone.

## Rejected alternatives

- Generate What's New from every opened GitHub issue: misleading and potentially private.
- Generate released notes directly from closed PR labels: merged != published; missing documentation integrity.
- Make hand-edited CHANGELOG the only source: drift, duplicates and zero provenance.
- Immediately publish every phase merge: violates stable release qualification.

## Consequences

Additional structured metadata and consistency gates are required. Version cache must support offline users. Security advisories follow independent disclosure rules. GitHub Wiki publishing may lag but local versioned Help must not be missing.
