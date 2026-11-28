# P03-T01 — Predevelopment baseline (DONE)

2026-11-25. Protected main baseline `2520271026a22053a9f11e47259f28f5249b5373`.

P02 primary PR #12 merge `115b6c79fece26b5e4ec58ef8ad2364d7a77d244`; [trusted receipt run](https://github.com/Vertex-Systems-Network/zynoa-2-local/actions/runs/45610951439) success, [bot receipt](https://github.com/Vertex-Systems-Network/zynoa-2-local/pull/12#issuecomment-7161982157) independently read back with correct source/target/merge SHA. PR #24 is merged; no user data or runtime source edited. This seed opens the P03 primary PR before binding the manifest to its actual PR number.

## Acceptance still pending

- Exact P03 HEAD Windows native build/runtime and prior regression baseline (current desktop workflow restricted to P01/P02).
- Actual Ollama model health and measurement; candidate dependencies/version/license and UX alternatives validated.
- Typed schema, UI control inventory, threat/rollback ADR, tests-first data safety contracts.
- No implementation, screenshot, release or persistent worker claim.

## Baseline implementation

PR #25 activates P03 on its own branch. `.github/workflows/p03-native-baseline.yml` adds real exact-head Windows build and native startup proof with binary SHA-256, real fresh-profile vault/diagnostics/registry/event verification and existing Python regression tests. No prior phase workflow is changed. CI artifacts and logs must be independently verified before T01 acceptance. Existing pinned dependencies: Tauri 2.12.7, React 19.2.0, rusqlite 0.43.0, TypeScript 5.9.3. Candidate design is native SQLite transaction plus loopback Ollama NDJSON, no new dependency yet. Further research, ADR and threat/test inventory pending. Current schema v1 assertions intentionally baseline-only; update with explicit migration acceptance when T02 adds a schema.

## T01 observed baseline failure and remediation

[Windows run #45611349181](https://github.com/Vertex-Systems-Network/zynoa-2-local/actions/runs/45611349181): 750 tests executed, 31 errors, 46 skipped. Every error was WinError 32 on temporary SQLite cleanup in dev_job_queue/dev_task_graph. Native build and startup were skipped after failure. [Issue #26](https://github.com/Vertex-Systems-Network/zynoa-2-local/issues/26) is a real P03 blocker. Python sqlite3 connection context does not close the connection (https://docs.python.org/3/library/sqlite3.html#how-to-use-the-connection-context-manager). Use closing(conn) outside the existing transaction context, preserve all tests, add explicit closed-connection and rollback assertion. No broad governance rewrite. Fresh Windows run required.

## Research and tests-first decisions

See [ADR](../adr/0030-p03-chat-data-and-local-inference.md) for official-source alternatives, risk and acceptance inventory. Exact T02 migration tests and data safety contract are specified there; implementation waits for T01 baseline evidence. Additional Linux job probes a real Ollama v0.40.18 (release SHA256 pinned), qwen2.5:0.5b local model, synthetic prompt, loopback only, no user content or tool executions; runtime version, digest, TTFT and generation counts captured. This is a preflight measurement, not the app inference adapter or a quality benchmark. Pending exact-head CI.

Initial local-model workflow [#45617804576](https://github.com/Vertex-Systems-Network/zynoa-2-local/actions/runs/45617804576) failed before creating jobs; corrected job-level runner.temp expression to shell-time RUNNER_TEMP in executing step. This is configuration repair only, not evidence of model runtime success.

## T01 acceptance — verified 2026-11-25

Exact source `37b7cc366789936c872093733d130791d4062402`: [native Windows #45617988221](https://github.com/Vertex-Systems-Network/zynoa-2-local/actions/runs/45617988221) success, 751 Python tests executed (705 passed, 46 platform skips, zero errors), Rust 32/32, TS/UI/build/cold boot/diagnostic/vault/registry/audit checks passed. [Governance #45617988316](https://github.com/Vertex-Systems-Network/zynoa-2-local/actions/runs/45617988316) 751/751 and workspace-windows pass. Former SQLite handle failure #26 resolved. [Native artifact #15023438277](https://github.com/Vertex-Systems-Network/zynoa-2-local/actions/runs/45617988221/artifacts/15023438277) downloaded independently, ZIP SHA-256 c640cf6972d9b183204bcad81836f9231fb40cc0672ef53ae441a3e4adad5271; JSON source exact match, executable SHA-256 ab0338937153caefc264764d05a4bcc16ad7515e63a2742da8d17a6e4cc61f36, window/metadata ready 7718 ms. [Local model #45617988600](https://github.com/Vertex-Systems-Network/zynoa-2-local/actions/runs/45617988600) passed; [artifact #15022359257](https://github.com/Vertex-Systems-Network/zynoa-2-local/actions/runs/45617988600/artifacts/15022359257) ZIP SHA-256 43da588abdabc2835765f1f0fa91c02b4a21d512e6a4090097b6454b4c4b9fb6 independently verified, exact source, runtime 0.40.18, model digest a8b0c51577010a279d933d14c2a8ab4b268079d44c5c8830c0a93900f1827c67, TTFT 689 ms, total 847 ms, 10 tokens, nine content chunks. Synthetic Linux model smoke, not Windows product inference. Inherited warnings: native library build 36, lib test 5; retain #18 warning ledger, resolve relevant warnings during P03. No product release or screenshot claim. Preflight architecture/acceptance ADR recorded. T02 may start, subsequent feature acceptance must use new exact source. Local checkout unavailable (DNS), evidence from connector/CI and actual downloaded ZIPs.
