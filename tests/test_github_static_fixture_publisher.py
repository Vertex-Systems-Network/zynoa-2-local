"""P00 only-operator static GitHub probe writer: Git Data API mock policy.

No live Github mutation or untrusted Python execution in CI. The separate
manual connector readback is not the same as deployed worker token evidence.
"""
import base64
import hashlib
import json
import unittest

from tools.github_static_fixture_publisher import (
    ProbeWriteDenied, _PROBE_PATH, _PROBE_SOURCE, _SOURCE_SHA,
    _route_allowed, publish_static_fixture,
)

REPO = "Vertex-Systems-Network/zynoa-2-local"
A = "a"*40
C = "c"*40
D = "d"*40
P = "phase/00-governance"


class FakeGit:
    def __init__(self):
        self.calls = []
        self.head = A
        self.current_file = False
        self.draft = True
        self.fail_ref = False
        self.bad_blob = False
        self.bad_parent = False
        self.bad_remote_file = False
        self.stale_second_pr = False
        self.bad_ref_response = False
        self.bad_commit_tree = False
        self.pr_reads = 0
        data = _PROBE_SOURCE.encode("utf-8")
        self.blob_sha = hashlib.sha1(
            b"blob " + str(len(data)).encode("ascii") + b"\x00" + data
        ).hexdigest()

    def __call__(self, method, suffix, token, payload, timeout):
        self.calls.append((method, suffix, payload))
        assert token == "trusted-private-token"
        assert timeout == 10.0
        if method == "GET" and suffix == "/pulls/1":
            self.pr_reads += 1
            sha = self.head
            if self.stale_second_pr and self.pr_reads == 2:
                sha = "b" * 40
            return {
                "number": 1, "state": "open", "draft": self.draft,
                "merged_at": None,
                "head": {"sha": sha, "ref": P, "repo": {"full_name": REPO}},
                "base": {"ref": "main"},
            }
        if method == "GET" and suffix.startswith("/git/commits/"):
            assert suffix.endswith(A) or suffix.endswith(D)
            return {"tree": {"sha": "b"*40 if suffix.endswith(A) else C}}
        if method == "GET" and suffix.startswith("/contents/"):
            if not self.current_file:
                return {"not_found": True}
            source = "WRONG" if self.bad_remote_file else _PROBE_SOURCE
            return {
                "type": "file", "path": _PROBE_PATH,
                "encoding": "base64",
                "content": base64.b64encode(source.encode("utf-8")).decode("ascii"),
            }
        if method == "POST" and suffix == "/git/blobs":
            return {"sha": "f"*40 if self.bad_blob else self.blob_sha}
        if method == "POST" and suffix == "/git/trees":
            return {"sha": C}
        if method == "POST" and suffix == "/git/commits":
            return {
                "sha": D,
                "tree": {"sha": "f"*40 if self.bad_commit_tree else C},
                "parents": [{
                    "sha": "f"*40 if self.bad_parent else A,
                    "url": "https://api.github.com/repos/" + REPO + "/git/commits/" + A,
                }],
            }
        if method == "PATCH" and suffix == "/git/refs/heads/phase%2F00-governance":
            if self.fail_ref:
                raise ProbeWriteDenied("GitHub non-fast-forward refused")
            self.current_file = True
            self.head = D
            return {
                "ref": "refs/heads/" + P,
                "object": {"sha": "f"*40 if self.bad_ref_response else D},
            }
        raise AssertionError("unexpected command " + method + " " + suffix)


