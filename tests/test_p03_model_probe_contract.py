from pathlib import Path
import unittest

class ModelProbeContractTests(unittest.TestCase):
    def test_first_model_selection_skips_disabled_placeholder(self):
        src=(Path(__file__).parents[1]/"scripts/probe_p03_chat_ui.ps1").read_text()
        self.assertIn("placeholder at index zero", src)
        self.assertIn("SendWait('{DOWN}')", src)
        self.assertIn("ZYN-MODEL-PROBE-003", src)

if __name__ == "__main__": unittest.main()
