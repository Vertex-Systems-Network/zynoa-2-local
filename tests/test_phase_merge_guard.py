"""Fail-closed merge executor tests. ALL tests are mocked; zero real merges."""
import unittest
from tools.phase_merge_guard import GuardedMerger, MergeBlocked

SHA = "a" * 40
MAIN = "b" * 40
MERGED_SHA = "c" * 40
STATE = {
    "phase": "P00",
    "phase_status": "IN_PROGRESS",
    "active_branch": "phase/00-governance",
    "primary_pr": 1,
}
ELIGIBLE = {
    "authenticated_remote": True,
    "phase": "P00",
    "head_branch": "phase/00-governance",
    "pr_number": 1,
    "base_branch": "main",
    "pr_head_sha": SHA,
    "base_sha": MAIN,
    "main_sha": MAIN,
    "merged": False,
    "draft": False,
    "pr_state": "open",
    "mergeable": True,
    "checks_passed": True,
    "workflow_provenance_verified": True,
    "workflow_source_verified": True,
    "blocker_policy_complete": True,
    "branch_protected": True,
    "rules_policy_verified": True,
    "auto_merge_available": True,
    "open_critical_blockers": 0,
}

class FakeReader:
    repo = "Vertex-Systems-Network/zynoa-2-local"
    def __init__(self):
        self.current = dict(ELIGIBLE)
        self.main_sha = MAIN
        self.calls = 0
    def observe(self, state):
        self.calls += 1
        return dict(self.current)
    def branch(self, branch):
        assert branch == "main"
        return {"commit": {"sha": self.main_sha}}

class FakeMerge:
    def __init__(self, reader):
        self.calls = []
        self.reader = reader
        self.fail = False
    def __call__(self, url, token, payload):
        self.calls.append((url, token, payload))
        if self.fail:
            return {"merged": False}
        self.reader.current.update({
            "merged": True, "merge_sha": MERGED_SHA,
            "main_matches_merge": True,
        })
        self.reader.main_sha = MERGED_SHA
        return {"merged": True, "sha": MERGED_SHA}

