# ADR-0018 — Separate Untrusted Model Fixture Content from Privileged Execution

**Date:** 2026-11-20 · **Status:** P00 scoped source decision; host/runtime not yet deployed.

## Context
The existing P00 local model planner generates only DRAFT_ONLY file paths; the fixture stager previews candidate text while the Docker broker optionally compiles Python without running it. No trusted, bounded route exists to obtain **model-authored fixture content** for that preview. Combining content and privileged host execution would cross the unproven OS sandbox boundary.

## Decision
Add `tools.local_fixture_drafter` as a separate structured-output local Ollama adapter. A trusted host supplies validated P00-T20 plan and `WorkspaceScope`, and the request includes only one approved `tests/fixtures/*.py` path plus canonical plan fingerprint. The model can return `source` as untrusted text, but may not choose new path/task/branch/tools. Independently check response identity, UTF-8/size/line bounds, duplicate fields and disposable staging receipt. The in-memory result has a safe source-free representation/receipt. **No model source is parsed/compiled/executed on the host.**

## Rejected alternatives
- Allow planner output to include arbitrary code and tool calls: couples identity approval with executable authority and no external host/sandbox proof.
- Write the model's source into the repository before testing: unsafe against untrusted paths/races, and violates one-phase scoped grant design.
- Pretend CI mock model reply attests a running local Ollama/developer host: false inference and deployment claim.

## Consequences and follow-up
The P00-T20 chain now has a bounded candidate-content input for isolated syntax evaluation, but **full autonomous code edit/test/repair and PR updates are still incomplete**. Only a trusted external host may later turn on the independently reviewed default-disabled rootless syntax broker. Preserve user privacy, no Docker/GitHub tool access, and separate premerge Issue #3 vs postmerge Issue #4. This change is unmerged, unreleased and does not fulfill M22 product UI/screenshots.

[Operator contract](../operations/P00_LOCAL_FIXTURE_DRAFTING.md) · [Existing planner](../operations/P00_LOCAL_MODEL_PLANNING.md) · [Infrastructure blocker](https://github.com/Vertex-Systems-Network/zynoa-2-local/issues/3).
