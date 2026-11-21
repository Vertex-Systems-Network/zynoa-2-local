"""P00 AI worker on an ephemeral GitHub-hosted runner (owner has no own host).

Runs the existing default-denied functional repair loop with REAL local Ollama
inference and REAL rootless Docker, then prints the sanitized receipt.
"""
import json, os, sys, tempfile
from pathlib import Path
from tools.workspace_policy import WorkspaceScope
from tools.dev_fixture_functional_repair_loop import run_fixture_functional_repair
from tools.docker_fixture_runtime_broker import run_python_fixture_tests
import subprocess

# P00-T19: hostile candidates must never PASS, must not hang the host, and must
# leave no container behind. Each also defines a correct solve() so a PASS would
# mean the attack itself succeeded silently.
_GOOD = "def solve(x):\n    return x * 2\n"
HOSTILE = {
    "network": "import socket\nsocket.create_connection(('1.1.1.1', 80), 2)\n" + _GOOD,
    "cpu_hang": "while True:\n    pass\n" + _GOOD,
    "memory": "x = bytearray(1024 * 1024 * 1024)\n" + _GOOD,
    "fork": "import os\nfor _ in range(200):\n    os.fork()\n" + _GOOD,
    "write_root": "open('/etc/zynoa', 'w').write('x')\n" + _GOOD,
}


def hostile_checks(scope, docker, sock) -> dict:
    out = {}
    for name, src in HOSTILE.items():
        try:
            status = run_python_fixture_tests(
                PLAN, src, scope, expected_task_id="P00-T20", enabled=True,
                operator_ack=True, execution_grant=True,
                docker_binary=docker, socket_url=sock)["status"]
        except Exception as exc:  # broker refusal/timeout is a contained outcome
            status = "REFUSED:" + type(exc).__name__
        left = subprocess.run([docker, "ps", "-aq"], capture_output=True, text=True,
                              check=True).stdout.strip()
        assert "PASS" not in status, (name, status)
        assert not left, (name, "container left behind")
        out[name] = status
    return out

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
        receipt["hostile_containment"] = hostile_checks(
            scope, os.environ["ZYNOA_DOCKER"], f"unix:///run/user/{os.geteuid()}/docker.sock")
    receipt["host"] = {"kind": "github-hosted-runner", "run_id": os.environ.get("GITHUB_RUN_ID"),
                       "sha": os.environ.get("GITHUB_SHA"), "image": os.environ.get("ImageOS")}
    print(json.dumps(receipt, indent=2))
    return 0 if receipt["status"] == "FIXTURE_FUNCTIONAL_PASS_HOST_UNATTESTED" else 1


if __name__ == "__main__":
    sys.exit(main())
