"""P01-T08 M24 native storage class/ownership policy contracts."""
from pathlib import Path
import unittest

ROOT = Path(__file__).resolve().parents[1]

class NativeLocationRegistryContracts(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.native = (ROOT/"apps/desktop/src-tauri/src/locations.rs").read_text(encoding="utf-8")
        cls.lib = (ROOT/"apps/desktop/src-tauri/src/lib.rs").read_text(encoding="utf-8")
        cls.ipc = (ROOT/"apps/desktop/src-tauri/src/ipc.rs").read_text(encoding="utf-8")
        cls.workflow = (ROOT/".github/workflows/p01-desktop.yml").read_text(encoding="utf-8")

    def test_registered_classes_and_ownership_are_native_only(self):
        for marker in ("UserVault", "Diagnostics", "Backups", "Cache",
                       "DownloadStaging", "ManagedModels", "ExternalRuntime",
                       "ExternalReadOnly", "AppManaged", "schema_version",
                       "deny_unknown_fields", "safe_relative"):
            self.assertIn(marker, self.native)
        self.assertIn("mod locations;", self.lib)
        self.assertNotIn("locations::", self.ipc)
        self.assertNotIn("#[tauri::command]", self.native)

    def test_registered_paths_are_relative_and_read_only_for_external_runtimes(self):
        for marker in (
            'os_local.join(APP_ID)', 'storage-locations-v1.json',
            "create_new(true)", "file.sync_all()", "Err(LocationFault::Denied)",
            "real_registry_persists_relative_defaults_without_user_paths",
            "external_runtime_is_never_moved_and_file_is_not_touched",
            "malformed_or_modified_registry_is_never_deleted_or_repaired_silently",
        ):
            self.assertIn(marker, self.native)
        self.assertIn("NativeLocationRegistry::open(&os_local, &app_local)", self.lib)

    def test_windows_runner_checks_native_storage_registry_on_real_boot(self):
        self.assertIn("tests.test_p01_locations", self.workflow)
        self.assertIn("storage-locations-v1.json", self.workflow)
        self.assertIn("cargo test --lib --release", self.workflow)
        self.assertNotIn("contents: write", self.workflow)

    def test_real_native_readiness_not_just_process_survival(self):
        for marker in (
            "AddSeconds(45)", "Test-Path -LiteralPath $diagnostics",
            "Test-Path -LiteralPath $vault",
            "Test-Path -LiteralPath $registry",
            "Desktop exited before native readiness",
            "ZYN-BOOT-READY: missing native startup outputs",
        ):
            self.assertIn(marker, self.workflow)
        self.assertIn("Verify native boot wrote only allowlisted diagnostic metadata", self.workflow)
        self.assertIn("Verify real native vault outside executable after cold boot", self.workflow)
        self.assertIn("Verify local storage ownership registry after real native boot", self.workflow)

    def test_no_unimplemented_migration_or_privacy_claims(self):
        doc=(ROOT/"docs/operations/P01_LOCATION_REGISTRY.md").read_text(encoding="utf-8")
        self.assertIn("NOT a relocation engine", doc)
        self.assertIn("no silent external-runtime changes", doc)

if __name__=="__main__":
    unittest.main()
