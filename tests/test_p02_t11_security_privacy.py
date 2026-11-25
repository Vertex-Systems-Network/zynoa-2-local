"""Fail-closed negative regression for T11 security/privacy and PR privilege boundaries."""
from pathlib import Path
import unittest
from tools.verify_p02_t11_security_privacy import (
    audit_source_contract, audit_sources, verify_premerge_state, P02SecurityViolation, FRONTEND,
)
ROOT=Path(__file__).resolve().parents[1]
def fixtures():
    import json
    def contents(x): return (ROOT/x).read_text(encoding="utf-8")
    return [
      json.loads(contents("apps/desktop/src-tauri/tauri.conf.json")),
      json.loads(contents("apps/desktop/src-tauri/capabilities/main-readonly.json")),
      contents("apps/desktop/src-tauri/src/ipc.rs"),
      {x:contents(x) for x in FRONTEND},
      contents(".github/workflows/p01-desktop.yml"),
      json.loads(contents("docs/state/PHASE.json")),
      json.loads(contents("docs/state/pr-tasks/P02.json"))
    ]
class SecurityReviewTests(unittest.TestCase):
    def test_current_tree_meets_narrow_security_contract(self):
        r=audit_source_contract(*fixtures()[:5])
        self.assertEqual(r["frontend_files_reviewed"],len(FRONTEND))
        self.assertTrue(r["strict_content_security_policy_verified"])
        self.assertTrue(r["tauri_readonly_capability_verified"])
        self.assertFalse(r["protected_merge_verified"])
        self.assertFalse(r["full_narrator_certified"])
    def test_broader_ipc_privileges_or_csp_are_denied(self):
        for path,value in (
            ((1,"permissions"),["allow-workspace-handshake","shell:allow-execute"]),
            ((1,"windows"),["main","unexpected"]),
            ((0,"app","security","capabilities"),["main-readonly","open-network"]),
            ((0,"app","security","csp"),"default-src *; script-src 'unsafe-eval'"),
        ):
            v=fixtures()
            current=v[path[0]]
            for name in path[1:-1]:current=current[name]
            current[path[-1]]=value
            with self.subTest(path=path),self.assertRaises(P02SecurityViolation):
                audit_source_contract(*v[:5])
    def test_fetch_html_injection_and_persistent_browser_storage_are_denied(self):
        for injected in ("fetch('https://example.org');","dangerouslySetInnerHTML",
                         "localStorage.setItem('key','value');","eval(code);"):
            v=fixtures()
            v[3]["apps/desktop/src/ui/HelpCenter.tsx"]+="\n"+injected
            with self.subTest(injected=injected),self.assertRaises(P02SecurityViolation):
                audit_source_contract(*v[:5])
    def test_untrusted_pr_permissions_or_fake_done_state_are_denied(self):
        v=fixtures();v[4]+="\npull-requests: write"
        with self.assertRaises(P02SecurityViolation):audit_source_contract(*v[:5])
        v=fixtures()
        v[5].update(phase="P02",phase_status="IN_PROGRESS")
        for task in v[6]["tasks"]:
            if task["id"]=="P02-T10": task["status"]="DONE"
            if task["id"]=="P02-T11": task["status"]="IN_PROGRESS"
        verify_premerge_state(v[5],v[6])
        next(t for t in v[6]["tasks"] if t["id"]=="P02-T11")["status"]="DONE"
        with self.assertRaises(P02SecurityViolation):audit_sources(*v)
    def test_premerge_gate_rejects_closed_or_later_phase(self):
        v=fixtures()
        for task in v[6]["tasks"]:
            if task["id"]=="P02-T10": task["status"]="DONE"
            if task["id"]=="P02-T11": task["status"]="IN_PROGRESS"
        for phase,status in (("P02","MERGED_VERIFIED"),("P03","IN_PROGRESS")):
            v[5].update(phase=phase,phase_status=status)
            with self.subTest(phase=phase,status=status),self.assertRaises(P02SecurityViolation):
                audit_sources(*v)
        self.assertTrue(audit_source_contract(*v[:5])["strict_content_security_policy_verified"])
    def test_broken_readonly_native_contract_is_rejected(self):
        v=fixtures()
        v[2]=v[2].replace("writable: false","writable: true")
        with self.assertRaises(P02SecurityViolation):audit_source_contract(*v[:5])
if __name__=="__main__":unittest.main()
