# P02 — Real Windows native accessibility provider and keyboard probe

## Expanded native keyboard proof after provider focus mismatch (2026-11-23)

Native Windows [run #45214008515](https://github.com/Vertex-Systems-Network/zynoa-2-local/actions/runs/45214008515) failed the earlier focus assertion. Downloaded original artifact #14838970137 confirms both Preferences selectors were present, enabled and keyboard-focusable; the command modal and named search were available and Escape worked. The Windows UIA provider returned `aria_active_descendant_list_item` as its focused element instead of the combobox input, so **no keyboard-focus acceptance was granted**.

The next source implementation goes beyond a provider focus label: it types a fixed non-private option ID (`M19-OPT-06`) through Windows SendKeys, requires the input's own UI Automation `ValuePattern` to return that exact ID, requires the matching bundled Wiki option to appear, activates Enter and checks that the modal vanishes and Help option detail appears, then reopens and dismisses the modal with Escape. The fail-closed proof schema now contains **nine** exact booleans plus native input-value provenance; a focused list item or a fabricated PASS flag cannot satisfy the validator without the real typed input.

The implementation is source-scoped until a **completed passing exact-head native Windows run** is independently verified. These tests do not certify NVDA/Narrator use, all 29 final M02/M19 screenshots, full preference controls, real Wiki publication or a release.


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

## Native Enter failure isolated and application-level focus repair (2026-11-23)

[Windows #45234283387](https://github.com/Vertex-Systems-Network/zynoa-2-local/actions/runs/45234283387) **FAILED** `ZYN-A11Y-005` on source `92df8a803587a0c7eeae0712e016a8a9eb07c2bd`. The original native receipt (artifact 14848762352) independently establishes **8/9 scoped results true**: both Preferences selectors visible/focusable; named modal/search; actual M19-OPT-06 keyboard input reflected via WebView2 ValuePattern; matching local option result; modal reopened and Escape dismissed. Native input and modal were removed by Enter, but UIA could not find the selected option heading as a visible element; the ninth check failed. Because UIA did not directly establish whether the heading existed offscreen or was absent from its tree, offscreen rendering remains a supported hypothesis rather than a proven provider state. A separately downloaded original Tauri option reference screenshot from the previously passing 54-image run shows the M19-OPT-06 Help details visibly rendered after user scroll.

**User-facing fix:** The selected M19 option detail is a real `role=region` labelled by its focusable H3 title. A scoped post-modal pair of requestAnimationFrame callbacks moves keyboard focus and scroll position onto the opened destination, cancelling when the destination changes. Generic main-content focus skips option Help routes. Keyboard and Help source contracts updated; native Windows CI at this code version **pending**. No screen reader certification or all 29 final manifest PNG approval is claimed.

## Exact-source Windows scoped acceptance (2026-11-23)

The repaired source `171cde66b85c9188a57e16e2ae51a700b5fd7939` passed [Windows #45237056822](https://github.com/Vertex-Systems-Network/zynoa-2-local/actions/runs/45237056822) and all other same-source Governance, Reviewdog and task-board checks (see GitHub PR). Original GitHub artifact **14850658096** was downloaded, and the machine-readable native UIA receipt was independently read and tied to that exact build SHA. All **nine** scoped checks are true, including actual keyboard text in the native search input ValuePattern; typed result matching; the visible selected M19-OPT-06 heading after Enter; second modal open and Escape close. UIA issues `[]`, status `SCOPED_NATIVE_UIA_PASS`, duration 2,908ms, native PID confirmed. This is stronger than static React/ARIA attributes but **not** a manually run NVDA/Narrator screen-reader trial.

One original real Windows Tauri screenshot `docs/screenshots/_ci/M19/M19-T10-REF-OPT-06.png` was independently opened and rehashed (998×701; SHA256 `68f9f189a07a3ef64abb14106c8a75dff45e9b6065721c13da673a0a0773c771`). The gold outline around the exact "Wiki mapping and link checker" heading is visible, the selected option ID is correct, and content is legible. [Scoped visual review](../screenshots/M19/P02-option-focus-native-review.json). The source capture remains `candidate_pending_visual_review` and `capture_verified=false` because a scoped manual review does not promote it to a final 29-image manifest asset.

The 54 real native candidate pairs passed CI; final T10 readiness remained `NOT_READY`, **0/29 final M02/M19 assets VERIFIED**. The original performance report contains startup-to-metadata 11,224ms and screenshot suite 73,012ms, one Windows run only. No performance budget is approved. Full accessibility, final option/screen screenshots, Help/Wiki publication, final PR merge and release remain blocked.
