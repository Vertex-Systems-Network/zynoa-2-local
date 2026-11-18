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
