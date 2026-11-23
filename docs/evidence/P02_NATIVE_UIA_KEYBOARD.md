# P02 — Real Windows native accessibility provider and keyboard probe

**Scope:** M02 design system and M19 Help discovery. **Phase:** P02, primary draft PR #12.

## Implementation

`scripts/probe_p02_native_a11y.ps1` binds `UIAutomationClient` / `UIAutomationTypes` to the real running Tauri window HWND and verifies the PID. It does not launch a synthetic browser, read private desktop content, install dependencies or execute arbitrary commands. The probe runs **before** the existing 54-image capture so keyboard mappings remain at their defaults; it restores the Overview view after inspecting the modal.

Required UIA checks: named/focusable `Interface appearance` and `Navigation density` selectors; visible `Command palette` accessible title; visible/focusable `Search available commands and offline Help` input; native keyboard focus reaches the search; Escape closes the dialog. Missing controls or failed focus/escape result in an explicit failing source-SHA-bound JSON receipt.

`tools/verify_p02_native_uia.py` validates exact SHA, native PID provenance, all six booleans, no-user-data guard, duration and **explicit false** full screen-reader/final screenshot/option-wide claims. Negative tests cover spoofed origin, bad SHA, missing accessible names, no keyboard focus, dishonest approval and invalid timing. Windows CI exports both raw UIA and validated scoped report in the same source-bound artifact as actual native screenshots.

## Evidence boundaries

Passing a provider/API name and focus probe is **not** a full NVDA/Narrator user test. No final screen-reader approval, theme/motion certification, full option-control keyboard cycle, 15 M02 + 14 M19 screenshot manifest completion, performance budget, hosted Wiki, merge or release follows from these six checks. Run exact SHA CI and visually/auditor-review live artifacts before changing any task status.

**Rollback:** Revert the scoped CI/native UIA files and associated tests/docs on the active P02 PR; app runtime and user data schema remain unchanged.

## Actual CI outcomes — do not mark full accessibility verified

- [First native UIA run #45208244566](https://github.com/Vertex-Systems-Network/zynoa-2-local/actions/runs/45208244566) **FAILED** at native accessibility gate, after source contracts and Tauri binary compiled. Original artifact #14834557780: both selector names were not accepted as focusable, command palette and input accessible names visible, Escape passed, search OS focus check failed.
- [Diagnostic run #45209973684](https://github.com/Vertex-Systems-Network/zynoa-2-local/actions/runs/45209973684) **FAILED** at native UIA. Original artifact #14835008829 independently inspected: both Preferences selectors *present and enabled* in Windows UI Automation but `keyboard_focusable=false`; input *present, enabled, focusable* but actual reported OS focus was a different named element. Dialog name and Escape passed. These failures are not waived.
- [Hardening run #45211869007](https://github.com/Vertex-Systems-Network/zynoa-2-local/actions/runs/45211869007) at commit `bbf9b7a14b56981ff029ab3723e7324943453d8a` **FAILED BEFORE UIA**: Windows process did not produce the native diagnostic event, vault, or location registry by the bounded 45-second boot gate. The real application was not ready; no UIA outcome for the hardening can be inferred. Original artifact #14836433700 proves only successful compiled executable and prior source checks, not working startup or UIA.

**Current verified limit:** Source Python native-a11y negative/contracts, TypeScript/Node UI and Rust tests passed in the first two Windows runs; live OS-level accessibility acceptance is **OPEN**. Browser screenshots, source labels and the presence of a Tauri executable do not substitute for a passing live UIA + native startup test. Maintain the 29 final screenshot statuses as PENDING.
