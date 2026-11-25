//! P01-T08 M24 native-only managed location registry (no arbitrary moves).
//! Manifest stores relative class/ownership metadata, never private full paths.
use serde::{Deserialize, Serialize};
use std::fs::{self, OpenOptions};
use std::io::Write;
use std::path::{Component, Path, PathBuf};

const SCHEMA_VERSION: u8 = 1;
const APP_ID: &str = "com.zynoa.desktop";
const MAX_MANIFEST_BYTES: u64 = 4096;

#[derive(Clone, Copy, Debug, Deserialize, Serialize, Eq, PartialEq)]
#[serde(rename_all = "snake_case")]
pub(crate) enum LocationOwner { AppManaged, ExternalReadOnly }

#[derive(Clone, Copy, Debug, Deserialize, Serialize, Eq, PartialEq)]
#[serde(rename_all = "snake_case")]
pub(crate) enum LocationKind {
    UserVault, Diagnostics, Backups, Cache, DownloadStaging,
    ManagedModels, ExternalRuntime,
}

#[derive(Clone, Debug, Deserialize, Serialize, Eq, PartialEq)]
#[serde(deny_unknown_fields)]
struct LocationEntry {
    kind: LocationKind,
    owner: LocationOwner,
    relative: Option<String>,
    move_allowed: bool,
}

#[derive(Clone, Debug, Deserialize, Serialize, Eq, PartialEq)]
#[serde(deny_unknown_fields)]
struct LocationManifest {
    schema_version: u8,
    app_id: String,
    locations: Vec<LocationEntry>,
}

#[derive(Clone, Copy, Debug, Eq, PartialEq)]
pub(crate) enum LocationFault { InvalidRoot, CorruptManifest, Denied, StorageUnavailable }

pub(crate) struct NativeLocationRegistry {
    app_root: PathBuf,
    manifest: LocationManifest,
}

fn expected() -> LocationManifest {
    use LocationKind::*;
    let managed = |kind, relative: &str| LocationEntry {
        kind, owner: LocationOwner::AppManaged,
        relative: Some(relative.to_string()), move_allowed: false,
    };
    LocationManifest {
        schema_version: SCHEMA_VERSION,
        app_id: APP_ID.to_string(),
        locations: vec![
            managed(UserVault, "data"),
            managed(Diagnostics, "diagnostics"),
            managed(Backups, "backups"),
            managed(Cache, "cache"),
            managed(DownloadStaging, "staging"),
            managed(ManagedModels, "managed/models"),
            LocationEntry { kind: ExternalRuntime, owner: LocationOwner::ExternalReadOnly,
                            relative: None, move_allowed: false },
        ],
    }
}

fn check_regular_directory(path: &Path) -> Result<(), LocationFault> {
    let metadata = fs::symlink_metadata(path).map_err(|_| LocationFault::InvalidRoot)?;
    if !metadata.is_dir() || metadata.file_type().is_symlink() {
        return Err(LocationFault::InvalidRoot);
    }
    Ok(())
}

fn safe_relative(relative: &str) -> bool {
    let path = Path::new(relative);
    !relative.is_empty() && !path.is_absolute()
        && path.components().all(|c| matches!(c, Component::Normal(_)))
}

impl NativeLocationRegistry {
    pub(crate) fn open(os_local: &Path, app_root: &Path) -> Result<Self, LocationFault> {
        if !os_local.is_absolute() || app_root != os_local.join(APP_ID) {
            return Err(LocationFault::InvalidRoot);
        }
        check_regular_directory(os_local)?;
        check_regular_directory(app_root)?;
        let expected = expected();
        if expected.locations.iter().any(|entry|
            entry.relative.as_ref().is_some_and(|r| !safe_relative(r))) {
            return Err(LocationFault::InvalidRoot);
        }
        let path = app_root.join("storage-locations-v1.json");
        match fs::symlink_metadata(&path) {
            Ok(meta) => {
                if !meta.is_file() || meta.file_type().is_symlink()
                    || meta.len() > MAX_MANIFEST_BYTES {
                    return Err(LocationFault::CorruptManifest);
                }
                let bytes = fs::read(&path).map_err(|_| LocationFault::StorageUnavailable)?;
                let stored: LocationManifest = serde_json::from_slice(&bytes)
                    .map_err(|_| LocationFault::CorruptManifest)?;
                if stored != expected { return Err(LocationFault::CorruptManifest); }
            }
            Err(err) if err.kind() == std::io::ErrorKind::NotFound => {
                // New-only write: never replace an existing user's config file.
                let bytes = serde_json::to_vec(&expected)
                    .map_err(|_| LocationFault::StorageUnavailable)?;
                if bytes.len() as u64 > MAX_MANIFEST_BYTES {
                    return Err(LocationFault::StorageUnavailable);
                }
                let mut opts = OpenOptions::new();
                opts.write(true).create_new(true);
                #[cfg(unix)]
                {
                    use std::os::unix::fs::OpenOptionsExt;
                    opts.mode(0o600);
                }
                let mut file = opts.open(&path).map_err(|_| LocationFault::StorageUnavailable)?;
                file.write_all(&bytes).map_err(|_| LocationFault::StorageUnavailable)?;
                file.sync_all().map_err(|_| LocationFault::StorageUnavailable)?;
            }
            Err(_) => return Err(LocationFault::StorageUnavailable),
        }
        Ok(Self { app_root: app_root.to_path_buf(), manifest: expected })
    }

