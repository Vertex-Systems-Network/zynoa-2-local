# M23 — Durable User Data, Chat History, Files, Backup and Restore

**Status: SPECIFICATION ONLY. This document defines protection objectives, not a guarantee that no device or storage failure can cause data loss.**

## 1. Data ownership and classification

Separate **user-owned data** from **reconstructible caches**, **third-party runtime model weights**, **machine secrets**, and **files merely referenced by path**. Never use a single hidden unstructured folder or tie any user data to the executable installation directory.

| Category | Contents | Persistence/backup policy |
|---|---|---|
| Chat history | Conversation tree, messages, edits, titles, model and source refs, attachments metadata | Critical, backup ON |
| Projects | Workspaces, settings, snippets, saved prompts, agents, tasks/checkpoints | Critical, backup ON |
| User-created files | Imported/generated managed files, designs, exports, code artifacts | Critical, backup ON when managed |
| Referenced external files | Original files located outside app data vault | Keep reference + identity; optional explicit inclusion in full backup, NEVER silently copy entire folders |
| Indexed knowledge | Source metadata, indexes, embeddings | Index manifests essential; embeddings may be rebuilt |
| Settings | Preferences, configured storage paths, layouts, memory settings | Critical, backup ON except secrets |
| Credentials | OAuth tokens, PATs, encryption keys | OS keychain, not plaintext export; explicit encrypted recovery policy |
| AI model binaries | Ollama/HF/ComfyUI weights | Excluded from standard backup by default; export a versioned redownload manifest; optional opt-in full archival |
| Temporary files | Partial downloads, renderer cache, thumbnails, GPU cache | Not backed up |
| Logs | Error fingerprints, diagnostics | Sanitized/retained according to policy; optional export |

### Required data guarantees (engineering targets)

- Every acknowledged chat message is committed transactionally before marked stored in UI.
- Generate stable `conversationId`, `messageId`, `artifactId`, `checksum`, `revision` and typed storage events.
- Use SQLite WAL for normalized history, FK/integrity constraints, migrations, and uniquely addressed managed artifact blobs on disk.
- Atomic save: write temp file, fsync when appropriate, checksum, atomic rename, DB transaction refers to committed content; reconcile orphans on startup.
- DB `sqlite3_backup` Online Backup API or `VACUUM INTO` under tested conditions; **never naively copy a live WAL database file** as the only backup strategy.
- Incremental snapshot chain must be recoverable without depending on a stale cache. Periodically create independently restorable full snapshot.
- Run local integrity audit at launch after unclean shutdown; do not rewrite damaged source before attempting recovery to a new location.
- If disk is full, app must NOT show false 'saved' state; preserve best-effort in-memory buffer until user can free space, then show explicit unsaved status.

## 2. User Data Vault layout

Example Windows location (resolved using OS APIs; do not hardcode username):

```
%LOCALAPPDATA%/AIWorkspace/
    data/state.sqlite
    data/artifacts/sha256/xx/<hash>
    data/projects/<projectId>/manifest.json
    data/indexes/
    backups/catalog.sqlite
    backups/snapshots/<backupId>.awbackup
    cache/                 # disposable, separate
    logs/                  # redacted
```

Executable binaries, user data, caches, external files, and model storage remain logically and physically separate. User data folder has a stable app identifier across updates; installer/uninstall must not recursively delete it. Uninstall offers clear *separate* optional user-data deletion action; default keeps it. Backup targets may be independent internal/external storage. Storage locations are accessible through Settings and Diagnostics.

### User data DB sketch

`conversations(id, title, created_at, updated_at, deleted_at)`; `messages(id, conversation_id, parent_id, role, content_ref, status, revision, created_at)`; `managed_artifacts(id, sha256, bytes, mime, path, owner_scope, created_at)`; `artifact_links(message_id, artifact_id, role)`; `projects(id, metadata, root_path, last_seen)`; `backup_jobs(id, status, source_revision, destination, manifest_hash, verified_at)`; `backup_items(job_id, content_sha256, class, logical_id)`; `restore_jobs(id, checkpoint_before_restore, status, manifest_hash)`; `schema_migrations(version, application_version, result)`; `change_journal(seq, entity_type, entity_id, revision, operation, persisted_at)`; `settings(key, value, version)`.

Default backups exclude credentials and model weights, and warn that original external project files remain outside app custody unless explicitly included.

## 3. Backup profiles and defaults

