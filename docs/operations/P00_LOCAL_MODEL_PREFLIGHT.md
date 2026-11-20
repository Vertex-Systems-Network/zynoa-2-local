# P00 Local AI Model Preflight — Ollama (No Inference, No Install)

**Implementation:** `tools/local_model_probe.py` · **Phase:** P00 external developer bootstrap. **State:** Local-only probe implemented and unit-tested, but **not executed on a provisioned user's development host**. No 24/7 agent or automated coding loop is deployed.

## Purpose

The autonomous developer cannot work without an actual local model runtime. A document naming Ollama is not proof that it is installed, reachable, has a model downloaded, or can reliably complete coding tasks. This preflight checks the **actual host**, explicitly distinguishes "server up" from "model installed", and never executes generated code.

## Exact checks

- Accept only explicit loopback URL `http://127.0.0.1:<port>` or `http://[::1]:<port>`; default port is 11434.
- Refuse remote/LAN/public URLs, untrusted URL paths/query, credentials, redirects, and HTTP proxies (no network exfiltration).
- GET `/api/version` and `/api/tags` with bounded response sizes and timeouts; no `/api/chat`, `/api/generate` or prompt transmission.
- Validate model inventory shape/name limits and reduce response to a safe provider/version/model-count result, with a bounded list of names. Do not return credentials/private filesystem paths.
- `LOCAL_MODEL_PRESENT` means Ollama is available and has listed models, **not** that a chosen model has been benchmarked, that RAM/VRAM are sufficient, or that the autonomous coding agent has been deployed.
- `OLLAMA_RUNNING_NO_MODELS` is an explicit host readiness blocker; `LOCAL_MODEL_UNAVAILABLE` is a safe negative result.

## Command (on the actual development machine)

```bash
python -m tools.local_model_probe
# Optional loopback port override:
python -m tools.local_model_probe --endpoint http://127.0.0.1:11434
```

If no Ollama runtime is running, exit code is 2; no prompt is sent and no GitHub modification is attempted. A successful status code does not allow the worker to skip OS sandbox, token storage, protected-main CI or documented acceptance.

## Next requirements BEFORE coding automation

1. Install Ollama on a user-controlled development host and acquire a compatible coder model through verified model manager/download paths, with user data vault and storage relocation constraints.
2. Record actual host CPU/RAM/GPU, model readiness and measured coding capability, speed/latency and context performance.
3. Deploy an OS-supervised worker with a secure credential store, durable queue/backup/heartbeat and independently brokered filesystem/process/network sandbox.
4. Prove one safe independent test-repository task end-to-end (model plan, bounded patch, trusted tests, error fixing, same branch/PR, required CI), then guarded GitHub merge policy—never from self-reported model success.

**Current live GitHub facts:** PR #1 remains DRAFT. `main` is unprotected and Issue #3 remains an actual premerge infrastructure blocker. The local model preflight cannot be run through the GitHub connector on the user's desktop, and CI mocks do not attest a local Ollama installation.

[Ollama local API](https://docs.ollama.com/api) · [P00 worker runbook](P00_WORKER_RUNBOOK.md) · [continuous autonomy audit](P00_CONTINUOUS_AUTONOMY_AUDIT.md) · [Issue #3](https://github.com/Vertex-Systems-Network/zynoa-2-local/issues/3).
