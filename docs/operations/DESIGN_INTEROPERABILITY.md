# DESIGN-IO — Cross-Tool Editable Design Import & Export

**State:** SPECIFICATION ONLY. **Research:** P00. **Designer core:** P08 (M11/M12). **Import/export implementation:** P08I, a separate phase after verified P08 completion and merge. No interoperability feature is implemented yet.

## Objective

Users must be able to import design projects from external UI design tools into Zynoa Designer as **editable documents**, and export Zynoa projects to other tools/formats where legal, documented interfaces are available. "Any design tool" is a future extensible adapter goal, not a guarantee of proprietary native-format compatibility or lossless conversion.

### Strict phase gate

- **P00:** Source-backed design/format research, adapter contracts, licensing alternatives, fixtures and tests planning. NO working importer/exporter code.
- **P02:** Shared professional GUI and design system. NO fake active cross-tool import/export controls.
- **P08:** Finish and independently verify the **native Designer core** first: versioned internal document format, layers/frames, vector/text editing, auto-layout, components, tokens, asset library, native save/reopen, undo/redo, crash recovery, standard raster/vector exports, full docs/screenshots, and verified merged PR.
- **P08I:** Only after remote P08 merge SHA and all M11/M12 core completion gates pass, create `phase/08i-design-interoperability` and one primary PR. Implement external-tool adapters, import/export wizards, interoperability tests, full compatibility reporting, documentation, Wiki and real screenshots.
- **P09+:** Add independently verified format plugins and maintenance updates without breaking the canonical document format.

**P08I is NOT part of P08's acceptance gate.** Core Designer can be finalized before cross-tool interoperability is built.

## Format targets: capability assumptions to verify

| Design tool | Proposed import | Proposed export | Restrictions |
|---|---|---|---|
| Figma | Authorized official API/plugin-assisted export, documented formats, SVG/assets | Official plugin/API-assisted delivery, SVG/PNG/PDF, supported code/tokens | Proprietary .fig native writing is NOT promised. Validate terms and API limits |
| Penpot | Documented interchange, SVG, tokens, APIs | Documented interchange/plugin APIs, SVG, tokens | Validate version compatibility, editable object fidelity and license |
| OpenPencil-A: open-pencil/open-pencil | Documented .pen and supported formats | .pen or documented interoperability formats | Verify schema/version/license; do not assume .fig round-trip |
| OpenPencil-B: ZSeven-W/openpencil | Documented .op format / adapters | .op or documented converter | Separate adapter from OpenPencil-A |
| Sketch | .sketch if legal/documented parser exists | Official interchange/plugin where supported | Experimental until target-app verified |
| Other UI tools | Common SVG, PNG, PDF, design tokens, documented JSON/API | SVG, PNG, PDF, tokens, CSS/HTML/React, authorized target connector | Per-tool adapter + explicit support/fidelity label |

For each direction and tool/version classify **Supported**, **Partial**, **Experimental**, or **Unsupported**; never silently flatten imported layers or claim native editable export if only PNG was produced. Unsupported proprietary formats must show truthful alternatives.

## Canonical design document

Designer owns a versioned **Zynoa Design Document (ZDD)** graph: document/page/frame/group/path/image/text (runs and fonts), layout/constraints, component/instance/variants, token bindings, effects, prototypes, asset hashes and stable IDs. Adapters map external schemas to/from ZDD without making external files the internal source of truth. Preserve source application/version, adapter version, original SHA, imported node-ID mapping, unsupported properties, unit/coordinate transforms, asset provenance and loss report. Use deterministic serialization, migration and checkpointed undo.

## Adapter interface (planned; not yet implemented)

```ts
interface DesignFormatAdapter {
  id: string;
  capabilities(): Promise<CapabilityMatrix>;
  inspect(input: SafeInput): Promise<ProbeResult>;
  import(input: SafeInput, options: ImportOptions, signal: AbortSignal): AsyncIterable<Progress | ZddDocument>;
  export(doc: ZddDocument, options: ExportOptions, signal: AbortSignal): AsyncIterable<Progress | ExportArtifact>;
  verify(input: SafeInput, output: ExportArtifact): Promise<FidelityReport>;
}
```

All adapters run in restricted workers with capability-based file and network access. Record schema versions and independent compatibility fixtures.

## User experience (P08I only)

**Import Wizard:** Select tool/file → detect format from contents → scan for malicious content → preview pages/layers/frames → mapping options (fonts, constraints, tokens, components, assets) → explicit warnings/fidelity estimate → choose local destination → convert → verify editable layers → show report/recovery and undo.

**Export Wizard:** Select tool/format/version → capability/unsupported-property check → choose pages/assets/text/font policies and target folder → preview loss summary → export with progress/cancel → verify file checksum and open in target application or documented reader → complete report.

**Compatibility Center:** Format/versions/direction matrix, supported features, known issues, last tested versions, unsupported effects, text/font deltas, component/token/variant mismatch, flattened nodes, target validation method, links to documentation. Offline-first wherever possible.

## Import security and privacy

Treat files as untrusted: size/complexity quotas, ZIP traversal/zip bomb defense, SVG/XML external entity/script protections, URL-fetch blocking by default, safe font/asset parsing, CPU/memory/time limits, isolated adapters, checksummed staged writes and rollback. No implicit cloud upload; public tool APIs require explicit configured authorization. Original user source never overwritten by default. Data Vault M23, Storage M24, Incidents M18, Help M19 and Changelog M26 integrations mandatory.

## Acceptance contract for P08I

- **DESIGN-IO-01:** Remote **P08 verified** merged SHA and accepted native M11/M12 core before creating P08I branch.
- **DESIGN-IO-02:** Real editable import per declared supported input (not flattened raster).
- **DESIGN-IO-03:** Real export reopened in target application/official reader; mere file creation is not a pass.
- **DESIGN-IO-04:** Test fidelity of fonts, text, vectors, layout, component overrides, variants, tokens and asset hashes, with transparent warnings.
- **DESIGN-IO-05:** Stable IDs, undo/redo, backup/restore, idempotent import and crash recovery.
- **DESIGN-IO-06:** Corrupt/oversized/malicious fixtures, denied path, interrupted conversion and timeout handled safely.
- **DESIGN-IO-07:** Every import/export option has working UI, real screenshots, annotated Help and Wiki links.
- **DESIGN-IO-08:** Versioned compatibility matrix; no unverified "all formats" marketing or UI claims.
- **DESIGN-IO-09:** Checksum, user-selected storage, cancellation and safe rollback; source files untouched.
- **DESIGN-IO-10:** Performance tests for complex documents and responsive conversion cancellation.

Research sources: https://github.com/open-pencil/open-pencil ; https://github.com/ZSeven-W/openpencil ; https://github.com/penpot/penpot ; https://developers.figma.com/docs/plugins/ . Re-verify actual features and licenses at P08I preflight.

## Release/maintenance

A separately documented P08I phase, branch, PR, tests, screenshots, Help/Wiki, change records and verified merge are mandatory. P00 may only plan and research. No current product implementation, real imported assets or screenshots are claimed by this specification.
