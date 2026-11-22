"""P01-T05: native-only secret and grant boundary regression contracts.

Actual Windows Credential Manager roundtrip + revoke tests run in cargo test.
"""
import json
from pathlib import Path
import unittest

ROOT = Path(__file__).resolve().parents[1]
NATIVE = ROOT / "apps/desktop/src-tauri"


class NativeSecurityContractTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.security = (NATIVE / "src/security.rs").read_text(encoding="utf-8")
        cls.secrets = (NATIVE / "src/secrets.rs").read_text(encoding="utf-8")
        cls.ipc = (NATIVE / "src/ipc.rs").read_text(encoding="utf-8")
        cls.lib = (NATIVE / "src/lib.rs").read_text(encoding="utf-8")
        cls.cargo = (NATIVE / "Cargo.toml").read_text(encoding="utf-8")

    def test_native_grants_are_deny_first_and_revocable(self):
        for marker in (
            "#[derive(Default)]", "HashSet<Capability>", "pub(crate) fn revoke(",
            "native_window_label != \"main\"", "for_local_read_only_shell",
            "ReadUserFile", "WriteUserFile", "OutboundNetwork",
            "ReadCredential", "WriteCredential",
            "default_policy_denies_all_native_capabilities",
            "revocation_is_immediate_and_cannot_be_recovered_by_request_replay",
        ):
            self.assertIn(marker, self.security)
        self.assertIn("allow_local_workspace_handshake(window.label())", self.ipc)

    def test_secrets_never_leave_native_or_become_debug_or_json(self):
        self.assertIn("struct SensitiveText(Zeroizing<String>)", self.secrets)
        self.assertNotIn("derive(Debug", self.secrets.split("struct SensitiveText")[0].split("enum SecretFault")[-1])
        self.assertNotIn("pub struct SensitiveText", self.secrets)
        self.assertNotIn("#[tauri::command]", self.secrets)
        self.assertNotIn("Serialize", self.secrets)
        self.assertNotIn("println!", self.secrets)
        self.assertNotIn("eprintln!", self.secrets)
        self.assertNotIn("println!", self.security)
        self.assertNotIn("secret", self.ipc.lower())
        self.assertNotIn("secret", (ROOT / "apps/desktop/src/ipc.ts").read_text(encoding="utf-8").lower())
        self.assertIn("generate_handler![ipc::workspace_handshake]", self.lib)
        self.assertNotIn("secrets::", self.lib)

    def test_keyring_real_windows_backend_and_sanitized_failures(self):
        self.assertIn('keyring = { version = "=3.6.3", default-features = false, features = ["windows-native"] }', self.cargo)
        self.assertIn('zeroize = "=1.8.2"', self.cargo)
        self.assertIn("keyring::Entry::new", self.secrets)
        self.assertIn("SecretFault::Unavailable", self.secrets)
        for native_operation in (".set_password(", ".get_password(", ".delete_credential("):
            self.assertIn(native_operation, self.secrets)
        self.assertIn("real_windows_credential_store_roundtrip_and_explicit_delete", self.secrets)
        self.assertIn("Windows keychain fixture cleanup failed", self.secrets)

    def test_main_window_acl_remains_only_workspace_read(self):
        cap = json.loads((NATIVE / "capabilities/main-readonly.json").read_text(encoding="utf-8"))
        self.assertEqual(["main"], cap["windows"])
        self.assertEqual(["allow-workspace-handshake"], cap["permissions"])
        self.assertNotIn("remote", cap)
        build = (NATIVE / "build.rs").read_text(encoding="utf-8")
        self.assertIn('commands(&["workspace_handshake"])', build)

    def test_no_unsafe_release_or_signing_claims(self):
        docs = (ROOT / "docs/operations/P01_NATIVE_SECURITY.md").read_text(encoding="utf-8")
        self.assertIn("NOT production-signed", docs)
        self.assertIn("Windows Credential Manager", docs)
        self.assertIn("no WebView secret commands", docs)
        workflow = (ROOT / ".github/workflows/p01-desktop.yml").read_text(encoding="utf-8")
        self.assertIn("tests.test_p01_native_security", workflow)
        self.assertIn("cargo test --lib --release", workflow)
        self.assertNotIn("contents: write", workflow)


if __name__ == "__main__":
    unittest.main()
