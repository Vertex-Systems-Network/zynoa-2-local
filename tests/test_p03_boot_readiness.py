"""Readiness predicate regression: fixtures are not native acceptance proof."""
from contextlib import closing
from pathlib import Path
import sqlite3
import tempfile
import unittest

from scripts.probe_p03_boot_readiness import ledger_ready


class NativeBootReadinessTests(unittest.TestCase):
    def test_absent_file_is_not_created(self):
        with tempfile.TemporaryDirectory() as root:
            path = Path(root) / "change-events-v1.sqlite"
            self.assertFalse(ledger_ready(path))
            self.assertFalse(path.exists())

    def test_bootstrap_waits_until_schema_transaction_commits(self):
        with tempfile.TemporaryDirectory() as root:
            path = Path(root) / "change-events-v1.sqlite"
            with closing(sqlite3.connect(path)) as db:
                db.execute("PRAGMA journal_mode=WAL")
                self.assertFalse(ledger_ready(path))
                db.executescript(
                    "BEGIN IMMEDIATE;"
                    "CREATE TABLE audit_events(id INTEGER PRIMARY KEY);"
                    "CREATE TRIGGER audit_events_no_update BEFORE UPDATE ON audit_events "
                    "BEGIN SELECT RAISE(ABORT,'immutable'); END;"
                    "CREATE TRIGGER audit_events_no_delete BEFORE DELETE ON audit_events "
                    "BEGIN SELECT RAISE(ABORT,'immutable'); END;"
                    "PRAGMA user_version=1;"
                )
                self.assertFalse(ledger_ready(path))
                db.commit()
                self.assertTrue(ledger_ready(path))
                self.assertEqual(db.execute("SELECT count(*) FROM audit_events").fetchone()[0], 0)

    def test_incomplete_or_wrong_version_schema_is_not_ready(self):
        with tempfile.TemporaryDirectory() as root:
            path = Path(root) / "change-events-v1.sqlite"
            with closing(sqlite3.connect(path)) as db:
                db.executescript(
                    "PRAGMA journal_mode=WAL;"
                    "CREATE TABLE audit_events(id INTEGER PRIMARY KEY);"
                    "PRAGMA user_version=1;"
                )
                self.assertFalse(ledger_ready(path))
                db.executescript(
                    "CREATE TRIGGER audit_events_no_update BEFORE UPDATE ON audit_events "
                    "BEGIN SELECT RAISE(ABORT,'immutable'); END;"
                    "CREATE TRIGGER audit_events_no_delete BEFORE DELETE ON audit_events "
                    "BEGIN SELECT RAISE(ABORT,'immutable'); END;"
                    "PRAGMA user_version=2;"
                )
                self.assertFalse(ledger_ready(path))


if __name__ == "__main__":
    unittest.main()
