"""Windows CI also uses the real AST parser; guard against duplicate script tails."""
import unittest
from pathlib import Path
ROOT = Path(__file__).resolve().parents[1]

class NativeProbeIntegrity(unittest.TestCase):
    def test_one_of_each_journey_and_literal_path_guard(self):
        source = (ROOT / "scripts/probe_p03_chat_ui.ps1").read_text(encoding="utf-8")
        for marker in ("if ($ModelAcceptance) {\n try {",
                       "$script:stage='model baseline identity'",
                       "$script:stage='verify empty fixture'",
                       "function Select-SyntheticFile",
                       "if ($AttachmentAcceptance) {",
                       "ZYN-ATTACH-PROBE-002"):
            self.assertEqual(source.count(marker), 1, marker)
        guard = next(line for line in source.splitlines() if "ZYN-ATTACH-PROBE-002" in line)
        self.assertIn("+$')", guard)
        self.assertIn("-cnotmatch", guard)

    def test_picker_uses_exact_owned_dialog_field(self):
        source = (ROOT / "scripts/probe_p03_chat_ui.ps1").read_text(encoding="utf-8")
        picker = source.split("function Select-SyntheticFile", 1)[1].split("if ($AttachmentAcceptance)", 1)[0]
        for marker in ("FilenameEdits($dialog)", "IsChild($dialog,$filenameEdit)",
                       "GetWindowRect($dialog", "OwnsKeyboardFocus($dialog,$filenameEdit)",
                       "GetForegroundWindow() -ne $dialog", "ReadEditText($dialog,$filenameEdit) -cne $Path",
                       "dialog-control-inventory.txt"):
            self.assertIn(marker, picker)
        for marker in ("GetDlgCtrlID(child)==1152", "GetDlgCtrlID(parent)==1148",
                       "EnumChildWindows(dialog", "GetGUIThreadInfo", "SendMessageTimeout"):
            self.assertIn(marker, source)
        self.assertNotIn("SendWait('%n')", picker)
        self.assertNotIn("SetValue(", picker)

    def test_ast_validation_precedes_build_and_original_acceptance_gates(self):
        workflow = (ROOT / ".github/workflows/p03-native-baseline.yml").read_text(encoding="utf-8")
        self.assertIn("[System.Management.Automation.Language.Parser]::ParseFile", workflow)
        self.assertIn("$parseErrors.Count -gt 0", workflow)
        start = workflow.index("name: Parse Windows native probe before build")
        for gate in ("name: Native Windows desktop build", "name: P03 T03 actual Windows conversation UI",
                     "name: P03 T05–T07 real Windows model", "name: P03 T08 actual Windows attachment"):
            self.assertLess(start, workflow.index(gate))

if __name__ == "__main__":
    unittest.main()
