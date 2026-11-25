"""Read-only phase continuation: real job metadata, fixed paths, no test or state changes."""
import copy
import unittest
from pathlib import Path
from tools.p02_ci_continuation import (
    ContinuationDenied, REPO, BRANCH, SOURCE_FILES, select_task, route_job,
    validate_candidate, verify_remote,
)

SHA = "a" * 40
STATE = {"phase":"P02","phase_status":"IN_PROGRESS","active_branch":BRANCH,
         "primary_pr":12,"lease_holder":None,"worker_running":False}
TASKS = [{"id":"P02-T11","status":"IN_PROGRESS"},
         {"id":"P02-T12","status":"IN_PROGRESS"},{"id":"P02-T13","status":"TODO"}]
RUN = {"id":123,"run_attempt":1,"event":"pull_request","head_sha":SHA,
       "head_branch":BRANCH,"path":".github/workflows/p01-desktop.yml",
       "repository":{"full_name":REPO},"head_repository":{"full_name":REPO}}
JOB = {"id":456,"run_id":123,"name":"desktop-windows","status":"completed",
       "conclusion":"failure","steps":[{"name":"P02 live NVDA speech plus real Windows keyboard journey (fail closed)",
                                          "conclusion":"failure"}]}
PR = {"number":12,"state":"open","merged":False,
      "head":{"sha":SHA,"ref":BRANCH,"repo":{"full_name":REPO}},
      "base":{"ref":"main","repo":{"full_name":REPO}}}
BRANCH_FACT = {"name":BRANCH,"commit":{"sha":SHA}}

class ContinuationTests(unittest.TestCase):
    def test_order_and_blocked_first(self):
        self.assertEqual(select_task(STATE,TASKS),"P02-T12")
        t=copy.deepcopy(TASKS); t[1]["status"]="DONE"
        self.assertEqual(select_task(STATE,t),"P02-T13")
        t[2]["status"]="DONE"
        self.assertEqual(select_task(STATE,t),"P02-T11")
        t=copy.deepcopy(TASKS); t[1]["status"]="BLOCKED"
        self.assertIsNone(select_task(STATE,t))
        self.assertIsNone(select_task(dict(STATE,lease_holder="other@now"),TASKS))

    def test_exact_remote_identity_and_stale(self):
        self.assertEqual(verify_remote(PR,BRANCH_FACT,RUN,JOB,SHA,123,1),"failure")
        for obj,key,value in ((PR,"state","closed"),(RUN,"head_sha","b"*40),
                              (RUN,"event","push"),(JOB,"run_id",124),
                              (JOB,"status","in_progress"),(RUN,"run_attempt",2)):
            p,b,r,j=map(copy.deepcopy,(PR,BRANCH_FACT,RUN,JOB))
            target={id(PR):p,id(RUN):r,id(JOB):j}[id(obj)]
            target[key]=value
            with self.assertRaises(ContinuationDenied):
                verify_remote(p,b,r,j,SHA,123,1)

    def test_failure_routes_only_fixed_product_paths(self):
        action,paths=route_job("P02-T12",JOB)
        self.assertEqual(action,"DRAFT_REPAIR")
        self.assertEqual(paths,("apps/desktop/src/ui/HelpCenter.tsx","apps/desktop/src/ui/CommandPalette.tsx"))
        self.assertTrue(set(paths)<=SOURCE_FILES)
        self.assertEqual(route_job("P02-T12",dict(JOB,conclusion="success",steps=[]))[0],"REVIEW_EVIDENCE")
        self.assertEqual(route_job("P02-T12",dict(JOB,steps=[{"name":"arbitrary","conclusion":"failure"}]))[0],"UNROUTED_FAILURE")
        self.assertEqual(route_job("P02-T13",JOB)[0],"REVIEW_EVIDENCE")

    def test_mixed_and_spoofed_step_names_do_not_authorize_draft(self):
        m26={"name":"P02-T12 M26 twenty native option candidates","conclusion":"failure"}
        self.assertEqual(route_job("P02-T12",dict(JOB,steps=[m26])),
                         ("DRAFT_REPAIR",("apps/desktop/src/ui/ChangeCenter.tsx",)))
        for other in ({"name":"P02-T12 M26 unregistered step","conclusion":"failure"},
                      {"name":"Desktop shell and IPC safety contracts","conclusion":"failure"},
                      JOB["steps"][0]):
            self.assertEqual(route_job("P02-T12",dict(JOB,steps=[m26,other])),
                             ("UNROUTED_FAILURE",()))
        self.assertEqual(route_job("P02-T12",dict(JOB,steps=[])),
                         ("UNROUTED_FAILURE",()))

    def test_candidate_anchor_and_protected_paths(self):
        path="apps/desktop/src/ui/HelpCenter.tsx"
        sources={path:"const item = 1;\nconst other = 2;\n"}
        candidate={"action":"PROPOSE_EDIT","path":path,"old":"const item = 1;",
                   "new":"const item = 2;","reason":"Improve focus behavior"}
        self.assertEqual(validate_candidate(candidate,sources)["replacement"],"const item = 2;\nconst other = 2;\n")
        for patch in (dict(candidate,path=".github/workflows/p01-desktop.yml"),
                      dict(candidate,old="missing"),dict(candidate,new=""),
                      dict(candidate,new=candidate["old"]),dict(candidate,extra=True),
                      dict(candidate,reason="bad\ntext")):
            with self.assertRaises(ContinuationDenied):
                validate_candidate(patch,sources)
        with self.assertRaises(ContinuationDenied):
            validate_candidate(candidate,{path:sources[path]+sources[path]})
        self.assertIsNone(validate_candidate({"action":"NO_SAFE_EDIT","path":"","old":"","new":"","reason":"Need native evidence"},sources))

if __name__=="__main__":
    unittest.main()
