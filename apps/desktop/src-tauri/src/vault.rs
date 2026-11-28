//! M23 native SQLite vault, P01 foundation and P03 additive chat schema; not a WebView command.
//! All operations are within the trusted app-local data path, never the binary.
//! User content is never logged, sent to telemetry or silently replaced.
use rusqlite::{params, Connection, ErrorCode, OpenFlags, OptionalExtension, TransactionBehavior, MAIN_DB};
use serde::{Deserialize, Serialize};
use std::fs::{self, OpenOptions};
use std::path::{Path, PathBuf};
use std::time::{Duration, SystemTime, UNIX_EPOCH};

const SCHEMA_VERSION: i64 = 4;
const ARTIFACT_SCHEMA_VERSION: i64 = 3;
const CHAT_SCHEMA_VERSION: i64 = 2;
const MAX_MESSAGE_ATTACHMENTS: usize = 8;
// Explicit bounded recovery inspection, never a deletion authorization.
const MAX_RECOVERY_ENTRIES: usize = 4096;
const MAX_RECOVERY_BYTES: u64 = 100 * 1024 * 1024;
const MAX_MESSAGE_ATTACHMENT_BYTES: u64 = 100 * 1024 * 1024;
const LEGACY_VERSION: i64 = 1;
const MAX_CONTENT_BYTES: usize = 262_144;
const MAX_TITLE_BYTES: usize = 512;
const MAX_PAGE: u32 = 200;
const MAX_CONTEXT_MESSAGES: usize = 512;
const TEXT_ARTIFACT_NOTICE: &str = "Saved assistant response as text artifact.";
const TEXT_ARTIFACT_NAME: &str = "assistant-response.txt";

/// Domain-separated deterministic identifiers, not filesystem paths.
fn text_artifact_ids(conversation_id: &str, source_id: &str) -> (String, String) {
    use sha2::{Digest, Sha256};
    let derive = |domain: &str| {
        let mut h = Sha256::new();
        h.update(domain.as_bytes());
        h.update([0u8]);
        h.update(conversation_id.as_bytes());
        h.update([0u8]);
        h.update(source_id.as_bytes());
        format!("{:x}", h.finalize())
    };
    (derive("zynoa-text-artifact-message-v1"), derive("zynoa-text-artifact-file-v1"))
}

// Retain the exact original P01 table, including its opaque conversation
// records. Do not guess how legacy content maps to normalized messages.
const LEGACY_SCHEMA: &str = "CREATE TABLE records(
                   id TEXT PRIMARY KEY NOT NULL,
                   class TEXT NOT NULL CHECK(class IN ('conversation','project','preference')),
                   payload TEXT NOT NULL,
                   revision INTEGER NOT NULL CHECK(revision >= 1),
                   created_at INTEGER NOT NULL
                 )";

const CHAT_SCHEMA: &str = "
CREATE TABLE conversations(
    id TEXT PRIMARY KEY NOT NULL CHECK(length(id) BETWEEN 8 AND 64 AND id NOT GLOB '*[^A-Za-z0-9_-]*'),
    title TEXT NOT NULL CHECK(length(CAST(title AS BLOB)) BETWEEN 1 AND 512 AND instr(title,char(0))=0),
    revision INTEGER NOT NULL CHECK(typeof(revision)='integer' AND revision>=1),
    created_at INTEGER NOT NULL,
    updated_at INTEGER NOT NULL
);
CREATE TABLE messages(
    id TEXT PRIMARY KEY NOT NULL CHECK(length(id) BETWEEN 8 AND 64 AND id NOT GLOB '*[^A-Za-z0-9_-]*'),
    conversation_id TEXT NOT NULL REFERENCES conversations(id) ON DELETE RESTRICT,
    parent_id TEXT,
    ordinal INTEGER NOT NULL CHECK(typeof(ordinal)='integer' AND ordinal>=1),
    role TEXT NOT NULL CHECK(role IN ('user','assistant','system')),
    content TEXT NOT NULL CHECK(length(CAST(content AS BLOB)) BETWEEN 1 AND 262144 AND instr(content,char(0))=0),
    status TEXT NOT NULL CHECK(status IN ('complete','cancelled','failed')),
    revision INTEGER NOT NULL CHECK(typeof(revision)='integer' AND revision>=1),
    created_at INTEGER NOT NULL,
    CHECK(parent_id IS NULL OR parent_id<>id),
    UNIQUE(conversation_id,id),
    UNIQUE(conversation_id,ordinal),
    FOREIGN KEY(conversation_id,parent_id) REFERENCES messages(conversation_id,id) ON DELETE RESTRICT
);
CREATE TABLE schema_migrations(
    version INTEGER PRIMARY KEY CHECK(version=2),
    from_version INTEGER NOT NULL CHECK(from_version IN (0,1)),
    application_version TEXT NOT NULL,
    backup_id TEXT,
    result TEXT NOT NULL CHECK(result='applied'),
    applied_at INTEGER NOT NULL,
    CHECK((from_version=0 AND backup_id IS NULL) OR (from_version=1 AND backup_id IS NOT NULL))
);
CREATE TABLE chat_change_journal(
    seq INTEGER PRIMARY KEY,
    entity_type TEXT NOT NULL CHECK(entity_type IN ('conversation','message')),
    entity_id TEXT NOT NULL,
    revision INTEGER NOT NULL CHECK(typeof(revision)='integer' AND revision>=1),
    operation TEXT NOT NULL CHECK(operation IN ('insert','message_added')),
    persisted_at INTEGER NOT NULL,
    UNIQUE(entity_type,entity_id,revision)
);
CREATE INDEX chat_journal_entity ON chat_change_journal(entity_type,entity_id,seq);
";

// V2 history stays intact. V3 has its own immutable migration receipt so older
// V2 snapshots remain verifiable without rewriting their migration history.
const ARTIFACT_SCHEMA: &str = "
CREATE TABLE managed_artifacts(
    id TEXT PRIMARY KEY NOT NULL CHECK(length(id) BETWEEN 8 AND 64 AND id NOT GLOB '*[^A-Za-z0-9_-]*'),
    conversation_id TEXT NOT NULL REFERENCES conversations(id) ON DELETE RESTRICT,
    name TEXT NOT NULL CHECK(length(CAST(name AS BLOB)) BETWEEN 1 AND 160 AND instr(name,char(0))=0),
    sha256 TEXT NOT NULL CHECK(length(sha256)=64 AND sha256 NOT GLOB '*[^0-9a-f]*'),
    bytes INTEGER NOT NULL CHECK(typeof(bytes)='integer' AND bytes BETWEEN 0 AND 26214400),
    created_at INTEGER NOT NULL,
    UNIQUE(conversation_id,id)
);
CREATE TABLE artifact_links(
    conversation_id TEXT NOT NULL,
    message_id TEXT NOT NULL,
    artifact_id TEXT NOT NULL UNIQUE,
    position INTEGER NOT NULL CHECK(typeof(position)='integer' AND position BETWEEN 0 AND 7),
    PRIMARY KEY(conversation_id,message_id,position),
    FOREIGN KEY(conversation_id,message_id) REFERENCES messages(conversation_id,id) ON DELETE RESTRICT,
    FOREIGN KEY(conversation_id,artifact_id) REFERENCES managed_artifacts(conversation_id,id) ON DELETE RESTRICT
);
CREATE TABLE artifact_schema_migrations(
    version INTEGER PRIMARY KEY CHECK(version=3),
    from_version INTEGER NOT NULL CHECK(from_version IN (0,1,2)),
    backup_id TEXT,
    applied_at INTEGER NOT NULL,
    CHECK((from_version IN (0,1) AND backup_id IS NULL) OR (from_version=2 AND backup_id IS NOT NULL))
);
";

// V4 keeps private review decisions alongside the durable conversation.
const TOOL_REVIEW_SCHEMA: &str = "
CREATE TABLE tool_review_decisions(
    request_id TEXT PRIMARY KEY NOT NULL CHECK(length(request_id) BETWEEN 8 AND 64 AND request_id NOT GLOB '*[^A-Za-z0-9_-]*'),
    conversation_id TEXT NOT NULL REFERENCES conversations(id) ON DELETE RESTRICT,
    turn_id TEXT NOT NULL CHECK(length(turn_id) BETWEEN 8 AND 64 AND turn_id NOT GLOB '*[^A-Za-z0-9_-]*'),
    target_id TEXT NOT NULL CHECK(length(target_id) BETWEEN 8 AND 64 AND target_id NOT GLOB '*[^A-Za-z0-9_-]*'),
    target_sha256 TEXT NOT NULL CHECK(length(target_sha256)=64 AND target_sha256 NOT GLOB '*[^0-9a-f]*'),
    tool TEXT NOT NULL CHECK(tool IN ('local.read_attachment','local.write_artifact')),
    decision TEXT NOT NULL CHECK(decision IN ('approve','deny')),
    recorded_at INTEGER NOT NULL CHECK(typeof(recorded_at)='integer' AND recorded_at>0)
);
CREATE TRIGGER tool_review_no_replace BEFORE INSERT ON tool_review_decisions
    WHEN EXISTS(SELECT 1 FROM tool_review_decisions WHERE request_id=NEW.request_id)
    BEGIN SELECT RAISE(ABORT,'immutable review decision'); END;
CREATE TRIGGER tool_review_no_update BEFORE UPDATE ON tool_review_decisions
    BEGIN SELECT RAISE(ABORT,'immutable review decision'); END;
CREATE TRIGGER tool_review_no_delete BEFORE DELETE ON tool_review_decisions
    BEGIN SELECT RAISE(ABORT,'immutable review decision'); END;
CREATE TABLE tool_review_schema_migrations(
    version INTEGER PRIMARY KEY CHECK(version=4),
    from_version INTEGER NOT NULL CHECK(from_version IN (0,1,2,3)),
    backup_id TEXT,
    applied_at INTEGER NOT NULL,
    CHECK((from_version IN (0,1,2) AND backup_id IS NULL) OR (from_version=3 AND backup_id IS NOT NULL))
);
";

pub(crate) struct LinkedAttachment {
    pub(crate) id: String,
    pub(crate) receipt: crate::artifact_contracts::AttachmentReceipt,
}

#[derive(Clone, Copy)]
pub(crate) enum ChatRole { User, Assistant, System }
impl ChatRole {
    fn name(self) -> &'static str {
        match self { Self::User => "user", Self::Assistant => "assistant", Self::System => "system" }
    }
}

#[derive(Clone, Copy)]
pub(crate) enum ChatStatus { Complete, Cancelled, Failed }
impl ChatStatus {
    fn name(self) -> &'static str {
        match self { Self::Complete => "complete", Self::Cancelled => "cancelled", Self::Failed => "failed" }
    }
}

// Deliberately no Debug implementation for structures holding private text.
pub(crate) struct ChatMessageInput<'a> {
    pub(crate) id: &'a str,
    pub(crate) conversation_id: &'a str,
    pub(crate) parent_id: Option<&'a str>,
    pub(crate) role: ChatRole,
    pub(crate) content: &'a str,
    pub(crate) status: ChatStatus,
}

// Native thread metadata, deliberately separate from message bodies.
pub(crate) struct ConversationSummary {
    pub(crate) id: String,
    pub(crate) title: String,
    pub(crate) revision: i64,
    pub(crate) created_at: i64,
    pub(crate) updated_at: i64,
}

pub(crate) struct StoredChatMessage {
    pub(crate) id: String,
    pub(crate) parent_id: Option<String>,
    pub(crate) ordinal: i64,
    pub(crate) role: String,
    pub(crate) content: String,
    pub(crate) status: String,
    pub(crate) revision: i64,
    pub(crate) created_at: i64,
}

/// Native receipt for a managed artifact derived from committed assistant text.
pub(crate) struct TextArtifactReceipt {
    pub(crate) message_id: String,
    pub(crate) source_id: String,
    pub(crate) attachment: LinkedAttachment,
    pub(crate) replayed: bool,
}

pub(crate) struct ChatWriteReceipt {
    pub(crate) id: String,
    pub(crate) revision: i64,
    pub(crate) conversation_revision: i64,
    pub(crate) ordinal: Option<i64>,
}

#[derive(Clone, Debug, PartialEq, Eq, Serialize, Deserialize)]
#[serde(deny_unknown_fields)]
pub(crate) struct InferenceSettings {
    pub(crate) model: String,
    pub(crate) context_limit: u32,
    pub(crate) revision: i64,
}

pub(crate) struct ModelContext {
    pub(crate) messages: Vec<StoredChatMessage>,
    pub(crate) estimated_tokens: u32,
    pub(crate) limit: u32,
    pub(crate) omitted_messages: u32,
}

#[derive(Debug, Clone, Copy, PartialEq, Eq)]
pub(crate) enum VaultFault {
    InvalidLocation, InvalidRecord, Conflict, Corrupt, UnsupportedSchema, StorageUnavailable, BackupAuthentication,
}

#[derive(Debug, Clone, Copy, PartialEq, Eq)]
pub(crate) enum ContentClass { Conversation, Project, Preference }
impl ContentClass {
    fn name(self) -> &'static str {
        match self {
            Self::Conversation => "conversation",
            Self::Project => "project",
            Self::Preference => "preference",
        }
    }
}

// One bounded, session-only selected-file draft per native vault. No renderer
// filesystem path or hash grants access to existing managed content.
struct AttachmentUpload {
    id: String,
    name: String,
    total: u64,
    data: Vec<u8>,
}
#[derive(Default)]
struct AttachmentDraft {
    conversation_id: String,
    message_id: String,
    uploads: Vec<AttachmentUpload>,
}
pub(crate) const MAX_ATTACHMENT_CHUNK: usize = 64 * 1024;
#[derive(Debug, Default, PartialEq, Eq)]
pub(crate) struct ManagedRecoveryInventory {
    pub(crate) referenced_hashes: usize,
    pub(crate) verified_referenced: usize,
    pub(crate) verified_unreferenced: usize,
    pub(crate) unavailable_referenced: usize,
    pub(crate) damaged_or_unreadable: usize,
    pub(crate) interrupted_stages: usize,
    pub(crate) unexpected_entries: usize,
    pub(crate) unlinked_metadata: usize,
}
#[derive(Clone, Serialize)]
#[serde(rename_all="camelCase")]
pub(crate) struct ReviewPreview {
    conversation_id: String,
    request_id: String,
    source_id: String,
    target_id: String,
    target_sha256: String,
    tool: String,
}

#[derive(Serialize)]
#[serde(rename_all="camelCase")]
pub(crate) struct ReviewTrace {
    request_id: String,
    target_id: String,
    target_sha256: String,
    tool: String,
    decision: String,
    recorded_at: i64,
}

struct PendingToolReview {
    identity: crate::artifact_contracts::ToolReviewIdentity,
    source_id: String,
    attachment_id: Option<String>,
    conversation_revision: i64,
    expires: std::time::Instant,
}

#[derive(Serialize)]
#[serde(rename_all="camelCase")]
pub(crate) struct ConversationExportReceipt {
    pub(crate) conversation_id:String,
    pub(crate) revision:i64,
    pub(crate) export_id:String,
    pub(crate) relative_path:String,
    pub(crate) bytes:u64,
    pub(crate) sha256:String,
    pub(crate) message_count:usize,
    pub(crate) attachment_count:usize,
}

#[derive(Serialize)]
#[serde(rename_all="camelCase")]
pub(crate) struct PortableBackupReceipt {
    pub(crate) backup_id:String,
    pub(crate) relative_path:String,
    pub(crate) bytes:u64,
    pub(crate) sha256:String,
    pub(crate) item_count:usize,
}
#[derive(Serialize)]
#[serde(rename_all="camelCase")]
pub(crate) struct PortableRestoreReceipt {
    pub(crate) backup_id:String,
    pub(crate) restore_id:String,
    pub(crate) relative_path:String,
    pub(crate) item_count:usize,
    pub(crate) conversation_count:u64,
    pub(crate) active_profile_changed:bool,
}

pub(crate) struct NativeVault {
    app_root: PathBuf,
    conn: Connection,
    attachment_draft: AttachmentDraft,
    discarded_uploads: std::collections::VecDeque<(String,String)>,
    pending_review: Option<PendingToolReview>,
}

fn safe_id(value: &str) -> bool {
    (8..=64).contains(&value.len())
        && value.bytes().all(|b| b.is_ascii_alphanumeric() || b == b'-' || b == b'_')
}

fn checked_directory(path: &Path) -> Result<(), VaultFault> {
    let meta = fs::symlink_metadata(path).map_err(|_| VaultFault::InvalidLocation)?;
    if !meta.is_dir() || meta.file_type().is_symlink() {
        return Err(VaultFault::InvalidLocation);
    }
    Ok(())
}

fn checked_child(parent: &Path, child: &str) -> Result<PathBuf, VaultFault> {
    checked_directory(parent)?;
    let path = parent.join(child);
    match fs::create_dir(&path) {
        Ok(()) => (),
        Err(e) if e.kind() == std::io::ErrorKind::AlreadyExists => (),
        Err(_) => return Err(VaultFault::StorageUnavailable),
    }
    checked_directory(&path)?;
    Ok(path)
}

fn reject_nonregular_file(path: &Path) -> Result<bool, VaultFault> {
    match fs::symlink_metadata(path) {
        Ok(meta) if meta.file_type().is_symlink() || !meta.is_file() =>
            Err(VaultFault::InvalidLocation),
        Ok(_) => Ok(true),
        Err(e) if e.kind() == std::io::ErrorKind::NotFound => Ok(false),
        Err(_) => Err(VaultFault::StorageUnavailable),
    }
}

fn map_sql(err: rusqlite::Error) -> VaultFault {
    match err {
        rusqlite::Error::SqliteFailure(failure, _)
            if failure.code == ErrorCode::ConstraintViolation => VaultFault::Conflict,
        _ => VaultFault::StorageUnavailable,
    }
}

fn integrity_check(db: &Connection) -> Result<(), VaultFault> {
    let check: String = db.query_row("PRAGMA integrity_check", [], |row| row.get(0))
        .map_err(|_| VaultFault::Corrupt)?;
    if check != "ok" { return Err(VaultFault::Corrupt); }
    Ok(())
}

fn valid_text(value: &str, max: usize) -> bool {
    !value.trim().is_empty() && value.len() <= max && !value.contains('\0')
}

pub(crate) fn valid_model(value: &str) -> bool {
    !value.is_empty() && value.len() <= 128 && value.bytes().all(|b|
        b.is_ascii_alphanumeric() || matches!(b, b'.'|b'_'|b':'|b'/'|b'-'))
        && value.split('/').all(|part| !part.is_empty() && part != "." && part != "..")
}

fn valid_context_limit(value: u32) -> bool {
    matches!(value, 512|1024|2048|4096|8192|16384|32768)
}

fn version(db: &Connection) -> Result<i64, VaultFault> {
    db.query_row("PRAGMA user_version", [], |r| r.get(0)).map_err(|_| VaultFault::Corrupt)
}

fn normalize_sql(sql: &str) -> String {
    sql.chars().filter(|c| !c.is_ascii_whitespace() && *c != ';').collect::<String>().to_ascii_lowercase()
}

fn verify_legacy_table(db: &Connection) -> Result<(), VaultFault> {
    let sql: String = db.query_row(
        "SELECT sql FROM sqlite_schema WHERE type='table' AND name='records'", [], |r| r.get(0)
    ).map_err(|_| VaultFault::Corrupt)?;
    if normalize_sql(&sql) != normalize_sql(LEGACY_SCHEMA) { return Err(VaultFault::Corrupt); }
    Ok(())
}

