# P03-T04–T07 — Local inference, streaming, model choice and context preflight

Date: 2026-11-25. Phase P03, branch `phase/03-chat`, draft PR #25. T01–T03 are verified DONE. This coordinated batch deliberately holds all commits locally until T04–T07 pass together, then pushes one final head so remote runners execute once.

## Scope and selected boundary

- Use Ollama's native loopback API at the single fixed origin `http://127.0.0.1:11434`; no renderer HTTP, arbitrary URL, redirect, proxy, credential, cloud or LAN authority. Runtime/model installation and download remain P05.
- Add a native model gateway separate from the conversation storage command. Health reads `/api/version` and `/api/tags`; generation posts `/api/chat` with streaming enabled. Only models returned by the installed-model inventory may be selected.
- Preserve the native vault as sole durable chat authority. Commit user input before generation. Persist assistant output only after a terminal complete/cancelled/failed outcome; return a typed post-commit receipt. Never hold the vault lock while waiting on Ollama.
- Stream typed text deltas to the current native window with exact turn/correlation IDs. One active turn per conversation. Stop is idempotent and cooperative. Retry creates a new attempt ID and never overwrites prior output.
- Store per-conversation model and context limit in the existing versioned native preference substrate. Values are durable, bounded and transactionally revisioned without changing the already accepted v2 chat schema. Existing conversation/message and opaque legacy records remain unchanged.
- Context assembly is native and deterministic: explicit system boundary, bounded newest complete conversation messages, UTF-8 byte and conservative token estimate budgets, no silent cross-thread data, cancelled/failed assistant content excluded by default. The UI shows estimated used/limit values before send.

## Alternatives and sources

Native Ollama API is selected over its OpenAI-compatible facade because native tags, completion metadata and NDJSON semantics are required. Embedding llama.cpp is deferred because it expands runtime distribution and hardware scope. Renderer fetch is rejected because it bypasses Tauri's capability boundary. Official sources revalidated 2026-11-25: https://docs.ollama.com/api/chat, https://docs.ollama.com/api/streaming, https://docs.ollama.com/api/tags, https://docs.ollama.com/faq. Existing ADR-0030 remains controlling.

## Tests-first acceptance

1. Native gateway tests use a loopback fixture only: reject non-loopback/redirect/proxy-style authority, bounded headers/body/NDJSON, malformed events, missing installed model, timeout, disconnect and runtime error. No external connection in unit tests.
2. Vault tests prove preference revision/conflict handling, per-thread isolation, restart persistence and transaction rollback. Existing v1→v2 migration and all T02/T03 tests remain green.
3. Turn tests prove ordered deltas, one terminal event, cancellation idempotency, retry with a new ID, no lock held during transport, exact committed assistant receipt and no success acknowledgement after persistence failure.
4. Context tests cover empty/history, stable chronological assembly, exact conversation isolation, UTF-8 and token bounds, oversized latest user input rejection, and exclusion of failed/cancelled assistant records.
5. Frontend tests cover installed-model-only selection, per-thread persistence, health/error/offline states, Send/Stop/Retry focus, stale event rejection, context disclosure and strict native reply/event validation.
6. Run governance, full Python suite, Node tests, TypeScript build and Rust tests locally once at batch close. Push only the verified final batch head; GitHub Windows/model/governance workflows then supply exact-head native proof. Until those remote checks pass, T04–T07 stay IN_PROGRESS.

No attachments, tools, export, portable encrypted backup, release, model download, automatic runtime installation or phase completion is claimed.
