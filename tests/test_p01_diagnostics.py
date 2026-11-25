"""P01-T06 native diagnostics: no arbitrary payloads, real Windows CI evidence."""
from pathlib import Path
import unittest

ROOT = Path(__file__).resolve().parents[1]


class NativeDiagnosticsContractTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        native = ROOT / "apps/desktop/src-tauri/src"
        cls.source = (native / "diagnostics.rs").read_text(encoding="utf-8")
        cls.lib = (native / "lib.rs").read_text(encoding="utf-8")
        cls.ipc = (native / "ipc.rs").read_text(encoding="utf-8")
        cls.workflow = (ROOT / ".github/workflows/p01-desktop.yml").read_text(encoding="utf-8")

    def test_durable_bounded_spool_rejects_corruption(self):
        for marker in (
            "MAX_SPOOL_BYTES", "MAX_LINE_BYTES", "MAX_UNIQUE_GROUPS",
            "checked_add(1)", "file.sync_data()", "grouped_snapshot",
            "deny_unknown_fields", "options.append(true).create(true)",
            "invalid_or_corrupt_spool_never_overwrites_user_content",
        ):
            self.assertIn(marker, self.source)

    def test_native_boot_uses_os_owned_app_local_directory_only(self):
        for marker in (
            "app.path().local_data_dir()", "app.path().app_local_data_dir()",
            "NativeDiagnostics::initialize(&os_local, &app_local)",
            "app.manage(runtime)", ".setup(|app|",
        ):
            self.assertIn(marker, self.lib)
        self.assertIn('os_local_data_root.join("com.zynoa.desktop")', self.source)
        self.assertIn("reject_linked_directory", self.source)
        self.assertIn("os_local_boot_creates_app_owned_record_and_replays_without_data_loss", self.source)
        self.assertIn("app_root_cannot_be_redirected_to_external_or_symlink_path", self.source)

    def test_sanitized_panic_and_ipc_denial_without_raw_user_text(self):
        for marker in (
            "std::panic::set_hook", "inner.try_lock()", "Code::RuntimeFault",
            "Code::IpcDenied", "Module::M18", "Module::M16",
        ):
            self.assertIn(marker, self.source)
        self.assertIn("runtime.install_redacted_panic_hook()", self.lib)
        self.assertIn("diagnostics: tauri::State<'_, crate::diagnostics::NativeDiagnostics>", self.ipc)
        self.assertIn("diagnostics.record_denied_ipc()", self.ipc)
        self.assertIn("generate_handler![ipc::workspace_handshake, chat_ipc::chat_request]", self.lib)
        for forbidden in ("#[tauri::command]", "reqwest", "println!", "eprintln!"):
            self.assertNotIn(forbidden, self.source)

    def test_native_writer_exclusivity_and_actual_panic_redaction(self):
        for marker in ("options.share_mode(0)", "open_exclusive_instance_guard",
                       "native_writer_lock_blocks_second_instance_and_recovers_after_exit",
                       "actual_panic_hook_omits_secret_payload_from_local_spool"):
            self.assertIn(marker, self.source)
        app = (ROOT / "apps/desktop/src/App.tsx").read_text(encoding="utf-8")
        self.assertIn("No workspace data stored", app)
        self.assertIn("No automatic issue publishing", app)
        self.assertNotIn("The native diagnostic spine is not yet connected", app)

    def test_windows_cold_boot_checks_real_local_spool(self):
        self.assertIn("tests.test_p01_diagnostics", self.workflow)
        self.assertIn("cargo test --lib --release", self.workflow)
        self.assertIn("events-v1.jsonl", self.workflow)
        self.assertIn("BootReady", self.workflow)
        self.assertNotIn("contents: write", self.workflow)

    def test_unfinished_security_and_reporting_gates_remain_explicit(self):
        doc = (ROOT / "docs/operations/P01_DIAGNOSTICS.md").read_text(encoding="utf-8")
        self.assertIn("no automatic issue publishing", doc)
        self.assertIn("production diagnostics UI", doc)


if __name__ == "__main__":
    unittest.main()
