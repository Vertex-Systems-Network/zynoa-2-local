"""P00 fixed functional fixture repair policy; mocked model and Docker in CI.

No model-generated Python is executed by this test suite. Runtime broker
invocations are stubbed, and receipt spoofing is denied.
"""
from __future__ import annotations

import hashlib
import json
import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch

from tools.dev_fixture_functional_repair_loop import (
    FunctionalRepairDenied, run_fixture_functional_repair,
)
from tools.docker_fixture_runtime_broker import FixtureRuntimeDenied
from tools.docker_syntax_broker import DEFAULT_IMAGE, DockerSyntaxDenied
from tools.local_fixture_drafter import make_fixture_request
from tools.workspace_policy import WorkspaceScope

TASK="P00-T20"
FILE="tests/fixtures/integrated.py"
BAD="def solve(x):\n    return x\n"
GOOD="def solve(x):\n    return x * 2\n"
BROKEN="def solve(\n"
SVALID="PYTHON_SYNTAX_VALID_NO_CODE_EXECUTION"
SINVALID="PYTHON_SYNTAX_INVALID_NO_CODE_EXECUTION"
TPASS="FIXTURE_TESTS_PASSED_ISOLATION_UNVERIFIED"
TFAIL="FIXTURE_TESTS_FAILED_ISOLATION_UNVERIFIED"


