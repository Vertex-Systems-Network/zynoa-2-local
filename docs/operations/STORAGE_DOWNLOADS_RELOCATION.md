# M24 — Download Locations, Storage Quotas and Safe Relocation

**Status: SPECIFICATION ONLY.**

## 1. User requirement

User should choose location for every downloadable **optional runtime/module payload**, model cache, managed asset library, downloads, temporary downloads, exports and backups. Users can change paths after installation via UI and move already downloaded content without redownloading where technically safe. Distinguish app binary location (OS installer controls it), external runtimes installed by other products (we must not silently take ownership), managed sidecar runtimes, and model files.

## 2. Storage classes / example settings

| Class | Default (resolved via native folder API) | Custom location | Move existing | Notes |
|---|---|---|---|---|
| User Data Vault | `%LOCALAPPDATA%/AIWorkspace/data` | Yes, advanced safeguarded migration | Yes | Never co-locate with disposable cache by default |
| Ollama models | Ollama's detected directory | Yes through `OLLAMA_MODELS` with runtime-aware restart | Yes, validated | External daemon may be shared, don't change without scope |
| Hugging Face models/cache | HF SDK default | Yes via `HF_HOME` / `HF_HUB_CACHE` per process | Yes | Must avoid split snapshots/symlink loops |
| llama.cpp/GGUF | Managed model library | Yes | Yes | Hash tracked |
| ComfyUI checkpoints/LoRA | Managed media model library | Yes through supported extra model path config | Yes | Many subcategories; validate profile |
| Managed runtime sidecars | App managed runtimes root | Yes (some installers may constrain) | Yes only where relocatable | Pin executable hashes/licenses |
| Design assets | Managed user file store | Yes | Yes | Included in backups |
| Research/source files | Managed library | Yes | Yes | Excludes arbitrary user external references |
| Download staging | Per-volume temp directory | Yes | Yes, with resumable state | Keep sufficient free disk |
| Export/output | OS user Documents or user-set | Yes | N/A | No silent change of output paths |
| Backups | User-selected independent target | Yes | Yes, with backup catalog re-index | Cross-disk recommended |
| App executable | Installer selected OS app location | Installer controls | No in-app arbitrary move | Avoid invalidating code signatures/updater |

**Critical runtime integration**: changing `OLLAMA_MODELS` works for a runtime started with that environment; an independently installed Ollama app/service may have its own lifecycle and environment. If runtime is outside client ownership, guide user through safe restart rather than silently rewriting system-wide configuration. Hugging Face respects `HF_HOME` and `HF_HUB_CACHE` as applicable to the process/runtime. ComfyUI supports `extra_model_paths.yaml` / models-directory configuration. Do not assume all versions behave identically; capability probe per backend.

## 3. Storage Settings UI

Tabs: Overview (drive usage by class), Model Locations, Module/Runtime Locations, Chat/Data Vault, Backup Locations, Downloads/Network, Relocation Queue, Storage Cleanup, Diagnostics.

For every class show: current path, owner/runtime, whether location is movable, volume free/capacity, estimated current bytes, available compatibility, encryption/privacy if relevant, and `Browse`, `Move Existing`, `Use Without Moving`, `Verify`, `Revert`, `Open Folder` controls. Do not offer `Move` if runtime is busy or path unsafe. On choosing new folder, display whether newly downloaded files only or existing files will be migrated.

## 4. Safe relocation state machine

`IDLE → VALIDATING_DESTINATION → INVENTORY & SPACE_ESTIMATE → QUIESCING_RUNTIME → COPYING_TO_STAGING → HASH_VERIFY → UPDATE_RUNTIME_CONFIG → RESTART_RUNTIME → HEALTH_PROBE → ATOMIC_POINTER_COMMIT → CLEANUP_OLD (delayed)`

Failure states: `PAUSED`, `DISK_FULL`, `PERMISSION_DENIED`, `FILES_LOCKED`, `BACKEND_INCOMPATIBLE`, `ROLLBACK_PENDING`, `NEEDS_MANUAL_RESTART`.

Sequence:

1. Probe folder writable, canonicalized, sufficiently spacious, mounted and not containing unsafe symlink/junction escape.
2. Validate target not same/subdirectory as source and avoid moving to filesystem which lacks required filename semantics/permissions.
3. Pause active models and downloads; checkpoint partial transfers with ETags/ranges where supported.
4. Snapshot immutable inventory of each file (`relative_path`, size, SHA-256, class, runtime owner) and dependency manifests.
5. Same-volume atomic rename may be used **only after validating safety**; otherwise copy to isolated staging under destination (NEVER delete source yet).
6. Verify file count, bytes, hashes; resume interrupted copies by verified chunks where safe.
7. Write new versioned config to temp, atomically swap; update app-managed runtime environment and startup scripts.
8. Restart/probe runtime and load a representative model/artifact; validate metadata and source references.
9. Commit manifest/path pointer; provide user old-folder cleanup prompt or safe delayed GC. If health probe fails, restore prior config and keep source untouched.
10. For disowned/external runtime, report manual steps or limited capability, not falsely claim migration completed.

## 5. Fast downloads architecture

Transport adapter with resume/range requests where provider supports them, bounded concurrent transfers, weighted disk IO/backpressure, bandwidth limits, retry with jitter, partial chunk hashes, expected content hashes where published, interruption checkpoints and file-level dedupe. Trusted signed binaries: signature verification independent of model hash. Model versions use immutable IDs/revisions where possible. Do not assume Hugging Face's Xet transport follows ordinary HTTP range semantics internally; use official SDK high-performance facilities when applicable.

Download manager owns: task ID, source URI/ref, backend, expected size/digest, destination store ID, retry count, range/etag, chunk completion bitmap when supported, bandwidth estimate, allocated space, last error. No overlapping downloads clobber identical files. Cache eviction must never delete a model used by a running task.

### Quotas and cleanup

Per-location soft/hard quota, low-disk warning, unused model age, pinned models, cache TTL and GC preview. User data is never evicted as a model cache. Model dependencies and project references count toward pinning. Cleanup must show reclaimable bytes and have undo/recovery where possible. Backup files have independent retention, not cache cleanup.

### Failure test matrix

- C: to D: copy with app process crash, interruption at 3%/50%/99%, resume, final SHA match and old source preserved.
- Ollama owned vs independent daemon, model registry unchanged, actual sample inference post-move.
- Hugging Face SDK under custom HF cache, sample load after restart.
- ComfyUI checkpoints + LoRA from moved folders, sampling/render test.
- Filesystem case differences, spaces, Unicode, non-ASCII model names, long paths, NTFS permissions, read-only folders and Windows junctions.
- Removable drive unplugged/replugged; network drive offline; file locking/antivirus; partial download resume.
- Destination path inside source, source inside destination, backup path inside model cache (reject), disk full, config write rejected, no privileged elevation.
- Two simultaneous path migration requests serialized and idempotent; duplicate handling; cleanup never deletes only copy.

**Official runtime references (verified 2026-11-18):**
- https://github.com/ollama/ollama/blob/main/docs/faq.mdx
- https://huggingface.co/docs/huggingface_hub/package_reference/environment_variables
- https://github.com/Comfy-Org/ComfyUI/blob/master/extra_model_paths.yaml.example
