# P03-T02 — Native chat-data schema and migration (IN_PROGRESS)

T01 accepted on exact source 37b7cc366789936c872093733d130791d4062402 after native Windows and real Ollama artifact readback. T02 implements the ADR-0030 storage slice in apps/desktop/src-tauri/src/vault.rs without new dependencies, IPC or UI exposure. Scope: additive v1 -> v2 schema; legacy opaque records unchanged, normalized conversation/message records, atomic journal, bounded stable ordinal history, verified snapshot and staged restore only.

## Acceptance inventory (actual CI pending)

Nine native Rust tests:
- fresh schema v2, WAL/FULL/FK and migration history;
- real v1 fixture migrates, preserves text/revision/timestamp and verifies exclusive pre-migration backup, no duplicate migration;
- unavailable snapshot location rejects migration and preserves v1;
- injected DDL failure rolls back schema and version;
- future and malformed schema reject without reinitialization;
- postcommit typed receipts, reopened history and scope/ordinal pagination;
- duplicate, invalid and cross-conversation parent/missing thread reject without journal/revision side effects;
- injected journal failure rolls back message and conversation revision; retry has original ordinal;
- real online v2 snapshot and separate v1/v2 staged restore, no active data overwrite.

CI runs existing full Python suite, all Rust release tests plus named native T02 tests, TypeScript/UI/build, native executable boot and read-only actual schema v2 integrity, foreign-key check, empty synthetic profile, migration row, registry, diagnostics and ledger. It uploads source-bound executable proof, Rust test output and schema JSON with test-log hash. No test or artifact claimed before run results and independent ZIP readback.

## Limits and recovery

Backup is local unencrypted v1 copy (verified SQLite Online Backup API); it is not a portable encrypted archive, offsite guarantee or sole-copy deletion permission. Unknown schema rejects. Migration rolls back on failure; reserved snapshot remains available if completed. Legacy opaque history remains in original records; no unsupported automatic conversion. Terminal partial status is persisted separately from model generation success. UI, full backup/restore activation, artifact bytes, real crash/reinstall and user-facing errors are later tasks. New native chat methods not yet wired may trigger dead-code warnings; do not suppress. Actual warning counts and exact-head test evidence pending.
