# P01-T08 — M24 native data location registry foundation

**Current status:** IN_PROGRESS pending Windows Rust build and real boot tests. Native-only versioned path manifest is **NOT a relocation engine** and exposes no frontend path-setting command. The app does not install or modify Ollama, Hugging Face, ComfyUI or other external runtimes.

**Managed classes:** user vault, diagnostics, backups, cache, staging and app-managed model storage. A separate external-runtime reference has `external_read_only` ownership and no inferred physical path. The registry persists relative path labels only in `storage-locations-v1.json`, never a username/absolute user folder path. Root comes from native Tauri OS local-data resolver, bound to the app identifier. Cache, staging and model directories are not automatically created just because they are listed. Entries are versioned and deny unknown fields. Corrupt/changed existing manifests are rejected and preserved, not overwritten.

**No moves/cleanup allowed:** until a guarded destination grant, per-volume inventory, quiesce, staging, hashing, activation and rollback exist, all move requests return denied. In particular there are **no silent external-runtime changes**, no model downloads or deletions, no automatic migration, and no user-facing consent UI.

**Windows proof planned:** pinned Rust tests verify version persistence, relative-only defaults, corruption preservation, external-runtime refusal and root/path traversal guards. Windows native boot verifies that the physical registry exists under local app data and contains only allowlisted ownership categories. No user vault file content is read by the registry.

**Pending T08 completion:** real Windows CI, bounded migration previews and ownership rules, durable registry recovery, path/junction race audit and integration with native M23/M18. This P01 foundation does not implement the full M24 storage-relocation UI, advanced path choices, external backend integration or downloadable-class migration. Those remain future phase/help/screenshot gates.

**Windows CI startup readiness:** a new bounded cold-boot check waits for the native diagnostic spool, SQLite vault and storage registry and fails if any are missing or the executable exits early. This replaces a process-survival-only assertion, not the detailed individual file integrity checks. Latest source runtime failure was `ZYN-DIAG-101`; root cause remains unverified pending this run. No file path values or user content are logged.