fn validate_schema(db: &Connection) -> Result<i64, VaultFault> {
    let v = version(db)?;
    if !matches!(v, LEGACY_VERSION | CHAT_SCHEMA_VERSION | ARTIFACT_SCHEMA_VERSION | SCHEMA_VERSION) { return Err(VaultFault::UnsupportedSchema); }
    integrity_check(db)?;
    verify_legacy_table(db)?;
    if v == LEGACY_VERSION {
        let count: i64 = db.query_row(
            "SELECT count(*) FROM sqlite_schema WHERE name NOT LIKE 'sqlite_%'", [], |r| r.get(0)
        ).map_err(|_| VaultFault::Corrupt)?;
        if count != 1 { return Err(VaultFault::Corrupt); }
    } else {
        for table in ["conversations", "messages", "schema_migrations", "chat_change_journal"] {
            let found: i64 = db.query_row(
                "SELECT count(*) FROM sqlite_schema WHERE type='table' AND name=?1", [table], |r| r.get(0)
            ).map_err(|_| VaultFault::Corrupt)?;
            if found != 1 { return Err(VaultFault::Corrupt); }
        }
        let migrated: i64 = db.query_row(
            "SELECT count(*) FROM schema_migrations WHERE version=2 AND result='applied' AND
             ((from_version=0 AND backup_id IS NULL) OR (from_version=1 AND backup_id IS NOT NULL))",
            [], |r| r.get(0)
        ).map_err(|_| VaultFault::Corrupt)?;
        if migrated != 1 { return Err(VaultFault::Corrupt); }
        if v >= ARTIFACT_SCHEMA_VERSION {
            for table in ["managed_artifacts", "artifact_links", "artifact_schema_migrations"] {
                let found: i64 = db.query_row(
                    "SELECT count(*) FROM sqlite_schema WHERE type='table' AND name=?1", [table], |r| r.get(0)
                ).map_err(|_| VaultFault::Corrupt)?;
                if found != 1 { return Err(VaultFault::Corrupt); }
            }
            let migrated: i64 = db.query_row(
                "SELECT count(*) FROM artifact_schema_migrations WHERE version=3 AND
                 ((from_version IN (0,1) AND backup_id IS NULL) OR (from_version=2 AND backup_id IS NOT NULL))",
                [], |r| r.get(0)
            ).map_err(|_| VaultFault::Corrupt)?;
            if migrated != 1 { return Err(VaultFault::Corrupt); }
        }
        if v == SCHEMA_VERSION {
            let found: i64 = db.query_row(
                "SELECT count(*) FROM sqlite_schema WHERE (type='table' AND name IN
                 ('tool_review_decisions','tool_review_schema_migrations')) OR (type='trigger' AND name IN
                 ('tool_review_no_update','tool_review_no_delete','tool_review_no_replace'))",
                [], |r| r.get(0)
            ).map_err(|_| VaultFault::Corrupt)?;
            if found != 5 { return Err(VaultFault::Corrupt); }
            let migrated: i64 = db.query_row(
                "SELECT count(*) FROM tool_review_schema_migrations WHERE version=4 AND
                 ((from_version IN (0,1,2) AND backup_id IS NULL) OR (from_version=3 AND backup_id IS NOT NULL))",
                [], |r| r.get(0)
            ).map_err(|_| VaultFault::Corrupt)?;
            if migrated != 1 { return Err(VaultFault::Corrupt); }
        }
        let mut check = db.prepare("PRAGMA foreign_key_check").map_err(|_| VaultFault::Corrupt)?;
        let mut rows = check.query([]).map_err(|_| VaultFault::Corrupt)?;
        if rows.next().map_err(|_| VaultFault::Corrupt)?.is_some() { return Err(VaultFault::Corrupt); }
    }
    Ok(v)
}

fn apply_v2(db: &Connection, from: i64, backup_id: Option<&str>) -> Result<(), VaultFault> {
    db.execute_batch(CHAT_SCHEMA).map_err(map_sql)?;
    db.execute(
        "INSERT INTO schema_migrations(version,from_version,application_version,backup_id,result,applied_at)
         VALUES(2,?1,?2,?3,'applied',unixepoch())",
        params![from, env!("CARGO_PKG_VERSION"), backup_id],
    ).map_err(map_sql)?;
    db.execute_batch("PRAGMA user_version=2;").map_err(map_sql)?;
    Ok(())
}

fn apply_v3(db: &Connection, from: i64, backup_id: Option<&str>) -> Result<(), VaultFault> {
    db.execute_batch(ARTIFACT_SCHEMA).map_err(map_sql)?;
    db.execute(
        "INSERT INTO artifact_schema_migrations(version,from_version,backup_id,applied_at)
         VALUES(3,?1,?2,unixepoch())", params![from,backup_id],
    ).map_err(map_sql)?;
    db.execute_batch("PRAGMA user_version=3;").map_err(map_sql)?;
    Ok(())
}

fn apply_v4(db: &Connection, from: i64, backup_id: Option<&str>) -> Result<(), VaultFault> {
    db.execute_batch(TOOL_REVIEW_SCHEMA).map_err(map_sql)?;
    db.execute(
        "INSERT INTO tool_review_schema_migrations(version,from_version,backup_id,applied_at)
         VALUES(4,?1,?2,unixepoch())", params![from,backup_id],
    ).map_err(map_sql)?;
    db.execute_batch("PRAGMA user_version=4;").map_err(map_sql)?;
    Ok(())
}

// Managed content is native-only and derived from verified SHA-256, never a renderer path.
// These helpers assume the OS-owned app directory is not concurrently mutated by an
// external same-user process. They reject observed links/reparse points but do not
// claim OS sandbox isolation or adversarial path-race protection.
fn managed_plain(meta: &fs::Metadata) -> bool {
    #[cfg(windows)]
    {
        use std::os::windows::fs::MetadataExt;
        if meta.file_attributes() & 0x400 != 0 { return false; }
    }
    !meta.file_type().is_symlink()
}

fn managed_directory(path: &Path) -> Result<(), VaultFault> {
    let meta = fs::symlink_metadata(path).map_err(|_| VaultFault::InvalidLocation)?;
    if !meta.is_dir() || !managed_plain(&meta) { return Err(VaultFault::InvalidLocation); }
    Ok(())
}

fn managed_child(parent: &Path, child: &str) -> Result<PathBuf, VaultFault> {
    managed_directory(parent)?;
    let path = parent.join(child);
    match fs::create_dir(&path) {
        Ok(()) => (),
        Err(e) if e.kind() == std::io::ErrorKind::AlreadyExists => (),
        Err(_) => return Err(VaultFault::StorageUnavailable),
    }
    managed_directory(&path)?;
    Ok(path)
}

fn managed_hash_valid(hash: &str) -> bool {
    hash.len() == 64 && hash.bytes().all(|b| b.is_ascii_digit() || (b'a'..=b'f').contains(&b))
}

// SQLite INTEGER is signed. Reject corrupt lengths before converting to a receipt.
fn managed_length_from_sql(value: i64) -> Result<u64, VaultFault> {
    let length = u64::try_from(value).map_err(|_| VaultFault::Corrupt)?;
    if length > crate::artifact_contracts::MAX_ATTACHMENT { return Err(VaultFault::Corrupt); }
    Ok(length)
}

fn read_verified_blob(path: &Path, receipt: &crate::artifact_contracts::AttachmentReceipt)
    -> Result<Vec<u8>, VaultFault>
{
    use std::io::Read;
    let meta = fs::symlink_metadata(path).map_err(|_| VaultFault::StorageUnavailable)?;
    if !meta.is_file() || !managed_plain(&meta) { return Err(VaultFault::InvalidLocation); }
    if meta.len() != receipt.bytes || receipt.bytes > crate::artifact_contracts::MAX_ATTACHMENT {
        return Err(VaultFault::Corrupt);
    }
    let mut opts = OpenOptions::new();
    opts.read(true);
    #[cfg(windows)]
    {
        use std::os::windows::fs::OpenOptionsExt;
        opts.custom_flags(0x00200000); // FILE_FLAG_OPEN_REPARSE_POINT
    }
    let file = opts.open(path).map_err(|_| VaultFault::StorageUnavailable)?;
    let opened = file.metadata().map_err(|_| VaultFault::StorageUnavailable)?;
    if !opened.is_file() || !managed_plain(&opened) || opened.len() != receipt.bytes {
        return Err(VaultFault::Corrupt);
    }
    let mut bytes = Vec::new();
    file.take(receipt.bytes + 1).read_to_end(&mut bytes).map_err(|_| VaultFault::StorageUnavailable)?;
    if !crate::artifact_contracts::verify_attachment(receipt, &bytes) { return Err(VaultFault::Corrupt); }
    Ok(bytes)
}

fn snapshot_connection_new(app_root: &Path, source: &Connection, snapshot_id: &str)
    -> Result<PathBuf, VaultFault>
{
    if !safe_id(snapshot_id) { return Err(VaultFault::InvalidRecord); }
    let expected_version = version(source)?;
    let backup_root = checked_child(app_root, "backups")?;
    let directory = checked_child(&backup_root, "snapshots")?;
    let path = directory.join(format!("{snapshot_id}.sqlite"));
    if reject_nonregular_file(&path)? { return Err(VaultFault::Conflict); }
    for suffix in ["-wal", "-shm", "-journal"] {
        if reject_nonregular_file(&directory.join(format!("{snapshot_id}.sqlite{suffix}")))? {
            return Err(VaultFault::Conflict);
        }
    }
    let file = OpenOptions::new().create_new(true).write(true).open(&path)
        .map_err(|_| VaultFault::Conflict)?;
    drop(file);
    source.backup(MAIN_DB, &path, None::<fn(rusqlite::backup::Progress)>).map_err(map_sql)?;
    let verify = Connection::open_with_flags(&path, OpenFlags::SQLITE_OPEN_READ_ONLY).map_err(map_sql)?;
    if validate_schema(&verify)? != expected_version { return Err(VaultFault::Corrupt); }
    drop(verify);
    OpenOptions::new().write(true).open(&path).and_then(|file| file.sync_all())
        .map_err(|_| VaultFault::StorageUnavailable)?;
    Ok(path)
}

fn portable_fault(f:crate::backup_contracts::PortableFault)->VaultFault{
    use crate::backup_contracts::PortableFault;
    match f {PortableFault::Invalid=>VaultFault::InvalidRecord,
        PortableFault::Authentication=>VaultFault::BackupAuthentication,
        PortableFault::Storage=>VaultFault::StorageUnavailable}
}

// Reject extra tables, virtual tables, triggers and changed SQL definitions
// in authenticated archives too. Authentication does not imply trusted schema.
fn validate_portable_db(db:&Connection)->Result<(),VaultFault>{
    if validate_schema(db)?!=SCHEMA_VERSION{return Err(VaultFault::UnsupportedSchema);}
    let expected=Connection::open_in_memory().map_err(map_sql)?;
    expected.execute_batch(LEGACY_SCHEMA).map_err(map_sql)?;
    apply_v2(&expected,0,None)?;apply_v3(&expected,0,None)?;apply_v4(&expected,0,None)?;
    fn objects(db:&Connection)->Result<Vec<(String,String,String,Option<String>)>,VaultFault>{
        let mut q=db.prepare("SELECT type,name,tbl_name,sql FROM sqlite_schema WHERE name NOT LIKE 'sqlite_%' ORDER BY type,name")
            .map_err(map_sql)?;
        let rows=q.query_map([],|r|Ok((r.get(0)?,r.get(1)?,r.get(2)?,r.get(3)?))).map_err(map_sql)?;
        rows.collect::<Result<Vec<_>,_>>().map_err(map_sql)
    }
    if objects(db)?!=objects(&expected)?{return Err(VaultFault::Corrupt);}
    Ok(())
}

fn portable_blobs(db:&Connection)->Result<std::collections::BTreeMap<String,crate::artifact_contracts::AttachmentReceipt>,VaultFault>{
    use crate::artifact_contracts::{AttachmentReceipt,valid_managed_basename};
    let mut q=db.prepare("SELECT name,sha256,bytes FROM managed_artifacts ORDER BY sha256,id LIMIT 4097").map_err(map_sql)?;
    let rows=q.query_map([],|r|Ok((r.get::<_,String>(0)?,r.get::<_,String>(1)?,r.get::<_,i64>(2)?))).map_err(map_sql)?;
    let mut result=std::collections::BTreeMap::<String,AttachmentReceipt>::new();
    for (index,row) in rows.enumerate(){
        if index>=4096{return Err(VaultFault::InvalidRecord);}
        let (name,sha256,size)=row.map_err(|_|VaultFault::Corrupt)?;
        let bytes=managed_length_from_sql(size)?;
        if !valid_managed_basename(&name)||!managed_hash_valid(&sha256){return Err(VaultFault::Corrupt);}
        if let Some(old)=result.get(&sha256){if old.bytes!=bytes{return Err(VaultFault::Corrupt);}}
        else {result.insert(sha256.clone(),AttachmentReceipt{name,sha256,bytes});}
    }
    Ok(result)
}

fn read_portable_file(path:&Path,max:usize)->Result<Vec<u8>,VaultFault>{
    use std::io::Read;
    let meta=fs::symlink_metadata(path).map_err(|_|VaultFault::StorageUnavailable)?;
    if !meta.is_file()||!managed_plain(&meta)||meta.len()>max as u64{return Err(VaultFault::InvalidLocation);}
    let mut opts=OpenOptions::new();opts.read(true);
    #[cfg(windows)]
    {use std::os::windows::fs::OpenOptionsExt;opts.custom_flags(0x00200000);}
    let file=opts.open(path).map_err(|_|VaultFault::StorageUnavailable)?;
    let opened=file.metadata().map_err(|_|VaultFault::StorageUnavailable)?;
    if !opened.is_file()||!managed_plain(&opened)||opened.len()!=meta.len(){return Err(VaultFault::Corrupt);}
    let mut data=Vec::new();
    file.take(max as u64+1).read_to_end(&mut data).map_err(|_|VaultFault::StorageUnavailable)?;
    if data.len()>max||data.len() as u64!=meta.len(){return Err(VaultFault::Corrupt);}
    Ok(data)
}
fn write_portable_new(path:&Path,bytes:&[u8])->Result<(),VaultFault>{
    use std::io::Write;
    let mut opts=OpenOptions::new();opts.create_new(true).write(true);
    #[cfg(unix)]
    {use std::os::unix::fs::OpenOptionsExt;opts.mode(0o600);}
    let mut f=opts.open(path).map_err(|e|if e.kind()==std::io::ErrorKind::AlreadyExists{VaultFault::Conflict}else{VaultFault::StorageUnavailable})?;
    f.write_all(bytes).and_then(|_|f.sync_all()).map_err(|_|VaultFault::StorageUnavailable)?;
    drop(f);
    let data=zeroize::Zeroizing::new(read_portable_file(path,bytes.len())?);
    if data.as_slice()!=bytes{return Err(VaultFault::Corrupt);}
    Ok(())
}

impl NativeVault {
    pub(crate) fn open(app_root: &Path) -> Result<Self, VaultFault> {
        if !app_root.is_absolute() || app_root.file_name() != Some(std::ffi::OsStr::new("com.zynoa.desktop")) {
            return Err(VaultFault::InvalidLocation);
        }
        checked_directory(app_root)?;
        let data = checked_child(app_root, "data")?;
        let file = data.join("state.sqlite");
        let existed = reject_nonregular_file(&file)?;
        // SQLite can create these sidecars. Refuse pre-existing linked or
        // non-file occupants before opening a potentially user-owned vault.
        for suffix in ["-wal", "-shm", "-journal"] {
            reject_nonregular_file(&data.join(format!("state.sqlite{suffix}")))?;
        }
        let flags = OpenFlags::SQLITE_OPEN_READ_WRITE | OpenFlags::SQLITE_OPEN_CREATE;
        let mut conn = Connection::open_with_flags(&file, flags).map_err(map_sql)?;
        conn.busy_timeout(Duration::from_secs(2)).map_err(map_sql)?;
        if existed { validate_schema(&conn)?; }
        conn.execute_batch("PRAGMA journal_mode=WAL; PRAGMA synchronous=FULL; PRAGMA foreign_keys=ON;")
            .map_err(map_sql)?;
        // Serialize migration against other writers; inspect again inside the
        // lock so a concurrent opener cannot run the migration twice.
        let tx = conn.transaction_with_behavior(TransactionBehavior::Immediate).map_err(map_sql)?;
        match version(&tx)? {
            0 if !existed => {
                tx.execute_batch(LEGACY_SCHEMA).map_err(map_sql)?;
                apply_v2(&tx, 0, None)?;
                apply_v3(&tx, 0, None)?;
                apply_v4(&tx, 0, None)?;
            }
            LEGACY_VERSION => {
                validate_schema(&tx)?;
                let stamp = SystemTime::now().duration_since(UNIX_EPOCH)
                    .map_err(|_| VaultFault::StorageUnavailable)?.as_nanos();
                let backup_id = format!("pre_v2_{}_{stamp}", std::process::id());
                // The reserved writer lock holds the v1 committed state still.
                // A separate read-only connection snapshots that state, not the
                // transaction being migrated; never raw-copy a live WAL file.
                let source = Connection::open_with_flags(&file, OpenFlags::SQLITE_OPEN_READ_ONLY)
                    .map_err(map_sql)?;
                source.busy_timeout(Duration::from_secs(2)).map_err(map_sql)?;
                if validate_schema(&source)? != LEGACY_VERSION { return Err(VaultFault::Conflict); }
                snapshot_connection_new(app_root, &source, &backup_id)?;
                drop(source);
                apply_v2(&tx, LEGACY_VERSION, Some(&backup_id))?;
                apply_v3(&tx, LEGACY_VERSION, None)?;
                apply_v4(&tx, LEGACY_VERSION, None)?;
            }
            CHAT_SCHEMA_VERSION => {
                validate_schema(&tx)?;
                let stamp = SystemTime::now().duration_since(UNIX_EPOCH)
                    .map_err(|_| VaultFault::StorageUnavailable)?.as_nanos();
                let backup_id = format!("pre_v3_{}_{stamp}", std::process::id());
                let source = Connection::open_with_flags(&file, OpenFlags::SQLITE_OPEN_READ_ONLY)
                    .map_err(map_sql)?;
                source.busy_timeout(Duration::from_secs(2)).map_err(map_sql)?;
                if validate_schema(&source)? != CHAT_SCHEMA_VERSION { return Err(VaultFault::Conflict); }
                snapshot_connection_new(app_root, &source, &backup_id)?;
                drop(source);
                apply_v3(&tx, CHAT_SCHEMA_VERSION, Some(&backup_id))?;
                apply_v4(&tx, CHAT_SCHEMA_VERSION, None)?;
            }
            ARTIFACT_SCHEMA_VERSION => {
                validate_schema(&tx)?;
                let stamp = SystemTime::now().duration_since(UNIX_EPOCH)
                    .map_err(|_| VaultFault::StorageUnavailable)?.as_nanos();
                let backup_id = format!("pre_v4_{}_{stamp}", std::process::id());
                let source = Connection::open_with_flags(&file, OpenFlags::SQLITE_OPEN_READ_ONLY)
                    .map_err(map_sql)?;
                source.busy_timeout(Duration::from_secs(2)).map_err(map_sql)?;
                if validate_schema(&source)? != ARTIFACT_SCHEMA_VERSION { return Err(VaultFault::Conflict); }
                snapshot_connection_new(app_root, &source, &backup_id)?;
                drop(source);
                apply_v4(&tx, ARTIFACT_SCHEMA_VERSION, Some(&backup_id))?;
            }
            SCHEMA_VERSION => { validate_schema(&tx)?; }
            _ => return Err(VaultFault::UnsupportedSchema),
        }
        // Check constraints and version before committing the atomic DDL.
        if validate_schema(&tx)? != SCHEMA_VERSION { return Err(VaultFault::Corrupt); }
        tx.commit().map_err(map_sql)?;
        Ok(Self { app_root: app_root.to_path_buf(), conn, attachment_draft: AttachmentDraft::default(), discarded_uploads: std::collections::VecDeque::new(), pending_review: None })
    }

    /// Persist an exact native review decision, never a capability grant.
    /// A replay (even identical) conflicts; a future broker must separately
    /// verify provenance, target and expiry and atomically consume authority.
    pub(crate) fn record_tool_review(&mut self,
        expected: &crate::artifact_contracts::ToolReviewIdentity,
        actual: &crate::artifact_contracts::ToolReviewIdentity,
        choice: crate::artifact_contracts::ReviewChoice) -> Result<(), VaultFault>
    {
        use crate::artifact_contracts::{classify_tool_review, ReviewState};
        let decision = match classify_tool_review(expected, Some((actual, choice))) {
            ReviewState::ApprovedCandidate => "approve",
            ReviewState::Denied => "deny",
            _ => return Err(VaultFault::InvalidRecord),
        };
        let (conversation, turn, request, target, digest, tool) = expected.record_fields();
        let tx = self.conn.transaction_with_behavior(TransactionBehavior::Immediate).map_err(map_sql)?;
        tx.execute(
            "INSERT INTO tool_review_decisions(request_id,conversation_id,turn_id,target_id,target_sha256,tool,decision,recorded_at)
             VALUES(?1,?2,?3,?4,?5,?6,?7,unixepoch())",
            params![request,conversation,turn,target,digest,tool,decision],
        ).map_err(map_sql)?;
        tx.commit().map_err(map_sql)?;
        Ok(())
    }

    /// Historical decision readback only. Never use a stored approval to
    /// authorize execution: this method does not establish liveness or expiry.
    pub(crate) fn read_tool_review(&self,
        expected: &crate::artifact_contracts::ToolReviewIdentity)
        -> Result<Option<crate::artifact_contracts::ReviewChoice>, VaultFault>
    {
        use crate::artifact_contracts::{ToolReviewIdentity, ReviewChoice};
        let (conversation, _, request, _, _, _) = expected.record_fields();
        let row = self.conn.query_row(
            "SELECT conversation_id,turn_id,request_id,target_id,target_sha256,tool,decision,recorded_at
             FROM tool_review_decisions WHERE conversation_id=?1 AND request_id=?2",
            params![conversation,request], |r| Ok((
                r.get::<_,String>(0)?,r.get::<_,String>(1)?,r.get::<_,String>(2)?,
                r.get::<_,String>(3)?,r.get::<_,String>(4)?,r.get::<_,String>(5)?,
                r.get::<_,String>(6)?,r.get::<_,i64>(7)?
            )),
        ).optional().map_err(|_| VaultFault::Corrupt)?;
        let Some((conversation,turn,request,target,digest,tool,decision,recorded_at)) = row else {
            return Ok(None);
        };
        let actual = ToolReviewIdentity::new(&conversation,&turn,&request,&target,&digest,&tool)
            .ok_or(VaultFault::Corrupt)?;
        if recorded_at <= 0 { return Err(VaultFault::Corrupt); }
        let choice = match decision.as_str() {
            "approve" => ReviewChoice::Approve,
            "deny" => ReviewChoice::Deny,
            _ => return Err(VaultFault::Corrupt),
        };
        if &actual != expected { return Err(VaultFault::Conflict); }
        Ok(Some(choice))
    }

