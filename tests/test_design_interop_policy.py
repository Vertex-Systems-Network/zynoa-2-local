"""Unit checks for Designer interoperability stage gating (spec only)."""
import sys
import unittest
from pathlib import Path
ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "scripts"))
from check_design_interop_policy import validate

class InteroperabilityPolicyTest(unittest.TestCase):
    def test_current_repository_policy_is_consistent(self):
        self.assertEqual([], validate(ROOT))

    def test_empty_repo_missing_contract_is_rejected(self):
        self.assertTrue(validate(Path("/path/that/does/not/exist/for/zynoa/spec-test")))

    def test_separate_phase_entry(self):
        phases = (ROOT / "docs/PHASE_SPECS.md").read_text(encoding="utf-8")
        self.assertIn("## P08I", phases)
        self.assertIn("P08 verified", phases)
        self.assertIn("phase/08i-design-interoperability", phases)

if __name__ == "__main__":
    unittest.main()
