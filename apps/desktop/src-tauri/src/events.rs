//! P01-T09: native-only immutable, privacy-scoped M26 event journal.
//! No free-form user payload, no WebView IPC, remote upload or release promotion.
use rusqlite::{params, Connection, ErrorCode, OpenFlags, TransactionBehavior};
use std::fs;
use std::path::{Path, PathBuf};
use std::sync::Mutex;
use std::time::Duration;

const APP_ID: &str = "com.zynoa.desktop";
const SCHEMA_VERSION: i64 = 1;
const MAX_READ: usize = 100;

// Database schema discovery/first creation must never race between native
// connections in the same process. SQLite WAL still serializes append writes
// independently, including the per-stream sequence allocation transaction.
static OPEN_INIT_LOCK: Mutex<()> = Mutex::new(());

#[derive(Debug, Clone, Copy, Eq, PartialEq)]
pub(crate) enum EventFault {
    InvalidLocation, InvalidEvent, Conflict, Corrupt, UnsupportedSchema, StorageUnavailable,
}

#[derive(Clone, Copy, Debug, PartialEq, Eq)]
pub(crate) enum Audience { Developer, Private }
impl Audience {
    fn label(self) -> &'static str {
        match self { Self::Developer => "developer", Self::Private => "private" }
    }
}

#[derive(Clone, Copy, Debug)]
pub(crate) enum EventKind {
    IssueReported, ChangeStarted, TestFailed, TestPassed,
    DocsUpdated, ChangeVerified, ChangeReverted,
}
impl EventKind {
    fn label(self) -> &'static str {
        match self {
            Self::IssueReported => "issue.reported",
            Self::ChangeStarted => "change.started",
            Self::TestFailed => "test.failed",
            Self::TestPassed => "test.passed",
            Self::DocsUpdated => "docs.updated",
            Self::ChangeVerified => "change.verified",
            Self::ChangeReverted => "change.reverted",
        }
    }
}

#[derive(Clone, Copy, Debug)]
pub(crate) enum Origin { System, Worker, Ci }
impl Origin {
    fn label(self) -> &'static str {
        match self { Self::System => "system", Self::Worker => "worker", Self::Ci => "ci" }
    }
}

#[derive(Clone, Copy, Debug)]
pub(crate) enum Module { M01, M16, M17, M18, M23, M24, M26 }
#[derive(Clone, Copy, Debug)]
pub(crate) enum Retention { System, Support, Private }
impl Retention {
    fn label(self) -> &'static str {
        match self { Self::System => "system", Self::Support => "support", Self::Private => "private" }
    }
}

pub(crate) struct EventRequest<'a> {
    pub(crate) event_id: &'a str,
    pub(crate) stream_id: &'a str,
    pub(crate) idempotency_key: &'a str,
    pub(crate) correlation_id: &'a str,
    pub(crate) occurred_at_ms: u64,
    pub(crate) kind: EventKind,
    pub(crate) origin: Origin,
    pub(crate) module: Module,
    pub(crate) audience: Audience,
    pub(crate) retention: Retention,
}

#[derive(Clone, Debug, PartialEq, Eq)]
pub(crate) struct EventSummary {
    pub(crate) event_id: String,
    pub(crate) stream_id: String,
    pub(crate) sequence: u64,
    pub(crate) event_type: String,
    pub(crate) module: String,
}

pub(crate) struct NativeEventLedger {
    conn: Connection,
}

fn safe_token(s: &str, min: usize, max: usize) -> bool {
    (min..=max).contains(&s.len())
        && s.bytes().all(|b| b.is_ascii_alphanumeric() || b == b'_' || b == b'-')
}

fn valid_request(req: &EventRequest<'_>) -> bool {
    safe_token(req.event_id, 8, 64)
        && safe_token(req.stream_id, 4, 64)
        && safe_token(req.idempotency_key, 8, 64)
        && safe_token(req.correlation_id, 8, 64)
        && req.occurred_at_ms > 0
        && req.occurred_at_ms <= i64::MAX as u64
}

fn checked_directory(path: &Path) -> Result<(), EventFault> {
    let m = fs::symlink_metadata(path).map_err(|_| EventFault::InvalidLocation)?;
    if !m.is_dir() || m.file_type().is_symlink() {
        return Err(EventFault::InvalidLocation);
    }
    Ok(())
}

fn checked_file(path: &Path) -> Result<bool, EventFault> {
    match fs::symlink_metadata(path) {
        Ok(m) if !m.is_file() || m.file_type().is_symlink() =>
            Err(EventFault::InvalidLocation),
        Ok(_) => Ok(true),
        Err(e) if e.kind() == std::io::ErrorKind::NotFound => Ok(false),
        Err(_) => Err(EventFault::StorageUnavailable),
    }
}

