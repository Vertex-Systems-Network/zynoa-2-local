"""P02 T13 phase-scoped source and native candidate contracts."""
import json
import re
import tempfile
import unittest
from pathlib import Path
from tools.verify_p02_t13_candidates import verify, INVENTORY

ROOT=Path(__file__).resolve().parents[1]
class T13Contracts(unittest.TestCase):
    def test_exact_canonical_inventory(self):
        centers=json.loads(INVENTORY.read_text(encoding="utf-8"))["centers"]
        self.assertEqual([(c["module"],len(c["screens"]),len(c["options"])) for c in centers],
                         [("M23",9,18),("M24",8,18),("M25",7,14)])
        for center in centers:
            module=center["module"]
            doc=(ROOT/"docs/modules"/(module+".md")).read_text(encoding="utf-8")
            ids=set(re.findall(r"\b"+module+r"-(?:S\d{2}|OPT-\d{2})\b",doc))
            self.assertEqual(ids,{x["id"] for x in center["screens"]+center["options"]})
            self.assertEqual(sorted(x["id"] for x in center["options"]),sorted(i for s in center["screens"] for i in s["options"]))
            for option in center["options"]:
                self.assertIn(option["kind"],("blocked","select","toggle"))
                self.assertTrue(option["reason"])
    def test_actual_ui_and_no_mutation(self):
        view=(ROOT/"apps/desktop/src/ui/SystemCenter.tsx").read_text(encoding="utf-8")
        for token in ('aria-current=','aria-describedby=','tabIndex={0}','tabIndex={-1}','disabled aria-label=','updateCenterDraft','Reset session drafts','centerAvailability','onDiagnostics','No simulated history','filterCenterScreens','returnToScreen','clearSearch'):
            self.assertIn(token,view)
        for token in ("invoke(","fetch(","localStorage","sessionStorage","window.open","dangerouslySetInnerHTML"):
            self.assertNotIn(token,view)
        app=(ROOT/"apps/desktop/src/App.tsx").read_text(encoding="utf-8")
        self.assertIn("<SystemCenter key={view}",app)
        self.assertIn('backup: "backup-center", locations: "data-locations", updates: "update-center"',app)
    def test_native_capture_and_fail_closed(self):
        capture=(ROOT/"scripts/capture_p01_desktop.ps1").read_text(encoding="utf-8")
        for token in ("SystemCenterModule","Capture-SystemTarget","Focus-M26Control","Wait-M26Name","Save-NativeFollowup","Assert-M26Foreground","T13-journey.capture.json"):
            self.assertIn(token,capture)
        with tempfile.TemporaryDirectory() as d:
            with self.assertRaises(OSError):verify(Path(d),"M23","a"*40,"123")
            with self.assertRaises(ValueError):verify(Path(d),"M23","invalid","123")
if __name__=="__main__":unittest.main()
