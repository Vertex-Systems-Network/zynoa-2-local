//! P01 M18 native-only event spool; never a WebView command or telemetry relay.
//! Only allowlisted event classes are accepted. Data root comes from M24 later.
use serde::{Deserialize, Serialize};
use std::collections::BTreeMap;
use std::fs::{self, File, OpenOptions};
use std::io::{BufRead, BufReader, Write};
use std::path::{Path, PathBuf};
use std::sync::atomic::{AtomicU64, Ordering};
use std::sync::{Arc, Mutex};

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
    PersistenceFailure, RecoveryUnavailable, RuntimeFault, BootReady,
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

#[derive(Clone)]
pub(crate) struct NativeDiagnostics {
    inner: Arc<Mutex<DiagnosticSpool>>,
    _instance_guard: Arc<File>,
}

impl NativeDiagnostics {
    /// Resolve an OS-provided local application directory, never an IPC path.
    /// The app identifier cannot be redirected into the binary or user files.
    pub(crate) fn initialize(
        os_local_data_root: &Path, app_local_data_root: &Path,
    ) -> Result<Self, DiagnosticFault> {
        if !os_local_data_root.is_absolute()
            || app_local_data_root != os_local_data_root.join("com.zynoa.desktop") {
            return Err(DiagnosticFault::InvalidLocation);
        }
        reject_linked_directory(os_local_data_root)?;
        let root = create_checked_child(os_local_data_root, "com.zynoa.desktop")?;
        let directory = create_checked_child(&root, "diagnostics")?;
        let guard = open_exclusive_instance_guard(&directory)?;
        let mut spool = DiagnosticSpool::open(directory.join("events-v1.jsonl"))?;
        spool.record(Module::M01, Severity::Info, Code::BootReady, now_ms())?;
        Ok(Self { inner: Arc::new(Mutex::new(spool)), _instance_guard: Arc::new(guard) })
    }

    /// Captures only a fixed category. No panic text, path, stack or user content.
    pub(crate) fn install_redacted_panic_hook(&self) {
        let inner = Arc::clone(&self.inner);
        std::panic::set_hook(Box::new(move |_| {
            if let Ok(mut spool) = inner.try_lock() {
                let _ = spool.record(Module::M18, Severity::Critical,
                                     Code::RuntimeFault, now_ms());
            }
        }));
    }

    pub(crate) fn record_denied_ipc(&self) {
        if let Ok(mut spool) = self.inner.try_lock() {
            let _ = spool.record(Module::M16, Severity::Warning, Code::IpcDenied, now_ms());
        }
    }

    #[cfg(test)]
    fn snapshot(&self) -> Vec<SafeDiagnostic> {
        self.inner.lock().unwrap().grouped_snapshot()
    }
}


fn open_exclusive_instance_guard(directory: &Path) -> Result<File, DiagnosticFault> {
    let file = directory.join("writer.lock");
    check_path(&file)?;
    let mut options = OpenOptions::new();
    options.write(true).create(true);
    #[cfg(windows)]
    {
        // Kernel-held exclusive handle, automatically released on a crash.
        // FILE_FLAG_OPEN_REPARSE_POINT avoids following a replaced link.
        use std::os::windows::fs::OpenOptionsExt;
        options.share_mode(0).custom_flags(0x0020_0000);
    }
    #[cfg(unix)]
    {
        use std::os::unix::fs::OpenOptionsExt;
        options.mode(0o600);
    }
    options.open(&file).map_err(|_| DiagnosticFault::Unavailable)
}

fn now_ms() -> u64 {
    std::time::SystemTime::now().duration_since(std::time::UNIX_EPOCH)
        .map(|d| d.as_millis().min(u128::from(u64::MAX)) as u64)
        .unwrap_or(0)
}

fn reject_linked_directory(path: &Path) -> Result<(), DiagnosticFault> {
    let metadata = fs::symlink_metadata(path).map_err(|_| DiagnosticFault::InvalidLocation)?;
    if !metadata.is_dir() || metadata.file_type().is_symlink() {
        return Err(DiagnosticFault::InvalidLocation);
    }
    Ok(())
}