fn sql_error(err: rusqlite::Error) -> EventFault {
    match err {
        rusqlite::Error::SqliteFailure(fault, _) if fault.code == ErrorCode::ConstraintViolation =>
            EventFault::Conflict,
        _ => EventFault::StorageUnavailable,
    }
}

fn integrity_check(conn: &Connection) -> Result<(), EventFault> {
    let result: String = conn.query_row("PRAGMA integrity_check", [], |r| r.get(0))
        .map_err(|_| EventFault::Corrupt)?;
    if result != "ok" { return Err(EventFault::Corrupt); }
    Ok(())
}

fn verify_schema(conn: &Connection) -> Result<(), EventFault> {
    let n: i64 = conn.query_row(
        "SELECT COUNT(*) FROM sqlite_master WHERE name IN
         ('audit_events','audit_events_no_update','audit_events_no_delete')",
        [], |r| r.get(0),
    ).map_err(|_| EventFault::Corrupt)?;
    if n != 3 { return Err(EventFault::Corrupt); }
    Ok(())
}

impl NativeEventLedger {
    pub(crate) fn open(app_root: &Path) -> Result<Self, EventFault> {
        // A second native opener must not observe a just-created SQLite file
        // before its schema/trigger transaction commits. This is a fail-closed
        // process-local bootstrap lock, not a substitute for SQL WAL locks.
        let _bootstrap_guard = OPEN_INIT_LOCK.lock()
            .map_err(|_| EventFault::StorageUnavailable)?;
        if !app_root.is_absolute() || app_root.file_name() != Some(std::ffi::OsStr::new(APP_ID)) {
            return Err(EventFault::InvalidLocation);
        }
        checked_directory(app_root)?;
        let directory = app_root.join("data");
        checked_directory(&directory)?;
        let file = directory.join("change-events-v1.sqlite");
        let existed = checked_file(&file)?;
        for suffix in ["-wal", "-shm", "-journal"] {
            checked_file(&directory.join(format!("change-events-v1.sqlite{suffix}")))?;
        }
        let conn = Connection::open_with_flags(&file,
            OpenFlags::SQLITE_OPEN_READ_WRITE | OpenFlags::SQLITE_OPEN_CREATE,
        ).map_err(sql_error)?;
        conn.busy_timeout(Duration::from_secs(2)).map_err(sql_error)?;
        if existed {
            let v: i64 = conn.query_row("PRAGMA user_version", [], |r| r.get(0))
                .map_err(|_| EventFault::Corrupt)?;
            if v != SCHEMA_VERSION { return Err(EventFault::UnsupportedSchema); }
            integrity_check(&conn)?;
            verify_schema(&conn)?;
        }
        conn.execute_batch("PRAGMA journal_mode=WAL; PRAGMA synchronous=FULL; PRAGMA foreign_keys=ON;")
            .map_err(sql_error)?;
        if !existed {
            conn.execute_batch(
                "BEGIN IMMEDIATE;
                 CREATE TABLE audit_events (
                   row_id INTEGER PRIMARY KEY AUTOINCREMENT,
                   event_id TEXT NOT NULL UNIQUE,
                   stream_id TEXT NOT NULL,
                   sequence INTEGER NOT NULL CHECK(sequence >= 1),
                   idempotency_key TEXT NOT NULL UNIQUE,
                   correlation_id TEXT NOT NULL,
                   occurred_at_ms INTEGER NOT NULL CHECK(occurred_at_ms >= 1),
                   event_type TEXT NOT NULL CHECK(event_type IN
                     ('issue.reported','change.started','test.failed','test.passed',
                      'docs.updated','change.verified','change.reverted')),
                   origin TEXT NOT NULL CHECK(origin IN ('system','worker','ci')),
                   module_id TEXT NOT NULL,
                   audience TEXT NOT NULL CHECK(audience IN ('developer','private')),
                   retention TEXT NOT NULL CHECK(retention IN ('system','support','private')),
                   UNIQUE(stream_id,sequence)
                 );
                 CREATE TRIGGER audit_events_no_update BEFORE UPDATE ON audit_events
                   BEGIN SELECT RAISE(ABORT,'immutable audit history'); END;
                 CREATE TRIGGER audit_events_no_delete BEFORE DELETE ON audit_events
                   BEGIN SELECT RAISE(ABORT,'immutable audit history'); END;
                 PRAGMA user_version=1;
                 COMMIT;"
            ).map_err(sql_error)?;
        }
        Ok(Self { conn })
    }

