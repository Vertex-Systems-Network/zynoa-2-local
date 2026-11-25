from pathlib import Path
import unittest

ROOT = Path(__file__).resolve().parents[1]

class P03FutureContractTests(unittest.TestCase):
    def setUp(self):
        self.src = (ROOT / "apps/desktop/src-tauri/src/artifact_contracts.rs").read_text()
    def test_attachment_export_and_tool_contracts_are_native_and_bounded(self):
        for fragment in ("Sha256", "MAX_ATTACHMENT", "verify_attachment", "export_manifest", "tool_is_allowed"):
            self.assertIn(fragment, self.src)
        self.assertNotIn("Command", self.src)
        self.assertNotIn("reqwest", self.src)
    def test_dangerous_tool_and_path_inputs_fail_closed(self):
        self.assertIn('"shell.exec"', self.src)
        self.assertIn("name.contains", self.src)

if __name__ == "__main__":
    unittest.main()
