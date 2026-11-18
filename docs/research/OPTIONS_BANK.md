# Evidence-Driven Options and Systems Bank

Do not choose a third-party component because it looks polished. Every module opens a dated evaluation record before implementation.

## Evaluation schema
`ID | module | user problem | candidate | source URL | license | last verified | architecture fit | Windows compatibility | speed evidence | UX evidence | operational risks | maintenance signals | alternatives | decision/status`.

Weights (initial): usability 25%, engineering fit 20%, speed 15%, accessibility 10%, maintenance 10%, license 10%, security 10%. Hard reject for license conflict, unsupported Windows packaging or unmitigated dangerous defaults. Scores remain **unrated** until tested; do not invent benchmark scores.

## Initial candidate bank (research candidates, not endorsements)

| Module | Candidate | Research angle / hypothesis | Licensing note | Status |
| --- | --- | --- | --- | --- |
| Desktop | Tauri 2 | native broker, lightweight shell, packaging | MIT/Apache family, verify dependencies | RESEARCH |
| UI | React, TypeScript, Radix, Tailwind | reusable structured design system | validate all packages | RESEARCH |
| UI reference | Claude desktop, Cursor, VS Code | fast interactions, file/project navigation | learn patterns, never copy assets | REFERENCE |
| Models | Ollama, llama.cpp | local inference, warm models, GPU offload | verify distribution and binaries | RESEARCH |
| Catalog | Hugging Face Hub | model metadata, hf_xet resumable downloads | model licenses vary independently | RESEARCH |
| Agent context | AGENTS.md, CLAUDE.md, GEMINI.md, Cursor rules | cross-agent instructions | not security controls | VERIFIED_PATTERN |
| Canvas editor | Konva + react-konva | selection/transform/drag scene graph | MIT according to primary sources | RESEARCH |
| Canvas editor | Fabric.js | vector/object canvas, SVG paths | verify exact package version | RESEARCH |
| Canvas reference | Penpot, Figma | components, auto-layout, variants and tokens | reference only; no copying | REFERENCE |
| Canvas SDK | tldraw | advanced infinite canvas capabilities | production license requirement: avoid for zero-paid objective | EXCLUDED_BASELINE |
| Coding | Monaco, xterm.js | editing, terminal integration | verify npm license | RESEARCH |
| Browser | Playwright | browser interaction and screenshot testing | verify packaged browsers | RESEARCH |
| Search | SearXNG | self-hosted metasearch | AGPL; separate service/legal review | RESEARCH |
| Media | ComfyUI | modular image-generation worker | check code and each custom-node/model license | RESEARCH |
| Storage | SQLite + FTS5 | fast local durable state | production proof required | RESEARCH |
| Version control | GitHub PR/branch protection | reproducible phase progression | platform features depend on repo setup | RESEARCH |

## Per-module research outputs
1. User journeys and jobs-to-be-done.
2. Direct competitors and open alternatives, each cited.
3. Feature matrix: must-have/should-have/defer.
4. Design pattern bank: screenshots/reference URLs, attribution, own implementation variations.
5. Reliability, startup and UX benchmarks on reference hardware.
6. License/security checklist.
7. ADR choosing implementation with stated tradeoffs.
8. Explicit updates to acceptance tests.

## Competitive analysis separation
A reference product may inform usability but never supply proprietary code, protected designs, licensed media, model weights or API access without authorized terms.

## v3.2 — changelog/release research options

Compare Keep a Changelog, Changesets, GitHub auto-generated release notes and custom verified-release event projection. Decision: use structured per-PR records and release proof as canonical; third-party tools may automate formatting/version bumps but cannot infer a shipped application from a merged PR. Reference `docs/operations/CHANGE_INTELLIGENCE_CHANGELOG.md` and ADR-0007. Review licensing and official docs before P00 integration.
