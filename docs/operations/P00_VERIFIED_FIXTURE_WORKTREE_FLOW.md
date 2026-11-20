# P00 — Same Candidate: Model → Syntax → Functional Check → Disposable Git File

**Phase:** P00, task P00-T20 still **IN_PROGRESS**. **Branch:** `phase/00-governance`, draft primary PR #1, no protected merge. This flow is source-only developer bootstrap, **not** an always-on worker, real model/OS isolation attestation or a general code repair system.

## Problem closed in this slice

Prior P00 steps independently (1) generated and SHA-hashed model Python text, (2) syntax-compiled inside optional rootless Docker, (3) checked a fixed five-case functional contract in optional rootless Docker, and (4) created a new fixture inside a detached Git worktree on a trusted test host. The independent APIs were **not joined into a single approval chain**. Passing test evidence for draft A must never be reused to publish a different draft B. A model cannot self-authorize a file write.

`tools/verified_fixture_worktree_flow.py` now holds the **same in-memory candidate** and independently checked SHA-256 from model response through both exact Docker broker receipts to the fd-scoped **no-overwrite** worktree writer. It does not read source bytes from a model-controlled receipt. Any validation failure aborts before publication, and one correction attempt occurs only after exact syntax-invalid or failed-functional receipt.

## Enforced contract

- Trusted host supplies an approved P00-T20 `DRAFT_ONLY` one-level `tests/fixtures/*.py` plan, the same immutable 40-character source commit SHA, a currently detached, no-checkout, separately controlled Git worktree, `WorkspaceScope`, local model ID, operator-owned CLI/socket and model transport, and **five independent explicitly true** grants: `enabled`, `operator_ack`, `syntax_enabled`, `execution_grant`, `write_grant`.
- BEFORE model inference: verifies non-root Linux file-operation support, the detached worktree pointer matching the source repo, immutable HEAD SHA, and the plan identity/path. With real default brokers, the rootless Docker CLI/Unix socket is also required.
- Model gets only fixed local Ollama JSON Schema and its own short P00 task/fixture metadata. On retry, it gets only its *own* preceding candidate plus fixed `PYTHON_SYNTAX_INVALID_NO_CODE_EXECUTION` or `FIXTURE_TESTS_FAILED_ISOLATION_UNVERIFIED`. No checkout source text, Docker stdout, secrets, arbitrary shell tool or extra files.
- Each draft is independently revalidated, ephemerally previewed and SHA-256 checked. Existing syntax receipt must have exactly the same phase/task/candidate hash/image digest and non-execution fields. Existing rootless fixed-function broker receipt must have exactly the same candidate hash, phase/task/image and `FIXTURE_TESTS_PASSED_ISOLATION_UNVERIFIED`. One failed syntax/functional verdict can cause a second candidate; repeated source SHA and more than 2 attempts are refused.
- **ONLY on the passing candidate:** call existing Linux nonroot `apply_one_disposable_fixture` with the identical source string object, identical SHA, original task/branch/plan and pinned source commit. It uses fd-scoped owner checks, `O_NOFOLLOW`, 0600 temporary file, fsync and atomic hardlink no-overwrite publication in the detached worktree. A writer exception stops the operation (existing file or partial publication requires trusted operator reconciliation).
- The source checkout, protected state/policy, existing files and GitHub remain untouched. There is no model-generated shell, no arbitrary project test runner or rebase/commit/push/merge. Candidate Python is not parsed/executed on controller.
- Result is **source-free hash/attempt receipt only**, explicitly `actual_ollama_model_independently_verified=false`, `rootless_container_independently_attested=false`, `persistent_worker_deployed=false`, `production_source_patch_verified=false`. A passing mocked Docker verdict and a new disposable file do **not** establish safe autonomous development.

The `model_transport`, `syntax_broker` and `runtime_broker` injection parameters are **trusted CI test seams only**. NEVER construct functions/brokers from untrusted model JSON or expose the orchestrator API to a user-facing app with arbitrary host paths/grants. On real host, use default broker functions only after separate operator authorization and actual OS sandbox review.

## Evidence and tests

```sh
python -m unittest tests.test_verified_fixture_worktree_flow -v
python -m unittest tests.test_scoped_worktree_fixture_writer -v
python -m unittest discover -s tests -v
```

Linux CI creates a **real private Git repo** with an empty trusted commit, a separate detached `--no-checkout` worktree, and a real new file through this exact flow after trusted **mocked Ollama and Docker** receipts. It tests source SHA end-to-end, failed test→one repair→corrected file only, invalid syntax→repair, failed twice→zero files, repeated candidate, forged syntax/functional SHA, invalid worktree, existing-file overwrite denial, missing grants, sensitive-error redaction and non-inference preflight. Windows CI must reject nonroot/dirfd source creation and never use a path-based fallback.

**This remains an in-process trusted-host prototype**. Same-UID interference, full OS isolation, real local model, a trusted authoritative provenance/signature rather than mock receipts, worker lease/restart/recovery, safe multi-file arbitrary patches and actual project tests, verified GitHub PR write identity, CI incidents and human release gates must be separately proven under [Issue #3](https://github.com/Vertex-Systems-Network/zynoa-2-local/issues/3). P00-T17/T19/T21–T24 BLOCKED, P00-T20 IN_PROGRESS, PR #1 draft, `worker_running=false`, no P01/app GUI/Wiki publication/release.

Official references (2026-11-20): [Python os descriptor-relative operations](https://docs.python.org/3.12/library/os.html), [Docker Rootless](https://docs.docker.com/engine/security/rootless/), [Docker rootless resource limits](https://docs.docker.com/engine/security/rootless/tips/). **Alternative A rejected:** accept a model/CI-supplied SHA receipt and later copy a different file into worktree (TOCTOU and swapped candidate). **Alternative B rejected:** let model choose `git apply`/test command in trusted source checkout (arbitrary tool grant). Chosen: one source object and digest held in one restricted trusted call, one no-replace detached fixture write, no remote writes. [ADR-0022](../adr/0022-tested-candidate-exact-source-worktree-binding.md).