class StaticGitProbePolicyTests(unittest.TestCase):
    def new(self):
        return FakeGit()

    def invoke(self, fake, **kwargs):
        opts = dict(token="trusted-private-token",
                    expected_head_sha=A,
                    enabled=True, operator_ack=True, manual_review=True,
                    transport=fake)
        opts.update(kwargs)
        return publish_static_fixture(**opts)

    def test_known_file_bytes_fixed_and_sha(self):
        self.assertEqual(hashlib.sha256(_PROBE_SOURCE.encode()).hexdigest(), _SOURCE_SHA)
        self.assertEqual("tests/fixtures/p00_trusted_remote_probe.py", _PROBE_PATH)
        self.assertIn("P00 static GitHub write probe", _PROBE_SOURCE)

    def test_success_remote_commit_ref_and_exact_file_readback(self):
        f = self.new()
        result = self.invoke(f)
        self.assertEqual("TRUSTED_STATIC_FIXTURE_REMOTE_WRITE_VERIFIED", result["status"])
        self.assertEqual(D, result["result_head_sha"])
        self.assertEqual(A, result["previous_head_sha"])
        self.assertEqual(1, result["github_writes"])
        self.assertEqual(_SOURCE_SHA, result["source_sha256"])
        self.assertFalse(result["force_push"])
        self.assertFalse(result["model_generated_source"])
        self.assertFalse(result["model_sandbox_attested"])
        self.assertFalse(result["fully_autonomous_pr_writer_verified"])
        self.assertFalse(result["persistent_worker_deployed"])
        ops = [method for method, _, _ in f.calls]
        self.assertEqual([
            "GET", "GET", "GET", "GET", "POST", "POST", "POST", "PATCH", "GET", "GET"
        ], ops)
        assert f.calls[7][2]["force"] is False
        self.assertEqual("refs/heads/" + P, "refs/heads/" + result["branch"])
        self.assertEqual(D, f.head)
        self.assertNotIn(_PROBE_SOURCE, json.dumps(result))
        self.assertNotIn("trusted-private-token", json.dumps(result))

    def test_all_write_routes_are_exact_allowlist(self):
        self.assertTrue(_route_allowed("POST", "/git/blobs", {
            "content": _PROBE_SOURCE, "encoding": "utf-8"
        }))
        for method, suffix, payload in [
            ("POST", "/git/blobs", {"content": "malicious", "encoding": "utf-8"}),
            ("PATCH", "/git/refs/heads/main", {"sha": D, "force": False}),
            ("PATCH", "/git/refs/heads/phase%2F00-governance", {"sha": D, "force": True}),
            ("POST", "/git/commits", {"message": "untrusted", "tree": C, "parents": [A]}),
            ("DELETE", "/git/refs/heads/phase%2F00-governance", None),
            ("POST", "/issues", {"title": "attack"}),
            ("POST", "/pulls/1/merge", {}),
            ("PUT", "/contents/tests/fixtures/attack.py", {}),
            ("GET", "/contents/.github/workflows/governance.yml?ref=" + A, None),
        ]:
            with self.subTest(method=method,suffix=suffix):
                self.assertFalse(_route_allowed(method, suffix, payload))

    def test_requires_exact_three_host_grants_no_http(self):
        for options in [{}, {"enabled": True},
                        {"enabled": True, "operator_ack": True},
                        {"enabled": True, "manual_review": True},
                        {"operator_ack": True, "manual_review": True},
                        {"enabled": 1, "operator_ack": True, "manual_review": True}]:
            f = self.new()
            with self.subTest(options=options), self.assertRaises(ProbeWriteDenied):
                publish_static_fixture(token="trusted-private-token",
                                       expected_head_sha=A, transport=f, **options)
            self.assertEqual([], f.calls)

    def test_bogus_token_and_wrong_sha_denied_before_remote(self):
        for kwargs in [{"token": "short"}, {"token": "x\nsecret-value"},
                       {"token": ""}, {"expected_head_sha": "main"},
                       {"expected_head_sha": "a"*39}, {"expected_head_sha": True},
                       {"transport": None}]:
            f = self.new()
            with self.subTest(kwargs=list(kwargs)),self.assertRaises(ProbeWriteDenied):
                self.invoke(f, **kwargs)
            self.assertEqual([], f.calls)

    def test_only_draft_active_expected_pr_can_mutate(self):
        for change in ({"draft": False}, {"head": "f"*40}):
            f = self.new()
            for key, value in change.items():
                setattr(f, key, value)
            with self.assertRaises(ProbeWriteDenied):
                self.invoke(f)
            self.assertEqual(["GET"], [x[0] for x in f.calls])

    def test_missing_file_proof_no_mutation(self):
        f = self.new()
        f.current_file = True
        with self.assertRaises(ProbeWriteDenied):
            self.invoke(f)
        self.assertFalse(any(x[0] == "POST" for x in f.calls))

    def test_pr_moves_at_precommit_gate_no_mutation(self):
        f = self.new()
        f.stale_second_pr = True
        with self.assertRaises(ProbeWriteDenied):
            self.invoke(f)
        self.assertEqual(["GET", "GET", "GET", "GET"], [x[0] for x in f.calls])
        self.assertEqual(A, f.head)

    def test_created_blob_sha_must_match_exact_source_git_object(self):
        f = self.new()
        f.bad_blob = True
        with self.assertRaises(ProbeWriteDenied):
            self.invoke(f)
        self.assertEqual(A, f.head)
        self.assertNotIn("PATCH", [x[0] for x in f.calls])

    def test_created_commit_parent_and_tree_must_match(self):
        for flag in ("bad_parent", "bad_commit_tree"):
            f = self.new()
            setattr(f, flag, True)
            with self.subTest(flag=flag), self.assertRaises(ProbeWriteDenied):
                self.invoke(f)
            self.assertEqual(A, f.head)
            self.assertNotIn("PATCH", [x[0] for x in f.calls])

    def test_nonfastforward_ref_conflict_is_fail_closed(self):
        f = self.new()
        f.fail_ref = True
        with self.assertRaises(ProbeWriteDenied):
            self.invoke(f)
        self.assertEqual(A, f.head)
        self.assertFalse(f.current_file)

    def test_unverified_ref_receipt_never_claims_success(self):
        f = self.new()
        f.bad_ref_response = True
        with self.assertRaises(ProbeWriteDenied):
            self.invoke(f)
        # Ref may have advanced despite invalid response. MUST reconcile.
        self.assertEqual(D, f.head)
        self.assertTrue(f.current_file)

    def test_file_readback_bytes_mismatch_never_claims_success(self):
        f = self.new()
        f.bad_remote_file = True
        with self.assertRaises(ProbeWriteDenied):
            self.invoke(f)
        self.assertTrue(f.current_file)

    def test_repeat_after_remote_file_exists_never_overwrites(self):
        f = self.new()
        self.invoke(f)
        f.calls.clear()
        with self.assertRaises(ProbeWriteDenied):
            self.invoke(f, expected_head_sha=D)
        self.assertNotIn("POST", [x[0] for x in f.calls])

if __name__ == "__main__":
    unittest.main()
