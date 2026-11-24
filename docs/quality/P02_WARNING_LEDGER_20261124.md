# P02 warning ledger — 2026-11-24

Observed actual Windows job [#45324467511](https://github.com/Vertex-Systems-Network/zynoa-2-local/actions/runs/45324467511), source `98a31d4d01255d28fa78f879d6c72eb0bd880ba3`, protected main `f24c72eff1c4fec03a6687575ea19e9593b57a2c`. All six affected Rust source files were compared by Git blob SHA and were byte-identical to main before this repair. 43 source-located warning occurrences; aggregate warning-count lines excluded. No claim of a warning-free build. [Issue #18](https://github.com/Vertex-Systems-Network/zynoa-2-local/issues/18). Baseline review due 2026-12-01 UTC and before each owning phase integration; no waiver or suppression. New or security-significant warnings remain blocking.

| Source + original line (under apps/desktop/src-tauri/) | Warning signature / fingerprint (path + message) | Owner / integration | Disposition |
| --- | --- | --- | --- |
| `src/locations.rs:226` | unused variable: `app` | M24 P05 | Mechanical source repair; fresh verification pending |
| `src/secrets.rs:46` | associated function `new` is never used | M16/P03 native integration | Inherited unused contract; retain API, resolve with real owned runtime integration; open |
| `src/events.rs:33` | variants `IssueReported`, `TestFailed`, `TestPassed`, `DocsUpdated`, `ChangeVerified`, and `ChangeReverted` are never constructed | M26 P02/P11 | Inherited unused contract; retain API, resolve with real owned runtime integration; open |
| `src/events.rs:51` | variants `System` and `Ci` are never constructed | M26 P02/P11 | Inherited unused contract; retain API, resolve with real owned runtime integration; open |
| `src/events.rs:59` | variants `M01`, `M16`, `M17`, `M18`, `M23`, and `M24` are never constructed | M26 P02/P11 | Inherited unused contract; retain API, resolve with real owned runtime integration; open |
| `src/events.rs:61` | variants `System` and `Support` are never constructed | M26 P02/P11 | Inherited unused contract; retain API, resolve with real owned runtime integration; open |
| `src/events.rs:5` | unused import: `PathBuf` | M26 P02/P11 | Mechanical source repair; fresh verification pending |
| `src/security.rs:7` | variants `ReadUserFile`, `WriteUserFile`, `OutboundNetwork`, `ReadCredential`, and `WriteCredential` are never constructed | M16/P03/P04 native policy | Inherited unused contract; retain API, resolve with real owned runtime integration; open |
| `src/security.rs:42` | method `revoke` is never used | M16/P03/P04 native policy | Inherited unused contract; retain API, resolve with real owned runtime integration; open |
| `src/secrets.rs:8` | enum `SecretFault` is never used | M16/P03 native integration | Inherited unused contract; retain API, resolve with real owned runtime integration; open |
| `src/secrets.rs:14` | struct `SensitiveText` is never constructed | M16/P03 native integration | Inherited unused contract; retain API, resolve with real owned runtime integration; open |
| `src/secrets.rs:17` | associated items `new` and `expose_for_native_store` are never used | M16/P03 native integration | Inherited unused contract; retain API, resolve with real owned runtime integration; open |
| `src/secrets.rs:29` | function `check_slot` is never used | M16/P03 native integration | Inherited unused contract; retain API, resolve with real owned runtime integration; open |
| `src/secrets.rs:40` | struct `WindowsCredentialVault` is never constructed | M16/P03 native integration | Inherited unused contract; retain API, resolve with real owned runtime integration; open |
| `src/secrets.rs:46` | associated items `new`, `entry`, `put`, `get`, and `forget` are never used | M16/P03 native integration | Inherited unused contract; retain API, resolve with real owned runtime integration; open |
| `src/diagnostics.rs:234` | method `grouped_snapshot` is never used | M18/P11 | Inherited unused contract; retain API, resolve with real owned runtime integration; open |
| `src/vault.rs:10` | constant `MAX_CONTENT_BYTES` is never used | M23 P03 | Inherited unused contract; retain API, resolve with real owned runtime integration; open |
| `src/vault.rs:14` | variant `InvalidRecord` is never constructed | M23 P03 | Inherited unused contract; retain API, resolve with real owned runtime integration; open |
| `src/vault.rs:18` | enum `ContentClass` is never used | M23 P03 | Inherited unused contract; retain API, resolve with real owned runtime integration; open |
| `src/vault.rs:20` | method `name` is never used | M23 P03 | Inherited unused contract; retain API, resolve with real owned runtime integration; open |
| `src/vault.rs:30` | fields `app_root` and `conn` are never read | M23 P03 | Inherited unused contract; retain API, resolve with real owned runtime integration; open |
| `src/vault.rs:34` | function `safe_id` is never used | M23 P03 | Inherited unused contract; retain API, resolve with real owned runtime integration; open |
| `src/vault.rs:128` | associated items `insert_new`, `read`, `snapshot_new`, and `restore_to_new_test_profile` are never used | M23 P03 | Inherited unused contract; retain API, resolve with real owned runtime integration; open |
| `src/locations.rs:41` | variant `Denied` is never constructed | M24 P05 | Inherited unused contract; retain API, resolve with real owned runtime integration; open |
| `src/locations.rs:44` | fields `app_root` and `manifest` are never read | M24 P05 | Inherited unused contract; retain API, resolve with real owned runtime integration; open |
| `src/locations.rs:131` | methods `resolve` and `move_existing` are never used | M24 P05 | Inherited unused contract; retain API, resolve with real owned runtime integration; open |
| `src/events.rs:11` | constant `MAX_READ` is never used | M26 P02/P11 | Inherited unused contract; retain API, resolve with real owned runtime integration; open |
| `src/events.rs:20` | variant `InvalidEvent` is never constructed | M26 P02/P11 | Inherited unused contract; retain API, resolve with real owned runtime integration; open |
| `src/events.rs:24` | enum `Audience` is never used | M26 P02/P11 | Inherited unused contract; retain API, resolve with real owned runtime integration; open |
| `src/events.rs:26` | method `label` is never used | M26 P02/P11 | Inherited unused contract; retain API, resolve with real owned runtime integration; open |
| `src/events.rs:32` | enum `EventKind` is never used | M26 P02/P11 | Inherited unused contract; retain API, resolve with real owned runtime integration; open |
| `src/events.rs:37` | method `label` is never used | M26 P02/P11 | Inherited unused contract; retain API, resolve with real owned runtime integration; open |
| `src/events.rs:51` | enum `Origin` is never used | M26 P02/P11 | Inherited unused contract; retain API, resolve with real owned runtime integration; open |
| `src/events.rs:53` | method `label` is never used | M26 P02/P11 | Inherited unused contract; retain API, resolve with real owned runtime integration; open |
| `src/events.rs:59` | enum `Module` is never used | M26 P02/P11 | Inherited unused contract; retain API, resolve with real owned runtime integration; open |
| `src/events.rs:61` | enum `Retention` is never used | M26 P02/P11 | Inherited unused contract; retain API, resolve with real owned runtime integration; open |
| `src/events.rs:63` | method `label` is never used | M26 P02/P11 | Inherited unused contract; retain API, resolve with real owned runtime integration; open |
| `src/events.rs:68` | struct `EventRequest` is never constructed | M26 P02/P11 | Inherited unused contract; retain API, resolve with real owned runtime integration; open |
| `src/events.rs:82` | struct `EventSummary` is never constructed | M26 P02/P11 | Inherited unused contract; retain API, resolve with real owned runtime integration; open |
| `src/events.rs:91` | field `conn` is never read | M26 P02/P11 | Inherited unused contract; retain API, resolve with real owned runtime integration; open |
| `src/events.rs:94` | function `safe_token` is never used | M26 P02/P11 | Inherited unused contract; retain API, resolve with real owned runtime integration; open |
| `src/events.rs:99` | function `valid_request` is never used | M26 P02/P11 | Inherited unused contract; retain API, resolve with real owned runtime integration; open |
| `src/events.rs:215` | methods `append` and `list_for` are never used | M26 P02/P11 | Inherited unused contract; retain API, resolve with real owned runtime integration; open |

## Toolchain warnings

- Windows desktop, rendered Wiki and isolated Narrator reported deprecated Node20 actions; official [setup-node v6](https://github.com/actions/setup-node/blob/main/README.md), [upload-artifact v6](https://github.com/actions/upload-artifact/releases/tag/v6.0.0) and [download-artifact v7](https://github.com/actions/download-artifact/releases/tag/v7.0.0) use Node24. Existing hosted runner supports checkout v6. Updated these three in-scope evidence workflows, kept app Node22 toolchain, disabled new implicit package-manager caching. No permission/acceptance relaxation; verify new exact-head logs.
- DEP0040, DEP0169 and DEP0005 originate from action dependency/runtime output; inspect after upgrades, not fixed until actual logs confirm. P00 worker checkout@v4/setup-python@v5 deprecation remains P00 infrastructure debt (#3). Trusted main governance untouched.
- Do not delete future security, vault, location or event-store contracts to silence dead code. No `allow(dead_code)`, warning filter, or global Rust flag was added.