- `Quick`: chats, prompts, settings, project manifests, managed attachments; fastest.
- `Complete`: all critical user-controlled managed files, designs, chat history, project metadata, indexes (if useful).
- `Custom`: category granular selection and external workspace inclusion with size preview.
- `Before Update`: automatic verified checkpoint before schema/binary change, with retention protected during migration.
- `Before Restore`: automatic safety snapshot of current profile before replacing data.

Proposed defaults: local incremental every 6 hours while app running, daily full snapshot when possible, 7 daily + 4 weekly + 3 monthly retention slots; all configurable with disk/usage limits. Scheduled backups when app is closed require an explicit installed OS scheduler/service; otherwise catch up on next launch. Retention is best-effort and storage dependent, not a magic guarantee.

### Portable backup format `.awbackup`

Manifest: format_version, app_version, schema_version, created_at, workspace scope, included/excluded classes, encryption KDF metadata, payload content hashes, chunk metadata, compression method, base snapshot dependencies, restore minimum version. Use standard versioned container; validate directory traversal and decompression bombs before extraction. Do not write decrypted content into world-readable temp folders.

Encryption: libsodium XChaCha20-Poly1305 AEAD + Argon2id for passphrase-based key derivation **or independently reviewed equivalent**. Per-backup random salts/nonces; never invent crypto. Recovery key/passphrase loss prevents decryption; explain and offer OS keychain-based local convenience as optional. Cloud backup is not silently enabled; if integrated later, end-to-end encryption before remote upload and per-provider scoped permissions.

## 4. Restore transaction

`select archive → inventory & size preview → verify checksum/AEAD and app/schema compatibility → pre-restore safety snapshot → restore to staged separate path → validate DB + artifact references + migrations dry-run → swap active user profile via atomic pointer/transaction → restart services → first-load check → mark verified`; failures roll back pointer to intact old vault. `Merge`, `Replace`, `Selective restore` are distinct actions, never auto-overwrite without a specifically configured restore policy. Default use safe new profile to preview before replace.

Restore policy must address duplicate conversation IDs, file conflicts, case-insensitive Windows paths, symlinks, partial artifacts, invalid archives, permissions, insufficient disk and migration mismatch.

**Recovery objectives (proposal, subject to benchmark):** successful recovery from a single bad app update with prior verified checkpoint; successful restore test from encrypted archive under app-supported schema; every backup completion runs basic manifest integrity validation; weekly automated restore dry-run for engineering fixtures. For hardware disk failure, second physical/offsite copy is required: backups solely on the same disk cannot guarantee survival.

## 5. UI and Help

`Settings → Data & Privacy`, `Settings → Backups`, `Settings → Data Locations`, `Chat → History`, `Help → Restore My Data`.

UI must show: total stored chats/files, location, free disk, latest backup state/time, encryption state, backup coverage, retention, restore verification status, export/import, full user-delete controls and cross-link to Help. Inform when referenced external files are outside backup. No secret content in diagnostics or GitHub incidents.

### Failure codes

`DAT-E001` failed transactional write; `DAT-E002` artifact checksum mismatch; `DAT-E003` storage full; `BKP-E001` destination unavailable; `BKP-E002` corrupt/incomplete archive; `BKP-E003` invalid passphrase/tag; `BKP-E004` incompatible schema; `BKP-E005` restore staging failed; `BKP-E006` backup coverage incomplete; `BKP-E007` key unavailable; `BKP-E008` offline backup location unavailable.

### Required verification scenarios

1. Save thousands of chats, attachments and project entries; restart app and compare IDs/hashes.
2. Crash during write, model run, backup creation and restore; no incorrectly acknowledged successful writes.
3. WAL busy with concurrent sessions during online snapshot; resultant SQLite passes `PRAGMA integrity_check` and file link checks.
4. Encrypted archive correct/wrong passphrase, tamper, truncated header/chunk; no partial unsafe restore.
5. Restore same backup twice (idempotent/explicit conflict handling), selective restore and new-profile preview.
6. Update stable A → B preserves user data, and tested compatible rollback from B → A never silently corrupts newer schema.
7. Uninstall/reinstall with same app identity retains vault; temp/cache cleanup must not remove artifacts.
8. External file changed/deleted, broken symbolic links, network drive disconnected and disk full show clear remediation.
9. Backup/restore folder path with Unicode, spaces, long Windows path, read-only volume and removable drive.
10. Rotate backup passphrase using re-encryption without copying plaintext outside safe temp staging; audit log.

**Official references:**
- https://www.sqlite.org/backup.html
- https://www.sqlite.org/wal.html
- https://learn.microsoft.com/en-us/windows/apps/design/app-settings/store-and-retrieve-app-data
