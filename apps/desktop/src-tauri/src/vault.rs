//! M23 P01 native-only SQLite vault foundation, not a WebView command.
//! All operations are within the trusted app-local data path, never the binary.
//! User content is never logged, sent to telemetry or silently replaced.
use rusqlite::{params, Connection, ErrorCode, OpenFlags, OptionalExtension, TransactionBehavior, MAIN_DB};
use std::fs::{self, OpenOptions};
use std::path::{Path, PathBuf};
use std::time::Duration;

const SCHEMA_VERSION: i64 = 1;
const MAX_CONTENT_BYTES: usize = 262_144;

#[derive(Debug, Clone, Copy, PartialEq, Eq)]
pub(crate) enum VaultFault {
    InvalidLocation, InvalidRecord, Conflict, Corrupt, UnsupportedSchema, StorageUnavailable,
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

pub(crate) struct NativeVault {
    app_root: PathBuf,
    conn: Connection,
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
        let conn = Connection::open_with_flags(&file, flags).map_err(map_sql)?;
        conn.busy_timeout(Duration::from_secs(2)).map_err(map_sql)?;
        if existed {
            let v: i64 = conn.query_row("PRAGMA user_version", [], |row| row.get(0))
                .map_err(|_| VaultFault::Corrupt)?;
            if v != SCHEMA_VERSION { return Err(VaultFault::UnsupportedSchema); }
            integrity_check(&conn)?;
        }
        conn.execute_batch("PRAGMA journal_mode=WAL; PRAGMA synchronous=FULL; PRAGMA foreign_keys=ON;")
            .map_err(map_sql)?;
        if !existed {
            conn.execute_batch(
                "BEGIN IMMEDIATE;
                 CREATE TABLE records(
                   id TEXT PRIMARY KEY NOT NULL,
                   class TEXT NOT NULL CHECK(class IN ('conversation','project','preference')),
                   payload TEXT NOT NULL,
                   revision INTEGER NOT NULL CHECK(revision >= 1),
                   created_at INTEGER NOT NULL
                 );
                 PRAGMA user_version=1;
                 COMMIT;"
            ).map_err(map_sql)?;
        }
        Ok(Self { app_root: app_root.to_path_buf(), conn })
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

    /// SQLite Online Backup API; never raw-copy a live WAL database or overwrite
    /// an existing backup. Snapshot stays private and unencrypted until M23 export.
    pub(crate) fn snapshot_new(&self, snapshot_id: &str) -> Result<PathBuf, VaultFault> {
        if !safe_id(snapshot_id) { return Err(VaultFault::InvalidRecord); }
        let backup_root = checked_child(&self.app_root, "backups")?;
        let directory = checked_child(&backup_root, "snapshots")?;
        let path = directory.join(format!("{snapshot_id}.sqlite"));
        if reject_nonregular_file(&path)? { return Err(VaultFault::Conflict); }
        // Reserve exact destination atomically; no in-place replacement.
        let file = OpenOptions::new().create_new(true).write(true).open(&path)
            .map_err(|_| VaultFault::Conflict)?;
        drop(file);
        self.conn.backup(MAIN_DB, &path, None::<fn(rusqlite::backup::Progress)>)
            .map_err(map_sql)?;
        let verify = Connection::open_with_flags(&path, OpenFlags::SQLITE_OPEN_READ_ONLY)
            .map_err(map_sql)?;
        integrity_check(&verify)?;
        Ok(path)
    }

    /// Restore drill into a NEW disposable path only; never alter the active DB.
    pub(crate) fn restore_to_new_test_profile(
        snapshot: &Path, destination: &Path,
    ) -> Result<(), VaultFault> {
        if !snapshot.is_absolute() || !destination.is_absolute() || !reject_nonregular_file(snapshot)?
            || reject_nonregular_file(destination)?
        { return Err(VaultFault::InvalidLocation); }
        checked_directory(destination.parent().ok_or(VaultFault::InvalidLocation)?)?;
        // Reserve a NEW preview inode; an existing file is NEVER overwritten.
        let reserved = OpenOptions::new().write(true).create_new(true)
            .open(destination).map_err(|_| VaultFault::Conflict)?;
        drop(reserved);
        let mut restored = Connection::open_with_flags(
            destination, OpenFlags::SQLITE_OPEN_READ_WRITE | OpenFlags::SQLITE_OPEN_CREATE,
        ).map_err(map_sql)?;
        restored.restore(MAIN_DB, snapshot, None::<fn(rusqlite::backup::Progress)>)
            .map_err(map_sql)?;
        integrity_check(&restored)?;
        let v: i64 = restored.query_row("PRAGMA user_version", [], |r| r.get(0))
            .map_err(|_| VaultFault::Corrupt)?;
        if v != SCHEMA_VERSION { return Err(VaultFault::UnsupportedSchema); }
        Ok(())
    }
}

#[cfg(test)]
mod tests {
    use super::*;
    use std::time::{SystemTime, UNIX_EPOCH};
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
}
