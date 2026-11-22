"""P01-T04 source-level Rust/TypeScript IPC parity and authority guards.

Rust unit tests execute on Windows; these guards also run in Governance.
"""
import json
from pathlib import Path
import unittest

ROOT = Path(__file__).resolve().parents[1]
APP = ROOT / "apps" / "desktop"


class ReadOnlyIpcContractTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.rust = (APP / "src-tauri/src/ipc.rs").read_text(encoding="utf-8")
        cls.web = (APP / "src/ipc.ts").read_text(encoding="utf-8")
        cls.cap = json.loads(
            (APP / "src-tauri/capabilities/main-readonly.json").read_text(encoding="utf-8")
        )
        cls.native = (APP / "src-tauri/src/lib.rs").read_text(encoding="utf-8")
        cls.build = (APP / "src-tauri/build.rs").read_text(encoding="utf-8")

    def test_version_command_scope_and_native_type_mirror(self):
        for text in (self.rust, self.web):
            self.assertIn("workspace.status", text)
            self.assertIn("correlation", text)
            self.assertIn("schema_version" if text == self.rust else "schemaVersion", text)
            self.assertIn("not_configured", text)
            self.assertIn("writable", text)
        self.assertIn("deny_unknown_fields", self.rust)
        self.assertIn("MAX_ENVELOPE_BYTES: usize = 1024", self.rust)
        self.assertIn("strict_json_rejects_extra_fields_and_path_payloads", self.rust)

    def test_actual_acl_denies_nonmain_or_remote_and_exposes_only_one_command(self):
        self.assertEqual(["main"], self.cap["windows"])
        self.assertEqual(["allow-workspace-handshake"], self.cap["permissions"])
        self.assertNotIn("remote", self.cap)
        self.assertIn('commands(&["workspace_handshake"])', self.build)
        self.assertIn("generate_handler![ipc::workspace_handshake]", self.native)
        self.assertIn('window.label() != "main"', self.rust)
        for forbidden in (".plugin(", "std::fs::write", "std::fs::remove", "reqwest", "std::process::Command"):
            self.assertNotIn(forbidden, self.native + self.rust)

    def test_negative_schema_timeout_and_readonly_replay_coverage(self):
        for name in (
            "wrong_version_command_scope_and_id_are_denied",
            "oversized_envelope_is_bounded_without_user_payload_logging",
            "strict_json_rejects_extra_fields_and_path_payloads",
            "repeated_read_is_idempotent_and_never_writable",
        ):
            self.assertIn("fn " + name, self.rust)
        for code in ("ZYN-IPC-001", "ZYN-IPC-002", "ZYN-IPC-003",
                     "ZYN-IPC-004", "ZYN-IPC-005", "ZYN-IPC-006"):
            self.assertIn(code, self.rust)
        self.assertIn("ZYN-IPC-TIMEOUT", self.web)
        self.assertIn("Promise.race", self.web)
        self.assertIn("clearTimeout(timer)", self.web)
        self.assertIn('invoke<unknown>("workspace_handshake", { request })', self.web)
        self.assertIn("return checkReply(result, correlationId)", self.web)

    def test_ui_reflects_real_result_only_and_does_not_enable_writes(self):
        app = (APP / "src/App.tsx").read_text(encoding="utf-8")
        self.assertIn("probeWorkspaceStatus()", app)
        self.assertIn('setTransport("unavailable")', app)
        self.assertIn("workspace not configured", app)
        self.assertIn("No verified backups", app)
        self.assertIn("disabled", app)
        self.assertNotIn("localStorage", app)

    def test_windows_runs_actual_rust_contract_tests(self):
        workflow = (ROOT / ".github/workflows/p01-desktop.yml").read_text(
            encoding="utf-8"
        )
        self.assertIn("cargo test --lib --release", workflow)
        self.assertIn("npm run check", workflow)
        self.assertIn("npm run tauri -- build --no-bundle", workflow)
        self.assertNotIn("contents: write", workflow)


if __name__ == "__main__":
    unittest.main()
