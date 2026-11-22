# P01-T07 native user vault — first implementation slice

**Status:** P01-T07 IN_PROGRESS, NOT DONE. Native Rust-only user data vault is **NOT connected to the frontend**, native app startup or any public IPC command. These are disposable Windows CI fixtures, not a persistent real user's workspace.

**Storage:** An independently pinned rusqlite 0.43.0 SQLite engine (MIT; bundled SQLite is public domain) uses the app-local `com.zynoa.desktop/data/state.sqlite` outside the executable. New installations get schema v1, SQLite WAL, FULL synchronous mode, foreign keys and bounded immutable first-write records. A success receipt is returned strictly after the SQLite transaction commits. Repeated IDs fail without overwriting earlier content. An unexpected existing SQLite schema or corrupt file is not replaced, reinitialized, migrated or deleted.

**Backup/recovery:** `snapshot_new` uses the SQLite Online Backup API, reserves a *new* snapshot path without overwriting an existing backup, and verifies integrity. `restore_to_new_test_profile` validates a snapshot into a separate disposable SQLite file. It never restores over the active vault. This internal snapshot is **NOT an encrypted portable backup**, is not safe against full disk loss when kept on the same disk, and is not exposed as a user-facing backup feature.

**Security limits:** Input comes only from trusted native tests; UI has no grants for save, read, or restore. Database file ACLs, secure OS ownership checks, transactional artifact blobs, idempotent updates, migrations, encryption/passphrase backup, full-schema content model, actual app boot persistence and uninstall/reinstall fixtures, low-disk failure injection, and user-facing recoverability are pending. T07 must not be accepted until relevant Windows integration and real restore evidence prove those guarantees. No actual user data is touched.

**Tests:** `python -m unittest tests.test_p01_vault`, Windows `cargo test --lib --release`, Windows executable build, Governance v3.2. GitHub CI links added only after successful runs.
