# P03-T02 — Native chat-data schema and migration (DONE)

T01 accepted on exact source 37b7cc366789936c872093733d130791d4062402 after native Windows and real Ollama artifact readback. T02 implements the ADR-0030 storage slice in apps/desktop/src-tauri/src/vault.rs without new dependencies, IPC or UI exposure. Scope: additive v1 -> v2 schema; legacy opaque records unchanged, normalized conversation/message records, atomic journal, bounded stable ordinal history, verified snapshot and staged restore only.

## Acceptance inventory (nine native tests passed)

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

Backup is local unencrypted v1 copy (verified SQLite Online Backup API); it is not a portable encrypted archive, offsite guarantee or sole-copy deletion permission. Unknown schema rejects. Migration rolls back on failure; reserved snapshot remains available if completed. Legacy opaque history remains in original records; no unsupported automatic conversion. Terminal partial status is persisted separately from model generation success. UI, full backup/restore activation, artifact bytes, real crash/reinstall and user-facing errors are later tasks. New native chat methods not yet wired may trigger dead-code warnings; do not suppress. Actual native library warnings: 44 versus 36 baseline (eight added warnings from not-yet-wired chat APIs); lib test warnings unchanged at 5. These remain open for T03/T14 resolution. No warning suppression.

## Independent exact-source acceptance — 2026-11-25

- Verified tested source `8d3944b35b08641f416967da8b758fedd98e7bce`; [native Windows run](https://github.com/Vertex-Systems-Network/zynoa-2-local/actions/runs/45620810721) SUCCESS and [Governance](https://github.com/Vertex-Systems-Network/zynoa-2-local/actions/runs/45620812774) SUCCESS (753 tests, zero failures), companion model, runner, PR sync and desktop workflows success (the old desktop job intentionally skipped, not claimed as a second native run).
- Windows Python 753 executed: 707 passed, 46 platform skips, zero failures. Full Rust release suite 41/41; focused native vault suite 9/9, zero failures or ignored, 0.83 seconds. Existing 32 tests preserved. TypeScript, frontend/UI, native build, actual fresh-profile startup, read-only schema v2, integrity/FK, WAL, migration row, diagnostics, registry and event DB checks all passed.
- [Original proof artifact #15024323818](https://github.com/Vertex-Systems-Network/zynoa-2-local/actions/runs/45620810721/artifacts/15024323818) downloaded; independently computed ZIP SHA-256 `eff0bebf2d81665c7016fb568fae17297420e633c74b1d83adbc8aa88e820ca0` matches remote digest. Exact source in both JSON files; original test-log SHA-256 `9b06c8fc59708cf3e2b3c4a1aae7fa0fb1d724005bd55c73a2243a5518d4a82d` independently matches schema proof. Log contains all nine named passed tests. Executable SHA-256 as reported by runner `ec984965b3b16bcb64954c460f40741f893f0461fe532221ae6121a1fdb5d3d5`; startup window and metadata 7224 ms. Executable itself not in ZIP; no independent executable rehash claim. Actual app-created SQLite DB read-only check schema v2 and integrity/FK OK, zero user data. Migration/rollback fixtures real SQLite tests, not a user profile.
- Scope accepted: T02 native data substrate only. Source is unmerged on PR #25. No screenshot, UI functionality, encrypted portable backup, crash/reinstall acceptance or release claim. Local Git clone unavailable, CI and connector exact-source proof used. T03 next; no subsequent feature started.
