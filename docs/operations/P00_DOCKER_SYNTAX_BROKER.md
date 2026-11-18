# P00 Rootless Docker Python Syntax Broker — Opt-in Execution Contract

**Module:** M22 • **Phase:** P00 • **PR:** [#1](https://github.com/Vertex-Systems-Network/zynoa-2-local/pull/1) • **Subtask:** P00-T26 (broker implementation).

**Present capability:** `tools/docker_syntax_broker.py` contains an explicit, deny-by-default Linux rootless Docker gate that can syntax-check a short AI-produced Python **fixture only** inside a pre-approved, digest-pinned container. It never executes the candidate's compiled code, never mounts the repository or user data, never creates GitHub commits/issues and never changes the active phase. **Tests exercise a mocked daemon, not a deployed user-host sandbox.** P00-T19 real OS isolation and P00-T20 full automated code patch/test/repair remain **unfinished**.

## Why this boundary is necessary

The previous [structured model planning contract](P00_LOCAL_MODEL_PLANNING.md) and [ephemeral fixture preview](P00_FIXTURE_DRAFT_STAGING.md) validate proposals but cannot run trustworthy syntax tests for untrusted source in the privileged controller. Running or even AST parsing the candidate directly on a host is not a safe execution boundary. A separate restricted runtime is required, with its Docker socket and image controlled exclusively by an independently authorized developer service.

### Official sources, checked 2026-11-18

- [Docker container run reference](https://docs.docker.com/reference/cli/docker/container/run/): `--network none`, `--read-only`, `--cap-drop ALL`, `--security-opt no-new-privileges`, `--user`, `--pids-limit`, `--memory`, `--cpus`, `--tmpfs`.
- [Docker rootless mode](https://docs.docker.com/engine/security/rootless/): daemon and containers run without root privileges; operator must still audit user namespaces, host service identity and Docker socket.
- [Docker rootless resource limits](https://docs.docker.com/engine/security/rootless/tips/): CPU, memory and PID cgroup controls may be **silently ignored** without cgroup v2 + systemd; delegation must also be verified on the actual host. The broker refuses an unattested `CgroupVersion` or `CgroupDriver`.
- [Docker image digests](https://docs.docker.com/reference/cli/docker/image/pull/): digests prevent silent mutable tag changes. The pinned official Python image reference was observed via [Docker Hub's 3.12-alpine image page](https://hub.docker.com/layers/library/python/3.12-alpine/images/sha256-a3ac3aabca1f7807d610421857539031b8e03e9ce9c7ff57576528ac07d0f970); the reference must be independently checked by the trusted operator before offline caching. **A digest is not an image-signature or vulnerability audit.**

## Exact trust flow

```text
Host creates WorkspaceScope + independently expected P00 task ID
                    |
Existing model returns DRAFT_ONLY tests/fixtures/<name>.py proposal
                    |
plan_python_syntax() rechecks task/phase/branch and source bounds
                    |
Run is DISABLED by default; trusted host must explicitly enable
                    |
Validate non-root POSIX identity, absolute Docker binary, nonlinked
current-UID rootless Unix socket, and Docker daemon security options
                    |
Require Docker INFO: rootless + cgroup v2 + systemd driver
                    |
Pre-cached digest-pinned official Python image, --pull never
                    |
Docker --network none, --read-only, --cap-drop ALL, no-new-privileges,
--user 65534, PID/memory/CPU limits, private /tmp, no host bind mounts
                    |
stdin candidate bytes -> host-controlled python -I -S -B -c compiler
                    |
Only known success/invalid markers accepted; stderr not returned
                    |
Sanitized SHA-256 result; NO candidate execution, no workspace/GitHub write
```

### Defined interface

`plan_python_syntax(plan, candidate, scope, *, expected_task_id, image=DEFAULT_IMAGE)` validates the plan as **data** and returns a hash-bound internal `SyntaxJob`, without calling Docker or opening the workspace. The candidate must be one UTF-8 `tests/fixtures/*.py` file, limited by the existing 8 KiB/200-line text contract. The model cannot set the image, Docker daemon URL, command, environment, mounts, working directory, execution mode or task authority.

`run_python_syntax(plan, candidate, scope, *, expected_task_id, image, enabled=False, docker_binary, socket_url, runner)` **revalidates** the original plan and candidate against the trusted host `WorkspaceScope`, rather than accepting an arbitrary model-created `SyntaxJob`. The default `enabled=False` rejects immediately before any Docker request. The trusted host must independently supply a bounded local configuration, a non-root Linux identity, and a Docker socket at `unix:///run/user/<uid>/docker.sock`. It refuses `/var/run/docker.sock`, remote TCP Docker, unknown/linked CLI paths and non-rootless or unconfirmed cgroup configurations.

**Exact image approval (P00 security correction, 2026-11-18):** A Docker Hub namespace and a syntactically valid `sha256` digest are not themselves approval. The broker now accepts only `DEFAULT_IMAGE` in its host-maintained `_APPROVED_IMAGES` set; a different correctly formatted digest is rejected **before Docker CLI/daemon access**, even when the run was otherwise enabled. To rotate the Python base image, an authorized developer must review its origin, compatibility and vulnerability status and update this allowlist through the *same protected phase PR* with regression evidence. This code assertion is distinct from independent deployed-host image verification and resource/isolation attestation. See [Docker policy image validation](https://docs.docker.com/build/policies/validate-images/) and [digest reference semantics](https://docs.docker.com/reference/cli/docker/image/pull/).

The fixed command has no `--privileged`, `--volume`, `--mount`, `--device`, `--publish`, Docker socket mount, shell expansion or model-controlled CLI args. `--pull never` prevents any implicit runtime network download; the allowed image must be **pre-cached and verified by an operator outside the AI job**. The candidate bytes are sent to STDIN; they are compiled **inside** the limited container but not evaluated or executed. This is a syntax check, **not a functional test**.

`run_python_syntax` returns only `PYTHON_SYNTAX_VALID_NO_CODE_EXECUTION` or `PYTHON_SYNTAX_INVALID_NO_CODE_EXECUTION`, exact P00 task, candidate SHA-256, pinned image digest, no-source-execution and zero GitHub/workspace writes. Any missing host authority, Docker failure, output mismatch, unexpected response, resource-limit uncertainty or ambiguous cleanup yields `DockerSyntaxDenied` and cannot advance task/phase.

## Model safety, recovery, warnings

- Docker CLI receives an environment containing only `HOME`, `PATH` and a fresh empty `DOCKER_CONFIG`. No GitHub token, user's chat history, workspace folders, SSH keys, model store or provider credentials are forwarded to Docker CLI or container.
- Before syntax checking, the broker checks Docker security options for an exact `rootless` marker, plus `CgroupVersion=2` and `CgroupDriver=systemd`. **Additionally, the fixed compiler script first reads the effective in-container cgroup-v2 `memory.max`, `pids.max` and `cpu.max`: it rejects `max`, missing, malformed, or ceilings exceeding 128 MiB, 32 PIDs, or 0.5 CPU. It also requires only the loopback interface and a read-only root filesystem.** Failure exits without either syntax marker. This is stronger than trusting daemon flags, but operators must still independently test delegated controllers and adversarial containment on the real host before P00-T19 can pass.
- Each container name is random and prefixed `zynoa-p00-syntax-`; fixed labels identify P00 syntax-only jobs. Normal `--rm` removes the container. On timeout it attempts `docker rm --force <exact generated name>`; unsuccessful cleanup fails closed and must be investigated. A future supervisor needs independently verified crash-recovery reclamation.
- Output limits and exact markers prevent stdout/stderr or model-written content being treated as a command or sensitive diagnostic. Python syntax errors are classified without returning raw code snippets.
- Docker and containers share the host kernel: rootless mode and cgroup controls reduce exposure but **do not make arbitrary generated code safe enough for deployment without host hardening, image/provenance review and an independent test host**.
- Native Windows Docker Desktop is **not automatically considered the same security boundary**. Windows CI checks the static command/policy, not a live Linux rootless service; proper Windows/WSL2 host isolation still needs design, installation and actual tests.

## Verified vs unverified

| Acceptance criterion | Source/CI contract | Status |
|---|---|---|
| Model cannot select image, command, socket, mount or scope | `tests/test_docker_syntax_broker.py` | Unit coverage |
| Only digest-pinned image; no implicit pull | Source arg policy | Unit coverage |
| No rootful/local TCP or unauthenticated Docker execution | Socket/daemon attestation gate | Unit coverage; actual host UNTESTED |
| cgroup v2 + systemd required or refuse | Daemon info checks | Mock coverage; actual host UNTESTED |
| In-container enforcement before any untrusted parsing | Runtime guard for memory.max/pids.max/cpu.max, read-only root, loopback interface | Trusted-code unit semantics and mocked Docker output only; **actual container UNTESTED** |
| Fixed memory/PID/CPU/network/filesystem restrictions | Docker command policy | Unit coverage; actual enforcement UNTESTED |
| Candidate only compiled, never executed | Fixed compiler source | Mock coverage; no live container observed |
| Timeout targeted cleanup and sanitized receipts | Policy/tests | Mock coverage |
| Real rootless host with patched daemon and delegated cgroups | Independently provisioned worker required | **BLOCKED** |
| Real isolated Python compilation and filesystem/network negative test | End-to-end host CI/worker proof | **BLOCKED** |
| Actual AI-generated edits, tests, repair, PR update | Separate broker/worktree/CI gates | **BLOCKED** |

### Operator sequence (not performed by GitHub connector)

1. Provision a dedicated non-admin Linux account on a user-controlled worker machine. Install and verify **rootless** Docker, seccomp, user-namespace support, systemd cgroup v2 delegation and safe Docker socket mode/ownership. Keep Docker daemon/admin credentials outside AI reach.
2. Scan and independently verify the pinned image, then cache it using an operator-approved process. Do not grant the AI worker image pull/publish capability; execute with `--pull never`.
3. Check the installed Docker binary and runtime/daemon socket identity on that host. No stage may silently fall back to system-wide rootful Docker.
4. Run the approved fixed compiler on the actual rootless host with only non-sensitive fixtures; verify the inside-container `memory.max=134217728`, `pids.max=32`, `cpu.max=50000 100000` (or tighter limits), read-only root and loopback-only interface. Exercise a negative fixture with intentionally missing delegated controls **on a disposable test host** and verify it blocks before parsing. Validate no network, no mounts/host file reachability, stale-container cleanup and sanitized receipts. Persist independent OS-level and remote CI evidence in the existing PR/handoff; do not assume the fixed guard alone proves the entire sandbox.
5. Only after host isolation is actually proved, consider adding scoped `RUN_FIXTURE` and `PATCH_WORKTREE` authorities as **separate interfaces** with new tests. Do not reuse the syntax checker to execute arbitrary test code or perform GitHub actions.

**Phase invariant:** [Issue #3](https://github.com/Vertex-Systems-Network/zynoa-2-local/issues/3) remains open, P00-T19 is BLOCKED, P00-T20 is IN_PROGRESS, PR #1 remains DRAFT, and P01 cannot start without verified protected P00 merge.

[Workspace policy](P00_WORKTREE_POLICY.md) · [Fixture preview](P00_FIXTURE_DRAFT_STAGING.md) · [Model planner](P00_LOCAL_MODEL_PLANNING.md) · [Host bootstrap](P00_HOST_BOOTSTRAP.md) · [P00 task table](../state/pr-tasks/P00.json).

### Additional primary research (2026-11-18)

Docker's [rootless resource-limits guidance](https://docs.docker.com/engine/security/rootless/tips/) explicitly warns that CPU/memory/PIDs flags can be ignored, while its [runtime metrics documentation](https://docs.docker.com/engine/containers/runmetrics/) describes cgroup v2 controller files inside the container. [Docker run reference](https://docs.docker.com/reference/cli/docker/container/run/) describes the read-only and network isolation flags. The opt-in compiler now checks the effective kernel-visible values before compiling a candidate; a mocked runner can still forge positive output, so live delegated-controller and isolation failure-injection remains a separate blocking acceptance gate.
