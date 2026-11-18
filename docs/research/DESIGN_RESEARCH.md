# P00/P02/P08 Research Program: Figma, Penpot & Two OpenPencils

**Do not collapse the two OpenPencil names:**

- **OpenPencil-A:** [open-pencil/open-pencil](https://github.com/open-pencil/open-pencil) — [official features](https://openpencil.dev/overview/features) — local-first scriptable editor with `.fig`/`.pen`, CLI/MCP and design lint.
- **OpenPencil-B:** [ZSeven-W/openpencil](https://github.com/ZSeven-W/openpencil) — [product](https://op.zseven.tech/) — Rust design-as-code, `.op` JSON, AI teams and MCP.
- **Penpot:** [GitHub](https://github.com/penpot/penpot) — open-source design tokens, components, variants, Flex/Grid and code inspection. Check MPL 2.0 integration obligations.
- **Figma:** [Product](https://www.figma.com/) / [Plugin API](https://developers.figma.com/docs/plugins/) — proprietary UX benchmark. Do not import proprietary source or scrape confidential assets.

## Required research artifacts per candidate

1. Version/commit/release checked, official links and license SPDX; dependency notices and any commercial restrictions.
2. Reproducible installation and minimal editor start on Windows 10/11; actual binary size and startup footprint.
3. Canvas benchmark at 1k, 10k and 50k nodes, including text-heavy and auto-layout scenarios, measured P50/P95 gestures and RAM.
4. Document fidelity: shapes, font fallback, text ranges, component overrides, variants, variables, vector paths, blur, masks and exports.
5. Programmatic editing: create/update/delete node, batch changes, undo/redo, plugin/MCP schema, determinism and error feedback.
6. Offline support, autosave/recovery, keyboard UX, accessibility, locale/RTL, import formats and crash recovery.
7. Licensing and supply chain: linking vs embedding vs sidecar vs contribution versus independent work; independent legal review when necessary.
8. Real screenshots captured from each test build with source and license; use original research screenshots only where allowed for internal comparison.
9. Improvement hypothesis: explain what our product adds (deep integrated AI workflows, local-first model routing, audited actions, unified help) beyond the reference.
10. Architecture Decision Record: score, select or defer, record why alternatives lost; benchmark evidence must be published in docs with links.

## Scoring rubric (proposed weights; actual results required)

| Criterion | Weight |
|---|---:|
| Real editing/undo reliability | 18% |
| Integration and automation API maturity | 17% |
| Canvas/text rendering fidelity | 16% |
| Node count & memory performance | 14% |
| License/distribution feasibility | 12% |
| Offline and Windows compatibility | 10% |
| Maintainability and upgrades | 7% |
| Accessibility and usability | 6% |

**No decision based solely on README features.** Test demo and direct engine API against pinned revisions. Explicitly distinguish read-only SDK from editable integration support. Do not promise Figma feature parity in the initial Design Studio phase.

## Pattern bank and evaluation documents

- [Candidate UX options (CSV)](OPTIONS_BANK_V3.csv)
- [Competitor matrix (CSV)](DESIGN_COMPETITOR_MATRIX.csv)
- [Design system](../design/DESIGN_SYSTEM.md)
- [Architecture ADR](../adr/0002-design-editor-selection.md)
- [Screens](../ui/SCREEN_INVENTORY.csv)

## Reference image policy

Reference screenshots may be linked for internal research with attribution and source URLs. Own product guide screenshots must come from our running product; do not use competitor captures or generated simulations as proof. Source examples: https://openpencil.dev/screenshot.png ; https://penpot.app/design/design-systems ; https://www.figma.com/dev-mode/.
