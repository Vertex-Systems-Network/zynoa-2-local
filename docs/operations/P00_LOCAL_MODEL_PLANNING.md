# P00 Local Model Proposal Gateway — Structured Ollama Planning, No Execution

**Module:** M22 · **Phase:** P00 / [draft PR #1](https://github.com/Vertex-Systems-Network/zynoa-2-local/pull/1)
**Status:** Production-style request validation plus mocked model transport tests; **NOT a deployed local Ollama service, coding agent, sandbox, GitHub updater or automatic worker loop**.
**Developer scope:** P00-T20 in progress, dependent on secure host deployment (T17), OS sandbox (T19) and independently authorized GitHub writes (T21).

## Purpose and predevelopment research

Until now P00 had a read-only model inventory check (`tools/local_model_probe.py`) but no tightly constrained inference contract. A future persistent developer host must distinguish **model proposal**, **host approval and capability grant**, **actual sandboxed patch/test execution**, and **independent GitHub checks**. Prompt instructions alone cannot enforce these boundaries.

Official Ollama API (reviewed 2026-11-18):
- [POST /api/chat](https://docs.ollama.com/api/chat): `model`, `messages`, `stream:false`, `format` JSON schema and runtime `options` are supported; a completed response includes `done` and `message.content`.
- [Structured Outputs](https://docs.ollama.com/capabilities/structured-outputs): provide schema to `format` and independently validate output, with low temperature for consistency.
- Alternatives: an OpenAI-compatible local gateway or llama.cpp server could implement this same normalized planner contract in future; do not treat unspecified provider behavior as already integrated. Ollama is the first concrete adapter.

## Implemented gateway

`tools/dev_model_planner.py` accepts four **trusted host inputs**: model ID, existing P00 task ID, short non-sensitive task brief, and a `WorkspaceScope` object constructed on the privileged host side. It sends only bounded metadata to explicit localhost Ollama and receives JSON structured proposal data. It cannot read user chats, source file contents, passwords, GitHub credentials or host absolute paths.

Request is restricted to `http://127.0.0.1:<port>` or `http://[::1]:<port>`; no LAN/public URL, redirect, HTTP proxy or unbounded payload. The only request is POST `/api/chat`, with `stream:false`, `temperature:0`, `num_predict:768` and a small JSON schema. No Ollama `tools` are offered, and a response attempting `tool_calls` is denied.

Supported proposal schema, intentionally tiny:

```json
{
  "schema_version": 1,
  "phase": "P00",
  "branch": "phase/00-governance",
  "task_id": "P00-T20",
  "summary": "Propose a fixture regression test",
  "file_proposals": [
    {
      "path": "tests/fixtures/example-draft.json",
      "action": "DRAFT_ONLY",
      "reason": "Candidate for separate host review"
    }
  ],
  "checks": ["phase-policy", "docs-integrity"]
}
```

- One to eight file proposals, each `DRAFT_ONLY`; `read/write/delete/execute/merge` are **not** valid model actions.
- Only three existing fixed read-only checks are selectable: `phase-policy`, `design-spec`, `docs-integrity`. The planner does **not** run these checks itself.
- Every proposed path passes the **existing host-derived** `WorkspaceScope.check(path, "write")`. Default P00 writable prefixes are `docs/help`, `docs/wiki`, `docs/research`, `tests/fixtures`; protected `.git`, `AGENTS.md`, `.github`, `docs/state`, security rules and controller sources are denied.
- Exact phase, primary branch, task ID and schema key set required; duplicate paths/checks, unsafe separators, symlinks/junctions, unsupported fields and oversized/unfinished model responses are denied.
- The output contains a SHA-256 plan fingerprint plus metadata. No code runs or changes are committed. A model phrase requesting dangerous actions is inert text, never a new capability.

## Security design / threats

1. **Untrusted model output:** A provider-enforced JSON schema reduces output ambiguity but is not authorization. The host performs a separate exact structural validation and workspace scope check. Model instructions cannot grant additional tools or repository branches.
2. **SSRF/proxy leak:** Only explicit loopback hostnames are accepted; proxies and redirects are disabled. A model does not select the endpoint. This is not protection against a malicious service already listening on localhost, compromised OS/user account or OS process inspection.
3. **Prompt/privacy:** Only a short host-supplied brief and a bounded list of permitted write-prefix names are transmitted. Never place user secrets, project source contents, paths to private user files, environment variables or API keys in task briefs. The model's output is not stored in the durable queue by this module; host operators must provide a safe event store later.
4. **File traversal / TOCTOU:** Existing workspace policy is a **preflight validator** only. Symlink checks and resolved paths do not secure an actual file handle against concurrent path replacement. Future isolated file broker must operate using OS-backed scoped handles; model proposals can never be directly written by this module.
5. **Code execution:** No subprocess, shell, download, dependency installation, Git write, issue creation, phase switch or PR merge is reachable through this adapter. Real automated code-fix still requires independently reviewed OS sandbox, resource/time budgets, secrets segregation and allowed tasks before P00-T20 can be marked DONE.
6. **No false readiness:** CI tests use deterministic mocked local responses. A mock does not prove Ollama is running on a developer machine or that the chosen local model is good at software development.

## Developer verification

```sh
python -m unittest tests.test_dev_model_planner -v
python -m unittest discover -s tests -v
python -m scripts.check_pr_task_board
```

Cross-platform unit cases check JSON request construction, response envelope validation, rejected remote hosts, unapproved task IDs, invalid/truncated payloads, HTML/control injection, duplicate fields, forbidden security paths, symlink escapes, no directory mutation, output fingerprint determinism and restricted transport methods. These tests exercise **mocked replies**, not real inference.

There is deliberately **no CLI** that fetches a model and writes generated files automatically. The next stage must establish a supervised host process, actual model inventory/inference measurements, a narrowly scoped OS sandbox and a verified broker before model suggestions may become testable worktree changes.

## Dependencies and next proof

| Gate | Actual requirement | State |
|---|---|---|
| P00-T15 | Real local model available + measured inference | IN_PROGRESS, host not provisioned |
| P00-T17 | Deployed supervisor/heartbeat/restart/identity | BLOCKED (Issue #3) |
| P00-T19 | OS execution, process/network/file-handle restrictions | BLOCKED (Issue #3) |
| P00-T20 | Proposal → bounded brokered edit/test/fix loop | IN_PROGRESS; **proposal only** |
| P00-T21 | Narrow protected GitHub writes, PR receipts | BLOCKED (Issue #3) |
| P00-T23 | Unattended end-to-end safe test-repo task | BLOCKED (Issue #3) |

**Do not merge P00 PR #1**, mark P00 complete, turn on automatic execution, report a GUI screenshot, or begin P01 until actual remote merge/security evidence exists. Preserve [P00 task manifest](../state/pr-tasks/P00.json), [P00 Host Bootstrap](P00_HOST_BOOTSTRAP.md), [worktree policy](P00_WORKTREE_POLICY.md), [continuous autonomy audit](P00_CONTINUOUS_AUTONOMY_AUDIT.md) and [Infrastructure Issue #3](https://github.com/Vertex-Systems-Network/zynoa-2-local/issues/3).


## P00-T20 separate fixture *content* drafting (2026-11-20)

The planner above deliberately returns only DRAFT_ONLY paths. [Local Fixture Drafting](P00_LOCAL_FIXTURE_DRAFTING.md) adds a **separate**, bounded structured-output Ollama request for *one* Python fixture's text after the plan has been validated and fingerprinted by the trusted host. The adapter refuses tool calls and keeps all source code unexecuted and out of GitHub/receipt logs. The existing `fixture_draft_stager` independently previews/hashes that candidate in disposable storage; the separate Docker syntax broker remains default-disabled and cannot execute the candidate. Tests use mocked Ollama, so no real local model readiness, trusted host deployment, code repair or P00 exit is claimed.
