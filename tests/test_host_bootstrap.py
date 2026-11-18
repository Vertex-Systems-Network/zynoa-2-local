"""P00 host-storage provisioning, SQLite online backup and restore tests.

All tests operate on explicitly created disposable directories. No GitHub
write, Ollama invocation, real production directory or service registration.
"""
from __future__ import annotations

import copy
import json
import os
import sqlite3
import stat
import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch

from tools.host_bootstrap import (
    HostLayout, HostBootstrapError, _sha256_file,
)
from tools.phase_controller import EventJournal

STATE = {
    "schema_version": 3, "phase": "P00", "phase_status": "IN_PROGRESS",
    "active_branch": "phase/00-governance", "primary_pr": 1,
    "worker_running": False,
}


class HostStorageTests(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        self.addCleanup(self.tmp.cleanup)
        self.base = Path(self.tmp.name).resolve()
        self.checkout = self.base / "trusted-source"
        (self.checkout / "docs" / "state").mkdir(parents=True)
        (self.checkout / "AGENTS.md").write_text("trusted fixture", encoding="utf-8")
        (self.checkout / "docs/state/PHASE.json").write_text(
            json.dumps(STATE), encoding="utf-8",
        )
        self.root = self.base / "data-root"
        self.host = HostLayout(self.checkout, self.root)

    def init(self):
        return self.host.initialize(authorized=True)

    def test_default_authorization_denies_any_host_write(self):
        with self.assertRaises(HostBootstrapError):
            self.host.initialize()
        self.assertFalse(self.root.exists())

    def test_init_creates_new_durable_local_db_without_worker(self):
        result = self.init()
        self.assertEqual("HOST_STORAGE_INITIALIZED", result["result"])
        self.assertEqual("PASS", result["db_integrity"])
        self.assertFalse(result["worker_running_verified"])
        self.assertFalse(result["os_sandbox_verified"])
        self.assertFalse(result["model_usable_verified"])
        self.assertEqual(0, result["github_writes"])
        self.assertTrue(self.host.db.is_file())
        self.assertTrue(self.host.marker.is_file())
        self.assertEqual(
            "HOST_STORAGE_VERIFIED",
            HostLayout(self.checkout, self.root).verify()["result"]
        )
        if os.name == "posix":
            for d in (self.root, self.host.state, self.host.backups):
                self.assertEqual(0, stat.S_IMODE(d.stat().st_mode) & 0o077)
            self.assertEqual(0, stat.S_IMODE(self.host.db.stat().st_mode) & 0o077)

    def test_repeat_initialization_cannot_overwrite_existing_journal(self):
        self.init()
        EventJournal(self.host.db).append("safe-1", "P00", "safe-test", {"status": "ok"})
        with self.assertRaises(HostBootstrapError):
            self.init()
        self.assertEqual(1, self.host.verify()["event_count"])

    def test_backup_and_restore_drill_preserves_event_snapshot(self):
        self.init()
        j = EventJournal(self.host.db)
        for i in range(4):
            j.append("event-" + str(i), "P00", "fixture", {"id": i})
        b = self.host.backup()
        self.assertEqual("BACKUP_VERIFIED", b["result"])
        self.assertEqual("RESTORE_DRILL_PASSED", b["restore_drill"])
        self.assertEqual(64, len(b["sha256"]))
        self.assertFalse(b["worker_running_verified"])
        restore = self.host.verify_backup(b["backup_name"])
        self.assertEqual(4, restore["event_count"])
        self.assertFalse(restore["live_db_overwritten"])
        self.assertEqual(4, self.host.verify()["event_count"])

    def test_backup_is_real_snapshot_not_live_db_alias(self):
        self.init()
        events = EventJournal(self.host.db)
        events.append("first", "P00", "fixture")
        b = self.host.backup()
        events.append("later", "P00", "fixture")
        self.assertEqual(1, self.host.verify_backup(b["backup_name"])["event_count"])
        self.assertEqual(2, self.host.verify()["event_count"])

    def test_backup_corruption_causes_fail_closed_digest_check(self):
        self.init()
        b = self.host.backup()
        path = self.host.backups / b["backup_name"]
        with path.open("r+b") as out:
            out.seek(88)
            out.write(b"CORRUPTED")
        with self.assertRaises(HostBootstrapError):
            self.host.verify_backup(b["backup_name"])
        self.assertEqual("PASS", self.host.verify()["db_integrity"])

    def test_bad_backup_name_never_escapes_host_root(self):
        self.init()
        for name in ("../controller.db", "controller.db", "/tmp/x.sqlite",
                     "controller-20261118T120000Z-aaaaaaaaaaaa.sqlite/..",
                     "controller-20261118T120000Z-bad.sqlite"):
            with self.subTest(name=name), self.assertRaises(HostBootstrapError):
                self.host.verify_backup(name)

    def test_backup_receipt_missing_fails_closed(self):
        self.init()
        b = self.host.backup()
        (self.host.backups / (b["backup_name"] + ".sha256")).unlink()
        with self.assertRaises(HostBootstrapError):
            self.host.verify_backup(b["backup_name"])

    def test_corrupt_phase_metadata_denied_before_init(self):
        altered = copy.deepcopy(STATE)
        altered["phase"] = "P01"
        (self.checkout / "docs/state/PHASE.json").write_text(json.dumps(altered))
        with self.assertRaises(HostBootstrapError):
            HostLayout(self.checkout, self.root)
        self.assertFalse(self.root.exists())

    def test_overlapping_repo_and_host_roots_rejected(self):
        for hostroot in (self.checkout, self.checkout / "subfolder",
                         self.base):
            with self.subTest(root=hostroot), self.assertRaises(HostBootstrapError):
                HostLayout(self.checkout, hostroot)

    def test_relative_or_filesystem_root_rejected(self):
        for hostroot in (Path("relative/data"), Path(self.root.anchor)):
            with self.subTest(hostroot=hostroot), self.assertRaises(HostBootstrapError):
                HostLayout(self.checkout, hostroot)

    def test_linked_host_root_rejected_before_writes(self):
        actual = self.base / "target"
        actual.mkdir()
        link = self.base / "alias"
        try:
            link.symlink_to(actual, target_is_directory=True)
        except (NotImplementedError, OSError):
            self.skipTest("symlink creation not allowed by host")
        with self.assertRaises(HostBootstrapError):
            HostLayout(self.checkout, link)

    def test_missing_or_modified_host_manifest_fails_closed(self):
        self.init()
        self.host.marker.write_text('{"schema":1,"phase":"P00","github_write_capability":true}')
        with self.assertRaises(HostBootstrapError):
            self.host.verify()

    def test_permission_relaxation_detected_on_posix(self):
        if os.name != "posix":
            self.skipTest("mode bits are not Windows ACLs")
        self.init()
        self.host.state.chmod(0o755)
        with self.assertRaises(HostBootstrapError):
            self.host.verify()

    def test_corrupt_sqlite_db_does_not_fake_healthy_backup(self):
        self.init()
        self.host.db.write_bytes(b"invalid SQLite DB")
        with self.assertRaises((HostBootstrapError, sqlite3.DatabaseError)):
            self.host.backup()

    def test_sha256_streaming_matches_stdlib(self):
        import hashlib
        fixture = self.checkout / "AGENTS.md"
        self.assertEqual(hashlib.sha256(fixture.read_bytes()).hexdigest(),
                         _sha256_file(fixture))


if __name__ == "__main__":
    unittest.main()
