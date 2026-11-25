"""Source and negative tests for the native Windows UIA audit."""
from pathlib import Path
import unittest

from tools.verify_p02_native_uia import verify, EXPECTED, InvalidUIAEvidence

ROOT = Path(__file__).resolve().parents[1]
SHA = "a" * 40


def good():
    return {
        "schema_version": 1,
        "module": "M02",
        "source_commit_sha": SHA,
        "target": "Real Windows Tauri WebView2 UI Automation HWND",
        "native_pid_matched": True,
        "scope": "Scoped accessible-name, keyboard focus and dialog dismissal probe",
        "results": {key: True for key in EXPECTED},
        "diagnostics": {
            "search_focus": {
                "method": "real_keyboard_text_and_input_ValuePattern",
                "exact_local_probe_id": "M19-OPT-06",
                "query_reflected_by_input_provider": True,
                "provider_focus_kind": "aria_active_descendant_list_item",
            },
        },
        "issues": [],
        "duration_ms": 1600,
        "full_screen_reader_verified": False,
        "all_option_controls_verified": False,
        "final_screenshot_manifest_verified": False,
        "no_user_data": True,
        "status": "SCOPED_NATIVE_UIA_PASS",
    }


class NativeUIAContracts(unittest.TestCase):
    def test_scoped_pass_never_becomes_full_screen_reader_signoff(self):
        outcome = verify(good(), SHA)
        self.assertEqual(9, outcome["native_aria_checks"])
        self.assertTrue(outcome["native_keyboard_journey_verified"])
        self.assertFalse(outcome["full_screen_reader_verified"])

    def test_untrusted_native_pid_is_rejected(self):
        proof = good()
        proof["native_pid_matched"] = False
        with self.assertRaisesRegex(InvalidUIAEvidence, "origin"):
            verify(proof, SHA)

    def test_accessible_input_name_or_focus_failure_rejected(self):
        for key in EXPECTED:
            with self.subTest(key=key):
                proof = good()
                proof["results"][key] = False
                with self.assertRaisesRegex(InvalidUIAEvidence, "accessible names"):
                    verify(proof, SHA)

    def test_uia_focused_listitem_alone_is_not_proof_of_keyboard_input(self):
        for mutation in (
            lambda item: item.pop("diagnostics"),
            lambda item: item["diagnostics"]["search_focus"].update(
                method="aria_active_descendant_list_item"),
            lambda item: item["diagnostics"]["search_focus"].update(
                query_reflected_by_input_provider=False),
            lambda item: item["diagnostics"]["search_focus"].update(
                exact_local_probe_id="M19-OPT-07"),
        ):
            with self.subTest(mutation=mutation):
                proof = good()
                mutation(proof)
                with self.assertRaisesRegex(InvalidUIAEvidence, "ValuePattern"):
                    verify(proof, SHA)

    def test_screen_reader_certificate_cannot_be_forged(self):
        proof = good()
        proof["full_screen_reader_verified"] = True
        with self.assertRaisesRegex(InvalidUIAEvidence, "scope boundary"):
            verify(proof, SHA)

    def test_bad_sha_and_fake_origin_rejected(self):
        proof = good()
        with self.assertRaisesRegex(InvalidUIAEvidence, "source SHA"):
            verify(proof, "b" * 40)
        proof["target"] = "HTML screenshot fixture"
        with self.assertRaisesRegex(InvalidUIAEvidence, "native Windows Tauri"):
            verify(proof, SHA)

    def test_duration_and_no_user_data_are_required(self):
        proof = good()
        proof["duration_ms"] = 0
        with self.assertRaisesRegex(InvalidUIAEvidence, "duration"):
            verify(proof, SHA)
        proof = good()
        proof["no_user_data"] = False
        with self.assertRaisesRegex(InvalidUIAEvidence, "privacy"):
            verify(proof, SHA)

    def test_source_uses_actual_process_ui_automation_with_bounded_probes(self):
        script = (ROOT / "scripts/probe_p02_native_a11y.ps1").read_text(encoding="utf-8")
        for snippet in ("UIAutomationClient", "UIAutomationTypes", "AutomationElement",
                        "MainWindowHandle", "SetForegroundWindow", "SourceSha",
                        "Find-NativeName", "keyboard_focus_enters_modal_search",
                        "escape_dismisses_modal", "full_screen_reader_verified = $false"):
            self.assertIn(snippet, script)
        self.assertIn("if ($item.Current.IsKeyboardFocusable) { return $item }", script)
        palette = (ROOT / "apps/desktop/src/ui/CommandPalette.tsx").read_text(encoding="utf-8")
        self.assertIn('ref={inputRef} autoFocus', palette)
        self.assertIn('aria-activedescendant=', palette)
        for forbidden in ("Invoke-WebRequest", "http://", "https://", "curl ",
                          "localStorage", "sessionStorage", "Get-Clipboard"):
            self.assertNotIn(forbidden, script)

    def test_real_webview2_focus_probe_requires_actual_input_value_and_navigation(self):
        script = (ROOT / "scripts/probe_p02_native_a11y.ps1").read_text(encoding="utf-8")
        for snippet in ("Read-NativeTextInputValue", "ValuePattern",
                        "M19-OPT-06", "keyboard_query_filters_to_exact_option",
                        "enter_opens_exact_option_help", "modal_reopens_after_help_navigation",
                        "Wiki mapping and link checker", "aria_active_descendant_list_item",
                        "Search available commands and offline Help"):
            self.assertIn(snippet, script)
        self.assertIn("$typedInExactInput = $confirmedValue -ceq $probeValue", script)
        self.assertIn("$searchInputGone -and $helpHeadingVisible", script)
        self.assertIn("search_input_removed_from_native_tree", script)
        self.assertIn("exact_option_heading_visible_in_native_tree", script)
        self.assertNotIn("$searchFocused = $true", script)

    def test_help_destination_focus_is_a_real_html_heading(self):
        widget = (ROOT / "apps/desktop/src/ui/HelpWorkflows.tsx").read_text(encoding="utf-8")
        app = (ROOT / "apps/desktop/src/App.tsx").read_text(encoding="utf-8")
        self.assertIn('tabIndex={-1} ref={selectedOptionHeadingRef}', widget)
        self.assertIn('aria-labelledby="help-selected-option-title"', widget)
        self.assertIn("selectedOptionHeadingRef.current?.focus({ preventScroll: false })", widget)
        self.assertIn('helpDestination?.kind !== "option"', app)

    def test_workflow_pins_native_probe_to_live_tauri_boot_and_artifact(self):
        flow = (ROOT / ".github/workflows/p01-desktop.yml").read_text(encoding="utf-8")
        self.assertIn("scripts\\probe_p02_native_a11y.ps1", flow)
        self.assertIn("python -m tools.verify_p02_native_uia", flow)
        self.assertIn("P02-native-uia.capture.json", flow)
        self.assertIn("P02-native-uia.verify.json", flow)


if __name__ == "__main__":
    unittest.main()
