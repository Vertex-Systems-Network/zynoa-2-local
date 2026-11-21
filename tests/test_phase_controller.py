"""P00 phase controller unit and recovery policy tests."""
from pathlib import Path
import sys
import tempfile
import unittest

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))
from tools.phase_controller import (
    EventJournal, PHASE_ORDER, PhasePolicyError, authorize_next_phase,
    next_phase, validate_snapshot,
)

SHA = "f" * 40


def fixture(phase="P08", status="MERGED_VERIFIED"):
    return {
        "schema_version": 3,
        "phase": phase,
        "phase_status": status,
        "active_branch": "phase/08-native-designer" if phase == "P08" else "phase/00-governance",
        "primary_pr": 22,
        "last_verified_remote_sha": SHA,
        "worker_running": False,
    }


def remote(branch="phase/08-native-designer"):
    return {
        "authenticated_remote": True,
        "merged": True,
        "checks_passed": True,
        "head_branch": branch,
        "pr_number": 22,
        "base_branch": "main",
        "merge_sha": SHA,
        "open_critical_blockers": 0,
    }


class PhaseControllerPolicyTests(unittest.TestCase):
    def test_stage_order_places_interoperability_after_core(self):
        self.assertEqual("P08I", next_phase("P08"))
        self.assertEqual("P09", next_phase("P08I"))
        self.assertEqual("P01", next_phase("P00"))

    def test_verified_core_allows_interoperability(self):
        self.assertTrue(authorize_next_phase(fixture(), "P08I", remote()))

    def test_p08_not_merged_disallows_interoperability(self):
        with self.assertRaises(PhasePolicyError):
            authorize_next_phase(fixture(status="IN_PROGRESS"), "P08I", remote())

    def test_untrusted_remote_flag_rejected(self):
        e = remote()
        e["authenticated_remote"] = False
        with self.assertRaises(PhasePolicyError):
            authorize_next_phase(fixture(), "P08I", e)

    def test_wrong_branch_rejected(self):
        with self.assertRaises(PhasePolicyError):
            authorize_next_phase(fixture(), "P08I", remote(branch="phase/00-governance"))

    def test_early_phase_jump_rejected(self):
        with self.assertRaises(PhasePolicyError):
            authorize_next_phase(fixture(), "P09", remote())

    def test_unresolved_critical_issue_blocks(self):
        e = remote()
        e["open_critical_blockers"] = 1
        with self.assertRaises(PhasePolicyError):
            authorize_next_phase(fixture(), "P08I", e)

    def test_bad_sha_blocks(self):
        e = remote()
        e["merge_sha"] = "a" * 40
        with self.assertRaises(PhasePolicyError):
            authorize_next_phase(fixture(), "P08I", e)

    def test_phase_branch_and_pr_policy(self):
        p = fixture("P08I")
        p["active_branch"] = "phase/08-core"
        self.assertTrue(any("P08I" in error for error in validate_snapshot(p)))

    def test_working_snapshot_has_no_worker_claim(self):
        p = fixture()
        self.assertEqual([], validate_snapshot(p))
        p["worker_running"] = True
        self.assertTrue(validate_snapshot(p))


class PhaseJournalTests(unittest.TestCase):
    def test_idempotent_append_and_restart(self):
        with tempfile.TemporaryDirectory() as temp:
            file = Path(temp) / "state" / "events.db"
            store = EventJournal(file)
            self.assertTrue(store.append("evt-1", "P00", "started", {"kind": "safe"}))
            self.assertFalse(store.append("evt-1", "P00", "started", {"kind": "safe"}))
            self.assertEqual(1, EventJournal(file).count())

    def test_invalid_phase_rejected(self):
        with tempfile.TemporaryDirectory() as temp:
            store = EventJournal(Path(temp) / "events.db")
            with self.assertRaises(PhasePolicyError):
                store.append("evt-1", "P999", "started")


if __name__ == "__main__":
    unittest.main()