    /// Bind a native review candidate to a saved, verified attachment. The
    /// caller must separately establish the live turn and request provenance.
    /// Neither the original path nor the managed bytes leave this boundary.
    pub(crate) fn prepare_attachment_review(&self, conversation_id: &str, turn_id: &str,
        request_id: &str, message_id: &str, artifact_id: &str)
        -> Result<crate::artifact_contracts::ToolReviewIdentity, VaultFault>
    {
        use crate::artifact_contracts::ToolReviewIdentity;
        if !safe_id(turn_id) || !safe_id(request_id) || !safe_id(artifact_id) {
            return Err(VaultFault::InvalidRecord);
        }
        let item = self.list_message_attachments(conversation_id,message_id)?
            .into_iter().find(|item| item.id == artifact_id).ok_or(VaultFault::Conflict)?;
        self.read_managed_blob(&item.receipt)?;
        ToolReviewIdentity::new(conversation_id,turn_id,request_id,&item.id,
            &item.receipt.sha256,"local.read_attachment").ok_or(VaultFault::InvalidRecord)
    }

    /// Bind a write candidate to the exact deterministic text artifact output
    /// of a complete assistant message. No file or database write occurs here.
    pub(crate) fn prepare_text_artifact_review(&self, conversation_id: &str, turn_id: &str,
        request_id: &str, source_id: &str)
        -> Result<crate::artifact_contracts::ToolReviewIdentity, VaultFault>
    {
        use crate::artifact_contracts::{ToolReviewIdentity, attachment_receipt};
        if !safe_id(turn_id) || !safe_id(request_id) { return Err(VaultFault::InvalidRecord); }
        let source = self.get_chat_message(conversation_id,source_id)?.ok_or(VaultFault::Conflict)?;
        if source.role != "assistant" || source.status != "complete"
            || !valid_text(&source.content,MAX_CONTENT_BYTES) { return Err(VaultFault::InvalidRecord); }
        let (_,artifact_id) = text_artifact_ids(conversation_id,source_id);
        let receipt = attachment_receipt(TEXT_ARTIFACT_NAME,source.content.as_bytes())
            .ok_or(VaultFault::Corrupt)?;
        ToolReviewIdentity::new(conversation_id,turn_id,request_id,&artifact_id,
            &receipt.sha256,"local.write_artifact").ok_or(VaultFault::InvalidRecord)
    }

    /// A new explicit local review supersedes any unconsumed review. IDs
    /// correlate native session state; they are not bearer capabilities.
    pub(crate) fn begin_tool_review(&mut self, conversation_id: &str, source_id: &str,
        attachment_id: Option<&str>) -> Result<ReviewPreview,VaultFault>
    {
        use sha2::{Digest,Sha256};
        static NEXT: std::sync::atomic::AtomicU64 = std::sync::atomic::AtomicU64::new(0);
        let revision=self.get_conversation(conversation_id)?.ok_or(VaultFault::Conflict)?.revision;
        let now=SystemTime::now().duration_since(UNIX_EPOCH).map_err(|_|VaultFault::StorageUnavailable)?;
        let seq=NEXT.fetch_add(1,std::sync::atomic::Ordering::Relaxed);
        let request=format!("{:x}",Sha256::digest(format!("zynoa-review-v1:{}:{}:{seq}",std::process::id(),now.as_nanos()).as_bytes()));
        // A user-initiated operation has a native action ID, not a model turn.
        let identity=match attachment_id {
            Some(id)=>self.prepare_attachment_review(conversation_id,&request,&request,source_id,id)?,
            None=>self.prepare_text_artifact_review(conversation_id,&request,&request,source_id)?,
        };
        let (_,_,_,target,digest,tool)=identity.record_fields();
        let preview=ReviewPreview{conversation_id:conversation_id.to_owned(),request_id:request,
            source_id:source_id.to_owned(),target_id:target.to_owned(),target_sha256:digest.to_owned(),tool:tool.to_owned()};
        self.pending_review=Some(PendingToolReview{identity,source_id:source_id.to_owned(),
            attachment_id:attachment_id.map(str::to_owned),conversation_revision:revision,
            expires:std::time::Instant::now()+Duration::from_secs(120)});
        Ok(preview)
    }

    /// Consume the live request once, under the native vault lock. Durable
    /// approval is recorded before dispatch and cannot be used as a grant later.
    /// Failed execution never silently replays; start a fresh review explicitly.
    pub(crate) fn finish_tool_review(&mut self, conversation_id: &str, request_id: &str,
        choice: crate::artifact_contracts::ReviewChoice) -> Result<bool,VaultFault>
    {
        use crate::artifact_contracts::ReviewChoice;
        if !safe_id(conversation_id)||!safe_id(request_id) {return Err(VaultFault::InvalidRecord);}
        let pending=self.pending_review.as_ref().ok_or(VaultFault::Conflict)?;
        let (thread,_,request,_,_,_)=pending.identity.record_fields();
        if thread!=conversation_id||request!=request_id {return Err(VaultFault::Conflict);}
        let pending=self.pending_review.take().ok_or(VaultFault::Conflict)?;
        if std::time::Instant::now()>=pending.expires {return Err(VaultFault::Conflict);}
        if self.get_conversation(conversation_id)?.ok_or(VaultFault::Conflict)?.revision!=pending.conversation_revision {
            return Err(VaultFault::Conflict);
        }
        if choice==ReviewChoice::Deny {
            self.record_tool_review(&pending.identity,&pending.identity,choice)?;
            return Ok(false);
        }
        let (_,turn,request,_,_,_)=pending.identity.record_fields();
        let actual=match &pending.attachment_id {
            Some(id)=>self.prepare_attachment_review(conversation_id,turn,request,&pending.source_id,id)?,
            None=>self.prepare_text_artifact_review(conversation_id,turn,request,&pending.source_id)?,
        };
        self.record_tool_review(&pending.identity,&actual,choice)?;
        match &pending.attachment_id {
            Some(id)=>{
                // Verify the exact local blob after durable approval. No bytes
                // are exposed to the WebView, model or arbitrary destination.
                let verified=self.prepare_attachment_review(conversation_id,turn,request,&pending.source_id,id)?;
                if verified!=pending.identity {return Err(VaultFault::Conflict);}
            },
            None=>{self.create_text_artifact(conversation_id,&pending.source_id)?;},
        }
        Ok(true)
    }