    /// Acknowledgement only after FULL-synchronous WAL transaction commit.
    /// Idempotent key and event ID cannot silently replay or overwrite history.
    pub(crate) fn append(&mut self, req: &EventRequest<'_>) -> Result<u64, EventFault> {
        if !valid_request(req) { return Err(EventFault::InvalidEvent); }
        let tx = self.conn.transaction_with_behavior(TransactionBehavior::Immediate)
            .map_err(sql_error)?;
        let seq: i64 = tx.query_row(
            "SELECT COALESCE(MAX(sequence),0) + 1 FROM audit_events WHERE stream_id=?1",
            params![req.stream_id], |r| r.get(0),
        ).map_err(sql_error)?;
        if seq <= 0 { return Err(EventFault::StorageUnavailable); }
        tx.execute(
            "INSERT INTO audit_events(
              event_id,stream_id,sequence,idempotency_key,correlation_id,
              occurred_at_ms,event_type,origin,module_id,audience,retention
             ) VALUES (?1,?2,?3,?4,?5,?6,?7,?8,?9,?10,?11)",
            params![
                req.event_id, req.stream_id, seq, req.idempotency_key, req.correlation_id,
                req.occurred_at_ms as i64, req.kind.label(), req.origin.label(),
                format!("{:?}", req.module), req.audience.label(), req.retention.label(),
            ],
        ).map_err(sql_error)?;
        tx.commit().map_err(sql_error)?;
        Ok(seq as u64)
    }

    /// Native-only and explicitly scoped; no release feed, remote API or WebView.
    pub(crate) fn list_for(
        &self, audience: Audience, limit: usize,
    ) -> Result<Vec<EventSummary>, EventFault> {
        if !(1..=MAX_READ).contains(&limit) { return Err(EventFault::InvalidEvent); }
        let mut statement = self.conn.prepare(
            "SELECT event_id, stream_id, sequence, event_type, module_id
               FROM audit_events WHERE audience=?1 ORDER BY row_id DESC LIMIT ?2"
        ).map_err(sql_error)?;
        let rows = statement.query_map(params![audience.label(), limit as i64], |r| {
            Ok(EventSummary {
                event_id: r.get(0)?, stream_id: r.get(1)?,
                sequence: r.get::<_, i64>(2)? as u64,
                event_type: r.get(3)?, module: r.get(4)?,
            })
        }).map_err(sql_error)?;
        rows.collect::<rusqlite::Result<Vec<_>>>().map_err(sql_error)
    }
}

#[cfg(test)]
mod tests {
    use super::*;
    use std::sync::atomic::{AtomicU64, Ordering};
    use std::time::{SystemTime, UNIX_EPOCH};
    static NEXT_FIXTURE: AtomicU64 = AtomicU64::new(0);

    struct Fixture(PathBuf);
    impl Fixture {
        fn new() -> Self {
            let stamp = SystemTime::now().duration_since(UNIX_EPOCH).unwrap().as_nanos();
            for _ in 0..64 {
                let seq = NEXT_FIXTURE.fetch_add(1, Ordering::Relaxed);
                let p = std::env::temp_dir()
                    .join(format!("zynoa-m26-{}-{stamp}-{seq}", std::process::id()));
                match fs::create_dir(&p) {
                    Ok(()) => return Self(p),
                    Err(e) if e.kind() == std::io::ErrorKind::AlreadyExists => continue,
                    Err(e) => panic!("fixture creation denied: {:?}", e.kind()),
                }
            }
            panic!("fixture collisions exhausted");
        }
        fn app(&self) -> PathBuf {
            let p = self.0.join(APP_ID);
            fs::create_dir_all(p.join("data")).unwrap();
            p
        }
    }
    impl Drop for Fixture {
        fn drop(&mut self) { let _ = fs::remove_dir_all(&self.0); }
    }

