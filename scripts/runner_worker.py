"""P00 AI worker on an ephemeral GitHub-hosted runner (owner has no own host).

Runs the existing default-denied functional repair loop with REAL local Ollama
inference and REAL rootless Docker, then prints the sanitized receipt.
"""
import json, os, sys, tempfile
from pathlib import Path
from tools.workspace_policy import WorkspaceScope
from tools.dev_fixture_functional_repair_loop import run_fixture_functional_repair

PLAN = {"schema_version": 1, "phase": "P00", "branch": "phase/00-governance",
        "task_id": "P00-T20", "summary": "Repair fixed integer transform fixture",
        "file_proposals": [{"path": "tests/fixtures/integrated.py", "action": "DRAFT_ONLY",
                            "reason": "Re-run isolated fixed test contract"}],
        "checks": ["phase-policy"]}


def main() -> int:
    with tempfile.TemporaryDirectory() as tmp:
        (Path(tmp) / "tests/fixtures").mkdir(parents=True)
        scope = WorkspaceScope(Path(tmp), "P00", "phase/00-governance", ("tests/fixtures",))
        receipt = run_fixture_functional_repair(
            os.environ["ZYNOA_MODEL"], PLAN, scope, expected_task_id="P00-T20",
            enabled=True, operator_ack=True, syntax_enabled=True, execution_grant=True,
            docker_binary=os.environ["ZYNOA_DOCKER"],
            socket_url=f"unix:///run/user/{os.geteuid()}/docker.sock")
    receipt["host"] = {"kind": "github-hosted-runner", "run_id": os.environ.get("GITHUB_RUN_ID"),
                       "sha": os.environ.get("GITHUB_SHA"), "image": os.environ.get("ImageOS")}
    print(json.dumps(receipt, indent=2))
    return 0 if receipt["status"] == "FIXTURE_FUNCTIONAL_PASS_HOST_UNATTESTED" else 1


if __name__ == "__main__":
    sys.exit(main())