    /// Historical decisions only, never a live capability or execution receipt.
    /// Exact thread and stable bounded cursor; validate each stored identity.
    pub(crate) fn list_tool_reviews(&self, conversation_id:&str, after:Option<&str>,limit:u32)
        -> Result<Vec<ReviewTrace>,VaultFault>
    {
        use crate::artifact_contracts::{ToolReviewIdentity,ReviewChoice};
        if !safe_id(conversation_id)||after.is_some_and(|id|!safe_id(id))||!(1..=51).contains(&limit) {
            return Err(VaultFault::InvalidRecord);
        }
        if self.get_conversation(conversation_id)?.is_none(){return Err(VaultFault::Conflict);}
        let mut stmt=self.conn.prepare("SELECT request_id,turn_id,target_id,target_sha256,tool,decision,recorded_at
            FROM tool_review_decisions WHERE conversation_id=?1 AND request_id>?2 ORDER BY request_id LIMIT ?3").map_err(map_sql)?;
        let rows=stmt.query_map(params![conversation_id,after.unwrap_or(""),limit],|r|Ok((
            r.get::<_,String>(0)?,r.get::<_,String>(1)?,r.get::<_,String>(2)?,r.get::<_,String>(3)?,
            r.get::<_,String>(4)?,r.get::<_,String>(5)?,r.get::<_,i64>(6)?
        ))).map_err(map_sql)?;
        let mut out=Vec::new();
        for row in rows {
            let (request,turn,target,digest,tool,decision,recorded_at)=row.map_err(|_|VaultFault::Corrupt)?;
            let identity=ToolReviewIdentity::new(conversation_id,&turn,&request,&target,&digest,&tool).ok_or(VaultFault::Corrupt)?;
            let expected=match decision.as_str(){"approve"=>ReviewChoice::Approve,"deny"=>ReviewChoice::Deny,_=>return Err(VaultFault::Corrupt)};
            if recorded_at<=0||self.read_tool_review(&identity)?!=Some(expected){return Err(VaultFault::Corrupt);}
            out.push(ReviewTrace{request_id:request,target_id:target,target_sha256:digest,tool,decision,recorded_at});
        }
        Ok(out)
    }

    /// Create a bounded encrypted full chat-vault archive. Snapshot in memory;
    /// no live WAL file copy and no new plaintext backup temp file.
    pub(crate) fn create_portable_backup(&self,backup_id:&str,passphrase:&[u8])->Result<PortableBackupReceipt,VaultFault>{
        use crate::backup_contracts::{self,PortableBuilder,MAX_PORTABLE_BYTES};
        use rusqlite::backup::{Backup,StepResult};
        use sha2::{Digest,Sha256};
        if !safe_id(backup_id)||!backup_contracts::valid_backup_passphrase(passphrase){return Err(VaultFault::InvalidRecord);}
        let pages:u64=self.conn.query_row("PRAGMA page_count",[],|r|r.get(0)).map_err(map_sql)?;
        let size:u64=self.conn.query_row("PRAGMA page_size",[],|r|r.get(0)).map_err(map_sql)?;
        if pages.checked_mul(size).filter(|n|*n<=MAX_PORTABLE_BYTES as u64).is_none(){return Err(VaultFault::InvalidRecord);}
        let mut snapshot=Connection::open_in_memory().map_err(map_sql)?;
        {
            let copy=Backup::new(&self.conn,&mut snapshot).map_err(map_sql)?;
            let mut done=false;
            for _ in 0..2048 {
                match copy.step(128).map_err(map_sql)?{
                    StepResult::Done=>{done=true;break;},
                    StepResult::More=>(),
                    StepResult::Busy|StepResult::Locked=>std::thread::sleep(Duration::from_millis(10)),
                    _=>return Err(VaultFault::StorageUnavailable),
                }
            }
            if !done{return Err(VaultFault::StorageUnavailable);}
        }
        snapshot.execute_batch("PRAGMA journal_mode=MEMORY; PRAGMA trusted_schema=OFF;").map_err(map_sql)?;
        validate_portable_db(&snapshot)?;
        let blobs=portable_blobs(&snapshot)?;
        let mut builder=PortableBuilder::new();
        let db=snapshot.serialize(MAIN_DB).map_err(map_sql)?;
        builder.add("database","state.sqlite",&db).map_err(portable_fault)?;
        drop(db);drop(snapshot);
        let mut items=1;
        for (hash,receipt) in blobs{
            let data=zeroize::Zeroizing::new(self.read_managed_blob(&receipt)?);
            builder.add("blob",&hash,&data).map_err(portable_fault)?;items+=1;
        }
        let exports=self.app_root.join("data").join("exports");
        match fs::symlink_metadata(&exports){
            Ok(_)=>{
                managed_directory(&exports)?;
                let mut files=Vec::new();
                for (index,entry) in fs::read_dir(&exports).map_err(|_|VaultFault::StorageUnavailable)?.enumerate(){
                    if index>=4096{return Err(VaultFault::InvalidRecord);}
                    let entry=entry.map_err(|_|VaultFault::StorageUnavailable)?;
                    let name=entry.file_name().into_string().map_err(|_|VaultFault::InvalidLocation)?;
                    if name.starts_with(".export-stage-"){continue;}
                    if !backup_contracts::valid_export_filename(&name){return Err(VaultFault::InvalidRecord);}
                    files.push((name,entry.path()));
                }
                files.sort_by(|a,b|a.0.cmp(&b.0));
                for (name,path) in files{
                    let data=zeroize::Zeroizing::new(read_portable_file(&path,32*1024*1024)?);
                    builder.add("export",&name,&data).map_err(portable_fault)?;items+=1;
                }
            },
            Err(e) if e.kind()==std::io::ErrorKind::NotFound=>(),
            Err(_)=>return Err(VaultFault::StorageUnavailable),
        }
        let created=SystemTime::now().duration_since(UNIX_EPOCH).map_err(|_|VaultFault::StorageUnavailable)?.as_secs();
        let plain=builder.finish(created).map_err(portable_fault)?;
        let archive=backup_contracts::seal_portable(plain,passphrase).map_err(portable_fault)?;
        let backups=managed_child(&self.app_root,"backups")?;
        let dir=managed_child(&backups,"portable")?;
        let filename=format!("{backup_id}.awbackup");
        let target=dir.join(&filename);
        let stage=dir.join(format!(".backup-stage-{backup_id}"));
        if fs::symlink_metadata(&target).is_ok(){return Err(VaultFault::Conflict);}
        write_portable_new(&stage,&archive)?;
        fs::hard_link(&stage,&target).map_err(|e|if e.kind()==std::io::ErrorKind::AlreadyExists{VaultFault::Conflict}else{VaultFault::StorageUnavailable})?;
        #[cfg(unix)]
        fs::File::open(&dir).and_then(|f|f.sync_all()).map_err(|_|VaultFault::StorageUnavailable)?;
        let _=fs::remove_file(&stage);
        Ok(PortableBackupReceipt{backup_id:backup_id.into(),relative_path:format!("backups/portable/{filename}"),
            bytes:archive.len() as u64,sha256:format!("{:x}",Sha256::digest(&archive)),item_count:items})
    }

    /// Authenticate and independently restore to a new private profile only.
    /// A verified marker is written last; no active profile pointer is changed.
    pub(crate) fn restore_portable_preview(&self,backup_id:&str,restore_id:&str,passphrase:&[u8])->Result<PortableRestoreReceipt,VaultFault>{
        use crate::backup_contracts::{self,MAX_PORTABLE_BYTES};
        if !safe_id(backup_id)||!safe_id(restore_id)||!backup_contracts::valid_backup_passphrase(passphrase){return Err(VaultFault::InvalidRecord);}
        let backups=self.app_root.join("backups");managed_directory(&backups)?;
        let dir=backups.join("portable");managed_directory(&dir)?;
        let archive=read_portable_file(&dir.join(format!("{backup_id}.awbackup")),MAX_PORTABLE_BYTES+60)?;
        let plain=backup_contracts::open_portable(&archive,passphrase).map_err(portable_fault)?;
        let items=backup_contracts::unpack_portable(&plain).map_err(portable_fault)?;
        let db_bytes=items.first().ok_or(VaultFault::Corrupt)?.1;
        // Validate SQLite in memory before any restore profile is created.
        let mut snapshot=Connection::open_in_memory().map_err(map_sql)?;
        snapshot.deserialize_read_exact(MAIN_DB,db_bytes,db_bytes.len(),true).map_err(|_|VaultFault::Corrupt)?;
        snapshot.execute_batch("PRAGMA trusted_schema=OFF; PRAGMA query_only=ON;").map_err(map_sql)?;
        validate_portable_db(&snapshot)?;
        let expected=portable_blobs(&snapshot)?;
        let present=items.iter().filter(|(i,_)|i.kind=="blob").collect::<Vec<_>>();
        if present.len()!=expected.len(){return Err(VaultFault::Corrupt);}
        for (item,data) in present{
            let receipt=expected.get(&item.id).ok_or(VaultFault::Corrupt)?;
            if !crate::artifact_contracts::verify_attachment(receipt,data){return Err(VaultFault::Corrupt);}
        }
        let count:u64=snapshot.query_row("SELECT count(*) FROM conversations",[],|r|r.get(0)).map_err(map_sql)?;
        drop(snapshot);
        let restored=managed_child(&backups,"restored")?;
        let stage=restored.join(restore_id);
        fs::create_dir(&stage).map_err(|e|if e.kind()==std::io::ErrorKind::AlreadyExists{VaultFault::Conflict}else{VaultFault::StorageUnavailable})?;
        managed_directory(&stage)?;
        let profile=managed_child(&stage,"com.zynoa.desktop")?;
        let data=managed_child(&profile,"data")?;
        for (item,bytes) in &items{
            let path=match item.kind.as_str(){
                "database"=>data.join("state.sqlite"),
                "blob"=>{
                    let artifacts=managed_child(&data,"artifacts")?;
                    let hashes=managed_child(&artifacts,"sha256")?;
                    managed_child(&hashes,&item.id[..2])?.join(&item.id)
                },
                "export"=>managed_child(&data,"exports")?.join(&item.id),
                _=>return Err(VaultFault::Corrupt),
            };
            write_portable_new(&path,bytes)?;
        }
        let verified=Connection::open_with_flags(data.join("state.sqlite"),OpenFlags::SQLITE_OPEN_READ_ONLY).map_err(map_sql)?;
        verified.execute_batch("PRAGMA trusted_schema=OFF; PRAGMA query_only=ON;").map_err(map_sql)?;
        validate_portable_db(&verified)?;
        if portable_blobs(&verified)?!=expected{return Err(VaultFault::Corrupt);}
        drop(verified);
        let receipt=PortableRestoreReceipt{backup_id:backup_id.into(),restore_id:restore_id.into(),
            relative_path:format!("backups/restored/{restore_id}/com.zynoa.desktop"),item_count:items.len(),
            conversation_count:count,active_profile_changed:false};
        let marker=serde_json::to_vec(&receipt).map_err(|_|VaultFault::Corrupt)?;
        write_portable_new(&stage.join("verified.json"),&marker)?;
        Ok(receipt)
    }

    /// Explicit plaintext export of one entire saved conversation. Never
    /// expose a renderer-chosen path, silently truncate, or overwrite a file.
    pub(crate) fn export_conversation(&self, conversation_id:&str, revision:i64, export_id:&str)
        -> Result<ConversationExportReceipt,VaultFault>
    {
        use sha2::{Digest,Sha256};
        use serde_json::json;
        use std::io::Write;
        const MAX_PACKAGE:usize=32*1024*1024;
        const MAX_MESSAGES:usize=4096;
        fn hex(bytes:&[u8])->String {
            const H:&[u8;16]=b"0123456789abcdef";
            let mut out=String::with_capacity(bytes.len()*2);
            for b in bytes {out.push(H[(b>>4) as usize] as char);out.push(H[(b&15) as usize] as char);}
            out
        }
        fn append(out:&mut Vec<u8>,bytes:&[u8])->Result<(),VaultFault>{
            if out.len().checked_add(bytes.len()).filter(|n|*n<=MAX_PACKAGE).is_none(){return Err(VaultFault::InvalidRecord);}
            out.extend_from_slice(bytes);Ok(())
        }
        if !safe_id(conversation_id)||!safe_id(export_id)||revision<=0{return Err(VaultFault::InvalidRecord);}
        // Read all pages and links in one database snapshot. The shared
        // native vault mutex prevents local-domain mutations during export.
        let tx=self.conn.unchecked_transaction().map_err(map_sql)?;
        let thread=self.get_conversation(conversation_id)?.ok_or(VaultFault::Conflict)?;
        if thread.revision!=revision{return Err(VaultFault::Conflict);}
        let mut bytes=Vec::new();
        append(&mut bytes,b"{\"schemaVersion\":1,\"kind\":\"zynoa-conversation-export\",\"conversation\":")?;
        append(&mut bytes,&serde_json::to_vec(&json!({"id":thread.id,"title":thread.title,
            "revision":thread.revision,"createdAt":thread.created_at,"updatedAt":thread.updated_at})).map_err(|_|VaultFault::Corrupt)?)?;
        append(&mut bytes,b",\"messages\":[")?;
        let mut after=0;let mut message_count=0usize;let mut attachment_count=0usize;
        loop {
            let page=self.list_chat_messages(conversation_id,after,64)?;
            if page.is_empty(){break;}
            for m in page {
                if message_count>=MAX_MESSAGES||m.ordinal<=after{return Err(VaultFault::InvalidRecord);}
                if !safe_id(&m.id)||m.parent_id.as_ref().is_some_and(|id|!safe_id(id))||
                    !matches!(m.role.as_str(),"user"|"assistant"|"system")||
                    !matches!(m.status.as_str(),"complete"|"cancelled"|"failed")||
                    m.content.len()>MAX_CONTENT_BYTES||m.content.contains('\0') {return Err(VaultFault::Corrupt);}
                if message_count>0{append(&mut bytes,b",")?;}
                let row=serde_json::to_vec(&json!({"id":m.id,"parentId":m.parent_id,"ordinal":m.ordinal,
                    "role":m.role,"content":m.content,"contentSha256":format!("{:x}",Sha256::digest(m.content.as_bytes())),
                    "status":m.status,"revision":m.revision,"createdAt":m.created_at})).map_err(|_|VaultFault::Corrupt)?;
                append(&mut bytes,&row[..row.len()-1])?;
                append(&mut bytes,b",\"attachments\":[")?;
                for (index,a) in self.list_message_attachments(conversation_id,&m.id)?.into_iter().enumerate(){
                    let encoded=a.receipt.bytes.checked_mul(2).ok_or(VaultFault::InvalidRecord)?;
                    if encoded>MAX_PACKAGE.saturating_sub(bytes.len()) as u64{return Err(VaultFault::InvalidRecord);}
                    let data=self.read_managed_blob(&a.receipt)?;
                    if index>0{append(&mut bytes,b",")?;}
                    let item=json!({"id":a.id,"name":a.receipt.name,"bytes":a.receipt.bytes,
                        "sha256":a.receipt.sha256,"dataHex":hex(&data)});
                    append(&mut bytes,&serde_json::to_vec(&item).map_err(|_|VaultFault::Corrupt)?)?;
                    attachment_count+=1;
                }
                append(&mut bytes,b"]}")?;
                after=m.ordinal;message_count+=1;
            }
        }
        append(&mut bytes,b"]}")?;
        tx.commit().map_err(map_sql)?;
        let hash=format!("{:x}",Sha256::digest(&bytes));
        let data=managed_child(&self.app_root,"data")?;
        let dir=managed_child(&data,"exports")?;
        let filename=format!("conversation-{export_id}.json");
        let target=dir.join(&filename);
        let stage=dir.join(format!(".export-stage-{export_id}"));
        if fs::symlink_metadata(&target).is_ok(){return Err(VaultFault::Conflict);}
        let mut options=OpenOptions::new();options.write(true).create_new(true);
        #[cfg(unix)]
        {use std::os::unix::fs::OpenOptionsExt;options.mode(0o600);}
        let mut file=options.open(&stage).map_err(|_|VaultFault::StorageUnavailable)?;
        file.write_all(&bytes).and_then(|_|file.sync_all()).map_err(|_|VaultFault::StorageUnavailable)?;
        drop(file);
        let meta=fs::symlink_metadata(&stage).map_err(|_|VaultFault::StorageUnavailable)?;
        if !meta.is_file()||!managed_plain(&meta)||meta.len()!=bytes.len() as u64{return Err(VaultFault::Corrupt);}
        let readback=fs::read(&stage).map_err(|_|VaultFault::StorageUnavailable)?;
        if readback!=bytes{return Err(VaultFault::Corrupt);}
        fs::hard_link(&stage,&target).map_err(|e|if e.kind()==std::io::ErrorKind::AlreadyExists{VaultFault::Conflict}else{VaultFault::StorageUnavailable})?;
        #[cfg(unix)]
        fs::File::open(&dir).and_then(|f|f.sync_all()).map_err(|_|VaultFault::StorageUnavailable)?;
        let _=fs::remove_file(&stage);
        Ok(ConversationExportReceipt{conversation_id:conversation_id.to_owned(),revision,export_id:export_id.to_owned(),
            relative_path:format!("data/exports/{filename}"),bytes:bytes.len() as u64,sha256:hash,message_count,attachment_count})
    }

    /// Accept only bytes already supplied to the local chat domain. The chunk
    /// offset and original metadata must match on retransmission. No disk write
    /// occurs until the user explicitly requests the message transaction.
    pub(crate) fn upload_attachment_chunk(&mut self, conversation_id: &str, message_id: &str,
        artifact_id: &str, name: &str, total: u64, offset: u64, chunk: &[u8])
        -> Result<Option<crate::artifact_contracts::AttachmentReceipt>, VaultFault>
    {
        if !safe_id(conversation_id) || !safe_id(message_id) || !safe_id(artifact_id)
            || !crate::artifact_contracts::valid_managed_basename(name)
            || total > crate::artifact_contracts::MAX_ATTACHMENT || chunk.len() > MAX_ATTACHMENT_CHUNK
            || (chunk.is_empty() && total != 0) || offset > total
            || offset.checked_add(chunk.len() as u64).map_or(true, |end| end > total) {
            return Err(VaultFault::InvalidRecord);
        }
        if self.get_conversation(conversation_id)?.is_none()
            || self.get_chat_message(conversation_id,message_id)?.is_some() {
            return Err(VaultFault::Conflict);
        }
        if self.discarded_uploads.iter().any(|(c,m)|c==conversation_id&&m==message_id) {
            return Err(VaultFault::Conflict);
        }
        let draft = &mut self.attachment_draft;
        if !draft.uploads.is_empty() && (draft.conversation_id != conversation_id || draft.message_id != message_id) {
            return Err(VaultFault::Conflict);
        }
        let index = match draft.uploads.iter().position(|a| a.id == artifact_id) {
            Some(i) => i,
            None => {
                if offset != 0 || draft.uploads.len() >= MAX_MESSAGE_ATTACHMENTS
                    || draft.uploads.iter().map(|a|a.total).sum::<u64>() + total > MAX_MESSAGE_ATTACHMENT_BYTES {
                    return Err(VaultFault::InvalidRecord);
                }
                draft.conversation_id = conversation_id.to_owned();
                draft.message_id = message_id.to_owned();
                draft.uploads.push(AttachmentUpload { id:artifact_id.to_owned(), name:name.to_owned(), total, data:Vec::new() });
                draft.uploads.len()-1
            }
        };
        let upload = &mut draft.uploads[index];
        if upload.name != name || upload.total != total { return Err(VaultFault::Conflict); }
        let start = offset as usize;
        let end = start + chunk.len();
        if start == upload.data.len() {
            upload.data.extend_from_slice(chunk);
        } else if end > upload.data.len() || upload.data.get(start..end) != Some(chunk) {
            return Err(VaultFault::Conflict);
        }
        // A replay returns the receipt only when this particular chunk ends the
        // file, not merely when a later chunk has already been acknowledged.
        if end as u64 == total {
            return Ok(Some(crate::artifact_contracts::attachment_receipt(name,&upload.data)
                .ok_or(VaultFault::InvalidRecord)?));
        }
        Ok(None)
    }

    pub(crate) fn discard_attachment_draft(&mut self, conversation_id: &str, message_id: &str)
        -> Result<(), VaultFault>
    {
        if !safe_id(conversation_id) || !safe_id(message_id) { return Err(VaultFault::InvalidRecord); }
        if !self.attachment_draft.uploads.is_empty()
            && (self.attachment_draft.conversation_id != conversation_id || self.attachment_draft.message_id != message_id) {
            return Err(VaultFault::Conflict);
        }
        // Bounded recent tombstones refuse delayed chunks after discard.
        if !self.discarded_uploads.iter().any(|(c,m)|c==conversation_id&&m==message_id) {
            if self.discarded_uploads.len() >= 64 { self.discarded_uploads.pop_front(); }
            self.discarded_uploads.push_back((conversation_id.to_owned(),message_id.to_owned()));
        }
        self.attachment_draft = AttachmentDraft::default();
        Ok(())
    }

    /// Resolve only this message's exact uploaded bytes, never a renderer-supplied
    /// hash reference to a different stored artifact. Failed writes retain draft.
    pub(crate) fn append_uploaded_message(&mut self, input: ChatMessageInput<'_>,
        expected: &[LinkedAttachment]) -> Result<ChatWriteReceipt, VaultFault>
    {
        let draft = &self.attachment_draft;
        let scoped = !draft.uploads.is_empty() && draft.conversation_id == input.conversation_id
            && draft.message_id == input.id;
        if expected.is_empty() {
            if scoped { return Err(VaultFault::Conflict); }
            return self.append_chat_message(input);
        }
        if !scoped || expected.len() != draft.uploads.len() || expected.len() > MAX_MESSAGE_ATTACHMENTS {
            return Err(VaultFault::Conflict);
        }
        let mut ids = std::collections::HashSet::new();
        for item in expected {
            if !ids.insert(item.id.as_str()) { return Err(VaultFault::InvalidRecord); }
            let upload = draft.uploads.iter().find(|a| a.id == item.id).ok_or(VaultFault::Conflict)?;
            if upload.data.len() as u64 != upload.total
                || !crate::artifact_contracts::verify_attachment(&item.receipt,&upload.data)
                || upload.name != item.receipt.name {
                return Err(VaultFault::Conflict);
            }
        }
        for item in expected {
            let upload = draft.uploads.iter().find(|a| a.id == item.id).ok_or(VaultFault::Conflict)?;
            let stored = self.stage_managed_blob(&upload.name,&upload.data)?;
            if stored != item.receipt { return Err(VaultFault::Corrupt); }
        }
        let result = self.append_chat_message_with_attachments(input,expected)?;
        self.attachment_draft = AttachmentDraft::default();
        Ok(result)
    }

    // P03-T08 storage primitive: native trusted bytes only. A blob receipt is not a
    // conversation save acknowledgement; metadata/links must still commit atomically.
    pub(crate) fn stage_managed_blob(&self, name: &str, bytes: &[u8])
        -> Result<crate::artifact_contracts::AttachmentReceipt, VaultFault>
    {
        use std::io::Write;
        use std::sync::atomic::{AtomicU64, Ordering};
        static NEXT_STAGE: AtomicU64 = AtomicU64::new(0);
        let receipt = crate::artifact_contracts::attachment_receipt(name, bytes)
            .ok_or(VaultFault::InvalidRecord)?;
        let dir = self.managed_blob_directory(&receipt.sha256, true)?;
        let target = dir.join(&receipt.sha256);
        match fs::symlink_metadata(&target) {
            Ok(_) => {
                read_verified_blob(&target, &receipt)?;
                return Ok(receipt);
            }
            Err(e) if e.kind() == std::io::ErrorKind::NotFound => (),
            Err(_) => return Err(VaultFault::StorageUnavailable),
        }
        let stamp = SystemTime::now().duration_since(UNIX_EPOCH)
            .map_err(|_| VaultFault::StorageUnavailable)?.as_nanos();
        let seq = NEXT_STAGE.fetch_add(1, Ordering::Relaxed);
        let temp = dir.join(format!(".stage-{}-{stamp}-{seq}", std::process::id()));
        let mut file = OpenOptions::new().write(true).create_new(true).open(&temp)
            .map_err(|_| VaultFault::StorageUnavailable)?;
        // Preserve an interrupted stage on error; do not delete a possible sole copy.
        file.write_all(bytes).and_then(|_| file.sync_all()).map_err(|_| VaultFault::StorageUnavailable)?;
        drop(file);
        read_verified_blob(&temp, &receipt)?;
        // Atomic no-replace publication on supported same-volume filesystems.
        // Never fall back to overwrite/rename if hard links are unavailable.
        match fs::hard_link(&temp, &target) {
            Ok(()) => (),
            Err(e) if e.kind() == std::io::ErrorKind::AlreadyExists => (),
            Err(_) => return Err(VaultFault::StorageUnavailable),
        }
        read_verified_blob(&target, &receipt)?;
        #[cfg(unix)]
        fs::File::open(&dir).and_then(|f| f.sync_all()).map_err(|_| VaultFault::StorageUnavailable)?;
        // The verified target exists. Stage cleanup is best effort; leftovers are
        // retained for later reconciliation, never treated as linked chat data.
        let _ = fs::remove_file(&temp);
        Ok(receipt)
    }

    fn managed_blob_directory(&self, hash: &str, create: bool) -> Result<PathBuf, VaultFault> {
        if !managed_hash_valid(hash) { return Err(VaultFault::InvalidRecord); }
        managed_directory(&self.app_root)?;
        let mut path = self.app_root.clone();
        for name in ["data", "artifacts", "sha256", &hash[..2]] {
            path = if create { managed_child(&path, name)? } else {
                let child = path.join(name);
                managed_directory(&child)?;
                child
            };
        }
        Ok(path)
    }

    pub(crate) fn read_managed_blob(&self, receipt: &crate::artifact_contracts::AttachmentReceipt)
        -> Result<Vec<u8>, VaultFault>
    {
        if !crate::artifact_contracts::valid_managed_basename(&receipt.name)
            || receipt.bytes > crate::artifact_contracts::MAX_ATTACHMENT {
            return Err(VaultFault::InvalidRecord);
        }
        let dir = self.managed_blob_directory(&receipt.sha256, false)?;
        read_verified_blob(&dir.join(&receipt.sha256), receipt)
    }

    /// Read-only, bounded candidate recovery inventory. A blob unreferenced in
    /// this snapshot may still be staged by another process or needed by a backup.
    /// Never remove, move, repair or expose a path on the basis of this result.
    pub(crate) fn inspect_managed_recovery(&mut self) -> Result<ManagedRecoveryInventory, VaultFault> {
        use std::collections::{HashMap, HashSet};
        use crate::artifact_contracts::AttachmentReceipt;
        managed_directory(&self.app_root)?;
        let mut report = ManagedRecoveryInventory::default();
        let mut referenced: HashMap<String,u64> = HashMap::new();
        let mut seen = HashSet::new();
        let mut entries = 0usize;
        let mut bytes_checked = 0u64;
        // Hold a stable DB view while inspecting managed storage. Staging
        // outside the transaction can still race this read-only observation.
        let tx = self.conn.transaction_with_behavior(TransactionBehavior::Deferred).map_err(map_sql)?;
        {
            let mut stmt = tx.prepare("SELECT a.sha256,a.bytes,a.name,l.artifact_id IS NOT NULL
                FROM managed_artifacts a LEFT JOIN artifact_links l ON l.artifact_id=a.id
                ORDER BY a.id LIMIT ?1").map_err(map_sql)?;
            let mut rows = stmt.query([(MAX_RECOVERY_ENTRIES+1) as i64]).map_err(map_sql)?;
            while let Some(row) = rows.next().map_err(map_sql)? {
                entries += 1;
                if entries > MAX_RECOVERY_ENTRIES { return Err(VaultFault::StorageUnavailable); }
                let hash: String = row.get(0).map_err(|_| VaultFault::Corrupt)?;
                let size = managed_length_from_sql(row.get(1).map_err(|_| VaultFault::Corrupt)?)?;
                let name: String = row.get(2).map_err(|_| VaultFault::Corrupt)?;
                let linked: bool = row.get(3).map_err(|_| VaultFault::Corrupt)?;
                if !managed_hash_valid(&hash) || !crate::artifact_contracts::valid_managed_basename(&name) {
                    return Err(VaultFault::Corrupt);
                }
                if let Some(previous) = referenced.insert(hash,size) {
                    if previous != size { return Err(VaultFault::Corrupt); }
                }
                if !linked { report.unlinked_metadata += 1; }
            }
        }
        report.referenced_hashes = referenced.len();
        let mut root = self.app_root.clone();
        for name in ["data","artifacts","sha256"] {
            root.push(name);
            match fs::symlink_metadata(&root) {
                Ok(meta) if meta.is_dir() && managed_plain(&meta) => (),
                Ok(_) => return Err(VaultFault::InvalidLocation),
                Err(e) if e.kind() == std::io::ErrorKind::NotFound => {
                    report.unavailable_referenced = referenced.len();
                    tx.commit().map_err(map_sql)?;
                    return Ok(report);
                }
                Err(_) => return Err(VaultFault::StorageUnavailable),
            }
        }
        for prefix in fs::read_dir(&root).map_err(|_| VaultFault::StorageUnavailable)? {
            entries += 1;
            if entries > MAX_RECOVERY_ENTRIES { return Err(VaultFault::StorageUnavailable); }
            let prefix = prefix.map_err(|_| VaultFault::StorageUnavailable)?;
            let prefix_name = prefix.file_name();
            let Some(prefix_name) = prefix_name.to_str() else { report.unexpected_entries += 1; continue; };
            let prefix_meta = fs::symlink_metadata(prefix.path()).map_err(|_| VaultFault::StorageUnavailable)?;
            if prefix_name.len()!=2 || !prefix_name.bytes().all(|b| b.is_ascii_digit() || (b'a'..=b'f').contains(&b))
                || !prefix_meta.is_dir() || !managed_plain(&prefix_meta) {
                report.unexpected_entries += 1;
                continue;
            }
            for item in fs::read_dir(prefix.path()).map_err(|_| VaultFault::StorageUnavailable)? {
                entries += 1;
                if entries > MAX_RECOVERY_ENTRIES { return Err(VaultFault::StorageUnavailable); }
                let item = item.map_err(|_| VaultFault::StorageUnavailable)?;
                let name = item.file_name();
                let Some(name) = name.to_str() else { report.unexpected_entries += 1; continue; };
                let meta = fs::symlink_metadata(item.path()).map_err(|_| VaultFault::StorageUnavailable)?;
                if !meta.is_file() || !managed_plain(&meta) {
                    report.unexpected_entries += 1;
                    continue;
                }
                if let Some(suffix) = name.strip_prefix(".stage-") {
                    let parts: Vec<_> = suffix.split('-').collect();
                    if parts.len()==3 && parts.iter().all(|part| !part.is_empty() && part.bytes().all(|b| b.is_ascii_digit())) {
                        report.interrupted_stages += 1;
                    } else { report.unexpected_entries += 1; }
                    continue;
                }
                if !managed_hash_valid(name) || &name[..2]!=prefix_name {
                    report.unexpected_entries += 1;
                    continue;
                }
                seen.insert(name.to_owned());
                let expected = referenced.get(name).copied();
                let size = expected.unwrap_or(meta.len());
                if meta.len()!=size || size>crate::artifact_contracts::MAX_ATTACHMENT {
                    report.damaged_or_unreadable += 1;
                    if expected.is_some() { report.unavailable_referenced += 1; }
                    continue;
                }
                bytes_checked = bytes_checked.checked_add(size).ok_or(VaultFault::StorageUnavailable)?;
                if bytes_checked > MAX_RECOVERY_BYTES { return Err(VaultFault::StorageUnavailable); }
                let receipt = AttachmentReceipt{name:"recovery.bin".into(),bytes:size,sha256:name.to_owned()};
                match read_verified_blob(&item.path(),&receipt) {
                    Ok(_) if expected.is_some() => report.verified_referenced += 1,
                    Ok(_) => report.verified_unreferenced += 1,
                    Err(_) => {
                        report.damaged_or_unreadable += 1;
                        if expected.is_some() { report.unavailable_referenced += 1; }
                    }
                }
            }
        }
        report.unavailable_referenced += referenced.keys().filter(|hash| !seen.contains(*hash)).count();
        tx.commit().map_err(map_sql)?;
        Ok(report)
    }

    /// New-only insert. A receipt is returned only AFTER transaction commit.
    /// Duplicate IDs fail, including retries: they cannot report a false save.
    pub(crate) fn insert_new(&mut self, id: &str, class: ContentClass, contents: &str)
        -> Result<i64, VaultFault>
    {
        if !safe_id(id) || contents.is_empty() || contents.len() > MAX_CONTENT_BYTES || contents.contains('\0') {
            return Err(VaultFault::InvalidRecord);
        }
        let tx = self.conn.transaction_with_behavior(TransactionBehavior::Immediate).map_err(map_sql)?;
        tx.execute("INSERT INTO records(id,class,payload,revision,created_at) VALUES(?1,?2,?3,1,unixepoch())",
                   params![id, class.name(), contents]).map_err(map_sql)?;
        tx.commit().map_err(map_sql)?;
        Ok(1)
    }

    pub(crate) fn read(&self, id: &str) -> Result<Option<String>, VaultFault> {
        if !safe_id(id) { return Err(VaultFault::InvalidRecord); }
        self.conn.query_row("SELECT payload FROM records WHERE id=?1", params![id], |r| r.get(0))
            .optional().map_err(map_sql)
    }

    /// Create a new conversation, including its journal event, atomically.
    pub(crate) fn create_conversation(&mut self, id: &str, title: &str)
        -> Result<ChatWriteReceipt, VaultFault>
    {
        if !safe_id(id) || !valid_text(title, MAX_TITLE_BYTES) { return Err(VaultFault::InvalidRecord); }
        let tx = self.conn.transaction_with_behavior(TransactionBehavior::Immediate).map_err(map_sql)?;
        tx.execute(
            "INSERT INTO conversations(id,title,revision,created_at,updated_at) VALUES(?1,?2,1,unixepoch(),unixepoch())",
            params![id,title]
        ).map_err(map_sql)?;
        tx.execute(
            "INSERT INTO chat_change_journal(entity_type,entity_id,revision,operation,persisted_at)
             VALUES('conversation',?1,1,'insert',unixepoch())", [id]
        ).map_err(map_sql)?;
        tx.commit().map_err(map_sql)?;
        Ok(ChatWriteReceipt { id:id.to_owned(), revision:1, conversation_revision:1, ordinal:None })
    }

    /// Persist a complete or explicitly terminal partial message. The return
    /// value acknowledges committed content, NOT successful model generation.
    pub(crate) fn append_chat_message(&mut self, input: ChatMessageInput<'_>)
        -> Result<ChatWriteReceipt, VaultFault>
    {
        self.append_chat_message_with_attachments(input, &[])
    }

    /// Commit message, attachment metadata, links and existing journal in one transaction.
    /// Native staged receipts only; this is not renderer authority or a file picker.
    pub(crate) fn append_chat_message_with_attachments(&mut self, input: ChatMessageInput<'_>,
        attachments: &[LinkedAttachment]) -> Result<ChatWriteReceipt, VaultFault>
    {
        if !safe_id(input.id) || !safe_id(input.conversation_id)
            || input.parent_id.is_some_and(|p| !safe_id(p) || p == input.id)
            || !valid_text(input.content, MAX_CONTENT_BYTES)
        { return Err(VaultFault::InvalidRecord); }
        if attachments.len() > MAX_MESSAGE_ATTACHMENTS { return Err(VaultFault::InvalidRecord); }
        let mut total = 0u64;
        let mut ids = std::collections::HashSet::new();
        for attachment in attachments {
            if !safe_id(&attachment.id) || !ids.insert(attachment.id.as_str()) {
                return Err(VaultFault::InvalidRecord);
            }
            total = total.checked_add(attachment.receipt.bytes).ok_or(VaultFault::InvalidRecord)?;
            if total > MAX_MESSAGE_ATTACHMENT_BYTES { return Err(VaultFault::InvalidRecord); }
            self.read_managed_blob(&attachment.receipt)?;
        }
        let tx = self.conn.transaction_with_behavior(TransactionBehavior::Immediate).map_err(map_sql)?;
        let ordinal: i64 = tx.query_row(
            "SELECT COALESCE(MAX(ordinal),0)+1 FROM messages WHERE conversation_id=?1",
            [input.conversation_id], |r| r.get(0)
        ).map_err(map_sql)?;
        tx.execute(
            "INSERT INTO messages(id,conversation_id,parent_id,ordinal,role,content,status,revision,created_at)
             VALUES(?1,?2,?3,?4,?5,?6,?7,1,unixepoch())",
            params![input.id,input.conversation_id,input.parent_id,ordinal,input.role.name(),input.content,input.status.name()]
        ).map_err(map_sql)?;
        for (position, attachment) in attachments.iter().enumerate() {
            tx.execute(
                "INSERT INTO managed_artifacts(id,conversation_id,name,sha256,bytes,created_at)
                 VALUES(?1,?2,?3,?4,?5,unixepoch())",
                params![attachment.id,input.conversation_id,attachment.receipt.name,
                    attachment.receipt.sha256,attachment.receipt.bytes as i64]
            ).map_err(map_sql)?;
            tx.execute(
                "INSERT INTO artifact_links(conversation_id,message_id,artifact_id,position)
                 VALUES(?1,?2,?3,?4)",
                params![input.conversation_id,input.id,attachment.id,position as i64]
            ).map_err(map_sql)?;
        }
        if tx.execute(
            "UPDATE conversations SET updated_at=unixepoch(),revision=revision+1 WHERE id=?1",
            [input.conversation_id]
        ).map_err(map_sql)? != 1 { return Err(VaultFault::Conflict); }
        let conversation_revision: i64 = tx.query_row(
            "SELECT revision FROM conversations WHERE id=?1",[input.conversation_id], |r| r.get(0)
        ).map_err(map_sql)?;
        tx.execute(
            "INSERT INTO chat_change_journal(entity_type,entity_id,revision,operation,persisted_at)
             VALUES('message',?1,1,'insert',unixepoch()),('conversation',?2,?3,'message_added',unixepoch())",
            params![input.id,input.conversation_id,conversation_revision]
        ).map_err(map_sql)?;
        tx.commit().map_err(map_sql)?;
        Ok(ChatWriteReceipt { id:input.id.to_owned(),revision:1,conversation_revision,ordinal:Some(ordinal) })
    }

    /// Materialize a complete assistant response exactly as UTF-8, with
    /// immutable provenance through the receipt message's parent and link.
    /// Native-only for now: no renderer path, name, bytes or role authority.
    pub(crate) fn create_text_artifact(&mut self, conversation_id: &str, source_id: &str)
        -> Result<TextArtifactReceipt, VaultFault>
    {
        let source = self.get_chat_message(conversation_id, source_id)?.ok_or(VaultFault::Conflict)?;
        if source.role != "assistant" || source.status != "complete"
            || !valid_text(&source.content, MAX_CONTENT_BYTES) {
            return Err(VaultFault::InvalidRecord);
        }
        let (message_id, artifact_id) = text_artifact_ids(conversation_id, source_id);
        let expected = crate::artifact_contracts::attachment_receipt(TEXT_ARTIFACT_NAME, source.content.as_bytes())
            .ok_or(VaultFault::InvalidRecord)?;
        if self.get_chat_message(conversation_id, &message_id)?.is_some() {
            // A replay must verify the original blob, not silently regenerate
            // a missing/corrupt acknowledged file.
            let stored = self.verify_text_artifact(conversation_id, source_id)?;
            return Ok(TextArtifactReceipt {message_id, source_id:source_id.to_owned(),
                attachment:stored, replayed:true});
        }
        let staged = self.stage_managed_blob(TEXT_ARTIFACT_NAME, source.content.as_bytes())?;
        if staged != expected { return Err(VaultFault::Corrupt); }
        let linked = LinkedAttachment {id:artifact_id.clone(), receipt:staged};
        let input = ChatMessageInput {id:&message_id, conversation_id, parent_id:Some(source_id),
            role:ChatRole::System, content:TEXT_ARTIFACT_NOTICE, status:ChatStatus::Complete};
        // Existing transaction commits provenance message, file metadata, link,
        // conversation revision and journal together. On error the staged
        // content may remain for non-destructive recovery.
        self.append_chat_message_with_attachments(input, std::slice::from_ref(&linked))?;
        Ok(TextArtifactReceipt {message_id, source_id:source_id.to_owned(),
            attachment:linked, replayed:false})
    }

    fn verify_text_artifact(&self, conversation_id: &str, source_id: &str)
        -> Result<LinkedAttachment, VaultFault>
    {
        let source = self.get_chat_message(conversation_id, source_id)?.ok_or(VaultFault::Conflict)?;
        if source.role != "assistant" || source.status != "complete"
            || !valid_text(&source.content, MAX_CONTENT_BYTES) {
            return Err(VaultFault::InvalidRecord);
        }
        let (message_id, artifact_id) = text_artifact_ids(conversation_id, source_id);
        let row = self.get_chat_message(conversation_id, &message_id)?.ok_or(VaultFault::Conflict)?;
        if row.role != "system" || row.status != "complete" || row.content != TEXT_ARTIFACT_NOTICE
            || row.parent_id.as_deref() != Some(source_id) {
            return Err(VaultFault::Conflict);
        }
        let mut items = self.list_message_attachments(conversation_id, &message_id)?;
        if items.len() != 1 { return Err(VaultFault::Corrupt); }
        let item = items.pop().ok_or(VaultFault::Corrupt)?;
        let expected = crate::artifact_contracts::attachment_receipt(TEXT_ARTIFACT_NAME, source.content.as_bytes())
            .ok_or(VaultFault::Corrupt)?;
        if item.id != artifact_id || item.receipt != expected { return Err(VaultFault::Corrupt); }
        if self.read_managed_blob(&item.receipt)?.as_slice() != source.content.as_bytes() {
            return Err(VaultFault::Corrupt);
        }
        Ok(item)
    }

    /// Scoped, verified text only. Never interpret markup or return a path.
    pub(crate) fn preview_text_artifact(&self, conversation_id: &str, source_id: &str)
        -> Result<String, VaultFault>
    {
        let item = self.verify_text_artifact(conversation_id, source_id)?;
        let bytes = self.read_managed_blob(&item.receipt)?;
        String::from_utf8(bytes).map_err(|_| VaultFault::Corrupt)
    }

    pub(crate) fn list_message_attachments(&self, conversation_id: &str, message_id: &str)
        -> Result<Vec<LinkedAttachment>, VaultFault>
    {
        if !safe_id(conversation_id) || !safe_id(message_id) { return Err(VaultFault::InvalidRecord); }
        if self.get_chat_message(conversation_id,message_id)?.is_none() { return Err(VaultFault::Conflict); }
        let mut stmt = self.conn.prepare(
            "SELECT a.id,a.name,a.sha256,a.bytes FROM artifact_links l
             JOIN managed_artifacts a ON a.conversation_id=l.conversation_id AND a.id=l.artifact_id
             WHERE l.conversation_id=?1 AND l.message_id=?2 ORDER BY l.position LIMIT 9"
        ).map_err(map_sql)?;
        let rows = stmt.query_map(params![conversation_id,message_id], |r| Ok((
            r.get::<_,String>(0)?,r.get::<_,String>(1)?,r.get::<_,String>(2)?,r.get::<_,i64>(3)?
        ))).map_err(map_sql)?;
        let mut result = Vec::new();
        let mut total = 0u64;
        for row in rows {
            let (id,name,sha256,bytes) = row.map_err(|_| VaultFault::Corrupt)?;
            let bytes = managed_length_from_sql(bytes)?;
            total = total.checked_add(bytes).ok_or(VaultFault::Corrupt)?;
            if total > MAX_MESSAGE_ATTACHMENT_BYTES { return Err(VaultFault::Corrupt); }
            let a = LinkedAttachment { id, receipt:crate::artifact_contracts::AttachmentReceipt {
                name,sha256,bytes,
            }};
            if !safe_id(&a.id) || !crate::artifact_contracts::valid_managed_basename(&a.receipt.name)
                || !managed_hash_valid(&a.receipt.sha256) || a.receipt.bytes > crate::artifact_contracts::MAX_ATTACHMENT {
                return Err(VaultFault::Corrupt);
            }
            result.push(a);
        }
        if result.len() > MAX_MESSAGE_ATTACHMENTS { return Err(VaultFault::Corrupt); }
        Ok(result)
    }

    fn conversation_row(row: &rusqlite::Row<'_>) -> rusqlite::Result<ConversationSummary> {
        Ok(ConversationSummary { id:row.get(0)?, title:row.get(1)?, revision:row.get(2)?,
            created_at:row.get(3)?, updated_at:row.get(4)? })
    }

    pub(crate) fn get_conversation(&self, id: &str) -> Result<Option<ConversationSummary>, VaultFault> {
        if !safe_id(id) { return Err(VaultFault::InvalidRecord); }
        self.conn.query_row("SELECT id,title,revision,created_at,updated_at FROM conversations WHERE id=?1",
            [id], Self::conversation_row).optional().map_err(map_sql)
    }

    /// Stable ID cursor, bounded metadata only. No message bodies in thread list.
    pub(crate) fn list_conversations(&self, after: Option<&str>, limit: u32)
        -> Result<Vec<ConversationSummary>, VaultFault>
    {
        if after.is_some_and(|id| !safe_id(id)) || !(1..=MAX_PAGE).contains(&limit) {
            return Err(VaultFault::InvalidRecord);
        }
        let mut stmt=self.conn.prepare("SELECT id,title,revision,created_at,updated_at FROM conversations
            WHERE id>?1 ORDER BY id LIMIT ?2").map_err(map_sql)?;
        let rows=stmt.query_map(params![after.unwrap_or(""),limit],Self::conversation_row).map_err(map_sql)?;
        let mut result=Vec::new();
        for row in rows { result.push(row.map_err(map_sql)?); }
        Ok(result)
    }

    /// Exact same-thread lookup for reconciliation after uncertain write outcomes.
    pub(crate) fn get_chat_message(&self, conversation_id: &str, id: &str)
        -> Result<Option<StoredChatMessage>, VaultFault>
    {
        if !safe_id(conversation_id)||!safe_id(id) { return Err(VaultFault::InvalidRecord); }
        self.conn.query_row("SELECT id,parent_id,ordinal,role,content,status,revision,created_at FROM messages
            WHERE conversation_id=?1 AND id=?2",params![conversation_id,id],|r| Ok(StoredChatMessage {
            id:r.get(0)?,parent_id:r.get(1)?,ordinal:r.get(2)?,role:r.get(3)?,content:r.get(4)?,
            status:r.get(5)?,revision:r.get(6)?,created_at:r.get(7)?,
        })).optional().map_err(map_sql)
    }

    /// Bounded stable ordinal pagination, scoped to a single conversation.
    pub(crate) fn list_chat_messages(&self, conversation_id: &str, after: i64, limit: u32)
        -> Result<Vec<StoredChatMessage>, VaultFault>
    {
        if !safe_id(conversation_id) || after < 0 || !(1..=MAX_PAGE).contains(&limit) {
            return Err(VaultFault::InvalidRecord);
        }
        let mut statement = self.conn.prepare(
            "SELECT id,parent_id,ordinal,role,content,status,revision,created_at FROM messages
             WHERE conversation_id=?1 AND ordinal>?2 ORDER BY ordinal LIMIT ?3"
        ).map_err(map_sql)?;
        let rows = statement.query_map(params![conversation_id,after,limit], |r| Ok(StoredChatMessage {
            id:r.get(0)?,parent_id:r.get(1)?,ordinal:r.get(2)?,role:r.get(3)?,
            content:r.get(4)?,status:r.get(5)?,revision:r.get(6)?,created_at:r.get(7)?,
        })).map_err(map_sql)?;
        let mut result = Vec::new();
        for row in rows { result.push(row.map_err(map_sql)?); }
        Ok(result)
    }

    /// Durable per-conversation inference choice stored in the existing
    /// versioned preference substrate. No runtime URL or credential is stored.
    pub(crate) fn set_inference_settings(&mut self, conversation_id: &str, model: &str,
        context_limit: u32) -> Result<InferenceSettings, VaultFault>
    {
        if !safe_id(conversation_id) || !valid_model(model) || !valid_context_limit(context_limit) {
            return Err(VaultFault::InvalidRecord);
        }
        let tx=self.conn.transaction_with_behavior(TransactionBehavior::Immediate).map_err(map_sql)?;
        let exists:i64=tx.query_row("SELECT count(*) FROM conversations WHERE id=?1",[conversation_id],|r|r.get(0)).map_err(map_sql)?;
        if exists!=1 {return Err(VaultFault::Conflict);}
        let current:Option<(String,i64)>=tx.query_row("SELECT class,revision FROM records WHERE id=?1",[conversation_id],|r|Ok((r.get(0)?,r.get(1)?))).optional().map_err(map_sql)?;
        let revision=match &current {None=>1,Some((class,n)) if class=="preference"=>*n+1,_=>return Err(VaultFault::Conflict)};
        let settings=InferenceSettings {model:model.to_owned(),context_limit,revision};
        let payload=serde_json::to_string(&settings).map_err(|_|VaultFault::InvalidRecord)?;
        if current.is_none() {
            tx.execute("INSERT INTO records(id,class,payload,revision,created_at) VALUES(?1,'preference',?2,1,unixepoch())",
                params![conversation_id,payload]).map_err(map_sql)?;
        } else {
            if tx.execute("UPDATE records SET payload=?2,revision=?3 WHERE id=?1 AND class='preference'",
                params![conversation_id,payload,revision]).map_err(map_sql)?!=1 {return Err(VaultFault::Conflict);}
        }
        tx.commit().map_err(map_sql)?;
        Ok(settings)
    }

    pub(crate) fn get_inference_settings(&self, conversation_id: &str)
        -> Result<Option<InferenceSettings>, VaultFault>
    {
        if !safe_id(conversation_id) {return Err(VaultFault::InvalidRecord);}
        let row:Option<(String,String,i64)>=self.conn.query_row(
            "SELECT class,payload,revision FROM records WHERE id=?1",[conversation_id],
            |r|Ok((r.get(0)?,r.get(1)?,r.get(2)?))).optional().map_err(map_sql)?;
        let Some((class,payload,revision))=row else{return Ok(None)};
        if class!="preference" {return Err(VaultFault::Conflict);}
        let settings:InferenceSettings=serde_json::from_str(&payload).map_err(|_|VaultFault::Corrupt)?;
        if settings.revision!=revision || !valid_model(&settings.model) || !valid_context_limit(settings.context_limit) {
            return Err(VaultFault::Corrupt);
        }
        Ok(Some(settings))
    }

    /// Assemble newest complete messages within a conservative token budget,
    /// then restore chronological order. Failed/cancelled output is excluded.
    pub(crate) fn model_context(&self, conversation_id:&str, context_limit:u32, reserve:u32)
        -> Result<ModelContext,VaultFault>
    {
        self.model_context_with_draft(conversation_id, context_limit, reserve, "")
    }

    pub(crate) fn estimate_message_tokens(content: &str) -> u32 {
        (content.len().min(u32::MAX as usize) as u32).saturating_add(16)
    }

    pub(crate) fn model_context_with_draft(&self, conversation_id:&str, context_limit:u32, reserve:u32, draft:&str)
        -> Result<ModelContext,VaultFault>
    {
        if !safe_id(conversation_id)||!valid_context_limit(context_limit)||reserve>=context_limit {
            return Err(VaultFault::InvalidRecord);
        }
        if self.get_conversation(conversation_id)?.is_none(){return Err(VaultFault::Conflict);}
        if draft.len()>MAX_CONTENT_BYTES || draft.contains('\0') {return Err(VaultFault::InvalidRecord);}
        let available=context_limit-reserve;
        let mut used=if draft.is_empty(){0}else{Self::estimate_message_tokens(draft)};
        if used>available{return Err(VaultFault::InvalidRecord);}
        let history_limit=MAX_CONTEXT_MESSAGES as u32-u32::from(!draft.is_empty());
        // Native artifact receipts are durable history, not model instructions.
        // Apply the same exclusion to both count and bounded assembly.
        let total:u32=self.conn.query_row("SELECT count(*) FROM messages WHERE conversation_id=?1 AND status='complete'
            AND NOT (role='system' AND content=?2 AND EXISTS (SELECT 1 FROM artifact_links l WHERE l.conversation_id=messages.conversation_id AND l.message_id=messages.id))",
            params![conversation_id,TEXT_ARTIFACT_NOTICE],|r|r.get(0)).map_err(map_sql)?;
        let mut stmt=self.conn.prepare("SELECT id,parent_id,ordinal,role,content,status,revision,created_at FROM messages
            WHERE conversation_id=?1 AND status='complete'
            AND NOT (role='system' AND content=?3 AND EXISTS (SELECT 1 FROM artifact_links l WHERE l.conversation_id=messages.conversation_id AND l.message_id=messages.id))
            ORDER BY ordinal DESC LIMIT ?2").map_err(map_sql)?;
        let rows=stmt.query_map(params![conversation_id,history_limit,TEXT_ARTIFACT_NOTICE],|r|Ok(StoredChatMessage{
            id:r.get(0)?,parent_id:r.get(1)?,ordinal:r.get(2)?,role:r.get(3)?,content:r.get(4)?,
            status:r.get(5)?,revision:r.get(6)?,created_at:r.get(7)?,})).map_err(map_sql)?;
        let mut selected=Vec::new();
        for row in rows {let row=row.map_err(map_sql)?;
            let estimate=Self::estimate_message_tokens(&row.content);
            if estimate>available && selected.is_empty() && draft.is_empty(){return Err(VaultFault::InvalidRecord);}
            if used.saturating_add(estimate)>available {break;}
            used+=estimate;selected.push(row);
        }
        selected.reverse();
        Ok(ModelContext{omitted_messages:total.saturating_sub(selected.len() as u32),messages:selected,
            estimated_tokens:used.saturating_add(reserve),limit:context_limit})
    }

    /// SQLite Online Backup API; never raw-copy a live WAL database or overwrite
    /// an existing backup. Snapshot stays private and unencrypted until M23 export.
    pub(crate) fn snapshot_new(&self, snapshot_id: &str) -> Result<PathBuf, VaultFault> {
        snapshot_connection_new(&self.app_root, &self.conn, snapshot_id)
    }

    /// Restore drill into a NEW disposable path only; never alter the active DB.
    pub(crate) fn restore_to_new_test_profile(
        snapshot: &Path, destination: &Path,
    ) -> Result<(), VaultFault> {
        if !snapshot.is_absolute() || !destination.is_absolute() || !reject_nonregular_file(snapshot)?
            || reject_nonregular_file(destination)?
        { return Err(VaultFault::InvalidLocation); }
        checked_directory(destination.parent().ok_or(VaultFault::InvalidLocation)?)?;
        let source = Connection::open_with_flags(snapshot, OpenFlags::SQLITE_OPEN_READ_ONLY).map_err(map_sql)?;
        let source_version = validate_schema(&source)?;
        drop(source);
        // Reserve a NEW preview inode; an existing file is NEVER overwritten.
        let reserved = OpenOptions::new().write(true).create_new(true)
            .open(destination).map_err(|_| VaultFault::Conflict)?;
        drop(reserved);
        let mut restored = Connection::open_with_flags(
            destination, OpenFlags::SQLITE_OPEN_READ_WRITE | OpenFlags::SQLITE_OPEN_CREATE,
        ).map_err(map_sql)?;
        restored.restore(MAIN_DB, snapshot, None::<fn(rusqlite::backup::Progress)>)
            .map_err(map_sql)?;
        if validate_schema(&restored)? != source_version { return Err(VaultFault::Corrupt); }
        Ok(())
    }
}

#[cfg(test)]
mod tests {
    use super::*;
    static NEXT_FIXTURE_ID: std::sync::atomic::AtomicU64 = std::sync::atomic::AtomicU64::new(0);
    struct Fixture(PathBuf);
    impl Fixture {
        fn new() -> Self {
            let n = SystemTime::now().duration_since(UNIX_EPOCH).unwrap().as_nanos();
            let seq = NEXT_FIXTURE_ID.fetch_add(1, std::sync::atomic::Ordering::Relaxed);
            let root = std::env::temp_dir().join(format!("zynoa-vault-test-{}-{n}-{seq}", std::process::id()));
            fs::create_dir(&root).unwrap();
            Self(root)
        }
        fn app(&self) -> PathBuf {
            let p = self.0.join("com.zynoa.desktop");
            fs::create_dir_all(&p).unwrap();
            p
        }
    }
    impl Drop for Fixture { fn drop(&mut self) { let _ = fs::remove_dir_all(&self.0); } }

    #[test]
    fn tool_review_v3_migration_preserves_chat_and_snapshot() {
        let f=Fixture::new();
        let app=f.app();
        let path=checked_child(&app,"data").unwrap().join("state.sqlite");
        let db=Connection::open(&path).unwrap();
        db.execute_batch(LEGACY_SCHEMA).unwrap();
        apply_v2(&db,0,None).unwrap();
        apply_v3(&db,0,None).unwrap();
        db.execute_batch("INSERT INTO conversations VALUES('thread_alpha','Synthetic',1,1,1);
            INSERT INTO messages VALUES('message_0001','thread_alpha',NULL,1,'user','previous chat','complete',1,1);").unwrap();
        drop(db);
        let v=NativeVault::open(&app).unwrap();
        assert_eq!(version(&v.conn).unwrap(),4);
        assert_eq!(v.get_chat_message("thread_alpha","message_0001").unwrap().unwrap().content,"previous chat");
        let id:String=v.conn.query_row("SELECT backup_id FROM tool_review_schema_migrations WHERE from_version=3",[],|r|r.get(0)).unwrap();
        let old=Connection::open_with_flags(app.join("backups").join("snapshots").join(format!("{id}.sqlite")),OpenFlags::SQLITE_OPEN_READ_ONLY).unwrap();
        assert_eq!(validate_schema(&old).unwrap(),3);
        assert_eq!(count(&old,"SELECT count(*) FROM messages WHERE content='previous chat'"),1);
        assert_eq!(count(&old,"SELECT count(*) FROM sqlite_schema WHERE name='tool_review_decisions'"),0);
    }

    #[test]
    fn tool_review_v3_migration_requires_backup() {
        let f=Fixture::new();
        let app=f.app();
        let path=checked_child(&app,"data").unwrap().join("state.sqlite");
        let db=Connection::open(&path).unwrap();
        db.execute_batch(LEGACY_SCHEMA).unwrap();
        apply_v2(&db,0,None).unwrap();
        apply_v3(&db,0,None).unwrap();
        drop(db);
        fs::write(app.join("backups"),b"occupied").unwrap();
        assert!(NativeVault::open(&app).is_err());
        let db=Connection::open_with_flags(path,OpenFlags::SQLITE_OPEN_READ_ONLY).unwrap();
        assert_eq!(validate_schema(&db).unwrap(),3);
        assert_eq!(count(&db,"SELECT count(*) FROM sqlite_schema WHERE name='tool_review_decisions'"),0);
        assert_eq!(fs::read(app.join("backups")).unwrap(),b"occupied");
    }

    #[test]
    fn portable_backup_restores_independent_vault_and_refuses_wrong_key_or_overwrite() {
        let f=Fixture::new();let app=f.app();let mut v=NativeVault::open(&app).unwrap();
        v.create_conversation("thread_alpha","Private chat").unwrap();
        let a=LinkedAttachment{id:"artifact_001".into(),receipt:v.stage_managed_blob("note.txt",b"private attachment bytes").unwrap()};
        let hash=a.receipt.sha256.clone();
        v.append_chat_message_with_attachments(sample_message("message_0001","thread_alpha",None),&[a]).unwrap();
        let revision=v.get_conversation("thread_alpha").unwrap().unwrap().revision;
        let exported=v.export_conversation("thread_alpha",revision,"export_001").unwrap();
        let pass=b"synthetic portable passphrase";
        let receipt=v.create_portable_backup("backup_001",pass).unwrap();
        assert_eq!(receipt.item_count,3);
        let path=app.join(&receipt.relative_path);
        let cipher=fs::read(&path).unwrap();
        assert!(!cipher.windows(24).any(|x|x==b"private attachment bytes"));
        assert!(v.restore_portable_preview("backup_001","wrong_001",b"incorrect passphrase").is_err());
        assert!(!app.join("backups/restored/wrong_001").exists());
        let restored=v.restore_portable_preview("backup_001","restore_001",pass).unwrap();
        assert!(!restored.active_profile_changed);assert_eq!(restored.conversation_count,1);
        let profile=app.join(&restored.relative_path);
        let other=NativeVault::open(&profile).unwrap();
        assert_eq!(other.get_chat_message("thread_alpha","message_0001").unwrap().unwrap().content,"synthetic message");
        let items=other.list_message_attachments("thread_alpha","message_0001").unwrap();
        assert_eq!(items[0].receipt.sha256,hash);
        assert_eq!(other.read_managed_blob(&items[0].receipt).unwrap(),b"private attachment bytes");
        assert_eq!(fs::read(profile.join(&exported.relative_path)).unwrap(),fs::read(app.join(&exported.relative_path)).unwrap());
        assert!(v.restore_portable_preview("backup_001","restore_001",pass).is_err());
        assert_eq!(fs::read(path).unwrap(),cipher);
        assert_eq!(v.get_conversation("thread_alpha").unwrap().unwrap().revision,revision);
    }

    #[test]
    fn conversation_export_is_complete_scoped_verified_and_new_only() {
        let f=Fixture::new();let app=f.app();let mut v=NativeVault::open(&app).unwrap();
        v.create_conversation("thread_alpha","One").unwrap();
        v.create_conversation("thread_bravo","Other private thread").unwrap();
        let a=LinkedAttachment{id:"artifact_001".into(),receipt:v.stage_managed_blob("note.txt",b"contents").unwrap()};
        let hash=a.receipt.sha256.clone();
        v.append_chat_message_with_attachments(sample_message("message_0001","thread_alpha",None),&[a]).unwrap();
        v.append_chat_message(ChatMessageInput{id:"assistant_001",conversation_id:"thread_alpha",
            parent_id:Some("message_0001"),role:ChatRole::Assistant,content:"Partial text",status:ChatStatus::Cancelled}).unwrap();
        v.append_chat_message(sample_message("message_0002","thread_bravo",None)).unwrap();
        let rev=v.get_conversation("thread_alpha").unwrap().unwrap().revision;
        assert!(v.export_conversation("thread_alpha",rev-1,"export_001").is_err());
        assert!(v.export_conversation("thread_alpha",rev,"../escape").is_err());
        let receipt=v.export_conversation("thread_alpha",rev,"export_001").unwrap();
        assert_eq!((receipt.message_count,receipt.attachment_count),(2,1));
        let path=app.join(&receipt.relative_path);
        let data=fs::read(&path).unwrap();
        use sha2::{Digest,Sha256};
        assert_eq!(receipt.sha256,format!("{:x}",Sha256::digest(&data)));
        let doc:serde_json::Value=serde_json::from_slice(&data).unwrap();
        assert_eq!(doc["conversation"]["id"],"thread_alpha");
        assert_eq!(doc["messages"][0]["ordinal"],1);
        assert_eq!(doc["messages"][1]["status"],"cancelled");
        assert_eq!(doc["messages"][1]["parentId"],"message_0001");
        assert_eq!(doc["messages"][0]["attachments"][0]["dataHex"],"636f6e74656e7473");
        assert_eq!(doc["messages"][0]["attachments"][0]["sha256"],hash);
        assert!(!String::from_utf8_lossy(&data).contains("thread_bravo"));
        assert!(v.export_conversation("thread_alpha",rev,"export_001").is_err());
        assert_eq!(fs::read(&path).unwrap(),data);
        drop(v);let v=NativeVault::open(&app).unwrap();
        assert_eq!(fs::read(&path).unwrap(),data);
        let blob=v.managed_blob_directory(&hash,false).unwrap().join(&hash);
        fs::write(blob,b"changed!").unwrap();
        assert!(v.export_conversation("thread_alpha",rev,"export_002").is_err());
        assert!(!app.join("data/exports/conversation-export_002.json").exists());
    }

    #[test]
    fn live_tool_review_consumes_once_and_keeps_historical_decisions() {
        use crate::artifact_contracts::ReviewChoice;
        let f=Fixture::new();let app=f.app();let mut v=NativeVault::open(&app).unwrap();
        v.create_conversation("thread_alpha","One").unwrap();
        v.create_conversation("thread_bravo","Two").unwrap();
        let a=LinkedAttachment{id:"artifact_001".into(),receipt:v.stage_managed_blob("note.txt",b"contents").unwrap()};
        v.append_chat_message_with_attachments(sample_message("message_0001","thread_alpha",None),&[a]).unwrap();
        v.append_chat_message(ChatMessageInput{id:"assistant_001",conversation_id:"thread_alpha",
            parent_id:Some("message_0001"),role:ChatRole::Assistant,content:"Synthetic answer",status:ChatStatus::Complete}).unwrap();
        let pending=v.begin_tool_review("thread_alpha","assistant_001",None).unwrap();
        assert!(v.finish_tool_review("thread_bravo",&pending.request_id,ReviewChoice::Approve).is_err());
        assert!(!v.finish_tool_review("thread_alpha",&pending.request_id,ReviewChoice::Deny).unwrap());
        assert!(v.finish_tool_review("thread_alpha",&pending.request_id,ReviewChoice::Approve).is_err());
        assert_eq!(count(&v.conn,"SELECT count(*) FROM managed_artifacts"),1);
        let pending=v.begin_tool_review("thread_alpha","message_0001",Some("artifact_001")).unwrap();
        assert!(v.finish_tool_review("thread_alpha",&pending.request_id,ReviewChoice::Approve).unwrap());
        assert!(v.finish_tool_review("thread_alpha",&pending.request_id,ReviewChoice::Approve).is_err());
        let pending=v.begin_tool_review("thread_alpha","assistant_001",None).unwrap();
        assert!(v.finish_tool_review("thread_alpha",&pending.request_id,ReviewChoice::Approve).unwrap());
        assert_eq!(count(&v.conn,"SELECT count(*) FROM managed_artifacts"),2);
        assert_eq!(v.preview_text_artifact("thread_alpha","assistant_001").unwrap(),"Synthetic answer");
        let expired=v.begin_tool_review("thread_alpha","assistant_001",None).unwrap();
        v.pending_review.as_mut().unwrap().expires=std::time::Instant::now();
        assert!(v.finish_tool_review("thread_alpha",&expired.request_id,ReviewChoice::Approve).is_err());
        let stale=v.begin_tool_review("thread_alpha","assistant_001",None).unwrap();
        v.append_chat_message(sample_message("message_0002","thread_alpha",None)).unwrap();
        assert!(v.finish_tool_review("thread_alpha",&stale.request_id,ReviewChoice::Approve).is_err());
        let lost=v.begin_tool_review("thread_alpha","assistant_001",None).unwrap();
        drop(v);let mut v=NativeVault::open(&app).unwrap();
        assert!(v.finish_tool_review("thread_alpha",&lost.request_id,ReviewChoice::Approve).is_err());
        let trace=v.list_tool_reviews("thread_alpha",None,50).unwrap();
        assert_eq!(trace.len(),3);
        assert_eq!(trace.iter().filter(|t|t.decision=="approve").count(),2);
        assert_eq!(trace.iter().filter(|t|t.decision=="deny").count(),1);
        assert!(v.list_tool_reviews("thread_bravo",None,50).unwrap().is_empty());
        assert_eq!(v.list_tool_reviews("thread_alpha",Some(&trace[0].request_id),50).unwrap().len(),2);
    }

    #[test]
    fn tool_review_readback_is_exact_scoped_and_fails_closed() {
        use crate::artifact_contracts::{ToolReviewIdentity,ReviewChoice};
        let f=Fixture::new();
        let app=f.app();
        let mut v=NativeVault::open(&app).unwrap();
        v.create_conversation("thread_alpha","One").unwrap();
        v.create_conversation("thread_bravo","Two").unwrap();
        let digest="a".repeat(64);
        let identity=|conversation,turn,request,target,hash,tool|
            ToolReviewIdentity::new(conversation,turn,request,target,hash,tool).unwrap();
        let a=identity("thread_alpha","turn_001","request_001","target_001",&digest,"local.read_attachment");
        let b=identity("thread_alpha","turn_001","request_002","target_001",&digest,"local.read_attachment");
        assert_eq!(v.read_tool_review(&a).unwrap(),None);
        v.record_tool_review(&a,&a,ReviewChoice::Approve).unwrap();
        v.record_tool_review(&b,&b,ReviewChoice::Deny).unwrap();
        drop(v);
        let v=NativeVault::open(&app).unwrap();
        assert_eq!(v.read_tool_review(&a).unwrap(),Some(ReviewChoice::Approve));
        assert_eq!(v.read_tool_review(&b).unwrap(),Some(ReviewChoice::Deny));
        let other=identity("thread_bravo","turn_001","request_001","target_001",&digest,"local.read_attachment");
        assert_eq!(v.read_tool_review(&other).unwrap(),None);
        let missing=identity("thread_alpha","turn_001","request_999","target_001",&digest,"local.read_attachment");
        assert_eq!(v.read_tool_review(&missing).unwrap(),None);
        for mismatch in [
            identity("thread_alpha","turn_002","request_001","target_001",&digest,"local.read_attachment"),
            identity("thread_alpha","turn_001","request_001","target_002",&digest,"local.read_attachment"),
            identity("thread_alpha","turn_001","request_001","target_001",&"b".repeat(64),"local.read_attachment"),
            identity("thread_alpha","turn_001","request_001","target_001",&digest,"local.write_artifact"),
        ] {
            assert_eq!(v.read_tool_review(&mismatch),Err(VaultFault::Conflict));
        }
        // Synthetic corruption only; production never disables constraints.
        v.conn.execute_batch("DROP TRIGGER tool_review_no_update;
            PRAGMA ignore_check_constraints=ON;
            UPDATE tool_review_decisions SET decision='unknown' WHERE request_id='request_001';
            PRAGMA ignore_check_constraints=OFF;").unwrap();
        assert_eq!(v.read_tool_review(&a),Err(VaultFault::Corrupt));
        assert_eq!(count(&v.conn,"SELECT count(*) FROM tool_review_decisions"),2);
    }

    #[test]
    fn tool_review_targets_are_derived_from_verified_saved_content() {
        let f=Fixture::new();
        let app=f.app();
        let mut v=NativeVault::open(&app).unwrap();
        v.create_conversation("thread_alpha","One").unwrap();
        v.create_conversation("thread_bravo","Two").unwrap();
        let a=LinkedAttachment{id:"artifact_001".into(),receipt:v.stage_managed_blob("note.txt",b"contents").unwrap()};
        let digest=a.receipt.sha256.clone();
        v.append_chat_message_with_attachments(sample_message("message_0001","thread_alpha",None),&[a]).unwrap();
        let read=v.prepare_attachment_review("thread_alpha","turn_001","request_001","message_0001","artifact_001").unwrap();
        assert_eq!(read.record_fields(),("thread_alpha","turn_001","request_001","artifact_001",digest.as_str(),"local.read_attachment"));
        assert!(v.prepare_attachment_review("thread_bravo","turn_001","request_001","message_0001","artifact_001").is_err());
        assert!(v.prepare_attachment_review("thread_alpha","turn_001","request_001","message_0001","artifact_002").is_err());
        assert!(v.prepare_attachment_review("thread_alpha","turn_001","../bad","message_0001","artifact_001").is_err());
        let blob=v.managed_blob_directory(&digest,false).unwrap().join(&digest);
        fs::write(&blob,b"changed!").unwrap();
        assert!(v.prepare_attachment_review("thread_alpha","turn_001","request_001","message_0001","artifact_001").is_err());
        fs::remove_file(&blob).unwrap();
        assert!(v.prepare_attachment_review("thread_alpha","turn_001","request_001","message_0001","artifact_001").is_err());
        let text="Synthetic assistant response";
        v.append_chat_message(ChatMessageInput{id:"assistant_001",conversation_id:"thread_alpha",
            parent_id:Some("message_0001"),role:ChatRole::Assistant,content:text,status:ChatStatus::Complete}).unwrap();
        v.append_chat_message(ChatMessageInput{id:"assistant_002",conversation_id:"thread_alpha",
            parent_id:Some("message_0001"),role:ChatRole::Assistant,content:"partial",status:ChatStatus::Cancelled}).unwrap();
        let write=v.prepare_text_artifact_review("thread_alpha","turn_001","request_002","assistant_001").unwrap();
        let (_,target)=text_artifact_ids("thread_alpha","assistant_001");
        let receipt=crate::artifact_contracts::attachment_receipt(TEXT_ARTIFACT_NAME,text.as_bytes()).unwrap();
        assert_eq!(write.record_fields(),("thread_alpha","turn_001","request_002",target.as_str(),receipt.sha256.as_str(),"local.write_artifact"));
        for source in ["message_0001","assistant_002","assistant_999"] {
            assert!(v.prepare_text_artifact_review("thread_alpha","turn_001","request_002",source).is_err());
        }
        assert!(v.prepare_text_artifact_review("thread_bravo","turn_001","request_002","assistant_001").is_err());
        assert_eq!(count(&v.conn,"SELECT count(*) FROM tool_review_decisions"),0);
        assert_eq!(count(&v.conn,"SELECT count(*) FROM managed_artifacts"),1);
        assert_eq!(count(&v.conn,"SELECT count(*) FROM messages"),3);
    }

    #[test]
    fn tool_review_decisions_are_exact_immutable_and_durable() {
        use crate::artifact_contracts::{ToolReviewIdentity,ReviewChoice};
        let f=Fixture::new();
        let app=f.app();
        let mut v=NativeVault::open(&app).unwrap();
        v.create_conversation("thread_alpha","One").unwrap();
        v.create_conversation("thread_bravo","Two").unwrap();
        let digest="a".repeat(64);
        let identity=|conversation,request| ToolReviewIdentity::new(conversation,"turn_001",request,
            "target_001",&digest,"local.read_attachment").unwrap();
        let a=identity("thread_alpha","request_001");
        let other=identity("thread_bravo","request_001");
        let missing=identity("thread_missing","request_003");
        assert!(v.record_tool_review(&a,&other,ReviewChoice::Approve).is_err());
        assert!(v.record_tool_review(&missing,&missing,ReviewChoice::Approve).is_err());
        assert_eq!(count(&v.conn,"SELECT count(*) FROM tool_review_decisions"),0);
        v.record_tool_review(&a,&a,ReviewChoice::Approve).unwrap();
        assert!(v.record_tool_review(&a,&a,ReviewChoice::Approve).is_err());
        assert!(v.record_tool_review(&a,&a,ReviewChoice::Deny).is_err());
        assert!(v.record_tool_review(&other,&other,ReviewChoice::Approve).is_err());
        let b=identity("thread_alpha","request_002");
        v.record_tool_review(&b,&b,ReviewChoice::Deny).unwrap();
        assert!(v.conn.execute("UPDATE tool_review_decisions SET decision='deny' WHERE request_id='request_001'",[]).is_err());
        assert!(v.conn.execute("DELETE FROM tool_review_decisions WHERE request_id='request_001'",[]).is_err());
        assert!(v.conn.execute("INSERT OR REPLACE INTO tool_review_decisions SELECT request_id,conversation_id,turn_id,target_id,target_sha256,tool,'deny',recorded_at FROM tool_review_decisions WHERE request_id='request_001'",[]).is_err());
        drop(v);
        let v=NativeVault::open(&app).unwrap();
        assert_eq!(count(&v.conn,"SELECT count(*) FROM tool_review_decisions WHERE conversation_id='thread_alpha'"),2);
        let choice:String=v.conn.query_row("SELECT decision FROM tool_review_decisions WHERE request_id='request_001'",[],|r|r.get(0)).unwrap();
        assert_eq!(choice,"approve");
        assert_eq!(count(&v.conn,"SELECT count(*) FROM tool_review_decisions WHERE decision='deny'"),1);
        assert_eq!(count(&v.conn,"SELECT count(*) FROM messages"),0);
    }

    #[test]
    fn text_artifact_is_native_scoped_immutable_replayable_and_context_neutral() {
        let f=Fixture::new();
        let app=f.app();
        let mut v=NativeVault::open(&app).unwrap();
        v.create_conversation("thread_alpha","Artifact").unwrap();
        v.create_conversation("thread_bravo","Other").unwrap();
        v.append_chat_message(sample_message("message_0001","thread_alpha",None)).unwrap();
        let text="Synthetic <script>plain text</script>\nUnicode: اردو 中文 🙂\n";
        v.append_chat_message(ChatMessageInput{id:"assistant_001",conversation_id:"thread_alpha",
            parent_id:Some("message_0001"),role:ChatRole::Assistant,content:text,status:ChatStatus::Complete}).unwrap();
        v.append_chat_message(ChatMessageInput{id:"assistant_002",conversation_id:"thread_alpha",
            parent_id:Some("message_0001"),role:ChatRole::Assistant,content:"partial",status:ChatStatus::Cancelled}).unwrap();
        assert!(v.create_text_artifact("thread_alpha","message_0001").is_err());
        assert!(v.create_text_artifact("thread_alpha","assistant_002").is_err());
        assert!(v.create_text_artifact("thread_bravo","assistant_001").is_err());
        assert!(v.preview_text_artifact("thread_alpha","assistant_001").is_err());
        let before=v.model_context("thread_alpha",2048,128).unwrap();
        let created=v.create_text_artifact("thread_alpha","assistant_001").unwrap();
        assert!(!created.replayed);
        assert_eq!(created.source_id,"assistant_001");
        assert_eq!(created.attachment.receipt.name,TEXT_ARTIFACT_NAME);
        assert_eq!(created.attachment.receipt.bytes,text.len() as u64);
        assert_eq!(v.preview_text_artifact("thread_alpha","assistant_001").unwrap(),text);
        let row=v.get_chat_message("thread_alpha",&created.message_id).unwrap().unwrap();
        assert_eq!(row.role,"system");
        assert_eq!(row.parent_id.as_deref(),Some("assistant_001"));
        let after=v.model_context("thread_alpha",2048,128).unwrap();
        assert_eq!(before.estimated_tokens,after.estimated_tokens);
        assert_eq!(before.omitted_messages,after.omitted_messages);
        assert_eq!(before.messages.iter().map(|m|&m.id).collect::<Vec<_>>(),
                   after.messages.iter().map(|m|&m.id).collect::<Vec<_>>());
        let revision=v.get_conversation("thread_alpha").unwrap().unwrap().revision;
        let journal=count(&v.conn,"SELECT count(*) FROM chat_change_journal");
        drop(v);
        let mut v=NativeVault::open(&app).unwrap();
        let replay=v.create_text_artifact("thread_alpha","assistant_001").unwrap();
        assert!(replay.replayed);
        assert_eq!(replay.message_id,created.message_id);
        assert_eq!(replay.attachment.id,created.attachment.id);
        assert_eq!(replay.attachment.receipt,created.attachment.receipt);
        assert_eq!(v.get_conversation("thread_alpha").unwrap().unwrap().revision,revision);
        assert_eq!(count(&v.conn,"SELECT count(*) FROM chat_change_journal"),journal);
        assert_eq!(count(&v.conn,"SELECT count(*) FROM managed_artifacts"),1);
        assert_eq!(count(&v.conn,"SELECT count(*) FROM artifact_links"),1);
        assert_eq!(v.preview_text_artifact("thread_alpha","assistant_001").unwrap(),text);
        assert!(v.preview_text_artifact("thread_bravo","assistant_001").is_err());
        assert_eq!(v.inspect_managed_recovery().unwrap().verified_referenced,1);
        let hash=&created.attachment.receipt.sha256;
        let path=v.managed_blob_directory(hash,false).unwrap().join(hash);
        let broken=vec![b'x';text.len()];
        fs::write(&path,&broken).unwrap();
        assert!(v.preview_text_artifact("thread_alpha","assistant_001").is_err());
        assert!(v.create_text_artifact("thread_alpha","assistant_001").is_err());
        assert_eq!(fs::read(&path).unwrap(),broken);
        assert_eq!(count(&v.conn,"SELECT count(*) FROM chat_change_journal"),journal);
        assert_eq!(v.inspect_managed_recovery().unwrap().unavailable_referenced,1);
    }

    #[test]
    fn managed_recovery_inventory_preserves_unlinked_blobs_stages_and_corruption() {
        let f=Fixture::new();
        let app=f.app();
        let mut v=NativeVault::open(&app).unwrap();
        assert_eq!(v.inspect_managed_recovery().unwrap(), ManagedRecoveryInventory::default());
        v.create_conversation("thread_alpha","Recovery").unwrap();
        let linked=v.stage_managed_blob("linked.txt",b"linked").unwrap();
        let orphan=v.stage_managed_blob("orphan.txt",b"unlinked").unwrap();
        let broken=v.stage_managed_blob("broken.txt",b"before").unwrap();
        let missing=v.stage_managed_blob("missing.txt",b"absent").unwrap();
        let items=[
            LinkedAttachment{id:"artifact_001".into(),receipt:linked.clone()},
            LinkedAttachment{id:"artifact_002".into(),receipt:broken.clone()},
            LinkedAttachment{id:"artifact_003".into(),receipt:missing.clone()},
        ];
        v.append_chat_message_with_attachments(sample_message("message_0001","thread_alpha",None),&items).unwrap();
        let dir=v.managed_blob_directory(&orphan.sha256,false).unwrap();
        let stage=dir.join(".stage-1-2-3");
        fs::write(&stage,b"interrupted only copy").unwrap();
        let unexpected=dir.join("unexpected.bin");
        fs::write(&unexpected,b"preserve").unwrap();
        let corrupt_path=v.managed_blob_directory(&broken.sha256,false).unwrap().join(&broken.sha256);
        fs::write(&corrupt_path,b"after!").unwrap();
        let missing_path=v.managed_blob_directory(&missing.sha256,false).unwrap().join(&missing.sha256);
        fs::remove_file(&missing_path).unwrap(); // synthetic failure fixture only
        let before=count(&v.conn,"SELECT count(*) FROM chat_change_journal");
        drop(v);
        let mut v=NativeVault::open(&app).unwrap();
        let report=v.inspect_managed_recovery().unwrap();
        assert_eq!(report,ManagedRecoveryInventory{referenced_hashes:3,verified_referenced:1,
            verified_unreferenced:1,unavailable_referenced:2,damaged_or_unreadable:1,
            interrupted_stages:1,unexpected_entries:1,unlinked_metadata:0});
        assert_eq!(fs::read(&stage).unwrap(),b"interrupted only copy");
        assert_eq!(fs::read(&unexpected).unwrap(),b"preserve");
        assert_eq!(fs::read(&corrupt_path).unwrap(),b"after!");
        assert_eq!(v.read_managed_blob(&orphan).unwrap(),b"unlinked");
        assert_eq!(count(&v.conn,"SELECT count(*) FROM chat_change_journal"),before);
        assert_eq!(v.list_message_attachments("thread_alpha","message_0001").unwrap().len(),3);
    }

    #[cfg(unix)]
    #[test]
    fn managed_recovery_inventory_does_not_follow_observed_symlink_entries() {
        use std::os::unix::fs::symlink;
        let f=Fixture::new();
        let mut v=NativeVault::open(&f.app()).unwrap();
        let receipt=v.stage_managed_blob("note.txt",b"source").unwrap();
        let directory=v.managed_blob_directory(&receipt.sha256,false).unwrap();
        let outside=f.0.join("outside.txt");
        fs::write(&outside,b"outside").unwrap();
        fs::remove_file(directory.join(&receipt.sha256)).unwrap();
        symlink(&outside,directory.join(&receipt.sha256)).unwrap();
        let report=v.inspect_managed_recovery().unwrap();
        assert_eq!(report.unexpected_entries,1);
        assert_eq!(report.verified_unreferenced,0);
        assert_eq!(fs::read(&outside).unwrap(),b"outside");
    }

    #[test]
    fn managed_blob_stage_deduplicates_and_reopens_without_original_path() {
        let f = Fixture::new();
        let app = f.app();
        let v = NativeVault::open(&app).unwrap();
        let receipt = v.stage_managed_blob("notes.txt", b"synthetic bytes").unwrap();
        let other = v.stage_managed_blob("copy.txt", b"synthetic bytes").unwrap();
        assert_eq!(receipt.sha256, other.sha256);
        let dir = app.join("data").join("artifacts").join("sha256").join(&receipt.sha256[..2]);
        assert_eq!(fs::read_dir(&dir).unwrap().count(), 1);
        assert_eq!(fs::read(dir.join(&receipt.sha256)).unwrap(), b"synthetic bytes");
        drop(v);
        let reopened = NativeVault::open(&app).unwrap();
        assert_eq!(reopened.read_managed_blob(&receipt).unwrap(), b"synthetic bytes");
        assert_eq!(reopened.read_managed_blob(&other).unwrap(), b"synthetic bytes");
        assert_eq!(reopened.stage_managed_blob("../outside", b"x"), Err(VaultFault::InvalidRecord));
        let mut malformed = receipt.clone();
        malformed.sha256 = "../outside".into();
        assert_eq!(reopened.read_managed_blob(&malformed), Err(VaultFault::InvalidRecord));
    }

    #[test]
    fn managed_blob_corrupt_existing_target_is_never_overwritten() {
        let f = Fixture::new();
        let app = f.app();
        let v = NativeVault::open(&app).unwrap();
        let receipt = v.stage_managed_blob("note.txt", b"original").unwrap();
        let path = app.join("data").join("artifacts").join("sha256")
            .join(&receipt.sha256[..2]).join(&receipt.sha256);
        fs::write(&path, b"tampered").unwrap();
        assert_eq!(v.read_managed_blob(&receipt), Err(VaultFault::Corrupt));
        assert_eq!(v.stage_managed_blob("note.txt", b"original"), Err(VaultFault::Corrupt));
        assert_eq!(fs::read(&path).unwrap(), b"tampered");
    }

    #[cfg(unix)]
    #[test]
    fn managed_blob_rejects_observed_symlink_directory_and_target() {
        use std::os::unix::fs::symlink;
        let f = Fixture::new();
        let app = f.app();
        let v = NativeVault::open(&app).unwrap();
        let outside = f.0.join("outside");
        fs::create_dir(&outside).unwrap();
        let artifacts = app.join("data").join("artifacts");
        symlink(&outside, &artifacts).unwrap();
        assert_eq!(v.stage_managed_blob("note.txt", b"x"), Err(VaultFault::InvalidLocation));
        assert_eq!(fs::read_dir(&outside).unwrap().count(), 0);
        fs::remove_file(&artifacts).unwrap();
        let receipt = v.stage_managed_blob("note.txt", b"x").unwrap();
        let target = artifacts.join("sha256").join(&receipt.sha256[..2]).join(&receipt.sha256);
        let original = outside.join("untouched");
        fs::write(&original, b"x").unwrap();
        fs::remove_file(&target).unwrap();
        symlink(&original, &target).unwrap();
        assert_eq!(v.read_managed_blob(&receipt), Err(VaultFault::InvalidLocation));
        assert_eq!(v.stage_managed_blob("note.txt", b"x"), Err(VaultFault::InvalidLocation));
        assert_eq!(fs::read(original).unwrap(), b"x");
    }

    #[test]
    fn attachment_sqlite_length_conversion_is_checked_and_bounded() {
        assert_eq!(managed_length_from_sql(0), Ok(0));
        assert_eq!(managed_length_from_sql(1), Ok(1));
        let max = crate::artifact_contracts::MAX_ATTACHMENT;
        assert_eq!(managed_length_from_sql(max as i64), Ok(max));
        for value in [-1, i64::MIN, max as i64 + 1, i64::MAX] {
            assert_eq!(managed_length_from_sql(value), Err(VaultFault::Corrupt));
        }
    }

    #[test]
    fn attachment_list_rejects_corrupt_persisted_length() {
        let f=Fixture::new();
        let mut v=NativeVault::open(&f.app()).unwrap();
        v.create_conversation("thread_alpha","One").unwrap();
        let a=LinkedAttachment{id:"artifact_001".into(),receipt:v.stage_managed_blob("note.txt",b"contents").unwrap()};
        v.append_chat_message_with_attachments(sample_message("message_0001","thread_alpha",None),&[a]).unwrap();
        // Deliberate synthetic DB corruption; production never disables CHECK constraints.
        v.conn.execute_batch("PRAGMA ignore_check_constraints=ON;
            UPDATE managed_artifacts SET bytes=-1 WHERE id='artifact_001';
            PRAGMA ignore_check_constraints=OFF;").unwrap();
        assert!(matches!(v.list_message_attachments("thread_alpha","message_0001"),Err(VaultFault::Corrupt)));
        assert_eq!(count(&v.conn,"SELECT count(*) FROM messages"),1);
        assert_eq!(count(&v.conn,"SELECT bytes FROM managed_artifacts WHERE id='artifact_001'"),-1);
    }

    #[test]
    fn attachment_v2_upgrade_preserves_chat_and_preupgrade_snapshot() {
        let f=Fixture::new();
        let app=f.app();
        let data=checked_child(&app,"data").unwrap();
        let path=data.join("state.sqlite");
        let db=Connection::open(&path).unwrap();
        db.execute_batch(LEGACY_SCHEMA).unwrap();
        apply_v2(&db,0,None).unwrap();
        db.execute_batch("INSERT INTO conversations VALUES('thread_alpha','Synthetic',1,1,1);
            INSERT INTO messages VALUES('message_0001','thread_alpha',NULL,1,'user','previous chat','complete',1,1);").unwrap();
        drop(db);
        let v=NativeVault::open(&app).unwrap();
        assert_eq!(version(&v.conn).unwrap(),4);
        assert_eq!(v.get_chat_message("thread_alpha","message_0001").unwrap().unwrap().content,"previous chat");
        let backup_id:String=v.conn.query_row("SELECT backup_id FROM artifact_schema_migrations WHERE from_version=2",[],|r|r.get(0)).unwrap();
        let backup=app.join("backups").join("snapshots").join(format!("{backup_id}.sqlite"));
        let old=Connection::open_with_flags(backup,OpenFlags::SQLITE_OPEN_READ_ONLY).unwrap();
        assert_eq!(validate_schema(&old).unwrap(),2);
        assert_eq!(count(&old,"SELECT count(*) FROM messages WHERE content='previous chat'"),1);
        assert_eq!(count(&old,"SELECT count(*) FROM sqlite_schema WHERE name='artifact_links'"),0);
    }

    #[test]
    fn attachment_v2_upgrade_refuses_missing_backup_without_mutating_schema() {
        let f=Fixture::new();
        let app=f.app();
        let path=checked_child(&app,"data").unwrap().join("state.sqlite");
        let db=Connection::open(&path).unwrap();
        db.execute_batch(LEGACY_SCHEMA).unwrap();
        apply_v2(&db,0,None).unwrap();
        drop(db);
        fs::write(app.join("backups"),b"occupied").unwrap();
        assert!(NativeVault::open(&app).is_err());
        let db=Connection::open_with_flags(path,OpenFlags::SQLITE_OPEN_READ_ONLY).unwrap();
        assert_eq!(validate_schema(&db).unwrap(),2);
        assert_eq!(count(&db,"SELECT count(*) FROM sqlite_schema WHERE name='artifact_links'"),0);
        assert_eq!(fs::read(app.join("backups")).unwrap(),b"occupied");
    }

    #[test]
    fn attachment_message_commit_scopes_links_and_reopens() {
        let f=Fixture::new();
        let app=f.app();
        let mut v=NativeVault::open(&app).unwrap();
        v.create_conversation("thread_alpha","One").unwrap();
        v.create_conversation("thread_other","Two").unwrap();
        let a=LinkedAttachment{id:"artifact_001".into(),receipt:v.stage_managed_blob("note.txt",b"contents").unwrap()};
        let receipt=v.append_chat_message_with_attachments(sample_message("message_0001","thread_alpha",None),&[a]).unwrap();
        assert_eq!(receipt.ordinal,Some(1));
        assert!(v.list_message_attachments("thread_other","message_0001").is_err());
        drop(v);
        let v=NativeVault::open(&app).unwrap();
        let links=v.list_message_attachments("thread_alpha","message_0001").unwrap();
        assert_eq!(links.len(),1);
        assert_eq!(links[0].id,"artifact_001");
        assert_eq!(v.read_managed_blob(&links[0].receipt).unwrap(),b"contents");
        assert_eq!(count(&v.conn,"SELECT count(*) FROM artifact_links"),1);
        assert_eq!(count(&v.conn,"SELECT count(*) FROM managed_artifacts"),1);
    }

    #[test]
    fn attachment_link_failure_rolls_back_message_metadata_and_journal() {
        let f=Fixture::new();
        let mut v=NativeVault::open(&f.app()).unwrap();
        v.create_conversation("thread_alpha","One").unwrap();
        let a=LinkedAttachment{id:"artifact_001".into(),receipt:v.stage_managed_blob("note.txt",b"contents").unwrap()};
        v.conn.execute_batch("CREATE TEMP TRIGGER fail_link BEFORE INSERT ON artifact_links
            BEGIN SELECT RAISE(ABORT,'fixture failure'); END;").unwrap();
        assert!(v.append_chat_message_with_attachments(sample_message("message_0001","thread_alpha",None),&[a]).is_err());
        assert_eq!(count(&v.conn,"SELECT count(*) FROM messages"),0);
        assert_eq!(count(&v.conn,"SELECT count(*) FROM managed_artifacts"),0);
        assert_eq!(count(&v.conn,"SELECT count(*) FROM artifact_links"),0);
        assert_eq!(count(&v.conn,"SELECT count(*) FROM chat_change_journal"),1);
        assert_eq!(count(&v.conn,"SELECT revision FROM conversations"),1);
        // The staged content remains available for explicit retry; never delete a sole copy.
        assert_eq!(v.stage_managed_blob("note.txt",b"contents").unwrap().bytes,8);
    }

    #[test]
    fn transactional_commit_ack_and_reopen_preserve_user_content() {
        let f = Fixture::new();
        let app = f.app();
        let mut v = NativeVault::open(&app).unwrap();
        assert_eq!(v.insert_new("conversation_001", ContentClass::Conversation, "private user text").unwrap(), 1);
        assert_eq!(v.read("conversation_001").unwrap().as_deref(), Some("private user text"));
        assert_eq!(v.insert_new("conversation_001", ContentClass::Conversation, "wrong overwrite"),
                   Err(VaultFault::Conflict));
        assert_eq!(v.read("conversation_001").unwrap().as_deref(), Some("private user text"));
        drop(v);
        let after = NativeVault::open(&app).unwrap();
        assert_eq!(after.read("conversation_001").unwrap().as_deref(), Some("private user text"));
        let mode: String = after.conn.query_row("PRAGMA journal_mode", [], |r| r.get(0)).unwrap();
        assert_eq!(mode.to_lowercase(), "wal");
    }

    #[test]
    fn online_wal_snapshot_and_disposable_restore_drill() {
        let f = Fixture::new();
        let app = f.app();
        let mut v = NativeVault::open(&app).unwrap();
        v.insert_new("project_alpha", ContentClass::Project, "offline manifest").unwrap();
        let backup = v.snapshot_new("checkpoint_001").unwrap();
        assert_eq!(v.snapshot_new("checkpoint_001"), Err(VaultFault::Conflict));
        v.insert_new("project_beta", ContentClass::Project, "later write").unwrap();
        let stage = f.0.join("preview-restored.sqlite");
        NativeVault::restore_to_new_test_profile(&backup, &stage).unwrap();
        let preview = Connection::open_with_flags(&stage, OpenFlags::SQLITE_OPEN_READ_ONLY).unwrap();
        let before: String = preview.query_row("SELECT payload FROM records WHERE id='project_alpha'", [], |r| r.get(0)).unwrap();
        assert_eq!(before, "offline manifest");
        let after: Option<String> = preview.query_row("SELECT payload FROM records WHERE id='project_beta'", [], |r| r.get(0)).optional().unwrap();
        assert!(after.is_none());
        assert_eq!(v.read("project_beta").unwrap().as_deref(), Some("later write"));
    }

    #[test]
    fn malformed_location_and_corrupt_source_preserved_without_repair_overwrite() {
        let f = Fixture::new();
        assert!(matches!(NativeVault::open(&f.0), Err(VaultFault::InvalidLocation)));
        let app = f.app();
        let data = app.join("data");
        fs::create_dir(&data).unwrap();
        let source = data.join("state.sqlite");
        fs::write(&source, b"DO_NOT_OVERWRITE_MY_DATA").unwrap();
        assert!(NativeVault::open(&app).is_err());
        assert_eq!(fs::read(source).unwrap(), b"DO_NOT_OVERWRITE_MY_DATA");
    }


    #[test]
    fn restore_never_overwrites_a_preexisting_destination() {
        let f = Fixture::new();
        let app = f.app();
        let mut vault = NativeVault::open(&app).unwrap();
        vault.insert_new("record_abc_001", ContentClass::Project, "snapshot-content").unwrap();
        let backup = vault.snapshot_new("snapshot_safe_001").unwrap();
        let occupied = f.0.join("user-existing.sqlite");
        fs::write(&occupied, b"DO_NOT_OVERWRITE").unwrap();
        assert_eq!(NativeVault::restore_to_new_test_profile(&backup, &occupied),
                   Err(VaultFault::InvalidLocation));
        assert_eq!(fs::read(occupied).unwrap(), b"DO_NOT_OVERWRITE");
    }

    #[cfg(unix)]
    #[test]
    fn sqlite_sidecar_symlink_target_must_remain_untouched() {
        let f = Fixture::new();
        let app = f.app();
        let data = app.join("data");
        fs::create_dir(&data).unwrap();
        let target = f.0.join("precious.txt");
        fs::write(&target, b"USER_CONTENT").unwrap();
        std::os::unix::fs::symlink(&target, data.join("state.sqlite-wal")).unwrap();
        assert!(matches!(NativeVault::open(&app), Err(VaultFault::InvalidLocation)));
        assert_eq!(fs::read(target).unwrap(), b"USER_CONTENT");
    }

    #[test]
    fn rejected_record_does_not_create_false_success_or_data() {
        let f = Fixture::new();
        let app = f.app();
        let mut v = NativeVault::open(&app).unwrap();
        for bad in ["", "../path", "space path", "a"] {
            assert_eq!(v.insert_new(bad, ContentClass::Preference, "x"),
                       Err(VaultFault::InvalidRecord));
        }
        assert_eq!(v.insert_new("valid_record_1", ContentClass::Preference, ""),
                   Err(VaultFault::InvalidRecord));
        assert_eq!(v.read("valid_record_1").unwrap(), None);
    }

    fn legacy_fixture(app: &Path) -> PathBuf {
        let data = app.join("data");
        fs::create_dir(&data).unwrap();
        let file = data.join("state.sqlite");
        let db = Connection::open(&file).unwrap();
        db.execute_batch("PRAGMA journal_mode=WAL; PRAGMA synchronous=FULL;").unwrap();
        db.execute_batch(LEGACY_SCHEMA).unwrap();
        db.execute_batch("PRAGMA user_version=1;").unwrap();
        db.execute("INSERT INTO records VALUES('legacy_chat_001','conversation','legacy opaque content',3,1234)", []).unwrap();
        drop(db);
        file
    }

    fn sample_message<'a>(id: &'a str, conversation_id: &'a str, parent_id: Option<&'a str>) -> ChatMessageInput<'a> {
        ChatMessageInput { id, conversation_id, parent_id, role:ChatRole::User,
            content:"synthetic message",status:ChatStatus::Complete }
    }

    fn count(db: &Connection, sql: &str) -> i64 { db.query_row(sql, [], |r| r.get(0)).unwrap() }

    #[test]
    fn p03_fresh_schema_wal_full_fk_and_migration_history() {
        let f = Fixture::new();
        let v = NativeVault::open(&f.app()).unwrap();
        assert_eq!(version(&v.conn).unwrap(), 4);
        assert_eq!(count(&v.conn,"SELECT count(*) FROM artifact_schema_migrations WHERE version=3 AND from_version=0 AND backup_id IS NULL"),1);
        assert_eq!(count(&v.conn,"SELECT count(*) FROM tool_review_schema_migrations WHERE version=4 AND from_version=0 AND backup_id IS NULL"),1);
        assert_eq!(count(&v.conn,"SELECT count(*) FROM tool_review_decisions"),0);
        assert_eq!(count(&v.conn,"PRAGMA synchronous"),2);
        assert_eq!(count(&v.conn,"PRAGMA foreign_keys"),1);
        assert_eq!(count(&v.conn,"SELECT count(*) FROM schema_migrations WHERE version=2 AND from_version=0 AND backup_id IS NULL"),1);
        assert_eq!(count(&v.conn,"SELECT count(*) FROM messages"),0);
        assert_eq!(count(&v.conn,"SELECT count(*) FROM chat_change_journal"),0);
        let mode:String = v.conn.query_row("PRAGMA journal_mode",[],|r|r.get(0)).unwrap();
        assert_eq!(mode.to_lowercase(),"wal");
    }

    #[test]
    fn p03_v1_migration_keeps_legacy_bytes_and_verified_backup() {
        let f=Fixture::new();
        let app=f.app();
        legacy_fixture(&app);
        let v=NativeVault::open(&app).unwrap();
        assert_eq!(version(&v.conn).unwrap(),4);
        assert_eq!(count(&v.conn,"SELECT count(*) FROM artifact_schema_migrations WHERE version=3 AND from_version=1 AND backup_id IS NULL"),1);
        assert_eq!(v.read("legacy_chat_001").unwrap().as_deref(),Some("legacy opaque content"));
        assert_eq!(count(&v.conn,"SELECT revision FROM records WHERE id='legacy_chat_001'"),3);
        assert_eq!(count(&v.conn,"SELECT created_at FROM records WHERE id='legacy_chat_001'"),1234);
        let backup_id:String=v.conn.query_row("SELECT backup_id FROM schema_migrations WHERE from_version=1",[],|r|r.get(0)).unwrap();
        let path=app.join("backups").join("snapshots").join(format!("{backup_id}.sqlite"));
        let original=Connection::open_with_flags(&path,OpenFlags::SQLITE_OPEN_READ_ONLY).unwrap();
        assert_eq!(validate_schema(&original).unwrap(),1);
        assert_eq!(count(&original,"SELECT count(*) FROM records WHERE payload='legacy opaque content' AND revision=3"),1);
        drop(original);
        drop(v);
        let again=NativeVault::open(&app).unwrap();
        assert_eq!(count(&again.conn,"SELECT count(*) FROM schema_migrations"),1);
        assert_eq!(fs::read_dir(app.join("backups").join("snapshots")).unwrap().filter_map(Result::ok)
            .filter(|e| e.path().extension().and_then(|x|x.to_str())==Some("sqlite")).count(),1);
    }

    #[test]
    fn p03_unavailable_backup_preserves_v1_without_migration() {
        let f=Fixture::new();
        let app=f.app();
        let file=legacy_fixture(&app);
        fs::write(app.join("backups"),b"do not overwrite").unwrap();
        assert!(NativeVault::open(&app).is_err());
        let original=Connection::open_with_flags(&file,OpenFlags::SQLITE_OPEN_READ_ONLY).unwrap();
        assert_eq!(validate_schema(&original).unwrap(),1);
        assert_eq!(count(&original,"SELECT count(*) FROM records WHERE payload='legacy opaque content'"),1);
        assert_eq!(fs::read(app.join("backups")).unwrap(),b"do not overwrite");
    }

    #[test]
    fn p03_failed_ddl_transaction_rolls_back_schema_and_version() {
        let f=Fixture::new();
        let app=f.app();
        let file=legacy_fixture(&app);
        let mut db=Connection::open(&file).unwrap();
        db.execute_batch("CREATE TABLE messages(occupied TEXT);").unwrap();
        {
            let tx=db.transaction_with_behavior(TransactionBehavior::Immediate).unwrap();
            assert!(apply_v2(&tx,1,Some("fixture_backup")).is_err());
        }
        assert_eq!(version(&db).unwrap(),1);
        assert_eq!(count(&db,"SELECT count(*) FROM sqlite_schema WHERE name='conversations'"),0);
        assert_eq!(count(&db,"SELECT count(*) FROM records WHERE payload='legacy opaque content'"),1);
        assert_eq!(count(&db,"SELECT count(*) FROM sqlite_schema WHERE name='messages'"),1);
    }

    #[test]
    fn p03_future_or_malformed_schema_is_not_reinitialized() {
        let f=Fixture::new();
        let app=f.app();
        let file=legacy_fixture(&app);
        let db=Connection::open(&file).unwrap();
        db.execute_batch("PRAGMA user_version=99;").unwrap();
        drop(db);
        assert!(matches!(NativeVault::open(&app),Err(VaultFault::UnsupportedSchema)));
        let db=Connection::open(&file).unwrap();
        assert_eq!(version(&db).unwrap(),99);
        assert_eq!(count(&db,"SELECT count(*) FROM records"),1);
        db.execute_batch("PRAGMA user_version=1; CREATE TABLE unexpected(id TEXT);").unwrap();
        drop(db);
        assert!(matches!(NativeVault::open(&app),Err(VaultFault::Corrupt)));
        let db=Connection::open(&file).unwrap();
        assert_eq!(version(&db).unwrap(),1);
        assert_eq!(count(&db,"SELECT count(*) FROM records"),1);
    }

    #[test]
    fn p03_message_ack_reopen_order_and_scoped_history() {
        let f=Fixture::new();
        let app=f.app();
        let mut v=NativeVault::open(&app).unwrap();
        let receipt=v.create_conversation("thread_alpha","Synthetic title").unwrap();
        assert_eq!((receipt.id.as_str(),receipt.revision,receipt.conversation_revision,receipt.ordinal),("thread_alpha",1,1,None));
        v.create_conversation("thread_other","Other thread").unwrap();
        let a=v.append_chat_message(sample_message("message_0001","thread_alpha",None)).unwrap();
        let mut next=sample_message("message_0002","thread_alpha",Some("message_0001"));
        next.role=ChatRole::Assistant;
        next.status=ChatStatus::Cancelled;
        next.content="saved partial response";
        let b=v.append_chat_message(next).unwrap();
        assert_eq!((a.ordinal,a.conversation_revision,b.ordinal,b.conversation_revision),(Some(1),2,Some(2),3));
        v.append_chat_message(sample_message("message_other","thread_other",None)).unwrap();
        drop(v);
        let again=NativeVault::open(&app).unwrap();
        let first=again.list_chat_messages("thread_alpha",0,1).unwrap();
        assert_eq!(first.len(),1);
        assert_eq!(first[0].id,"message_0001");
        assert_eq!(first[0].role,"user");
        assert_eq!(first[0].ordinal,1);
        assert_eq!(first[0].revision,1);
        assert!(first[0].created_at>0);
        let second=again.list_chat_messages("thread_alpha",first[0].ordinal,1).unwrap();
        assert_eq!(second[0].content,"saved partial response");
        assert_eq!(second[0].status,"cancelled");
        assert_eq!(second[0].parent_id.as_deref(),Some("message_0001"));
        assert_eq!(again.list_chat_messages("thread_alpha",2,2).unwrap().len(),0);
        assert_eq!(count(&again.conn,"SELECT count(*) FROM chat_change_journal"),8);
        assert!(again.list_chat_messages("thread_alpha",0,201).is_err());
    }

    #[test]
    fn p03_rejects_duplicate_invalid_and_cross_thread_without_partial_journal() {
        let f=Fixture::new();
        let mut v=NativeVault::open(&f.app()).unwrap();
        v.create_conversation("thread_alpha","One").unwrap();
        v.create_conversation("thread_other","Two").unwrap();
        v.append_chat_message(sample_message("message_0001","thread_alpha",None)).unwrap();
        assert!(matches!(v.create_conversation("thread_alpha","overwrite"),Err(VaultFault::Conflict)));
        assert!(matches!(v.append_chat_message(sample_message("message_0001","thread_alpha",None)),Err(VaultFault::Conflict)));
        assert!(matches!(v.append_chat_message(sample_message("message_0002","thread_other",Some("message_0001"))),Err(VaultFault::Conflict)));
        assert!(matches!(v.append_chat_message(sample_message("message_0003","missing_thread",None)),Err(VaultFault::Conflict)));
        let mut invalid=sample_message("message_0004","thread_alpha",None);
        invalid.content=" ";
        assert!(matches!(v.append_chat_message(invalid),Err(VaultFault::InvalidRecord)));
        assert_eq!(count(&v.conn,"SELECT count(*) FROM messages"),1);
        assert_eq!(count(&v.conn,"SELECT count(*) FROM chat_change_journal"),4);
        assert_eq!(count(&v.conn,"SELECT revision FROM conversations WHERE id='thread_alpha'"),2);
    }

    #[test]
    fn p03_injected_journal_failure_rolls_back_message_and_revision() {
        let f=Fixture::new();
        let app=f.app();
        let mut v=NativeVault::open(&app).unwrap();
        v.create_conversation("thread_alpha","Synthetic").unwrap();
        v.conn.execute_batch("CREATE TEMP TRIGGER fail_journal BEFORE INSERT ON chat_change_journal
            WHEN NEW.entity_type='message' BEGIN SELECT RAISE(ABORT,'fixture journal failure'); END;").unwrap();
        assert!(v.append_chat_message(sample_message("message_0001","thread_alpha",None)).is_err());
        drop(v);
        let mut again=NativeVault::open(&app).unwrap();
        assert_eq!(count(&again.conn,"SELECT count(*) FROM messages"),0);
        assert_eq!(count(&again.conn,"SELECT count(*) FROM chat_change_journal"),1);
        assert_eq!(count(&again.conn,"SELECT revision FROM conversations"),1);
        let mut msg=sample_message("message_0001","thread_alpha",None);
        msg.role=ChatRole::System;
        msg.status=ChatStatus::Failed;
        assert_eq!(again.append_chat_message(msg).unwrap().ordinal,Some(1));
    }

    #[test]
    fn p03_online_snapshot_restore_staged_v2_and_legacy_without_overwrite() {
        let f=Fixture::new();
        let app=f.app();
        legacy_fixture(&app);
        let mut v=NativeVault::open(&app).unwrap();
        let backup_id:String=v.conn.query_row("SELECT backup_id FROM schema_migrations",[],|r|r.get(0)).unwrap();
        let legacy=app.join("backups").join("snapshots").join(format!("{backup_id}.sqlite"));
        let legacy_preview=f.0.join("legacy-preview.sqlite");
        NativeVault::restore_to_new_test_profile(&legacy,&legacy_preview).unwrap();
        let old=Connection::open_with_flags(&legacy_preview,OpenFlags::SQLITE_OPEN_READ_ONLY).unwrap();
        assert_eq!(validate_schema(&old).unwrap(),1);
        drop(old);
        v.create_conversation("thread_alpha","Synthetic").unwrap();
        v.append_chat_message(sample_message("message_0001","thread_alpha",None)).unwrap();
        let snapshot=v.snapshot_new("p03_snapshot_01").unwrap();
        v.append_chat_message(sample_message("message_0002","thread_alpha",Some("message_0001"))).unwrap();
        let preview=f.0.join("v3-preview.sqlite");
        NativeVault::restore_to_new_test_profile(&snapshot,&preview).unwrap();
        let restored=Connection::open_with_flags(&preview,OpenFlags::SQLITE_OPEN_READ_ONLY).unwrap();
        assert_eq!(validate_schema(&restored).unwrap(),4);
        assert_eq!(count(&restored,"SELECT count(*) FROM messages"),1);
        assert_eq!(count(&v.conn,"SELECT count(*) FROM messages"),2);
        assert_eq!(count(&restored,"SELECT count(*) FROM records"),1);
        drop(restored);
        assert_eq!(NativeVault::restore_to_new_test_profile(&snapshot,&preview),Err(VaultFault::InvalidLocation));
    }

    #[test]
    fn thread_query_metadata_cursor_and_reopen() {
        let f=Fixture::new();
        let app=f.app();
        let mut v=NativeVault::open(&app).unwrap();
        assert!(v.list_conversations(None,20).unwrap().is_empty());
        v.create_conversation("thread_bravo","Second").unwrap();
        v.create_conversation("thread_alpha","First").unwrap();
        v.append_chat_message(sample_message("message_0001","thread_alpha",None)).unwrap();
        drop(v);
        let after=NativeVault::open(&app).unwrap();
        let page=after.list_conversations(None,1).unwrap();
        assert_eq!(page.len(),1);
        assert_eq!(page[0].id,"thread_alpha");
        assert_eq!(page[0].title,"First");
        assert_eq!(page[0].revision,2);
        assert!(page[0].created_at>0);
        assert!(page[0].updated_at>=page[0].created_at);
        let next=after.list_conversations(Some(&page[0].id),1).unwrap();
        assert_eq!(next[0].id,"thread_bravo");
        assert!(after.list_conversations(Some(&next[0].id),1).unwrap().is_empty());
        assert_eq!(after.get_conversation("thread_bravo").unwrap().unwrap().revision,1);
        assert!(after.get_conversation("missing_thread").unwrap().is_none());
        for limit in [0,201] { assert!(after.list_conversations(None,limit).is_err()); }
        assert!(after.list_conversations(Some("../invalid"),1).is_err());
        assert!(after.get_conversation("../invalid").is_err());
    }

    #[test]
    fn thread_query_exact_message_lookup_never_crosses_conversation() {
        let f=Fixture::new();
        let app=f.app();
        let mut v=NativeVault::open(&app).unwrap();
        v.create_conversation("thread_alpha","Alpha").unwrap();
        v.create_conversation("thread_bravo","Bravo").unwrap();
        v.append_chat_message(sample_message("message_0001","thread_alpha",None)).unwrap();
        drop(v);
        let after=NativeVault::open(&app).unwrap();
        let m=after.get_chat_message("thread_alpha","message_0001").unwrap().unwrap();
        assert_eq!(m.id,"message_0001");
        assert_eq!(m.content,"synthetic message");
        assert_eq!(m.ordinal,1);
        assert_eq!(m.role,"user");
        assert_eq!(m.status,"complete");
        assert!(after.get_chat_message("thread_bravo","message_0001").unwrap().is_none());
        assert!(after.get_chat_message("thread_alpha","missing_message").unwrap().is_none());
        assert!(after.get_chat_message("thread_alpha","../invalid").is_err());
        assert!(after.get_chat_message("../invalid","message_0001").is_err());
    }

    #[test]
    fn inference_settings_are_versioned_scoped_and_restart_safe() {
        let f=Fixture::new();let app=f.app();let mut v=NativeVault::open(&app).unwrap();
        v.create_conversation("thread_alpha","Alpha").unwrap();
        v.create_conversation("thread_bravo","Bravo").unwrap();
        let first=v.set_inference_settings("thread_alpha","qwen2.5:0.5b",1024).unwrap();
        assert_eq!((first.model.as_str(),first.context_limit,first.revision),("qwen2.5:0.5b",1024,1));
        assert!(v.get_inference_settings("thread_bravo").unwrap().is_none());
        let second=v.set_inference_settings("thread_alpha","qwen2.5:1.5b",2048).unwrap();
        assert_eq!(second.revision,2);
        assert!(v.set_inference_settings("thread_alpha","http://remote",2048).is_err());
        assert!(v.set_inference_settings("thread_alpha","qwen2.5:1.5b",777).is_err());
        drop(v);let after=NativeVault::open(&app).unwrap();
        assert_eq!(after.get_inference_settings("thread_alpha").unwrap().unwrap(),second);
    }

    #[test]
    fn context_preview_matches_persisted_draft() {
        let f=Fixture::new();let mut v=NativeVault::open(&f.app()).unwrap();
        v.create_conversation("thread_alpha","Alpha").unwrap();
        let old="x".repeat(240);
        let mut earlier=sample_message("message_user_001","thread_alpha",None);
        earlier.content=&old;
        v.append_chat_message(earlier).unwrap();
        let draft="中文🙂".repeat(12);
        let preview=v.model_context_with_draft("thread_alpha",512,256,&draft).unwrap();
        assert_eq!(preview.omitted_messages,1);
        assert!(preview.messages.is_empty());
        assert_eq!(preview.estimated_tokens,256+NativeVault::estimate_message_tokens(&draft));
        let mut newest=sample_message("message_user_002","thread_alpha",None);
        newest.content=&draft;
        v.append_chat_message(newest).unwrap();
        let actual=v.model_context("thread_alpha",512,256).unwrap();
        assert_eq!(actual.messages.len(),1);
        assert_eq!(actual.messages[0].id,"message_user_002");
        assert_eq!(actual.omitted_messages,preview.omitted_messages);
        assert_eq!(actual.estimated_tokens,preview.estimated_tokens);
        assert!(v.model_context_with_draft("thread_alpha",512,256,&"a".repeat(257)).is_err());
    }
    #[test]
    fn model_context_is_chronological_bounded_and_excludes_terminal_failures() {
        let f=Fixture::new();let mut v=NativeVault::open(&f.app()).unwrap();
        v.create_conversation("thread_alpha","Alpha").unwrap();
        v.create_conversation("thread_bravo","Bravo").unwrap();
        v.append_chat_message(sample_message("message_user_001","thread_alpha",None)).unwrap();
        let mut failed=sample_message("message_failed_01","thread_alpha",Some("message_user_001"));
        failed.role=ChatRole::Assistant;failed.status=ChatStatus::Failed;failed.content="do not replay";
        v.append_chat_message(failed).unwrap();
        v.append_chat_message(sample_message("message_other_01","thread_bravo",None)).unwrap();
        let context=v.model_context("thread_alpha",512,64).unwrap();
        assert_eq!(context.messages.len(),1);assert_eq!(context.messages[0].id,"message_user_001");
        assert_eq!(context.messages[0].role,"user");assert!(context.estimated_tokens<=context.limit);
        assert_eq!(context.omitted_messages,0);
        assert!(context.messages.iter().all(|m|m.content!="do not replay"&&m.id!="message_other_01"));
        let huge="x".repeat(262_144);let input=ChatMessageInput{id:"message_huge_0001",conversation_id:"thread_alpha",
            parent_id:None,role:ChatRole::User,content:&huge,status:ChatStatus::Complete};
        v.append_chat_message(input).unwrap();
        assert!(matches!(v.model_context("thread_alpha",512,64),Err(VaultFault::InvalidRecord)));
    }

}
