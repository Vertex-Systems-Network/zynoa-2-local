"""Local Ollama preflight tests: no network requests to real providers."""
import unittest

from tools.local_model_probe import (
    LocalModelUnavailable, probe_local_ollama, validate_local_base
)


class FakeLocalModel:
    def __init__(self, *, version="0.9.5", names=None):
        self.calls = []
        self.version = version
        self.names = ["qwen2.5-coder:7b"] if names is None else names

    def __call__(self, base, endpoint):
        self.calls.append((base, endpoint))
        if endpoint == "/api/version":
            return {"version": self.version}
        if endpoint == "/api/tags":
            return {"models": [{"name": name} for name in self.names]}
        raise AssertionError("unapproved endpoint")


class OllamaPreflightTests(unittest.TestCase):
    def test_loopback_endpoint_only(self):
        self.assertEqual("http://127.0.0.1:11434", validate_local_base("http://127.0.0.1:11434"))
        self.assertEqual("http://[::1]:11434", validate_local_base("http://[::1]:11434"))
        for url in (
            "http://localhost:11434",
            "http://192.168.0.2:11434",
            "https://127.0.0.1:11434", "http://127.0.0.1",
            "http://169.254.169.254/latest", "http://127.0.0.1:11434/path",
            "http://127.0.0.1:11434?secret=1",
            "http://user:pass@127.0.0.1:11434",
            "http://127.0.0.1:11434#fragment",
            "file:///etc/passwd", "http://[::1]:99999",
        ):
            with self.subTest(url=url), self.assertRaises(LocalModelUnavailable):
                validate_local_base(url)

    def test_local_inventory_never_invokes_inference(self):
        fake = FakeLocalModel()
        result = probe_local_ollama(transport=fake)
        self.assertEqual("LOCAL_MODEL_PRESENT", result["status"])
        self.assertEqual(["qwen2.5-coder:7b"], result["model_names"])
        self.assertEqual(1, result["model_count"])
        self.assertFalse(result["coding_agent_deployed"])
        self.assertFalse(result["os_sandbox_verified"])
        self.assertEqual(0, result["prompts_sent"])
        self.assertEqual(0, result["github_writes"])
        self.assertEqual([
            ("http://127.0.0.1:11434", "/api/version"),
            ("http://127.0.0.1:11434", "/api/tags"),
        ], fake.calls)

    def test_running_server_without_models_is_not_ready(self):
        fake = FakeLocalModel(names=[])
        result = probe_local_ollama(transport=fake)
        self.assertEqual("OLLAMA_RUNNING_NO_MODELS", result["status"])
        self.assertFalse(result["model_ready_for_coding"])

    def test_invalid_version_and_model_name_are_blocked(self):
        bad = FakeLocalModel(version="invalid secret value")
        with self.assertRaises(LocalModelUnavailable):
            probe_local_ollama(transport=bad)
        bad = FakeLocalModel(names=["good:1", "../../secrets"])
        with self.assertRaises(LocalModelUnavailable):
            probe_local_ollama(transport=bad)

    def test_non_mapping_server_response_is_blocked(self):
        def fake(base, endpoint):
            return {"version": "0.7"} if endpoint == "/api/version" else "not-json"
        with self.assertRaises(LocalModelUnavailable):
            probe_local_ollama(transport=fake)

    def test_overlarge_inventory_is_blocked(self):
        fake = FakeLocalModel(names=["x:1"] * 1001)
        with self.assertRaises(LocalModelUnavailable):
            probe_local_ollama(transport=fake)

    def test_model_names_sorted_and_deduplicated_for_display(self):
        fake = FakeLocalModel(names=["model-b:7b", "model-a:3b", "model-a:3b"])
        result = probe_local_ollama(transport=fake)
        self.assertEqual(["model-a:3b", "model-b:7b"], result["model_names"])
        self.assertEqual(3, result["model_count"])


if __name__ == "__main__":
    unittest.main()
