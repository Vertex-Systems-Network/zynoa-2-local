# P00 Bounded Local-Model Fixture Syntax Repair — Opt-In, No Source Execution

**Phase:** P00 · **Existing PR:** [#1](https://github.com/Vertex-Systems-Network/zynoa-2-local/pull/1) · **Task:** P00-T20 **IN_PROGRESS** · **Status:** implementation/CI source contract only, no independently deployed model/host verified.

This is the first bounded integration among existing modules: **Ollama-generated one-file fixture → independently bounded rootless Docker syntax-only verdict → one model correction for invalid syntax → second isolated syntax verdict → sanitized receipt**. It does **not** run the candidate's bytecode, save the generated source to a checkout, run a test suite against model code, fix the repository, commit/push a PR, deploy a daemon or start a next phase.

## Research and decision (2026-11-20)

Relevant official sources:
- [Ollama /api/chat](https://docs.ollama.com/api/chat) and [Structured Outputs](https://docs.ollama.com/capabilities/structured-outputs): a JSON Schema in `format` with `stream:false` makes outputs easier to validate. **Schema returned by the model is never permission**; host independently checks it and the task SHA.
- [Docker Rootless mode](https://docs.docker.com/engine/security/rootless/): privilege separation requires an independently provisioned current-user daemon/socket and a controlled image; rootless status alone does not prove isolation.
- [Docker Rootless Tips: resource limits](https://docs.docker.com/engine/security/rootless/tips/): `--memory`, `--cpus` and `--pids-limit` silently fail without cgroup v2/systemd, and CPU delegation may still be missing even when driver is systemd. Existing broker explicitly checks **in-container** memory/pid/CPU ceilings before Python syntax compilation. **Actual host enforcement/failure injection is still required.**
- [Python AST caveat](https://docs.python.org/3.12/library/ast.html): resource exhaustion means host-side parsing or importing arbitrary model-generated Python is forbidden here.

Alternatives: (A) run `compile()` in the controller process — rejected: untrusted AST parsing on a privileged host; (B) directly execute generated tests/patches with `subprocess` or workspace-shell — rejected: no verified OS sandbox or file-handle broker; (C) call an open-ended agent tool loop — rejected: model-supplied tools and retry budgets can cross phase/credential boundaries. **Chosen:** conservative two-attempt model **syntax-only** loop with trusted fixed policy; stop on all other failures.

## Implemented flow

```text
Operator-owned WorkspaceScope + expected P00-T20 + DRAFT_ONLY plan
  -> THREE explicit trusted opt-ins (enabled/operator_ack/syntax_enabled)
  -> validate one tests/fixtures/*.py file + model ID + phase/task/path
  -> verify rootless Docker CLI/socket exists (real broker path)
  -> locally request one candidate from structured Ollama (no model tools)
  -> recheck same plan SHA and source hash + independent ephemeral preview
  -> rootless Docker syntax broker: --network none / read-only / no mounts
     image digest pinned / cgroups checked / no Python bytecode execution
  -> valid: return source-free receipt, no patch or GitHub writes
  -> syntax-invalid: ask SAME localhost model for one correction only;
     send prior model candidate and fixed generic invalid-syntax marker
  -> independently validate corrected candidate/path/plan/source SHA
  -> identical candidate: DENY; changed candidate: run same broker once
  -> valid or still invalid: terminate, sanitized two-attempt receipt
  -> broker timeout, cgroup denial, bad marker, lost socket/cleanup failure:
     DENY without model retry or success claim
```

Only the **model's previously generated candidate** is included in the repair request to the same **local** Ollama endpoint. No external source code, user chat, GitHub credentials, absolute home path, environment variables, model tools, raw Docker stderr/stack traces or repository working-tree contents are included. Repair output is always checked against the same immutable plan digest/target file.

`tools.dev_fixture_repair_loop.run_fixture_syntax_repair` has a fixed `_MAX_ATTEMPTS = 2`; no user/model-supplied arbitrary retries, commands, patch locations, image identifiers or permissions. The model adapter and rootless syntax broker remain separately validated and bounded. The `syntax_broker` parameter exists **only for trusted test injection**: never let a model or untrusted workflow choose a Python callable/broker.

## Trusted Linux operator invocation — only after external host setup

The host must first independently provide a non-root Linux account, rootless daemon/socket and cached reviewed digest-pinned image. A workspace scope and existing `DRAFT_ONLY` plan must be constructed in the trusted controller, not accepted from model JSON or the user-facing Chat UI. **There is no unattended worker deployment in this PR.** A trusted host controller can then call:

```python
from tools.dev_fixture_repair_loop import run_fixture_syntax_repair

# model/plan/scope/owned_rootless_socket are trusted host policy inputs,
# not values from untrusted model-generated text or a UI prompt.
receipt = run_fixture_syntax_repair(
    model, plan, scope,
    expected_task_id="P00-T20",
    enabled=True,
    operator_ack=True,
    syntax_enabled=True,
    socket_url=owned_rootless_socket,
)
# receipt is metadata only; nothing is copied to the checkout.
```

Even a valid syntax receipt is **not** permission to execute candidate code or push GitHub changes. Real patches, real test execution, bounded repair across files, clean disposable worktrees and remote PR readbacks require a separate stronger OS sandbox and trusted host-issued write grants. Do not feed arbitrary model output to the optional `syntax_broker` callable parameter.

## Acceptance, safety tests, diagnostics

```sh
python -m unittest tests.test_dev_fixture_repair_loop -v
python -m unittest tests.test_local_fixture_drafter -v
python -m unittest tests.test_docker_syntax_broker -v
python -m unittest discover -s tests -v
python -m scripts.check_pr_task_board
```

CI tests use **mock Ollama and mocked Docker syntax receipts** on Linux and Windows; they check:
- Disabled by default / requires all three trusted opt-ins; only P00-T20/one flat fixture path.
- Verified initial invalid candidate → second request with prior candidate and *generic only* syntax result → verified corrected candidate with the same path/plan SHA.
- Valid initial candidate (single pass); invalid twice (bounded incomplete); identical invalid candidate refused.
- Model outage, malicious response/phase/path drift, Docker unavailable, bad cgroup verdict, forged receipt/sha/digest, source execution claim or GitHub write claim all DENY and never trigger infinite retries.
- No repo/source edits, no untrusted bytecode execution on the host, sanitized receipts excluding candidate content; Windows never opens a real rootless Docker socket.

**No CI fixture proves real model availability**, actual Docker isolation or host readiness; actual host observation must be separately recorded before updating Issue #3. There are no actual desktop UI screenshots or published Wiki mirror for this P00 bootstrap.

## Status and handoff

This operation advances *existing* P00-T20 source capabilities but **does not mark P00-T20 DONE**. P00-T17 real deployed worker, T19 attested OS isolation, T21 nonbypass GitHub writes, T22 verified developer-issue delivery, T23 unattended full fixture E2E, T24 policy-compliant PR merge remain blocked on [Issue #3](https://github.com/Vertex-Systems-Network/zynoa-2-local/issues/3). Current P00 task completion remains derived from manifest (19/28 DONE at baseline), not count of tests or source functions. Keep [PR #1](https://github.com/Vertex-Systems-Network/zynoa-2-local/pull/1) draft, no P01 until post-merge SHA readback [Issue #4](https://github.com/Vertex-Systems-Network/zynoa-2-local/issues/4). Related [model content adapter](P00_LOCAL_FIXTURE_DRAFTING.md) · [Docker broker](P00_DOCKER_SYNTAX_BROKER.md) · [ADR-0019](../adr/0019-bounded-fixture-syntax-repair.md) · [M22](../modules/M22.md).


## Experimental functional test extension (2026-11-20)

The preceding **syntax-only** flow is unchanged and never runs candidate code. A **separate**, stronger [P00 functional fixture runner](P00_SANDBOXED_FUNCTIONAL_FIXTURE.md) is now implemented behind four independent operator opt-ins. It first reuses syntax checks, then optionally executes a small model Python function against a fixed five-case test **inside** a rootless Docker container. Only a failed fixed test or invalid syntax permits one correction, never a Docker/transport failure. The model does not gain shell, repo edits or GitHub permissions. Both integrations remain mock-tested and NOT a deployed developer host or a complete P00-T20 loop.
