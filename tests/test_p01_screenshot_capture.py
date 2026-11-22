"""P01-T10 native screenshot proof is never a mock or browser preview."""
from pathlib import Path
import unittest

ROOT=Path(__file__).resolve().parents[1]

class NativeScreenshotCaptureContracts(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.script=(ROOT/"scripts/capture_p01_desktop.ps1").read_text(encoding="utf-8")
        cls.workflow=(ROOT/".github/workflows/p01-desktop.yml").read_text(encoding="utf-8")

    def test_real_native_window_required_and_blank_screen_denied(self):
        for marker in ("$proc.MainWindowHandle", "IsWindowVisible($hwnd)",
                       "GetWindowRect($hwnd", "CopyFromScreen(", "SetForegroundWindow",
                       "ZYN-SCREEN-002", "ZYN-SCREEN-007", "refuse replacing existing image"):
            self.assertIn(marker, self.script)
        self.assertIn("if ($SourceSha -notmatch '^[0-9a-f]{40}$') { throw", self.script)
        self.assertIn("if ($BuiltSha -notmatch '^[0-9a-f]{40}$' -or $BuiltSha -ne $SourceSha)", self.script)
        self.assertIn('Add-Type -TypeDefinition @\'\nusing System;', self.script)
        self.assertIn('SizeOf($visibleBounds)', self.script)
        self.assertNotIn('SizeOf([ZynoaScreenWin32+Rect])', self.script)
        self.assertNotIn("capture_verified = $true", self.script)
        for marker in ("DwmGetWindowAttribute(", "DWMWA_EXTENDED_FRAME_BOUNDS",
                       "$visibleBounds", "$bounds = $visibleBounds",
                       "ZYN-SCREEN-012", "ZYN-SCREEN-013",
                       "frame_bounds_source = 'DwmGetWindowAttribute"):
            self.assertIn(marker, self.script)
        for marker in ("System.Windows.Forms.Screen", "WorkingArea", "MoveWindow(",
                       "window still overlaps desktop/taskbar", "window_fully_visible"):
            self.assertIn(marker, self.script)

    def test_provenance_with_no_premature_verified_claims(self):
        for marker in ("source_commit_sha", "built_commit_sha = $BuiltSha", "sha256", "Get-FileHash",
                       "capture_verified = $false", "candidate_pending_visual_review",
                       "M01-S01.capture.json", "Disposable CI fixture", "ZYN-SCREEN-015"):
            self.assertIn(marker, self.script)

    def test_actual_native_secondary_views_not_fake_previews(self):
        for token in ("Save-NativeFollowup", "SendKeys]::SendWait",
                      "M01-S01-continued", "P01-Settings-preview",
                      "P01-Recovery-preview", "P01-Diagnostics-preview",
                      "ZYN-SCREEN-017", "ZYN-SCREEN-019",
                      "candidate_pending_visual_review", "capture_verified = $false"):
            self.assertIn(token, self.script)
        self.assertIn("docs/screenshots/M01/*.png", self.workflow)
        self.assertIn("docs/screenshots/M01/*.capture.json", self.workflow)

    def test_windows_ci_invokes_native_capture_while_process_is_alive(self):
        for marker in ("tests.test_p01_screenshot_capture", "capture_p01_desktop.ps1",
                       "docs/screenshots/M01/M01-S01.png", "ZYNOA_HEAD_SHA",
                       "Verify desktop executable cold boot"):
            self.assertIn(marker, self.workflow)
        self.assertIn("Native Windows desktop build (no release or signature)", self.workflow)
        self.assertEqual(2, self.workflow.count("ref: ${{ github.event.pull_request.head.sha }}"))
        self.assertIn("scripts/capture_p01_desktop\\.ps1", self.workflow)
        self.assertIn('PR_ACTION: ${{ github.event.action }}', self.workflow)
        self.assertIn('changed="$(git diff --name-only HEAD^ HEAD)"', self.workflow)
        self.assertIn('changed="$(git diff --name-only FETCH_HEAD HEAD)"', self.workflow)
        self.assertIn("ZYN-SCREEN-014", self.workflow)
        self.assertIn("[System.Management.Automation.Language.Parser]::ParseFile", self.workflow)
        self.assertIn("ZYN-SCREEN-PARSE", self.workflow)
        self.assertIn("-BuiltSha $builtSha", self.workflow)

if __name__=="__main__":
    unittest.main()
