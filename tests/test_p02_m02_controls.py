"""P02-M02 source regression; native Windows verification remains separate."""
from pathlib import Path
import unittest
ROOT=Path(__file__).resolve().parents[1]
APP=ROOT/"apps"/"desktop"

class M02InteractiveStateContracts(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.app=(APP/"src/App.tsx").read_text(encoding="utf-8")
        cls.wb=(APP/"src/ui/Workbench.tsx").read_text(encoding="utf-8")
        cls.model=(APP/"src/ui/component-states.ts").read_text(encoding="utf-8")
        cls.css=(APP/"src/styles.css").read_text(encoding="utf-8")
        cls.wf=(ROOT/".github/workflows/p01-desktop.yml").read_text(encoding="utf-8")
        cls.node=(APP/"tests/ui-logic.test.mjs").read_text(encoding="utf-8")
    def test_live_session_preferences(self):
        for marker in ('(prefers-color-scheme: dark)', '(prefers-reduced-motion: reduce)',
                       'setTheme("system"); setDensity("comfortable")',
                       'Restore interface defaults',
                       'disabled={theme === "system" && density === "comfortable"}',
                       'aria-live="polite"', 'systemDark={systemDark}', 'reducedMotion={reducedMotion}'):
            self.assertIn(marker,self.app)
        for forbidden in ('localStorage', 'sessionStorage', 'fetch(', 'invoke(', 'setItem('):
            self.assertNotIn(forbidden,self.app)
    def test_gallery_five_truthful_states_and_reset(self):
        for marker in ('componentPreviewStates.map', 'data-preview-state={previewState}',
                       'aria-pressed={previewState === item.id}', 'previewStateDetails(previewState)',
                       'setPreviewState("ready")', 'Show ready example', 'role="status"', 'ILLUSTRATIVE / '):
            self.assertIn(marker,self.wb)
        for state in ("ready","loading","empty","error","offline"):
            self.assertIn('id: "'+state+'"',self.model)
        self.assertIn('test("M02 interactive state explorer',self.node)
        for forbidden in ('fetch(', 'setTimeout(', 'localStorage', 'invoke('):
            self.assertNotIn(forbidden,self.model+self.wb)
    def test_split_reset_and_responsive_feedback(self):
        for marker in ('Restore 40 percent pane split','disabled={split === 40}',
                       'setSplit(40)','aria-live="polite"'):
            self.assertIn(marker,self.wb)
        for marker in ('.shell .gallery-state-explorer','.shell .gallery-state-result',
                       '.shell .settings-live-summary','@media (max-width:950px)'):
            self.assertIn(marker,self.css)
    def test_real_windows_offline_state_keyboard_sequence_uses_valid_sendkeys(self):
        native=(ROOT/"scripts/capture_p01_desktop.ps1").read_text(encoding="utf-8")
        self.assertIn("[System.Windows.Forms.SendKeys]::SendWait('^{2}')",native)
        self.assertIn("[System.Windows.Forms.SendKeys]::SendWait('^{6}')",native)
        self.assertIn("for ($stepIndex = 0; $stepIndex -lt 10; $stepIndex++)",native)
        self.assertNotIn("'^{2}^{6}'",native)
        self.assertIn("P02-T06-GALLERY-OFFLINE",native)

    def test_actual_windows_gallery_five_state_capture_matrix(self):
        capture=(ROOT/"scripts/capture_p01_desktop.ps1").read_text(encoding="utf-8")
        verifier=(ROOT/"tools/verify_p02_native_evidence.py").read_text(encoding="utf-8")
        for state in ("READY","LOADING","EMPTY","ERROR","OFFLINE"):
            self.assertIn("P02-T06-GALLERY-"+state,capture)
            self.assertIn("P02-T06-GALLERY-"+state,verifier)
        self.assertIn("five states must produce distinct real native frames",verifier)

    def test_native_ci_fail_closed(self):
        for marker in ('run: npm install --package-lock-only',
                       'run: npm ci --no-audit --no-fund',
                       'if ($LASTEXITCODE -ne 0) { throw "P02-T02 Python acceptance tests failed" }',
                       'if ($LASTEXITCODE -ne 0) { throw "P02-T02 native evidence audit failed" }',
                       'tests.test_p02_m02_controls -v'):
            self.assertIn(marker,self.wf)
if __name__=="__main__":
    unittest.main()
