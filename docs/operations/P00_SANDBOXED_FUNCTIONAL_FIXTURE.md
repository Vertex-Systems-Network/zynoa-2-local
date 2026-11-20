# P00 Single-Fixture Functional Execution — Rootless Container Only (Experimental)

**Phase:** P00 · **PR:** [#1](https://github.com/Vertex-Systems-Network/zynoa-2-local/pull/1) (draft / unmerged) · **Task:** P00-T20 **IN_PROGRESS**.

**Scope:** A *trusted operator* can opt in to checking **one small model-authored Python fixture** against a **fixed five-case contract** inside rootless Docker, and on a failure permit **one** new model draft. This is a constrained execution proof-of-concept, not a production sandbox attestation, general code-test runner, editor, autonomous programmer or GitHub writer. CI exercises mocked Docker/Ollama and a trusted literal Python harness reference; the operator's real host is unavailable.

## Why it is different from the prior source-only syntax step

The earlier `docker_syntax_broker.py` only used `compile()` inside Docker but **never ran model-written Python**. This step adds `tools/docker_fixture_runtime_broker.py`, which can execute a model's Python **inside** a separately authorized, no-network/no-repository-mount rootless Linux container, to assess a fixed `solve(x) == 2*x` function contract. The model never receives a shell or command tool. The controller host only validates byte lengths, phase/task/path, hashes and broker receipts: it never imports, parses, compiles or executes the candidate.

`tools/dev_fixture_functional_repair_loop.py` composes these three already-scoped components:

```text
Trusted host: P00-T20 + WorkspaceScope + one flat tests/fixtures/*.py DRAFT_ONLY plan
        |
Four explicit host grants (enabled / operator_ack / syntax_enabled / execution_grant)
        |
Local Ollama fixture model: structured text (no source checkout or credentials)
        |
Existing disposable preview and canonical-plan / source SHA-256 validation
        |
Existing rootless Docker syntax-only broker
        |                    |
   valid syntax          invalid syntax -> one generic model correction
        |
NEW rootless Docker runtime broker: fixed solve(x)=2*x test on 5 integers
        |                    |
   pass (unattested)   failure -> one generic model correction
        |
No more than TWO candidates, ever. No GitHub/checkout writes, no PR merge.
```

The model receives its **own previous candidate** on the second request and one of exactly two fixed feedback strings: `PYTHON_SYNTAX_INVALID_NO_CODE_EXECUTION` or `FIXTURE_TESTS_FAILED_ISOLATION_UNVERIFIED`. Neither raw stdout, stderr, Docker logs, host env, file handles, model tokens, repository sources nor user chat are provided. The original task/branch/plan SHA/path remain immutable. Success is metadata only and cannot authorize a git operation.

## Container isolation contract and warnings

The runtime broker extends the prior syntax policy with **execution-only** host flags:

- Local non-root Linux Docker identity; independently trusted absolute CLI, symlink-denied current-UID rootless Unix socket; rootless daemon, cgroup v2 + systemd driver required.
- Digest-pinned pre-cached official Python image with `--pull never`. Exact image must be independently reviewed by host operator; digest alone is not a signature/vulnerability audit.
- No checkout mounts, source volume, Docker socket inside container, environment secrets, WAN/LAN network or port publishing. Uses `--network none --ipc none --read-only --cap-drop ALL --security-opt no-new-privileges:true --security-opt seccomp=builtin --user 65534:65534`; fixed `--memory 128m --memory-swap 128m --cpus 0.5 --pids-limit 32`, and a tiny noexec tmpfs.
- A fixed in-container parent verifies **effective container-visible** `memory.max`, `pids.max`, `cpu.max`, loopback-only network interfaces and read-only root before taking any candidate input. The parent runs a separate fixed Python child under `-I -S -B`, with a 3-second timeout and discarded stderr; it compares five fixed expected function outputs.
- Timeout or excessive host Docker output causes process termination and a best-effort **targeted exact-container-name** cleanup. Missing cleanup proof terminates with an error.
- The fixed child harness can execute model code, which is fundamentally different from syntax-only compilation. **Only run on an independently secured and attested rootless host.** Rootless Docker is not a guarantee against container/kernal vulnerabilities, abusive sibling processes, malicious procfs access, missing controller delegation, resource exhaustion or test-harness spoofing. A test PASS is an **untrusted signal**, not a safe-to-push authorization.
- Markers and receipts explicitly contain `ISOLATION_UNVERIFIED`; all host/security attestation and deployment fields remain `false`. Even a valid model-generated `solve` is not evidence the full AI application coding workflow works.

Official sources checked 2026-11-20: [Docker rootless](https://docs.docker.com/engine/security/rootless/), [rootless resource limits](https://docs.docker.com/engine/security/rootless/tips/), [Docker run CLI flags](https://docs.docker.com/reference/cli/docker/container/run/), [Docker seccomp policy](https://docs.docker.com/engine/security/seccomp/), [Python isolated mode -I](https://docs.python.org/3.12/using/cmdline.html#cmdoption-I). Rejected (a) host subprocess running arbitrary model code, (b) tool-calling agent controlling Docker argv, (c) promoting a mock Docker PASS to production attestation.

## Test/recovery and operation

```sh
python -m unittest tests.test_docker_fixture_runtime_broker -v
python -m unittest tests.test_dev_fixture_functional_repair_loop -v
python -m unittest discover -s tests -v
python -m scripts.check_pr_task_board
```

Windows policy CI **never launches a real Linux Docker runtime**; Linux/Windows CI Docker and model responses are mocked. An additional trusted **literal reference fixture** is executed by the test harness solely to prove the fixed child test logic; it is not a model-generated candidate or a live rootless Docker run.

A future dedicated, non-root Linux operator host may instantiate the existing `WorkspaceScope` and execute `run_fixture_functional_repair(model, plan, scope, expected_task_id='P00-T20', enabled=True, operator_ack=True, syntax_enabled=True, execution_grant=True, socket_url=<trusted local rootless socket>)` with real independent host authorization. Do not feed a model-provided `syntax_broker` or `runtime_broker` callable (those injection hooks are for trusted unit-test fixtures only). Do not expose this API directly to untrusted user/browser content.

**Still required:** actual dedicated host/supervisor and heartbeat; live model inference; security review and host cgroup delegation + namespace/credential negative tests; host-controlled safe file-handle edits in a disposable worktree; real changed-source test execution and repair; trusted restricted GitHub write principal; CI failure/issue reconciliation; non-bypass merge and verified SHA. [Issue #3](https://github.com/Vertex-Systems-Network/zynoa-2-local/issues/3) stays OPEN; P00-T20 IN_PROGRESS, T17/T19/T21–T24 BLOCKED; PR #1 DRAFT; P01 not started. No M22 GUI screenshots or published Wiki.
