"""Contract regression for P01-T01's pre-development decision gate."""
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
ADR = ROOT / "docs" / "adr" / "0025-p01-desktop-foundation-predev.md"

class P01PredevelopmentContractTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.document = ADR.read_text(encoding="utf-8")

    def test_three_stacks_and_official_research_links_are_present(self):
        for technology in ("Tauri 2", "Electron", "Wails 3", "React", "TypeScript", "Rust"):
            with self.subTest(technology=technology):
                self.assertIn(technology, self.document)
        for host in ("https://v2.tauri.app/", "https://www.electronjs.org/",
                     "https://github.com/wailsapp/wails", "https://www.sqlite.org/"):
            with self.subTest(source=host):
                # SQLite official evidence is represented in the next test's
                # vault requirements and must be linked here for auditability.
                self.assertIn(host, self.document)

    def test_each_following_p01_task_has_tests_first(self):
        section = self.document.split("## 5. Tests-first acceptance map", 1)[1]
        for number in range(2, 12):
            with self.subTest(task=number):
                self.assertRegex(section, rf"\| P01-T{number:02d} \|")

    def test_baseline_is_not_misreported_as_product_acceptance(self):
        for pending in ("NOT_MEASURED", "PENDING", "not a shipped capability",
                        "no bootable P01 desktop application", "No auto-merge"):
            with self.subTest(pending=pending):
                self.assertIn(pending.lower(), self.document.lower())

    def test_critical_native_boundaries_and_recovery_are_tracked(self):
        for boundary in ("capability", "keychain", "idempotency",
                         "redaction", "online backup", "rollback",
                         "symlink", "consent", "Windows"):
            with self.subTest(boundary=boundary):
                self.assertIn(boundary.lower(), self.document.lower())

if __name__ == "__main__":
    unittest.main()
