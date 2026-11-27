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

    def test_saved_attachment_readback_checks_filename_and_size_in_history(self):
        source = (ROOT / "scripts/probe_p03_chat_ui.ps1").read_text(encoding="utf-8")
        view = (ROOT / "apps/desktop/src/ui/ChatView.tsx").read_text(encoding="utf-8")
        self.assertIn('aria-label={`Saved attachment: ${a.name}, ${a.bytes} bytes`}', view)
        probe = source.split("function Wait-SavedAttachment", 1)[1].split("if ($AttachmentAcceptance)", 1)[0]
        for marker in ("Saved messages", "Saved attachment: ", "$Bytes", "-cne $expected -and $name -cne $visible",
                       "!$item.Current.IsOffscreen", "synthetic-saved-history-uia.json"):
            self.assertIn(marker, probe)
        self.assertIn("Wait-SavedAttachment 'p03-attachment-fixture.bin' 70000", source)
        self.assertIn("Read-AttachmentVault 'reopened'", source)
        self.assertNotIn("Wait-Assistant 'p03-attachment-fixture.bin'", source)

    def test_real_partial_acceptance_requires_live_prefix_stop_and_reopen(self):
        source = (ROOT / "scripts/probe_p03_chat_ui.ps1").read_text(encoding="utf-8")
        verifier = (ROOT / "scripts/verify_p03_partial_ui_database.py").read_text(encoding="utf-8")
        workflow = (ROOT / ".github/workflows/p03-native-baseline.yml").read_text(encoding="utf-8")
        self.assertIn("Wait-RealStreamingPrefix", source)
        self.assertIn("Wait-Name 'Stop' 'Button' $true", source)
        self.assertIn("$normalized.StartsWith($prefix", source)
        self.assertIn("Read-PartialVault 'reopened'", source)
        self.assertIn('assistant[6:] == ("cancelled", 1)', verifier)
        self.assertIn("digest(prior) == previous", verifier)
        self.assertIn("== proof", verifier)
        self.assertIn("-PartialAcceptance -PriorModelProofDirectory", workflow)
        self.assertIn("p03-partial-ui-failure-", workflow)

    def test_retry_uses_actual_ui_and_independent_receipt(self):
        source = (ROOT / "scripts/probe_p03_chat_ui.ps1").read_text(encoding="utf-8")
        verifier = (ROOT / "scripts/verify_p03_partial_ui_database.py").read_text(encoding="utf-8")
        for marker in ("Read-PartialVault 'retry-baseline'", "Click-Control 'Retry turn'",
                       "Read-PartialVault 'retry-saved'", "Read-PartialVault 'retry-reopened'",
                       "ZYN-RETRY-PROBE-002", "p03-retry-ui-proof.json"):
            self.assertIn(marker, source)
        for marker in ('len(ordered) == 3', 'digest(original_rows) == original["fingerprint"]',
                       'completed[2:5] == (user[0], 3, "assistant")'):
            self.assertIn(marker, verifier)

    def test_actual_availability_journey_preserves_prior_history(self):
        source = (ROOT / "scripts/probe_p03_chat_ui.ps1").read_text(encoding="utf-8")
        verifier = (ROOT / "scripts/verify_p03_partial_ui_database.py").read_text(encoding="utf-8")
        for marker in ("p03-windows-models", "Invoke-FixtureModelCommand @('cp',$originalModel,$alias)",
                       "Invoke-FixtureModelCommand @('rm',$originalModel)", "Invoke-FixtureModelCommand @('cp',$alias,$originalModel)",
                       "Assert-Combo 'Model' 'Previously selected model unavailable'",
                       "ZYN-MODEL-AVAIL-007", "Assert-NoContextEstimate",
                       "Read-PartialVault 'retry-check'", "p03-model-availability-ui-proof.json"):
            self.assertIn(marker, source)
        self.assertIn('args.stage == "retry-check"', verifier)
        self.assertIn('json.loads(reopened.read_text(encoding="utf-8")) == proof', verifier)

    def test_model_layout_native_containment_gate(self):
        source = (ROOT / "scripts/probe_p03_chat_ui.ps1").read_text(encoding="utf-8")
        css = (ROOT / "apps/desktop/src/styles.css").read_text(encoding="utf-8")
        for marker in ("function Assert-ModelControlBounds", "BoundingRectangle", "GetWindowRect",
                       "ZYN-MODEL-LAYOUT-002", "$missingBounds=Assert-ModelControlBounds $true",
                       "$restoredBounds=Assert-ModelControlBounds $false", "horizontal_layout_bounds"):
            self.assertIn(marker, source)
        self.assertIn(".chat-model-controls .chat-notice { grid-column:1/-1;", css)
        self.assertIn("minmax(0, max-content) minmax(0, 1fr)", css)

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
