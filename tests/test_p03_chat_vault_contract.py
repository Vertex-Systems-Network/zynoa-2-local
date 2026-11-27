"""P03-T02 source contract; real SQLite acceptance remains native Windows Rust tests."""
import unittest
from pathlib import Path
ROOT = Path(__file__).resolve().parents[1]

class ChatVaultContract(unittest.TestCase):
    def setUp(self):
        self.vault = (ROOT/"apps/desktop/src-tauri/src/vault.rs").read_text(encoding="utf-8")
        self.workflow = (ROOT/".github/workflows/p03-native-baseline.yml").read_text(encoding="utf-8")
    def test_additive_native_schema_and_no_ui_grant(self):
        for marker in ("SCHEMA_VERSION: i64 = 4", "ARTIFACT_SCHEMA_VERSION: i64 = 3", "CREATE TABLE tool_review_decisions", "tool_review_schema_migrations", "tool_review_no_update", "tool_review_no_delete", "CHAT_SCHEMA_VERSION: i64 = 2", "CREATE TABLE managed_artifacts", "CREATE TABLE artifact_links", "artifact_schema_migrations", "LEGACY_VERSION: i64 = 1", "CREATE TABLE conversations",
                       "CREATE TABLE messages", "CREATE TABLE schema_migrations", "CREATE TABLE chat_change_journal",
                       "FOREIGN KEY(conversation_id,parent_id) REFERENCES messages(conversation_id,id)",
                       "snapshot_connection_new(app_root, &source, &backup_id)", "apply_v2(&tx, LEGACY_VERSION, Some(&backup_id))",
                       "tx.commit()", "PRAGMA synchronous=FULL", "PRAGMA foreign_keys=ON"):
            self.assertIn(marker,self.vault)
        self.assertNotIn("#[tauri::command]",self.vault)
        self.assertNotIn("vault::",(ROOT/"apps/desktop/src-tauri/src/ipc.rs").read_text(encoding="utf-8"))
    def test_real_windows_gate_and_named_native_tests(self):
        for name in ("fresh_schema_wal_full_fk_and_migration_history","v1_migration_keeps_legacy_bytes_and_verified_backup",
                     "unavailable_backup_preserves_v1_without_migration","failed_ddl_transaction_rolls_back_schema_and_version",
                     "future_or_malformed_schema_is_not_reinitialized","message_ack_reopen_order_and_scoped_history",
                     "rejects_duplicate_invalid_and_cross_thread_without_partial_journal",
                     "injected_journal_failure_rolls_back_message_and_revision","online_snapshot_restore_staged_v2_and_legacy_without_overwrite"):
            self.assertIn("fn p03_"+name,self.vault)
        for marker in ("cargo test --lib --release", "vault::tests::p03_", "9 passed; 0 failed; 0 ignored",
                       "PRAGMA foreign_key_check", "p03-vault-schema-proof.json", "test_log_sha256"):
            self.assertIn(marker,self.workflow)
        self.assertIn("contents: read",self.workflow)
        self.assertNotIn("contents: write",self.workflow)

if __name__=="__main__":
    unittest.main()
