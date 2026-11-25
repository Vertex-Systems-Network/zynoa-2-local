# P03-T01 — Predevelopment baseline (IN_PROGRESS)

2026-11-25. Protected main baseline `2520271026a22053a9f11e47259f28f5249b5373`.

P02 primary PR #12 merge `115b6c79fece26b5e4ec58ef8ad2364d7a77d244`; [trusted receipt run](https://github.com/Vertex-Systems-Network/zynoa-2-local/actions/runs/45610951439) success, [bot receipt](https://github.com/Vertex-Systems-Network/zynoa-2-local/pull/12#issuecomment-7161982157) independently read back with correct source/target/merge SHA. PR #24 is merged; no user data or runtime source edited. This seed opens the P03 primary PR before binding the manifest to its actual PR number.

## Acceptance still pending

- Exact P03 HEAD Windows native build/runtime and prior regression baseline (current desktop workflow restricted to P01/P02).
- Actual Ollama model health and measurement; candidate dependencies/version/license and UX alternatives validated.
- Typed schema, UI control inventory, threat/rollback ADR, tests-first data safety contracts.
- No implementation, screenshot, release or persistent worker claim.

## Baseline implementation

PR #25 activates P03 on its own branch. `.github/workflows/p03-native-baseline.yml` adds real exact-head Windows build and native startup proof with binary SHA-256, real fresh-profile vault/diagnostics/registry/event verification and existing Python regression tests. No prior phase workflow is changed. CI artifacts and logs must be independently verified before T01 acceptance. Existing pinned dependencies: Tauri 2.12.7, React 19.2.0, rusqlite 0.43.0, TypeScript 5.9.3. Candidate design is native SQLite transaction plus loopback Ollama NDJSON, no new dependency yet. Further research, ADR and threat/test inventory pending. Current schema v1 assertions intentionally baseline-only; update with explicit migration acceptance when T02 adds a schema.
