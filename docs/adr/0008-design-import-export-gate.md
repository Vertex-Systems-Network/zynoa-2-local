# ADR-0008 — Cross-tool design interoperability after native Designer completion

**Status:** PROPOSED; implementation deferred. **Date:** 2026-11-18. **Related:** ADR-0002, M11, M12, P08, P08I.

## Context

Users require Zynoa Designer to import editable projects from Figma, Penpot, two distinct OpenPencil projects and other supported tools, and export designs for use outside Zynoa. External formats, API permissions and fidelity limitations differ. Zynoa's own editable document model and undo/redo are not yet implemented.

## Decision

1. In P00, research official interchange methods, formats and licenses; add no production converters.
2. Complete/verify the native Designer core in **P08** first (stable schema, layers, vectors/text, constraints, components, tokens, assets, undo/redo, persistence, baseline SVG/PNG export, tests and real UI documentation).
3. Only after P08 has **passed its gates and merged to GitHub main**, create **P08I** as a separate branch/PR for adapter-based import/export. P08I follows P08 and precedes P09.
4. Use a versioned canonical Zynoa Design Document, not a third-party proprietary format, for primary storage.
5. Keep an explicit tool/format/version compatibility table and truthful Supported/Partial/Experimental/Unsupported statuses. A flattened PNG is not a successful editable document import.
6. Gate claims of native Figma/Penpot/OpenPencil interoperability on official/legal interfaces, target-app verification and real round-trip fixtures. No universal-format promise.
7. Imported files are untrusted; use isolated parsers, resource limits and recoverable staged writes. Integrate Data Vault/Storage and illustrated Help/Wiki.

## Alternatives not chosen

- Implement all import/export before design core: unstable schema and data-loss risk.
- Base canonical format on a competitor: upstream/vendor lock-in.
- Promise native .fig or .sketch two-way conversion without official API proof: unjustifiable.
- Flatten all source documents to raster: fails editable-design requirement.

## Acceptance

The [DESIGN-IO contract](../operations/DESIGN_INTEROPERABILITY.md) defines DESIGN-IO-01..10. P08I entry gate requires remote merged P08 SHA and verified native Designer completion. This ADR is a **future decision boundary**, not implementation evidence.
