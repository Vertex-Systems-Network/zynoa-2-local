"""P00 developer-only incident relay tests; no real GitHub writes."""
import json
import unittest
from tools.github_issue_bridge import DeveloperIssueBridge, IncidentPublishError

REPO = "Vertex-Systems-Network/zynoa-2-local"

SAFE_EVENT = {
    "source_type": "developer-ci",
    "severity": "P2",
    "module": "M22",
    "error_code": "TEST_FAILURE",
    "message_class": "AssertionError",
    "app_version": "0.0.1",
    "prompt": "PRIVATE CHAT CONTENT NEVER UPLOAD",
    "password": "TOPSECRET",
    "filepath": "C:\\Users\\Private\\file.txt",
    "code": "PRIVATE SOURCE CODE NEVER UPLOAD",
}

class FakeIssues:
    def __init__(self):
        self.events = []
        self.existing = []
        self.return_invalid = False
    def __call__(self, method, url, headers, data, timeout):
        self.events.append((method, url, data))
        assert headers["Authorization"] == "Bearer fake-issue-token"
        if method == "GET":
            return {} if self.return_invalid else self.existing
        if method == "POST":
            return {"number": 27, "html_url": "https://github.com/" + REPO + "/issues/27"}
        raise AssertionError("unexpected method")

class DeveloperIssueBridgeTests(unittest.TestCase):
    def new(self):
        fake = FakeIssues()
        bridge = DeveloperIssueBridge(REPO, token="fake-issue-token",
                                      publish_enabled=True, transport=fake)
        return bridge, fake

    def test_safe_create(self):
        bridge, fake = self.new()
        result = bridge.publish(SAFE_EVENT)
        self.assertEqual("CREATED", result["status"])
        self.assertEqual(27, result["issue_number"])
        payload = json.loads(next(body for method, url, body in fake.events if method == "POST"))
        text = json.dumps(payload)
        self.assertNotIn("PRIVATE CHAT CONTENT", text)
        self.assertNotIn("TOPSECRET", text)
        self.assertNotIn("PRIVATE SOURCE CODE", text)
        self.assertNotIn("file.txt", text)
        self.assertIn("zynoa-incident:", text)

    def test_remote_dedup_does_not_post(self):
        bridge, fake = self.new()
        record = DeveloperIssueBridge.safe_record(SAFE_EVENT)
        marker = "<!-- zynoa-incident:" + record["fingerprint"] + " -->"
        fake.existing = [{"number": 23, "html_url": "https://github.com/" + REPO + "/issues/23",
                          "body": "previous event\n" + marker}]
        result = bridge.publish(SAFE_EVENT)
        self.assertEqual("EXISTING", result["status"])
        self.assertEqual(1, len(fake.events))

    def test_disabled_never_calls_network(self):
        fake = FakeIssues()
        bridge = DeveloperIssueBridge(REPO, token="fake-issue-token",
                                      publish_enabled=False, transport=fake)
        with self.assertRaises(IncidentPublishError):
            bridge.publish(SAFE_EVENT)
        self.assertEqual([], fake.events)

    def test_end_user_incident_rejected(self):
        bridge, fake = self.new()
        event = {**SAFE_EVENT, "source_type": "desktop-client"}
        with self.assertRaises(IncidentPublishError):
            bridge.publish(event)
        self.assertEqual([], fake.events)

    def test_security_incident_rejected_from_public_issues(self):
        bridge, fake = self.new()
        with self.assertRaises(IncidentPublishError):
            bridge.publish({**SAFE_EVENT, "severity": "P0"})
        self.assertEqual([], fake.events)

    def test_dedup_failure_blocks_creation(self):
        bridge, fake = self.new()
        fake.return_invalid = True
        with self.assertRaises(IncidentPublishError):
            bridge.publish(SAFE_EVENT)
        self.assertEqual(1, len(fake.events))

    def test_pagination_limit_blocks_duplicate_creation(self):
        bridge, fake = self.new()
        fake.existing = [{"number": i + 1, "body": "no marker"} for i in range(100)]
        with self.assertRaises(IncidentPublishError):
            bridge.publish(SAFE_EVENT)
        self.assertEqual(4, len(fake.events))
        self.assertFalse(any(x[0] == "POST" for x in fake.events))

    def test_prohibited_repository(self):
        with self.assertRaises(ValueError):
            DeveloperIssueBridge("../secret", token="fake", publish_enabled=True)

if __name__ == "__main__":
    unittest.main()
