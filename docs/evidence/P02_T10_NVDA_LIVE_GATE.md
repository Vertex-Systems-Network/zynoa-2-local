# P02-T10: live NVDA speech gate (Windows CI)
Implemented on the active P02 PR as a **fail-closed** independent screen-reader gate, not a certificate.
Pinned official NV Access NVDA 2026.3.1 installer SHA-256: `6f80a5b0ca720a7d0d314b5be212f37388bbe81a1107ac3298c1821a1cd3f052`.
Source: https://www.nvaccess.org/post/nvda-2026-3-1/

On disposable GitHub-hosted Windows, create an isolated portable NVDA profile with a CI-only global plugin subscribing to the authentic NVDA `pre_synthSpeak` extension point. A real native Tauri process is foregrounded; keys enter Preferences, open the command palette, type `M19-OPT-06` into the actual WebView2 input (verified via UIA ValuePattern), and open the selected local Help option. Only allowlisted nonprivate speech text is recorded.

The verifier rejects missing process identity, invalid installer SHA, absent plugin startup, fake keyboard value, or any of the required genuine spoken announcements. This is separate from existing nine UIA checks and 29 actual Windows screenshots. **No PASS is claimed until the exact-head Windows Actions job finishes successfully**. Full Microsoft Narrator testing, performance budget and P02 merge remain separate. No user files/credentials, persistent OS add-ons, app release or new runtime dependencies.
