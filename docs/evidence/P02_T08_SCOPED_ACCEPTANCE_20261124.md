# P02-T08 — Scoped functional acceptance: Offline Help workflows (2026-11-24)

**Disposition:** P02-T08 is **DONE for its bounded task scope**: M19 contextual Help reader, local FAQ, glossary and interactive troubleshooting. This is **not** final M19 module or P02 phase acceptance. P02-T02, T10 and T11 remain IN_PROGRESS. Primary draft [PR #12](https://github.com/Vertex-Systems-Network/zynoa-2-local/pull/12) remains unmerged.

## Exact source and native execution

- **Trusted source:** `ee3b584bf39c42a955dd8b2f879c140a3962922f` and [exact-head Windows #45262533924](https://github.com/Vertex-Systems-Network/zynoa-2-local/actions/runs/45262533924) (SUCCESS), [Governance #45262533548](https://github.com/Vertex-Systems-Network/zynoa-2-local/actions/runs/45262533548) (SUCCESS). Windows executed the React/TypeScript, Node UI, Python M19 workflow/security tests, Tauri Rust/native build, actual native cold boot, screenshot and source-bound visual-provenance checks. Additional source change `35090079` modifies only the native FAQ screenshot framing and its regression test, not M19 application behavior; new exact-head CI requires independent confirmation.
- **Original source-matched artifact:** Windows job artifact `14861653640` was independently downloaded/reviewed. Contains 69 native Tauri capture/receipt pairs and 29 staged final-target *candidates*, with **29/29 source-bound SHA256 PNG hashes matched** in the nested 29-target ZIP. All are expressly candidate/pending visual review, not committed final module screenshots.
- **Native M19 visual review:** original 14 M19 screen/control PNGs were opened as a contact sheet with selected original full-res frames. Observed: offline Help catalog, article search and selected reader, real five-step guided tour, 4-choice troubleshooting wizard, FAQ disclosure and glossary terms, Wiki local mapping (not hosted), local report with no-send notice, local offline-ready summary. This is independent *feature-scope* review, not a screen-reader-driven E2E acceptance.
- **Contracts and negative cases:** `tests/test_p02_m19_workflows.py`, `apps/desktop/tests/ui-logic.test.mjs` and source in `apps/desktop/src/ui/HelpCenter.tsx`, `HelpWorkflows.tsx`, `help-workflows.ts` cover versioned local search, invalid schema and route rejection, bounded wizard state transitions, FAQ/glossary linked articles, copy-only incident report and denial of network/telemetry and localStorage side effects.

## Task-specific functional acceptance

| Capability | Implemented and verified functional boundary |
|---|---|
| Contextual Help | F1 and local route choose a bundled article; unmatched article query has clear empty state; no external open or automatic network |
| Article reader/search | Twelve bundled article references; schema/version validation, category and weighted keyword search, related guide navigation |
| FAQ | Five keyboard-toggleable native `details/summary` disclosures with linked local articles and source-driven content |
| Glossary | Six local terms/definitions in Help FAQ/glossary view; no external dictionary dependency |
| Troubleshooting | Four selectable real recovery cases, bounded multi-step progress, Previous / solved / retry, linked local guidance |
| Onboarding | Five guided lessons, Previous/Next/Finish/Restart, linked offline article, no fake saved workspace |
| Reporting privacy | Local sanitized incident payload and copy-only action, `transmitted: false`; no remote ticket or user-content upload |

## Strict exclusions / remaining real blockers

1. **T02** M02 final 15 required PNG assets are still absent from final GitHub paths and M02 module remains NOT YET VERIFIED. Do not bypass `tools/verify_p02_t02_acceptance.py`.
2. **T10** M19 final 14 PNGs + M02 final 15 PNGs still have manifest status PENDING (0/29 VERIFIED/committed). Windows native UI Automation is a scoped check (9/9), **not a complete NVDA/Narrator screen-reader audit**. Independent per-image final approval, approved multi-run performance budgets and full content keyboard coverage remain open.
3. The wizard currently has **textual** step instructions, **not annotated screenshot hotspot tours**. Remote GitHub Wiki publication/synchronization is unavailable, with truthful in-app labels. These are broader M19 module/phase obligations, not silently accepted under T08.
4. **T11** owner/maintainer approval, exact-head CI, GitHub Issue policy, independent security/privacy and protected main merge remain pending. PR #12 remains Draft; phase P02 cannot become MERGED_VERIFIED, and P03/release remain locked.

**Lease:** At acceptance time `docs/state/PHASE.json` reported `lease_holder:null`, `worker_running:false`; leave both untouched.
