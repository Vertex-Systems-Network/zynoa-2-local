# P00 Local Ollama Fixture-Content Draft — Strictly No Source Execution

**Module:** M22 · **Phase:** P00 · **Existing draft PR:** [#1](https://github.com/Vertex-Systems-Network/zynoa-2-local/pull/1) · **Task:** P00-T20 (still IN_PROGRESS).

**Capability:** request one small model-authored Python fixture as **untrusted text**, validate its owner/task/path, stage and hash it in a disposable temporary directory, return a trusted in-memory object and sanitized receipt. **This code is not a deployed Ollama provider, actual model inference attestation, OS sandbox, syntax runner, test/repair loop, Git worktree patcher, GitHub writer or P00 completion.**

## Why and how it fits

The existing `tools.dev_model_planner` can propose **paths** but intentionally does not return source code. `tools.fixture_draft_stager` already safely previews candidate text but cannot request a model. `tools.docker_syntax_broker` can optionally compile candidate source **inside an independently authorized rootless container**, never on the privileged host, but lacks an actual model-content input path. The new `tools.local_fixture_drafter` bridges only the first two components, preserving the third one's separately disabled policy.

```text
Trusted developer host defines P00-T20 + WorkspaceScope
  -> existing validated DRAFT_ONLY plan (exactly ONE tests/fixtures/*.py)
  -> independent SHA-256 of canonical validated plan
  -> Ollama loopback-only POST /api/chat with JSON schema (no tools)
  -> require model identity / done / assistant role / exact expected task,
     branch, plan digest and filename (reject duplicates, additions, tool_calls)
  -> UTF-8/NFC/size/line/control characters checked (no privileged AST parse)
  -> existing ephemeral preview + exact SHA-256 receipt parity
  -> LocalFixtureDraft in host memory, repr hides source; safe_receipt excludes it
  -> NO checkout edits, code run, shell, Docker, PR/issue write or next phase
```

After separate host approval and independent OS hardening, a trusted caller *may later* pass `draft.plan` and `draft.source` into the **existing** `plan_python_syntax(..., expected_task_id='P00-T20')` or default-disabled `run_python_syntax` with an explicitly authorized rootless Linux host. **Do not execute Python from the returned source on the host.** The adapter never calls Docker itself.

## Request and response contract

- Only `P00-T20`, `P00 / phase/00-governance`, exactly **one flat** `tests/fixtures/<safe>.py` path already approved by a **host-constructed** `WorkspaceScope`. Source/test path and the 64-hex-character plan fingerprint are echoed in a strictly validated response; model cannot switch them.
- Model name must pass the existing planner rules. Endpoint is only explicit `http://127.0.0.1:<port>` or `http://[::1]:<port>`. No proxy or redirects, no arbitrary endpoint, no allowed model tools. The existing bounded HTTP transport is reused rather than introducing a second unreviewed HTTP client.
- Structured Ollama JSON schema: exact keys `schema_version, phase, branch, task_id, plan_sha256, path, source`. `source` maximum **8192 UTF-8 bytes / 200 lines**; response JSON bounded at **32768 bytes**. Duplicate JSON keys, unexpected extra fields, incomplete generation, wrong model, tool calls, malformed Unicode and unsafe text fail closed without printing raw model output.
- Prompts only contain bounded plan summary/reason, task ID, path and digest. No working-directory absolute path, source checkout content, user prompts/chat data, credentials, GitHub token, Docker socket or environment variables sent.
- Returned `LocalFixtureDraft` retains source *in process memory for trusted follow-up only*, with `repr=False`. Do not serialize this object or log its source. Its `safe_receipt()` exposes only SHA-256 hashes and conservative `*_verified=false` fields. Model responses and receipts must never become self-authorizing grants.
- Existing `preview_fixture_drafts` writes only to a fresh disposable OS temporary directory, verifies file hash and removes it. No application/source checkout modifications. The adapter checks staging receipt task, path, source digest and nonexecution claims.
- No real local inference has been performed by GitHub Actions. The test transport is mocked. Model-runtime performance/quality and provider health remain pending until separately measured on a trusted owned host.

## Operator example (tests only)

```bash
python -m unittest tests.test_local_fixture_drafter -v
python -m unittest discover -s tests -v
```

A trusted host can construct a P00-T20 plan with one allowed Python fixture path, call `draft_local_fixture(model, plan, scope, expected_task_id='P00-T20')`, inspect `draft.safe_receipt()`, then **only** pass untrusted draft source to a separately approved isolated syntax broker. This adapter intentionally has no CLI enabling a surprise prompt, install, write or execution.

## Threat model, tests and recovery

- **Prompt injection:** untrusted plan summary/reason and model output never become allowed commands, tools, repository authority or Docker arguments. Exact host-issued task/path/digest and existing workspace policy bound the content; hostile Python source is retained as inert bytes.
- **Host interpreter exhaustion:** generated Python is never parsed/compiled, `ast.parse`d, imported or executed on the privileged host. Syntax validation requires a properly isolated non-root container on a deployed host; the existing rootless compiler is default-disabled.
- **Filesystem/symlink race:** the host path is checked by the existing policy, but those checks alone are not an OS file-handle sandbox. No source file is opened/written by the drafter. External broker/worktree grant remains mandatory before real edits.
- **Network or credential leakage:** request uses only the existing local loopback transport and no tools. A malicious listener on the chosen loopback port, host compromise or malicious model remains a separate deployment risk.
- **Failure:** reject wrong/missing model, schema, plan digest, task, source bytes, duplicate fields, transport outage, preflight symlink/escape and forged preview receipt; emit sanitized `LocalFixtureDenied` without source/credential details. The caller must not retry infinite loops or silently enable Docker.
- **Tests:** Linux and Windows mock/provider-denial tests; real disposable temporary preview, no checkout writes, no Docker use, rejected tool calls, plan drift, Unicode/bounds, and direct dry-run handoff to the existing **non-executing** syntax planner.

**Still blocked by [Issue #3](https://github.com/Vertex-Systems-Network/zynoa-2-local/issues/3):** operator-installed dedicated supervised host, real Ollama measured inference, independently verified rootless OS containment, sandboxed patch/test/repair, guarded write identity and safe remote PR integration. **P00-T20 remains IN_PROGRESS**, T19/T17/T21–T24 BLOCKED, P00 PR #1 DRAFT, no P01. [Source change record](../../.changes/records/CHG-P00-M22-LOCAL-FIXTURE-CONTENT-20261120.json) is unreleased.

## Research and alternatives (2026-11-20)

- [Ollama /api/chat docs](https://github.com/ollama/ollama/blob/main/docs/api.md): structured `format` JSON Schema, `stream:false`, `message.content`, `done` and optional `done_reason`.
- [Ollama OpenAPI contract](https://github.com/ollama/ollama/blob/main/docs/openapi.yaml): assistant message schema and `tool_calls` separation.
- [Python 3.12 ast safety](https://docs.python.org/3.12/library/ast.html): resource and recursion limits; avoid host AST parsing of untrusted generated source.
- **Alternative 1:** return raw free-form source from the planner — rejected because proposal path/identity and candidate-content trust boundaries would be conflated.
- **Alternative 2:** use a tool-calling model to edit files directly — rejected because untrusted model-controlled tool invocations have no safe OS broker or actual host attestation yet.
- **Chosen:** separate structured fixture text request, exact plan digest and independently validated temporary preview, no execution or write rights.


## P00-T20 local model fixture-content drafting — corrected source CI (2026-11-20)

**Verified source:** [`185767c82182`](https://github.com/Vertex-Systems-Network/zynoa-2-local/commit/185767c82182645267acfddb2ad8b48f3776e998), authenticated GitHub Actions [#44630397210](https://github.com/Vertex-Systems-Network/zynoa-2-local/actions/runs/44630397210) **SUCCESS**, both `governance-lint` and `workspace-windows` via trusted GitHub Actions App 15368. **315 Linux Python tests PASS**, **12 Windows `tests.test_local_fixture_drafter` PASS**, CHG-PR-GATE PASS (17 change records), versioned P00 task manifest PASS (28 tasks: 19 DONE / 3 IN_PROGRESS / 6 BLOCKED = 67%) and guarded merge DRY-RUN PASS (zero GitHub mutations).

Initial [CI #44630275074](https://github.com/Vertex-Systems-Network/zynoa-2-local/actions/runs/44630275074) FAILED on both OSes because `FixtureModelTests.run(self,**kwargs)` accidentally overrode `unittest.TestCase.run` and aborted test execution. Renamed the test helper to `generate` and updated its uses, **without weakening any production policy or skipping a test**. Corrected exact-HEAD CI now green.

New `tools/local_fixture_drafter.py` implements a structured loopback Ollama request for **one model-authored P00-T20 Python fixture** as untrusted text. Checks host-defined task/branch/path and canonical plan SHA-256, bounded JSON with duplicate-key refusal, no tools, UTF-8/Unicode and size restrictions, independent disposable fixture preview hash parity. The candidate remains in a hidden-repr in-memory container; safe receipts have only hashes and conservative false deployment/execution facts. This connects proposal-only model planning to preexisting disposable preview and separately default-disabled syntax-broker planning but **DOES NOT parse/execute generated code on the host, write checkout/source/GitHub, or attest a running Ollama**. Relevant docs: [operator guide](../operations/P00_LOCAL_FIXTURE_DRAFTING.md), [ADR-0018](../adr/0018-untrusted-local-fixture-content-boundary.md), M22 module + Help + unpublished Wiki, unreleased change `CHG-P00-M22-LOCAL-FIXTURE-CONTENT-20261120`.

**Truth boundary unchanged:** P00-T20 stays IN_PROGRESS (not model-driven plan/edit/test/repair); P00-T17 real supervisor, T19 sandbox, T21 remote writer and T23 E2E remain BLOCKED by [Issue #3](https://github.com/Vertex-Systems-Network/zynoa-2-local/issues/3). GitHub main **is now protected** with active ruleset (T18 DONE). PR #1 is still DRAFT/UNMERGED, `PHASE.json.worker_running=false`, no GUI screenshots, Wiki publication, release or P01. This evidence-only commit will need its own exact-HEAD CI result. Next external step is genuine dedicated host/model + rootless sandbox independent proof and trusted GitHub write integration; do not mark the phase complete from CI mocks.


## Bounded syntax-correction follow-up (2026-11-20)

[The P00 two-attempt syntax-only coordinator](P00_BOUNDED_FIXTURE_REPAIR.md) now calls the existing fixture-content gateway and existing default-disabled Docker syntax broker. On a syntax-invalid verdict ONLY, the same localhost Ollama model receives its *own preceding candidate*, the fixed `PYTHON_SYNTAX_INVALID_NO_CODE_EXECUTION` marker, original scoped path/task and identical plan fingerprint to propose corrected text. No Docker exception text, secret, repository content or model tools are sent. The source is still untrusted, independently previewed and checked each time; the second candidate must differ, and no more than two candidates can be tried. Model-generated code is never parsed or executed by the controller host and is never applied to the repository. Even simulated mock repair is NOT actual host model inference, sandbox proof or complete P00-T20 coding.