    pub(crate) fn resolve(&self, kind: LocationKind) -> Result<Option<PathBuf>, LocationFault> {
        let entry = self.manifest.locations.iter().find(|item| item.kind == kind)
            .ok_or(LocationFault::Denied)?;
        if entry.owner == LocationOwner::ExternalReadOnly {
            return Ok(None);
        }
        match entry.relative.as_deref() {
            Some(relative) if safe_relative(relative) =>
                Ok(Some(self.app_root.join(relative))),
            _ => Err(LocationFault::CorruptManifest),
        }
    }

    pub(crate) fn move_existing(&self, _kind: LocationKind, _target: &Path)
        -> Result<(), LocationFault> {
        // Movement needs inventory -> quiesce -> stage -> hash -> activate -> rollback.
        // No owner-grant, backend health probe, or verified migration yet.
        Err(LocationFault::Denied)
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
            let stamp = SystemTime::now().duration_since(UNIX_EPOCH).unwrap().as_nanos();
            let seq = NEXT_FIXTURE_ID.fetch_add(1, std::sync::atomic::Ordering::Relaxed);
            let root = std::env::temp_dir()
                .join(format!("zynoa-registry-{}-{stamp}-{seq}", std::process::id()));
            fs::create_dir(&root).unwrap();
            Self(root)
        }
        fn app(&self) -> PathBuf {
            let app = self.0.join(APP_ID);
            fs::create_dir(&app).unwrap();
            app
        }
    }
    impl Drop for Fixture { fn drop(&mut self) { let _ = fs::remove_dir_all(&self.0); } }

    #[test]
    fn real_registry_persists_relative_defaults_without_user_paths() {
        let fixture = Fixture::new();
        let app = fixture.app();
        let first = NativeLocationRegistry::open(&fixture.0, &app).unwrap();
        assert_eq!(first.resolve(LocationKind::UserVault).unwrap(), Some(app.join("data")));
        assert_eq!(first.resolve(LocationKind::Diagnostics).unwrap(), Some(app.join("diagnostics")));
        assert_eq!(first.resolve(LocationKind::Backups).unwrap(), Some(app.join("backups")));
        assert_eq!(first.resolve(LocationKind::ExternalRuntime).unwrap(), None);
        let raw = fs::read_to_string(app.join("storage-locations-v1.json")).unwrap();
        assert!(!raw.contains(&fixture.0.to_string_lossy().to_string()));
        assert!(raw.contains("external_read_only"));
        let second = NativeLocationRegistry::open(&fixture.0, &app).unwrap();
        assert_eq!(second.resolve(LocationKind::Cache).unwrap(), Some(app.join("cache")));
        assert!(!app.join("cache").exists(), "listing a storage class must not create it");
    }

    #[test]
    fn malformed_or_modified_registry_is_never_deleted_or_repaired_silently() {
        let f = Fixture::new();
        let app = f.app();
        let file = app.join("storage-locations-v1.json");
        fs::write(&file, b"{DO_NOT_DELETE").unwrap();
        assert!(matches!(NativeLocationRegistry::open(&f.0, &app),
                         Err(LocationFault::CorruptManifest)));
        assert_eq!(fs::read(&file).unwrap(), b"{DO_NOT_DELETE");
        let mut tampered = serde_json::to_value(expected()).unwrap();
        tampered["schema_version"] = serde_json::json!(99);
        fs::write(&file, serde_json::to_vec(&tampered).unwrap()).unwrap();
        assert!(matches!(NativeLocationRegistry::open(&f.0, &app),
                         Err(LocationFault::CorruptManifest)));
        assert_eq!(fs::read(&file).unwrap(), serde_json::to_vec(&tampered).unwrap());
    }

    #[test]
    fn external_runtime_is_never_moved_and_file_is_not_touched() {
        let f = Fixture::new();
        let app = f.app();
        let registry = NativeLocationRegistry::open(&f.0, &app).unwrap();
        let external = f.0.join("owned-by-other-tool.bin");
        fs::write(&external, b"OTHER_APP_DATA").unwrap();
        assert_eq!(registry.move_existing(LocationKind::ExternalRuntime, &external),
                   Err(LocationFault::Denied));
        assert_eq!(registry.move_existing(LocationKind::UserVault, &external),
                   Err(LocationFault::Denied));
        assert_eq!(fs::read(external).unwrap(), b"OTHER_APP_DATA");
    }

    #[test]
    fn unsupported_root_paths_and_traversal_are_denied() {
        let f = Fixture::new();
        f.app();
        assert!(matches!(NativeLocationRegistry::open(&f.0, &f.0.join("wrong.app")),
                         Err(LocationFault::InvalidRoot)));
        assert!(!safe_relative("../outside"));
        assert!(!safe_relative("/root"));
        assert!(!safe_relative("a/../b"));
    }

    #[cfg(unix)]
    #[test]
    fn symlinked_manifest_cannot_redirect_registry() {
        let f = Fixture::new();
        let app = f.app();
        let target = f.0.join("precious.txt");
        fs::write(&target, b"UNTOUCHED").unwrap();
        std::os::unix::fs::symlink(&target, app.join("storage-locations-v1.json")).unwrap();
        assert!(matches!(NativeLocationRegistry::open(&f.0, &app),
                         Err(LocationFault::CorruptManifest)));
        assert_eq!(fs::read(target).unwrap(), b"UNTOUCHED");
    }
}