fn create_checked_child(parent: &Path, child: &str) -> Result<PathBuf, DiagnosticFault> {
    reject_linked_directory(parent)?;
    let path = parent.join(child);
    match fs::create_dir(&path) {
        Ok(()) => (),
        Err(e) if e.kind() == std::io::ErrorKind::AlreadyExists => (),
        Err(_) => return Err(DiagnosticFault::Unavailable),
    }
    reject_linked_directory(&path)?;
    Ok(path)
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
    static NEXT_FIXTURE_ID: std::sync::atomic::AtomicU64 = std::sync::atomic::AtomicU64::new(0);
    struct Fixture(PathBuf);
    impl Fixture {
        fn new() -> Self {
            let ns = SystemTime::now().duration_since(UNIX_EPOCH).unwrap().as_nanos();
            let seq = NEXT_FIXTURE_ID.fetch_add(1, std::sync::atomic::Ordering::Relaxed);
            let path = std::env::temp_dir().join(format!("zynoa-m18-{}-{ns}-{seq}", std::process::id()));
            fs::create_dir(&path).unwrap();
            Self(path)
        }
        fn file(&self) -> PathBuf { self.0.join("diagnostics.jsonl") }
    }
    impl Drop for Fixture { fn drop(&mut self) { let _ = fs::remove_dir_all(&self.0); } }


    #[cfg(windows)]
    #[test]
    fn native_writer_lock_blocks_second_instance_and_recovers_after_exit() {
        let fixture = Fixture::new();
        let root = fixture.0.join("com.zynoa.desktop");
        let first = NativeDiagnostics::initialize(&fixture.0, &root).unwrap();
        assert!(matches!(
            NativeDiagnostics::initialize(&fixture.0, &root),
            Err(DiagnosticFault::Unavailable)
        ));
        drop(first);
        let second = NativeDiagnostics::initialize(&fixture.0, &root).unwrap();
        let boot = second.snapshot().into_iter()
            .find(|e| e.code == Code::BootReady).unwrap();
        assert_eq!(boot.occurrence_count, 2);
    }

    #[cfg(windows)]
    #[test]
    fn actual_panic_hook_omits_secret_payload_from_local_spool() {
        let fixture = Fixture::new();
        let root = fixture.0.join("com.zynoa.desktop");
        let runtime = NativeDiagnostics::initialize(&fixture.0, &root).unwrap();
        let old_hook = std::panic::take_hook();
        runtime.install_redacted_panic_hook();
        let result = std::panic::catch_unwind(|| {
            panic!("NEVER_STORE_SECRET_VALUE_123");
        });
        std::panic::set_hook(old_hook);
        assert!(result.is_err());
        drop(runtime);
        let raw = fs::read_to_string(root.join("diagnostics/events-v1.jsonl")).unwrap();
        assert!(raw.contains("RuntimeFault"));
        assert!(!raw.contains("NEVER_STORE_SECRET_VALUE_123"));
    }

    #[test]
    fn os_local_boot_creates_app_owned_record_and_replays_without_data_loss() {
        let fixture = Fixture::new();
        let app = fixture.0.join("com.zynoa.desktop");
        let diag = NativeDiagnostics::initialize(&fixture.0, &app).unwrap();
        assert!(diag.snapshot().iter().any(|e| e.module == Module::M01
            && e.code == Code::BootReady));
        diag.record_denied_ipc();
        let file = app.join("diagnostics").join("events-v1.jsonl");
        let persisted = fs::read_to_string(&file).unwrap();
        assert!(persisted.contains("BootReady"));
        assert!(persisted.contains("IpcDenied"));
        assert!(!persisted.contains("password"));
        assert!(!persisted.contains("stack"));
        assert_eq!(DiagnosticSpool::open(file).unwrap().grouped_snapshot().len(), 2);
    }

    #[test]
    fn app_root_cannot_be_redirected_to_external_or_symlink_path() {
        let fixture = Fixture::new();
        assert!(matches!(
            NativeDiagnostics::initialize(&fixture.0, &fixture.0.join("arbitrary")),
            Err(DiagnosticFault::InvalidLocation)
        ));
        let app = fixture.0.join("com.zynoa.desktop");
        fs::create_dir(&app).unwrap();
        fs::create_dir(app.join("diagnostics")).unwrap();
        let file = app.join("diagnostics/events-v1.jsonl");
        fs::write(&file, b"DO_NOT_REPLACE").unwrap();
        assert!(matches!(
            NativeDiagnostics::initialize(&fixture.0, &app),
            Err(DiagnosticFault::CorruptSpool)
        ));
        assert_eq!(fs::read(file).unwrap(), b"DO_NOT_REPLACE");
    }

    #[test]
    fn known_runtime_fault_is_only_a_category_without_panic_text() {
        let fixture = Fixture::new();
        let app = fixture.0.join("com.zynoa.desktop");
        let runtime = NativeDiagnostics::initialize(&fixture.0, &app).unwrap();
        // This calls the same category-only hook code without changing the
        // process-global panic hook for unrelated tests.
        if let Ok(mut spool) = runtime.inner.try_lock() {
            spool.record(Module::M18, Severity::Critical, Code::RuntimeFault, 42)
                 .unwrap();
        }
        let raw = fs::read_to_string(app.join("diagnostics/events-v1.jsonl")).unwrap();
        assert!(raw.contains("RuntimeFault"));
        assert!(!raw.contains("password"));
        assert!(!raw.contains("C:\\\\Users"));
    }

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