class FunctionalLoopTests(unittest.TestCase):
    def setUp(self):
        temp=tempfile.TemporaryDirectory()
        self.addCleanup(temp.cleanup)
        self.root=Path(temp.name)
        (self.root/"tests/fixtures").mkdir(parents=True)
        self.scope=WorkspaceScope(self.root,"P00","phase/00-governance",("tests/fixtures",))
        self.model_sources=[BAD,GOOD]
        self.syntax_status=[SVALID,SVALID]
        self.runtime_status=[TFAIL,TPASS]
        self.model_calls=[]
        self.syntax_calls=[]
        self.runtime_calls=[]

    def plan(self):
        return {"schema_version":1,"phase":"P00","branch":"phase/00-governance",
                "task_id":TASK,"summary":"Repair fixed integer transform fixture",
                "file_proposals":[{"path":FILE,"action":"DRAFT_ONLY",
                                   "reason":"Re-run isolated fixed test contract"}],
                "checks":["phase-policy"]}

    def model(self,base,payload):
        ctx=json.loads(payload["messages"][1]["content"])
        self.model_calls.append(ctx)
        self.assertEqual("http://127.0.0.1:11434",base)
        self.assertNotIn("tools",payload)
        _,_,path,digest=make_fixture_request(
            "coder:7b",self.plan(),self.scope,expected_task_id=TASK)
        self.assertEqual(FILE,ctx["path"])
        self.assertEqual(digest,ctx["plan_sha256"])
        source=self.model_sources[min(len(self.model_calls)-1,len(self.model_sources)-1)]
        return {"done":True,"done_reason":"stop","model":"coder:7b",
                "message":{"role":"assistant","content":json.dumps({
                    "schema_version":1,"phase":"P00",
                    "branch":"phase/00-governance","task_id":TASK,
                    "plan_sha256":digest,"path":path,"source":source
                })}}

    def syntax(self,plan,source,scope,**options):
        self.syntax_calls.append((source,options))
        self.assertEqual(self.plan(),plan)
        self.assertIs(self.scope,scope)
        self.assertIs(options["enabled"],True)
        self.assertEqual(TASK,options["expected_task_id"])
        state=self.syntax_status[min(len(self.syntax_calls)-1,len(self.syntax_status)-1)]
        return {"status":state,"phase":"P00","task_id":TASK,
                "candidate_sha256":hashlib.sha256(source.encode()).hexdigest(),
                "image_digest":DEFAULT_IMAGE.split("@",1)[1],
                "docker_commands_executed":4,
                "rootless_daemon_status_observed":True,
                "workspace_files_written":0,"github_writes":0,
                "model_source_executed":False,
                "independent_host_sandbox_verified":False,
                "persistent_worker_deployed":False}

    def runtime(self,plan,source,scope,**options):
        self.runtime_calls.append((source,options))
        self.assertEqual(self.plan(),plan)
        self.assertIs(self.scope,scope)
        self.assertIs(options["enabled"],True)
        self.assertIs(options["operator_ack"],True)
        self.assertIs(options["execution_grant"],True)
        self.assertEqual(TASK,options["expected_task_id"])
        status=self.runtime_status[min(len(self.runtime_calls)-1,len(self.runtime_status)-1)]
        return {"status":status,"phase":"P00","task_id":TASK,
                "candidate_sha256":hashlib.sha256(source.encode()).hexdigest(),
                "image_digest":DEFAULT_IMAGE.split("@",1)[1],
                "fixed_test_cases":5,
                "container_model_source_execution_requested":True,
                "controller_host_source_executed":False,
                "workspace_files_written":0,"github_writes":0,
                "independent_host_sandbox_verified":False,
                "real_container_run_independently_attested":False,
                "persistent_worker_deployed":False}

    def execute(self,**kwargs):
        return run_fixture_functional_repair(
            "coder:7b",self.plan(),self.scope,expected_task_id=TASK,
            enabled=True,operator_ack=True,syntax_enabled=True,
            execution_grant=True,
            model_transport=self.model,
            syntax_broker=self.syntax,runtime_broker=self.runtime,**kwargs)

    def test_functional_failure_then_model_correction_and_pass(self):
        before=[p.relative_to(self.root) for p in self.root.rglob("*")]
        report=self.execute()
        self.assertEqual("FIXTURE_FUNCTIONAL_PASS_HOST_UNATTESTED",report["status"])
        self.assertEqual(2,report["attempt_count"])
        self.assertTrue(report["repair_attempted"])
        self.assertEqual([BAD,GOOD],[x[0] for x in self.syntax_calls])
        self.assertEqual([BAD,GOOD],[x[0] for x in self.runtime_calls])
        self.assertEqual(TFAIL,report["attempts"][0]["functional_status"])
        self.assertEqual(TPASS,report["attempts"][1]["functional_status"])
        self.assertEqual(BAD,self.model_calls[1]["previous_candidate"])
        self.assertEqual(TFAIL,self.model_calls[1]["prior_result"])
        self.assertEqual(self.model_calls[0]["plan_sha256"],
                         self.model_calls[1]["plan_sha256"])
        self.assertNotIn("docker",json.dumps(self.model_calls))
        self.assertNotIn("github",json.dumps(self.model_calls))
        self.assertNotIn(BAD,json.dumps(report))
        self.assertNotIn(GOOD,json.dumps(report))
        self.assertEqual(0,report["workspace_files_written"])
        self.assertEqual(0,report["repository_patches_applied"])
        self.assertEqual(0,report["github_writes"])
        self.assertFalse(report["independent_host_sandbox_verified"])
        self.assertFalse(report["real_model_execution_independently_verified"])
        self.assertFalse(report["persistent_worker_deployed"])
        self.assertTrue(report["functional_runtime_broker_invoked"])
        self.assertEqual(before,[p.relative_to(self.root) for p in self.root.rglob("*")])

    def test_syntax_failure_then_fixed_model_correction_and_pass(self):
        self.model_sources=[BROKEN,GOOD]
        self.syntax_status=[SINVALID,SVALID]
        self.runtime_status=[TPASS]
        report=self.execute()
        self.assertEqual("FIXTURE_FUNCTIONAL_PASS_HOST_UNATTESTED",report["status"])
        self.assertEqual(2,len(self.syntax_calls))
        self.assertEqual(1,len(self.runtime_calls))
        self.assertEqual("NOT_RUN",report["attempts"][0]["functional_status"])
        self.assertEqual(SINVALID,self.model_calls[1]["prior_result"])
        self.assertEqual(BROKEN,self.model_calls[1]["previous_candidate"])

    def test_first_pass_needs_only_one_model_candidate(self):
        self.model_sources=[GOOD]
        self.runtime_status=[TPASS]
        report=self.execute()
        self.assertEqual(1,report["attempt_count"])
        self.assertEqual(1,len(self.model_calls))
        self.assertEqual(1,len(self.syntax_calls))
        self.assertEqual(1,len(self.runtime_calls))

    def test_two_functional_failures_stop_without_lying(self):
        self.model_sources=[BAD,"def solve(x):\n    return x + 1\n"]
        self.runtime_status=[TFAIL,TFAIL]
        report=self.execute()
        self.assertEqual("FIXTURE_FUNCTIONAL_UNRESOLVED",report["status"])
        self.assertEqual(2,report["max_attempts"])
        self.assertEqual(2,len(self.model_calls))
        self.assertEqual(2,len(self.runtime_calls))

    def test_two_invalid_syntaxes_do_not_run_untrusted_source(self):
        self.model_sources=[BROKEN,"def still_broken(\n"]
        self.syntax_status=[SINVALID,SINVALID]
        report=self.execute()
        self.assertEqual("FIXTURE_FUNCTIONAL_UNRESOLVED",report["status"])
        self.assertEqual(0,len(self.runtime_calls))
        self.assertFalse(report["functional_runtime_broker_invoked"])

    def test_repeated_model_draft_cannot_loop_indefinitely(self):
        self.model_sources=[BAD,BAD]
        with self.assertRaises(FunctionalRepairDenied):
            self.execute()
        self.assertEqual(2,len(self.model_calls))
        self.assertEqual(1,len(self.syntax_calls))
        self.assertEqual(1,len(self.runtime_calls))

    def test_optins_must_be_explicit_true_not_truthy(self):
        for flags in ({},{"enabled":True},{"enabled":True,"operator_ack":True},
                      {"enabled":True,"operator_ack":True,"syntax_enabled":True},
                      {"enabled":1,"operator_ack":True,"syntax_enabled":True,
                       "execution_grant":True}):
            with self.subTest(flags=flags),self.assertRaises(FunctionalRepairDenied):
                run_fixture_functional_repair(
                    "coder:7b",self.plan(),self.scope,expected_task_id=TASK,
                    model_transport=self.model,syntax_broker=self.syntax,
                    runtime_broker=self.runtime,**flags)
        self.assertFalse(self.model_calls)
        self.assertFalse(self.syntax_calls)
        self.assertFalse(self.runtime_calls)

    def test_wrong_task_or_invalid_plan_never_calls_model(self):
        for task in ("P01-T20","P00-T19","P00-T26",""):
            with self.subTest(task=task),self.assertRaises(FunctionalRepairDenied):
                run_fixture_functional_repair(
                    "coder:7b",self.plan(),self.scope,expected_task_id=task,
                    enabled=True,operator_ack=True,syntax_enabled=True,
                    execution_grant=True,model_transport=self.model,
                    syntax_broker=self.syntax,runtime_broker=self.runtime)
        bad=self.plan()
        bad["file_proposals"][0]["path"]="AGENTS.md"
        with self.assertRaises(FunctionalRepairDenied):
            run_fixture_functional_repair(
                "coder:7b",bad,self.scope,expected_task_id=TASK,
                enabled=True,operator_ack=True,syntax_enabled=True,
                execution_grant=True,model_transport=self.model,
                syntax_broker=self.syntax,runtime_broker=self.runtime)
        self.assertFalse(self.model_calls)

    def test_no_real_rootless_docker_preflight_rejects_model_first(self):
        with patch("tools.dev_fixture_functional_repair_loop._docker_binary",
                   side_effect=DockerSyntaxDenied("private host path")):
            with self.assertRaises(FunctionalRepairDenied):
                run_fixture_functional_repair(
                    "coder:7b",self.plan(),self.scope,expected_task_id=TASK,
                    enabled=True,operator_ack=True,syntax_enabled=True,
                    execution_grant=True,model_transport=self.model)
        self.assertFalse(self.model_calls)

    def test_forged_functional_receipt_refused(self):
        fields=[("status","PASS"),("phase","P01"),("task_id","P00-T19"),
                ("candidate_sha256","0"*64),("image_digest","sha256:bad"),
                ("fixed_test_cases",True),
                ("container_model_source_execution_requested",False),
                ("controller_host_source_executed",True),
                ("github_writes",1),
                ("workspace_files_written",True),
                ("independent_host_sandbox_verified",True),
                ("real_container_run_independently_attested",True),
                ("persistent_worker_deployed",True)]
        for name,wrong in fields:
            self.model_calls.clear()
            self.syntax_calls.clear()
            self.runtime_calls.clear()
            def forged(*args,**kwargs):
                x=self.runtime(*args,**kwargs)
                x[name]=wrong
                return x
            with self.subTest(field=name),self.assertRaises(FunctionalRepairDenied):
                run_fixture_functional_repair(
                    "coder:7b",self.plan(),self.scope,expected_task_id=TASK,
                    enabled=True,operator_ack=True,syntax_enabled=True,
                    execution_grant=True,model_transport=self.model,
                    syntax_broker=self.syntax,runtime_broker=forged)
            self.assertEqual(1,len(self.model_calls))
            self.assertEqual(1,len(self.runtime_calls))

    def test_sandbox_transport_error_never_retries_or_leaks(self):
        secret="DOCKER-UNTRUSTED-OUTPUT"
        def fail(*args,**kwargs):
            raise FixtureRuntimeDenied(secret)
        with self.assertRaises(FunctionalRepairDenied) as cm:
            run_fixture_functional_repair(
                "coder:7b",self.plan(),self.scope,expected_task_id=TASK,
                enabled=True,operator_ack=True,syntax_enabled=True,
                execution_grant=True,model_transport=self.model,
                syntax_broker=self.syntax,runtime_broker=fail)
        self.assertNotIn(secret,str(cm.exception))
        self.assertEqual(1,len(self.model_calls))

    def test_model_transport_failure_reports_safe_category(self):
        def fail(*args, **kwargs):
            raise ValueError("PRIVATE-MODEL-RESPONSE")
        with self.assertRaises(FunctionalRepairDenied) as cm:
            run_fixture_functional_repair(
                "coder:7b",self.plan(),self.scope,expected_task_id=TASK,
                enabled=True,operator_ack=True,syntax_enabled=True,
                execution_grant=True,model_transport=fail,
                syntax_broker=self.syntax,runtime_broker=self.runtime)
        self.assertIn("local fixture model response unavailable",str(cm.exception))
        self.assertNotIn("PRIVATE-MODEL-RESPONSE",str(cm.exception))
        self.assertEqual([],self.syntax_calls)


if __name__=="__main__":
    unittest.main()
