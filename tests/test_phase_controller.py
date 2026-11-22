"""P00 phase controller unit and recovery policy tests."""
from pathlib import Path
import sys
import tempfile
import unittest

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))
from tools.phase_controller import (
    EventJournal, PHASE_ORDER, PhasePolicyError, authorize_next_phase,
    next_phase, runner_job_plan, validate_snapshot,
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
        "blocker_policy_complete": True,
        "issue_scope_source": "authenticated_github_open_issue_labels",
        "issue_inventory_fingerprint": "a" * 64,
        "unclassified_issue_numbers": [],
        "blocker_issue_numbers": [],
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

    def test_critical_blocker_count_must_be_exact_integer_zero(self):
        # bool False and 0.0 previously passed Python's == 0 comparison.
        for invalid in (False, True, 0.0, "0", None, [], {}):
            with self.subTest(invalid=invalid), self.assertRaises(PhasePolicyError):
                evidence = remote()
                evidence["open_critical_blockers"] = invalid
                authorize_next_phase(fixture(), "P08I", evidence)
        evidence = remote()
        del evidence["open_critical_blockers"]
        with self.assertRaises(PhasePolicyError):
            authorize_next_phase(fixture(), "P08I", evidence)

    def test_remote_authentication_and_pr_types_are_exact(self):
        for field in ("authenticated_remote", "merged", "checks_passed"):
            for invalid in (1, "true", [], None):
                with self.subTest(field=field, invalid=invalid):
                    evidence = remote()
                    evidence[field] = invalid
                    with self.assertRaises(PhasePolicyError):
                        authorize_next_phase(fixture(), "P08I", evidence)
        evidence = remote()
        evidence["pr_number"] = "22"
        with self.assertRaises(PhasePolicyError):
            authorize_next_phase(fixture(), "P08I", evidence)

    def test_post_p00_transition_requires_complete_gitHub_issue_inventory(self):
        scenarios = (
            ("incomplete", "blocker_policy_complete", False),
            ("missing policy", "blocker_policy_complete", None),
            ("forged scope", "issue_scope_source", "user_supplied_zero"),
            ("missing scope", "issue_scope_source", None),
            ("invalid fingerprint", "issue_inventory_fingerprint", "0" * 63),
            ("missing fingerprint", "issue_inventory_fingerprint", None),
            ("unclassified issue", "unclassified_issue_numbers", [7]),
            ("unclassified bool", "unclassified_issue_numbers", False),
            ("blocking issue", "blocker_issue_numbers", [3]),
            ("blocking list spoof", "blocker_issue_numbers", 0),
        )
        for name, key, invalid in scenarios:
            with self.subTest(scenario=name):
                evidence = remote()
                evidence[key] = invalid
                with self.assertRaises(PhasePolicyError):
                    authorize_next_phase(fixture(), "P08I", evidence)
        for key in ("blocker_policy_complete", "issue_scope_source",
                    "issue_inventory_fingerprint", "unclassified_issue_numbers",
                    "blocker_issue_numbers"):
            with self.subTest(missing=key):
                evidence = remote()
                del evidence[key]
                with self.assertRaises(PhasePolicyError):
                    authorize_next_phase(fixture(), "P08I", evidence)

    def test_p00_legacy_transition_still_requires_a_real_zero(self):
        self.assertTrue(authorize_next_phase(
            fixture("P00"), "P01", remote(branch="phase/00-governance")))
        evidence = remote(branch="phase/00-governance")
        evidence["open_critical_blockers"] = False
        with self.assertRaises(PhasePolicyError):
            authorize_next_phase(fixture("P00"), "P01", evidence)

    def test_bad_sha_blocks(self):
        e = remote()
        e["merge_sha"] = "a" * 40
        with self.assertRaises(PhasePolicyError):
            authorize_next_phase(fixture(), "P08I", e)

    def test_phase_branch_and_pr_policy(self):
        p = fixture("P08I")
        p["active_branch"] = "phase/08-core"
        self.assertTrue(any("P08I" in error for error in validate_snapshot(p)))

    def test_active_phase_branch_prefix_is_enforced(self):
        for phase, branch in (
            ("P01", "phase/00-governance"),
            ("P01", "phase/02-ui"),
            ("P00", "phase/01-foundation"),
            ("P08", "phase/08i-design-interoperability"),
        ):
            with self.subTest(phase=phase, branch=branch):
                snapshot = fixture(phase)
                snapshot["active_branch"] = branch
                self.assertIn("active branch does not match active phase", validate_snapshot(snapshot))

    def test_p01_foundation_snapshot_is_accepted(self):
        snapshot = fixture("P01", status="IN_PROGRESS")
        snapshot["active_branch"] = "phase/01-foundation"
        snapshot["primary_pr"] = 10
        self.assertEqual([], validate_snapshot(snapshot))


    def test_p01_runner_never_inherits_p00_model_execution(self):
        state = fixture("P01", status="IN_PROGRESS")
        state.update(active_branch="phase/01-foundation", primary_pr=10)
        for changed in (
            ["scripts/runner_worker.py"],
            [".github/workflows/p00-runner-worker.yml"],
            ["tools/phase_worker.py"],
            ["tools/phase_controller.py", "scripts/runner_worker.py"],
        ):
            with self.subTest(changed=changed):
                plan = runner_job_plan(
                    state, changed, event="pull_request",
                    head_branch="phase/01-foundation", pr_number=10,
                )
                self.assertFalse(plan["p00_fixture"])
                self.assertEqual(
                    bool(set(changed) & {
                        ".github/workflows/p00-runner-worker.yml",
                        "tools/phase_worker.py", "tools/phase_controller.py",
                    }), plan["phase_observer"],
                )
        self.assertEqual(
            {"p00_fixture": False, "phase_observer": True},
            runner_job_plan(state, [], event="workflow_dispatch",
                            head_branch="phase/01-foundation"),
        )
        self.assertEqual(
            {"p00_fixture": False, "phase_observer": False},
            runner_job_plan(state, ["docs/state/HANDOFF.md"], event="pull_request",
                            head_branch="phase/01-foundation", pr_number=10),
        )

    def test_p00_fixture_runner_remains_p00_only(self):
        state = fixture("P00", status="IN_PROGRESS")
        self.assertEqual(
            {"p00_fixture": True, "phase_observer": False},
            runner_job_plan(state, ["scripts/runner_worker.py"], event="pull_request",
                            head_branch="phase/00-governance", pr_number=22),
        )
        self.assertEqual(
            {"p00_fixture": False, "phase_observer": False},
            runner_job_plan(state, ["docs/state/HANDOFF.md"], event="pull_request",
                            head_branch="phase/00-governance", pr_number=22),
        )

    def test_runner_denies_spoofed_phase_pr_event_and_dispatch(self):
        valid = fixture("P01", status="IN_PROGRESS")
        valid.update(active_branch="phase/01-foundation", primary_pr=10)
        cases = (
            (dict(valid, phase="P00"), "pull_request", "phase/01-foundation", 10),
            (dict(valid), "pull_request", "phase/00-governance", 10),
            (dict(valid), "pull_request", "phase/01-foundation", 1),
            (dict(valid), "pull_request", "phase/01-foundation", None),
            (dict(valid), "push", "phase/01-foundation", 10),
            (dict(valid, phase_status="MERGED_VERIFIED"), "pull_request", "phase/01-foundation", 10),
            (dict(valid), "workflow_dispatch", "main", None),
        )
        for snapshot, event, branch, pr in cases:
            with self.subTest(event=event, branch=branch, phase=snapshot["phase"]):
                with self.assertRaises(PhasePolicyError):
                    runner_job_plan(snapshot, ["tools/phase_worker.py"],
                                    event=event, head_branch=branch, pr_number=pr)

    def test_runner_rejects_invalid_path_list(self):
        state = fixture("P01", status="IN_PROGRESS")
        state.update(active_branch="phase/01-foundation", primary_pr=10)
        for bad in (None, "tools/phase_worker.py", [None], [""], ["x\0evil"]):
            with self.subTest(bad=bad), self.assertRaises(PhasePolicyError):
                runner_job_plan(state, bad, event="pull_request",
                                head_branch="phase/01-foundation", pr_number=10)

    def test_verified_closeout_workflow_disables_workers_only_on_exact_ref(self):
        content = (ROOT / ".github/workflows/p00-runner-worker.yml").read_text(
            encoding="utf-8")
        self.assertIn('state.get("phase_status") == "MERGED_VERIFIED"', content)
        self.assertIn('branch == f"phase/{state[\'phase\'][1:].lower()}-closeout"', content)
        self.assertIn('and state.get("lease_holder") is None', content)
        self.assertIn('and state.get("worker_running") is False', content)
        self.assertIn('plan = {"p00_fixture": False, "phase_observer": False}', content)
        self.assertIn('raise PhasePolicyError("untrusted verified-phase runner event")', content)

    def test_runner_workflow_never_executes_p00_fixture_for_p01(self):
        content = (ROOT / ".github/workflows/p00-runner-worker.yml").read_text(
            encoding="utf-8"
        )
        self.assertIn("runner_job_plan(", content)
        self.assertIn("needs.changes.outputs.p00_fixture == 'true'", content)
        self.assertIn("needs.changes.outputs.phase_observer == 'true'", content)
        self.assertIn("python -m tools.phase_worker --once", content)
        self.assertIn("needs.worker.result == 'success'", content)

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

    @staticmethod
    def trusted_transition_evidence():
        return {
            **remote(),
            "main_matches_merge": True,
            "branch_protected": True,
            "rules_policy_verified": True,
            "workflow_provenance_verified": True,
            "workflow_source_verified": True,
        }

    def test_verified_transition_persists_and_replays_without_duplicates(self):
        with tempfile.TemporaryDirectory() as temp:
            path = Path(temp) / "state" / "events.db"
            state, proof = fixture(), self.trusted_transition_evidence()
            first = EventJournal(path).record_verified_transition(state, "P08I", proof)
            self.assertTrue(first["created"])
            self.assertTrue(first["readback_verified"])
            self.assertFalse(first["external_checkpoint_published"])
            self.assertFalse(first["next_phase_started"])
            self.assertEqual(1, EventJournal(path).count())
            again = EventJournal(path).record_verified_transition(state, "P08I", proof)
            self.assertFalse(again["created"])
            self.assertEqual(first["event_id"], again["event_id"])
            self.assertEqual(1, EventJournal(path).count())

    def test_transition_evidence_missing_or_spoofed_cannot_write(self):
        with tempfile.TemporaryDirectory() as temp:
            store = EventJournal(Path(temp) / "state.db")
            for flag in ("main_matches_merge", "branch_protected",
                         "rules_policy_verified", "workflow_provenance_verified",
                         "workflow_source_verified"):
                for invalid in (None, False, 1, "true"):
                    with self.subTest(flag=flag, invalid=invalid):
                        proof = self.trusted_transition_evidence()
                        proof[flag] = invalid
                        with self.assertRaises(PhasePolicyError):
                            store.record_verified_transition(fixture(), "P08I", proof)
            self.assertEqual(0, store.count())

    def test_transition_source_policy_missing_inventory_and_merge_fail_closed(self):
        with tempfile.TemporaryDirectory() as temp:
            store = EventJournal(Path(temp) / "state.db")
            cases = (
                (fixture(status="IN_PROGRESS"), self.trusted_transition_evidence()),
                (fixture(), {**self.trusted_transition_evidence(),
                             "open_critical_blockers": False}),
                (fixture(), {**self.trusted_transition_evidence(),
                             "blocker_policy_complete": False}),
                (fixture(), {**self.trusted_transition_evidence(),
                             "unclassified_issue_numbers": [7]}),
                (fixture(), {**self.trusted_transition_evidence(),
                             "merge_sha": "a" * 40}),
            )
            for state, proof in cases:
                with self.subTest(proof=proof), self.assertRaises(PhasePolicyError):
                    store.record_verified_transition(state, "P08I", proof)
            self.assertEqual(0, store.count())

    def test_transition_collision_is_not_silently_treated_as_idempotence(self):
        with tempfile.TemporaryDirectory() as temp:
            store = EventJournal(Path(temp) / "state.db")
            event_id = "verified-transition:P08:P08I:" + SHA
            self.assertTrue(store.append(
                event_id, "P08", "phase_transition_verified", {"forged": True}))
            with self.assertRaises(PhasePolicyError):
                store.record_verified_transition(
                    fixture(), "P08I", self.trusted_transition_evidence())
            self.assertEqual(1, EventJournal(Path(temp) / "state.db").count())

    def test_transition_p00_legacy_path_requires_protection_and_readback(self):
        with tempfile.TemporaryDirectory() as temp:
            store = EventJournal(Path(temp) / "state.db")
            evidence = self.trusted_transition_evidence()
            evidence["head_branch"] = "phase/00-governance"
            result = store.record_verified_transition(fixture("P00"), "P01", evidence)
            self.assertTrue(result["readback_verified"])
            self.assertEqual(1, store.count())
            self.assertFalse(result["next_phase_started"])


if __name__ == "__main__":
    unittest.main()