class GuardedMergeTests(unittest.TestCase):
    def build(self, enabled=True):
        reader = FakeReader()
        transport = FakeMerge(reader)
        merger = GuardedMerger(reader, write_token="fake-scoped-token",
                             enabled=enabled, transport=transport)
        return merger, reader, transport

    def test_verified_merge_requires_exact_remote_readback(self):
        merger, reader, transport = self.build()
        result = merger.merge_current(STATE)
        self.assertTrue(result["merge_api_accepted"])
        self.assertTrue(result["remote_merge_verified"])
        self.assertFalse(result["next_phase_started"])
        self.assertEqual(1, len(transport.calls))
        self.assertEqual(SHA, transport.calls[0][2]["sha"])

    def test_disabled_identity_cannot_merge(self):
        merger, _, transport = self.build(enabled=False)
        with self.assertRaises(MergeBlocked):
            merger.merge_current(STATE)
        self.assertFalse(transport.calls)

    def test_draft_rejected(self):
        merger, reader, transport = self.build()
        reader.current["draft"] = True
        with self.assertRaises(MergeBlocked):
            merger.merge_current(STATE)
        self.assertFalse(transport.calls)

    def test_unprotected_main_rejected(self):
        merger, reader, transport = self.build()
        reader.current["branch_protected"] = False
        with self.assertRaises(MergeBlocked):
            merger.merge_current(STATE)
        self.assertFalse(transport.calls)

    def test_protection_without_verified_required_policy_rejected(self):
        merger, reader, transport = self.build()
        reader.current["rules_policy_verified"] = False
        with self.assertRaises(MergeBlocked):
            merger.merge_current(STATE)
        self.assertFalse(transport.calls)

    def test_unmerged_failing_checks_rejected(self):
        merger, reader, transport = self.build()
        reader.current["checks_passed"] = False
        with self.assertRaises(MergeBlocked):
            merger.merge_current(STATE)
        self.assertFalse(transport.calls)

    def test_open_critical_issue_rejected(self):
        merger, reader, transport = self.build()
        reader.current["open_critical_blockers"] = 1
        with self.assertRaises(MergeBlocked):
            merger.merge_current(STATE)
        self.assertFalse(transport.calls)

    def test_independent_blocker_scope_must_be_explicitly_complete(self):
        for missing in (False, None):
            merger, reader, transport = self.build()
            reader.current["blocker_policy_complete"] = missing
            with self.subTest(value=missing), self.assertRaises(MergeBlocked):
                merger.merge_current(STATE)
            self.assertFalse(transport.calls)
        merger, reader, transport = self.build()
        del reader.current["blocker_policy_complete"]
        with self.assertRaises(MergeBlocked):
            merger.merge_current(STATE)
        self.assertFalse(transport.calls)

    def test_critical_blocker_count_must_be_exact_zero_integer(self):
        for malformed in (None, False, True, "0", [], -1):
            merger, reader, transport = self.build()
            reader.current["open_critical_blockers"] = malformed
            with self.subTest(value=malformed), self.assertRaises(MergeBlocked):
                merger.merge_current(STATE)
            self.assertFalse(transport.calls)

    def test_checked_workflow_must_match_main_workflow_source(self):
        merger, reader, transport = self.build()
        reader.current["workflow_source_verified"] = False
        with self.assertRaises(MergeBlocked):
            merger.merge_current(STATE)
        self.assertFalse(transport.calls)

    def test_workflow_changed_during_second_preflight_blocks_merge(self):
        merger, reader, transport = self.build()
        base_observe = reader.observe
        def workflow_changed(state):
            snapshot = base_observe(state)
            if reader.calls == 2:
                snapshot["workflow_source_verified"] = False
            return snapshot
        reader.observe = workflow_changed
        with self.assertRaises(MergeBlocked):
            merger.merge_current(STATE)
        self.assertFalse(transport.calls)

    def test_verified_workflow_provenance_required_even_if_check_says_pass(self):
        for bad in (False, None):
            merger, reader, transport = self.build()
            reader.current["workflow_provenance_verified"] = bad
            with self.subTest(value=bad), self.assertRaises(MergeBlocked):
                merger.merge_current(STATE)
            self.assertFalse(transport.calls)

    def test_base_mismatch_rejected(self):
        merger, reader, transport = self.build()
        reader.current["base_sha"] = "0" * 40
        with self.assertRaises(MergeBlocked):
            merger.merge_current(STATE)
        self.assertFalse(transport.calls)

    def test_main_advances_while_preparing_merge(self):
        merger, reader, transport = self.build()
        reader.main_sha = "0" * 40
        with self.assertRaises(MergeBlocked):
            merger.merge_current(STATE)
        self.assertFalse(transport.calls)

    def test_reobserve_blocks_pr_and_policy_changes_without_remote_merge(self):
        for name, key, value in (
            ("PR became draft", "draft", True),
            ("new critical blocker", "open_critical_blockers", 1),
            ("issue triage invalidated", "blocker_policy_complete", False),
            ("CI invalidated", "checks_passed", False),
            ("trusted workflow lost", "workflow_provenance_verified", False),
            ("ruleset relaxed", "rules_policy_verified", False),
            ("PR SHA advanced", "pr_head_sha", "d" * 40),
            ("base advanced", "base_sha", "d" * 40),
        ):
            merger, reader, transport = self.build()
            initial_observe = reader.observe
            def changed_on_second(state):
                observed = initial_observe(state)
                if reader.calls == 2:
                    observed[key] = value
                return observed
            reader.observe = changed_on_second
            with self.subTest(name=name), self.assertRaises(MergeBlocked):
                merger.merge_current(STATE)
            self.assertFalse(transport.calls)

    def test_p01_issue_label_fingerprint_missing_or_changed_blocks_merge(self):
        phase = {**STATE, "phase": "P01"}
        for scenario in ("missing", "changed"):
            merger, reader, transport = self.build()
            reader.current["phase"] = "P01"
            reader.current["issue_inventory_fingerprint"] = "a" * 64
            if scenario == "missing":
                reader.current["issue_inventory_fingerprint"] = None
            else:
                prior = reader.observe
                def relabel_after_first(state):
                    observed = prior(state)
                    if reader.calls == 2:
                        observed["issue_inventory_fingerprint"] = "b" * 64
                    return observed
                reader.observe = relabel_after_first
            with self.subTest(scenario=scenario), self.assertRaises(MergeBlocked):
                merger.merge_current(phase)
            self.assertFalse(transport.calls)

    def test_stable_premerge_observes_twice_before_single_mock_merge(self):
        merger, reader, transport = self.build()
        merger.merge_current(STATE)
        self.assertEqual(3, reader.calls)  # twice premerge, once postmerge
        self.assertEqual(1, len(transport.calls))

    def test_no_authenticated_evidence_rejected(self):
        merger, reader, transport = self.build()
        reader.current["authenticated_remote"] = False
        with self.assertRaises(MergeBlocked):
            merger.merge_current(STATE)
        self.assertFalse(transport.calls)

    def test_invalid_merge_response_never_claims_verified(self):
        merger, reader, transport = self.build()
        transport.fail = True
        with self.assertRaises(MergeBlocked):
            merger.merge_current(STATE)

    def test_remote_postcheck_mismatch_not_marked_verified(self):
        merger, reader, transport = self.build()
        def false_postcheck(url, token, payload):
            transport.calls.append((url, token, payload))
            reader.current.update({
                "merged": True, "merge_sha": "d" * 40,
                "main_matches_merge": False,
            })
            return {"merged": True, "sha": MERGED_SHA}
        merger.transport = false_postcheck
        out = merger.merge_current(STATE)
        self.assertTrue(out["merge_api_accepted"])
        self.assertFalse(out["remote_merge_verified"])


if __name__ == "__main__":
    unittest.main()
