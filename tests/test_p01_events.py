"""P01-T09: strict native-only M26 append-only event ledger contracts."""
from pathlib import Path
import unittest

ROOT=Path(__file__).resolve().parents[1]

class NativeEventLedgerContracts(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.events=(ROOT/"apps/desktop/src-tauri/src/events.rs").read_text(encoding="utf-8")
        cls.lib=(ROOT/"apps/desktop/src-tauri/src/lib.rs").read_text(encoding="utf-8")
        cls.ipc=(ROOT/"apps/desktop/src-tauri/src/ipc.rs").read_text(encoding="utf-8")
        cls.workflow=(ROOT/".github/workflows/p01-desktop.yml").read_text(encoding="utf-8")

    def test_wal_transactional_commit_and_sql_append_only_triggers(self):
        for s in ("journal_mode=WAL","synchronous=FULL","TransactionBehavior::Immediate",
                  "tx.commit()","audit_events_no_update","audit_events_no_delete",
                  "UNIQUE(stream_id,sequence)","idempotency_key TEXT NOT NULL UNIQUE"):
            self.assertIn(s,self.events)

    def test_native_only_with_no_freeform_content_or_release_claims(self):
        self.assertIn("mod events;",self.lib)
        self.assertIn("events::NativeEventLedger::open(&app_local)",self.lib)
        self.assertNotIn("events::",self.ipc)
        self.assertNotIn("#[tauri::command]",self.events)
        self.assertNotIn("reqwest",self.events)
        self.assertNotIn("payload TEXT",self.events)
        self.assertNotIn("ReleasePublished",self.events)
        self.assertIn("generate_handler![ipc::workspace_handshake, chat_ipc::chat_request]",self.lib)

    def test_concurrent_first_open_serializes_schema_without_disabling_wal(self):
        self.assertIn("static OPEN_INIT_LOCK: Mutex<()>", self.events)
        self.assertIn("OPEN_INIT_LOCK.lock()", self.events)
        self.assertIn("simultaneous_first_openers_preserve_every_event_and_stream_sequence", self.events)
        self.assertIn("Barrier::new(WRITERS)", self.events)

    def test_real_rust_tests_cover_replay_privacy_conflict_concurrency(self):
        for s in ("durable_append_replay_and_no_duplicate_acknowledgement",
                  "sql_history_is_physically_append_only_and_scope_limited",
                  "concurrent_wal_writers_get_distinct_monotonic_stream_sequences",
                  "corrupt_schema_and_untrusted_user_payload_are_refused_without_repair"):
            self.assertIn("fn "+s,self.events)
        self.assertIn("cargo test --lib --release",self.workflow)
        self.assertIn("tests.test_p01_events",self.workflow)

    def test_cold_boot_database_is_real_but_unnamed_and_unpublished(self):
        self.assertIn("change-events-v1.sqlite",self.workflow)
        doc=(ROOT/"docs/operations/P01_EVENT_LEDGER.md").read_text(encoding="utf-8")
        self.assertIn("NOT a released changelog",doc)
        self.assertIn("no remote event delivery",doc)

if __name__=="__main__":
    unittest.main()
