"""P01-T07 M23 native-only transactional vault contracts.
Windows GitHub CI executes real WAL/online-backup/disposable-restore Rust tests.
"""
from pathlib import Path
import unittest

ROOT = Path(__file__).resolve().parents[1]


class NativeVaultContractTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.cargo = (ROOT/"apps/desktop/src-tauri/Cargo.toml").read_text(encoding="utf-8")
        cls.vault = (ROOT/"apps/desktop/src-tauri/src/vault.rs").read_text(encoding="utf-8")
        cls.lib = (ROOT/"apps/desktop/src-tauri/src/lib.rs").read_text(encoding="utf-8")
        cls.ci = (ROOT/".github/workflows/p01-desktop.yml").read_text(encoding="utf-8")

    def test_pinned_sqlite_native_dependency_and_ipc_denial(self):
        self.assertIn('rusqlite = { version = "=0.43.0", features = ["bundled", "backup"] }', self.cargo)
        self.assertIn("mod vault;", self.lib)
        self.assertIn("vault::NativeVault::open(&app_local)", self.lib)
        self.assertNotIn("vault::", (ROOT/"apps/desktop/src-tauri/src/ipc.rs").read_text(encoding="utf-8"))
        self.assertIn("generate_handler![ipc::workspace_handshake, chat_ipc::chat_request,", self.lib)
        self.assertNotIn("#[tauri::command]", self.vault)

    def test_no_ack_until_commit_and_no_overwrite(self):
        for marker in ("journal_mode=WAL", "synchronous=FULL", "foreign_keys=ON",
                       "transaction_with_behavior(TransactionBehavior::Immediate)",
                       "tx.commit()", "create_new(true)", "Connection::open_with_flags",
                       "snapshot_new", "restore_to_new_test_profile"):
            self.assertIn(marker, self.vault)

    def test_real_recovery_fixtures_have_correct_failure_protection(self):
        for name in ("transactional_commit_ack_and_reopen_preserve_user_content",
                     "online_wal_snapshot_and_disposable_restore_drill",
                     "malformed_location_and_corrupt_source_preserved_without_repair_overwrite",
                     "rejected_record_does_not_create_false_success_or_data"):
            self.assertIn("fn "+name, self.vault)
        self.assertNotIn("std::fs::copy", self.vault)
        self.assertNotIn("println!", self.vault)
        self.assertNotIn("eprintln!", self.vault)

    def test_app_boot_wires_os_local_native_vault_but_never_exposes_command(self):
        self.assertIn("vault::NativeVault::open(&app_local)", self.lib)
        self.assertIn("app.manage(std::sync::Arc::new(std::sync::Mutex::new(storage)))", self.lib)
        self.assertIn("generate_handler![ipc::workspace_handshake, chat_ipc::chat_request,", self.lib)
        self.assertNotIn("vault::", (ROOT/"apps/desktop/src-tauri/src/ipc.rs").read_text(encoding="utf-8"))
        for marker in ("state.sqlite{suffix}", '"-wal", "-shm", "-journal"',
                       "restore_never_overwrites_a_preexisting_destination",
                       "reserved = OpenOptions::new().write(true).create_new(true)"):
            self.assertIn(marker, self.vault)

    def test_windows_runs_real_vault_tests_and_scope_is_honest(self):
        self.assertIn("tests.test_p01_vault", self.ci)
        self.assertIn("cargo test --lib --release", self.ci)
        doc = (ROOT/"docs/operations/P01_NATIVE_VAULT.md").read_text(encoding="utf-8")
        self.assertIn("NOT connected to the frontend", doc)
        self.assertIn("NOT an encrypted portable backup", doc)


if __name__=="__main__":
    unittest.main()
