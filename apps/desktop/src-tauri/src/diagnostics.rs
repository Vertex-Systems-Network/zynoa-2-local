//! P01 M18 native-only event spool; never a WebView command or telemetry relay.
//! Only allowlisted event classes are accepted. Data root comes from M24 later.
use serde::{Deserialize, Serialize};
use std::collections::BTreeMap;
use std::fs::{self, File, OpenOptions};
use std::io::{BufRead, BufReader, Write};
use std::path::{Path, PathBuf};
use std::sync::atomic::{AtomicU64, Ordering};

const SCHEMA_VERSION: u8 = 1;
const MAX_SPOOL_BYTES: u64 = 1_048_576;
const MAX_LINE_BYTES: usize = 512;
const MAX_UNIQUE_GROUPS: usize = 128;
static TRACE_SEQUENCE: AtomicU64 = AtomicU64::new(0);

#[derive(Clone, Copy, Debug, Serialize, Deserialize, Eq, PartialEq)]
pub(crate) enum Module { M01, M16, M17, M18, M23, M24, M26 }
#[derive(Clone, Copy, Debug, Serialize, Deserialize, Eq, PartialEq)]
pub(crate) enum Severity { Info, Warning, Error, Critical }
#[derive(Clone, Copy, Debug, Serialize, Deserialize, Eq, PartialEq)]
pub(crate) enum Code {
    BootFailure, IpcDenied, PermissionDenied, CredentialUnavailable,
    PersistenceFailure, RecoveryUnavailable, RuntimeFault,
}
#[derive(Clone, Debug, Serialize, Deserialize, Eq, PartialEq)]
#[serde(deny_unknown_fields)]
pub(crate) struct SafeDiagnostic {
    schema_version: u8,
    module: Module,
    severity: Severity,
    code: Code,
    fingerprint: String,
    trace_id: String,
    first_seen_ms: u64,
    last_seen_ms: u64,
    occurrence_count: u32,
}
#[derive(Debug, Eq, PartialEq)]
pub(crate) enum DiagnosticFault { InvalidLocation, CorruptSpool, Full, Unavailable }
pub(crate) struct DiagnosticSpool {
    path: PathBuf,
    groups: BTreeMap<String, SafeDiagnostic>,
}
fn fingerprint(module: Module, severity: Severity, code: Code) -> String {
    format!("{module:?}:{severity:?}:{code:?}")
}
fn check_path(path: &Path) -> Result<(), DiagnosticFault> {
    if !path.is_absolute() || path.file_name().is_none() {
        return Err(DiagnosticFault::InvalidLocation);
    }
    let parent = path.parent().ok_or(DiagnosticFault::InvalidLocation)?;
    if !parent.is_dir()
        || fs::symlink_metadata(parent).map_err(|_| DiagnosticFault::Unavailable)?
             .file_type().is_symlink() {
        return Err(DiagnosticFault::InvalidLocation);
    }
    match fs::symlink_metadata(path) {
        Ok(m) if m.file_type().is_symlink() || !m.is_file() =>
            Err(DiagnosticFault::InvalidLocation),
        Ok(m) if m.len() > MAX_SPOOL_BYTES => Err(DiagnosticFault::Full),
        Ok(_) => Ok(()),
        Err(e) if e.kind() == std::io::ErrorKind::NotFound => Ok(()),
        Err(_) => Err(DiagnosticFault::Unavailable),
    }
}
impl DiagnosticSpool {
    pub(crate) fn open(path: PathBuf) -> Result<Self, DiagnosticFault> {
        check_path(&path)?;
        let mut groups: BTreeMap<String, SafeDiagnostic> = BTreeMap::new();
        if path.exists() {
            let file = File::open(&path).map_err(|_| DiagnosticFault::Unavailable)?;
            for line in BufReader::new(file).lines() {
                let line = line.map_err(|_| DiagnosticFault::CorruptSpool)?;
                if line.len() > MAX_LINE_BYTES { return Err(DiagnosticFault::CorruptSpool); }
                let event: SafeDiagnostic =
                    serde_json::from_str(&line).map_err(|_| DiagnosticFault::CorruptSpool)?;
                let key = fingerprint(event.module, event.severity, event.code);
                if event.schema_version != SCHEMA_VERSION
                    || event.fingerprint != key
                    || event.occurrence_count == 0
                    || event.last_seen_ms < event.first_seen_ms
                    || !event.trace_id.starts_with("native-")
                    || event.trace_id.len() > 80
                    || !event.trace_id.bytes().all(|b| b.is_ascii_alphanumeric() || b == b'-')
                { return Err(DiagnosticFault::CorruptSpool); }
                if let Some(prior) = groups.get(&key) {
                    if event.occurrence_count <= prior.occurrence_count
                        || event.first_seen_ms != prior.first_seen_ms
                        || event.last_seen_ms < prior.last_seen_ms
                    { return Err(DiagnosticFault::CorruptSpool); }
                }
                groups.insert(key, event);
                if groups.len() > MAX_UNIQUE_GROUPS { return Err(DiagnosticFault::CorruptSpool); }
            }
        }
        Ok(Self { path, groups })
    }
    /// Append + durable sync must succeed before returning the event.
    pub(crate) fn record(
        &mut self, module: Module, severity: Severity, code: Code, at_ms: u64,
    ) -> Result<SafeDiagnostic, DiagnosticFault> {
        check_path(&self.path)?;
        let key = fingerprint(module, severity, code);
        if self.groups.len() >= MAX_UNIQUE_GROUPS && !self.groups.contains_key(&key) {
            return Err(DiagnosticFault::Full);
        }
        let seq = TRACE_SEQUENCE.fetch_add(1, Ordering::Relaxed);
        let mut next = self.groups.get(&key).cloned().unwrap_or(SafeDiagnostic {
            schema_version: SCHEMA_VERSION, module, severity, code,
            fingerprint: key.clone(),
            trace_id: format!("native-{:x}-{:x}-{:x}", std::process::id(), at_ms, seq),
            first_seen_ms: at_ms, last_seen_ms: at_ms, occurrence_count: 0,
        });
        next.occurrence_count = next.occurrence_count.checked_add(1).ok_or(DiagnosticFault::Full)?;
        next.last_seen_ms = next.last_seen_ms.max(at_ms);
        let mut bytes = serde_json::to_vec(&next).map_err(|_| DiagnosticFault::Unavailable)?;
        if bytes.len() > MAX_LINE_BYTES { return Err(DiagnosticFault::Full); }
        bytes.push(b'\n');
        let size = match fs::metadata(&self.path) {
            Ok(m) => m.len(),
            Err(e) if e.kind() == std::io::ErrorKind::NotFound => 0,
            Err(_) => return Err(DiagnosticFault::Unavailable),
        };
        if size.saturating_add(bytes.len() as u64) > MAX_SPOOL_BYTES {
            return Err(DiagnosticFault::Full);
        }
        let mut options = OpenOptions::new();
        options.append(true).create(true);
        #[cfg(unix)]
        { use std::os::unix::fs::OpenOptionsExt; options.mode(0o600); }
        let mut file = options.open(&self.path).map_err(|_| DiagnosticFault::Unavailable)?;
        file.write_all(&bytes).map_err(|_| DiagnosticFault::Unavailable)?;
        file.sync_data().map_err(|_| DiagnosticFault::Unavailable)?;
        self.groups.insert(key, next.clone());
        Ok(next)
    }
    pub(crate) fn grouped_snapshot(&self) -> Vec<SafeDiagnostic> {
        self.groups.values().cloned().collect()
    }
}
#[cfg(test)]
mod tests {
    use super::*;
    use std::time::{SystemTime, UNIX_EPOCH};
    struct Fixture(PathBuf);
    impl Fixture {
        fn new() -> Self {
            let ns = SystemTime::now().duration_since(UNIX_EPOCH).unwrap().as_nanos();
            let path = std::env::temp_dir().join(format!("zynoa-m18-{}-{ns}", std::process::id()));
            fs::create_dir(&path).unwrap();
            Self(path)
        }
        fn file(&self) -> PathBuf { self.0.join("diagnostics.jsonl") }
    }
    impl Drop for Fixture { fn drop(&mut self) { let _ = fs::remove_dir_all(&self.0); } }
    #[test]
    fn real_file_replay_groups_incidents_without_private_text() {
        let f = Fixture::new();
        let mut spool = DiagnosticSpool::open(f.file()).unwrap();
        assert_eq!(spool.record(Module::M17, Severity::Error, Code::PermissionDenied, 100)
            .unwrap().occurrence_count, 1);
        assert_eq!(spool.record(Module::M17, Severity::Error, Code::PermissionDenied, 90)
            .unwrap().occurrence_count, 2);
        let replay = DiagnosticSpool::open(f.file()).unwrap().grouped_snapshot();
        assert_eq!(replay.len(), 1);
        assert_eq!(replay[0].occurrence_count, 2);
        assert_eq!(replay[0].last_seen_ms, 100);
        let raw = fs::read_to_string(f.file()).unwrap();
        assert_eq!(raw.lines().count(), 2);
        assert!(!raw.contains("password"));
    }
    #[test]
    fn invalid_or_corrupt_spool_never_overwrites_user_content() {
        assert_eq!(DiagnosticSpool::open(PathBuf::from("relative.jsonl")).err(),
                   Some(DiagnosticFault::InvalidLocation));
        let f = Fixture::new();
        fs::write(f.file(), b"{invalid\n").unwrap();
        assert_eq!(DiagnosticSpool::open(f.file()).err(), Some(DiagnosticFault::CorruptSpool));
        assert_eq!(fs::read(f.file()).unwrap(), b"{invalid\n");
        fs::write(f.file(), vec![b'X'; (MAX_SPOOL_BYTES + 1) as usize]).unwrap();
        assert_eq!(DiagnosticSpool::open(f.file()).err(), Some(DiagnosticFault::Full));
    }
    #[cfg(unix)]
    #[test]
    fn symlink_target_is_untouched() {
        let f = Fixture::new();
        let target = f.0.join("other-user-data.txt");
        fs::write(&target, b"DO_NOT_TOUCH").unwrap();
        std::os::unix::fs::symlink(&target, f.file()).unwrap();
        assert_eq!(DiagnosticSpool::open(f.file()).err(), Some(DiagnosticFault::InvalidLocation));
        assert_eq!(fs::read(target).unwrap(), b"DO_NOT_TOUCH");
    }
}