    fn request<'a>(event_id: &'a str, stream_id: &'a str, idempotency_key: &'a str,
                   audience: Audience) -> EventRequest<'a> {
        EventRequest {
            event_id, stream_id, idempotency_key,
            correlation_id: "correlation_001",
            occurred_at_ms: 1_700_000_000_000,
            kind: EventKind::ChangeStarted,
            origin: Origin::Worker,
            module: Module::M26,
            audience, retention: Retention::Private,
        }
    }

    #[test]
    fn durable_append_replay_and_no_duplicate_acknowledgement() {
        let f = Fixture::new();
        let root = f.app();
        let mut a = NativeEventLedger::open(&root).unwrap();
        assert_eq!(a.append(&request("event_0001", "stream_one", "unique_key_001", Audience::Developer)), Ok(1));
        assert_eq!(a.append(&request("event_0002", "stream_one", "unique_key_002", Audience::Developer)), Ok(2));
        assert_eq!(a.append(&request("event_0003", "stream_two", "unique_key_003", Audience::Private)), Ok(1));
        assert_eq!(a.append(&request("event_0001", "stream_one", "unique_key_001", Audience::Developer)), Err(EventFault::Conflict));
        drop(a);
        let b = NativeEventLedger::open(&root).unwrap();
        let public = b.list_for(Audience::Developer, 10).unwrap();
        let private = b.list_for(Audience::Private, 10).unwrap();
        assert_eq!(public.len(), 2);
        assert_eq!(private.len(), 1);
        assert_eq!(public[0].sequence, 2);
        assert_eq!(private[0].sequence, 1);
    }

    #[test]
    fn sql_history_is_physically_append_only_and_scope_limited() {
        let f = Fixture::new();
        let root = f.app();
        let mut a = NativeEventLedger::open(&root).unwrap();
        a.append(&request("event_0001", "stream_one", "unique_key_001", Audience::Developer)).unwrap();
        assert!(a.conn.execute("UPDATE audit_events SET event_type='test.passed'", []).is_err());
        assert!(a.conn.execute("DELETE FROM audit_events", []).is_err());
        assert_eq!(a.list_for(Audience::Private, 10).unwrap().len(), 0);
        assert_eq!(a.list_for(Audience::Developer, 0), Err(EventFault::InvalidEvent));
        assert_eq!(a.list_for(Audience::Developer, 101), Err(EventFault::InvalidEvent));
    }

    #[test]
    fn concurrent_wal_writers_get_distinct_monotonic_stream_sequences() {
        let f = Fixture::new();
        let root = f.app();
        let root_b = root.clone();
        let worker = std::thread::spawn(move || {
            let mut writer = NativeEventLedger::open(&root_b).unwrap();
            writer.append(&request("event_left_001", "stream_same", "unique_left_001",
                                   Audience::Developer)).unwrap()
        });
        let mut other = NativeEventLedger::open(&root).unwrap();
        let n = other.append(&request("event_right_01", "stream_same", "unique_right_01",
                                      Audience::Developer)).unwrap();
        let m = worker.join().unwrap();
        assert_ne!(n, m);
        let summary = NativeEventLedger::open(&root).unwrap()
            .list_for(Audience::Developer, 10).unwrap();
        assert_eq!(summary.len(), 2);
        assert!(summary.iter().any(|e| e.sequence == 1));
        assert!(summary.iter().any(|e| e.sequence == 2));
    }


    #[test]
    fn simultaneous_first_openers_preserve_every_event_and_stream_sequence() {
        use std::sync::{Arc, Barrier};
        const WRITERS: usize = 8;
        let fixture = Fixture::new();
        let root = fixture.app();
        let barrier = Arc::new(Barrier::new(WRITERS));
        let mut threads = Vec::new();
        for id in 0..WRITERS {
            let own_root = root.clone();
            let start = Arc::clone(&barrier);
            threads.push(std::thread::spawn(move || {
                start.wait();
                let mut ledger = NativeEventLedger::open(&own_root).unwrap();
                let event_id = format!("event_boot_{id:03}");
                let key = format!("key_boot_{id:03}");
                ledger.append(&request(&event_id, "stream_first_boot", &key,
                                       Audience::Developer)).unwrap()
            }));
        }
        let mut sequences: Vec<_> = threads.into_iter()
            .map(|t| t.join().unwrap()).collect();
        sequences.sort_unstable();
        assert_eq!(sequences, (1..=WRITERS as u64).collect::<Vec<_>>());
        let after_restart = NativeEventLedger::open(&root).unwrap();
        assert_eq!(after_restart.list_for(Audience::Developer, WRITERS)
                   .unwrap().len(), WRITERS);
    }

    #[test]
    fn corrupt_schema_and_untrusted_user_payload_are_refused_without_repair() {
        let f = Fixture::new();
        let root = f.app();
        let path = root.join("data/change-events-v1.sqlite");
        fs::write(&path, b"PRIVATE_EXISTING_FILE").unwrap();
        assert!(NativeEventLedger::open(&root).is_err());
        assert_eq!(fs::read(&path).unwrap(), b"PRIVATE_EXISTING_FILE");
        fs::remove_file(&path).unwrap();
        let mut ledger = NativeEventLedger::open(&root).unwrap();
        assert_eq!(ledger.append(&request("bad/secret", "stream_one", "unique_key_001",
                                          Audience::Private)), Err(EventFault::InvalidEvent));
        assert_eq!(ledger.list_for(Audience::Private, 10).unwrap().len(), 0);
    }

    #[cfg(unix)]
    #[test]
    fn linked_audit_file_never_redirects_into_other_user_data() {
        let f = Fixture::new();
        let root = f.app();
        let target = f.0.join("sensitive-original.txt");
        fs::write(&target, b"UNMODIFIED_PRIVATE").unwrap();
        std::os::unix::fs::symlink(&target, root.join("data/change-events-v1.sqlite")).unwrap();
        assert_eq!(NativeEventLedger::open(&root).err(), Some(EventFault::InvalidLocation));
        assert_eq!(fs::read(target).unwrap(), b"UNMODIFIED_PRIVATE");
    }
}
