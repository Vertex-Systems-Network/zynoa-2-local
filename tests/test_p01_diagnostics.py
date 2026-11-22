"""P01-T06 native diagnostic spool; real Rust tests run in Windows CI."""
from pathlib import Path
import unittest

ROOT = Path(__file__).resolve().parents[1]

class NativeDiagnosticsContractTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.source = (ROOT/"apps/desktop/src-tauri/src/diagnostics.rs").read_text(encoding="utf-8")
        cls.lib = (ROOT/"apps/desktop/src-tauri/src/lib.rs").read_text(encoding="utf-8")
        cls.ci = (ROOT/".github/workflows/p01-desktop.yml").read_text(encoding="utf-8")

    def test_durable_bounded_native_spool(self):
        for item in ("MAX_SPOOL_BYTES", "MAX_LINE_BYTES", "MAX_UNIQUE_GROUPS",
                     "checked_add(1)", "file.sync_data()", "grouped_snapshot",
                     "deny_unknown_fields", "options.append(true).create(true)"):
            self.assertIn(item, self.source)

    def test_no_arbitrary_user_content_or_remote_commands(self):
        for forbidden in ("#[tauri::command]", "reqwest", "println!", "eprintln!"):
            self.assertNotIn(forbidden, self.source)
        self.assertIn("mod diagnostics;", self.lib)
        self.assertIn("generate_handler![ipc::workspace_handshake]", self.lib)
        self.assertNotIn("diagnostics::", self.lib)

    def test_windows_rust_ci_and_permission_gates(self):
        self.assertIn("tests.test_p01_diagnostics", self.ci)
        self.assertIn("cargo test --lib --release", self.ci)
        self.assertNotIn("contents: write", self.ci)

    def test_runtime_and_telemetry_claims_disclosed(self):
        doc = (ROOT/"docs/operations/P01_DIAGNOSTICS.md").read_text(encoding="utf-8")
        self.assertIn("NOT connected to live runtime", doc)
        self.assertIn("no automatic issue publishing", doc)

if __name__ == "__main__":
    unittest.main()
