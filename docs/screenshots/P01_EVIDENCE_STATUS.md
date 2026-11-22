# P01 native screenshot status — candidate only

**No verified screenshot was committed by this change.** P01-T10 is IN_PROGRESS. The Windows CI job attempts a first native `M01-S01` Overview screenshot from the actual unsigned Tauri process, not a browser rendering, concept mock or generated image.

The capture script locates the real process main-window handle, checks visible bounds, attempts foreground display, copies screen pixels, rejects blank/monochrome images and writes a PNG and `M01-S01.capture.json` containing exact PR source SHA, SHA-256, size, alt text and `capture_verified=false`. Windows CI uploads both as a build-evidence artifact, without write access to the repository.

**Before acceptance:** retrieve and inspect the image for actual WebView rendering, clipping, text, correct state, privacy, OS/DPI and visual fidelity. Only then commit the reviewed binary and update `docs/ui/SCREEN_INVENTORY.csv` / Help/Wiki with hash and provenance. If GitHub-hosted Windows lacks an interactive desktop, the screenshot test must fail rather than claim success from a browser preview.

Remaining M01/M16/M17/M18 planned controls cannot be represented by fabricated screenshots. Their UI implementation, navigation states and real capture evidence remain pending.

**Candidate review — [Windows run #44989437051](https://github.com/Vertex-Systems-Network/zynoa-2-local/actions/runs/44989437051): REJECTED as screenshot evidence.** Real native Tauri window verified, 1044×788 image and SHA-256 `9d8e23e802831d23238c0a0dc549570647fd12bf051ebef76d081e2fb0beb3bd` match the CI artifact, but the runner's smaller desktop caused the Windows taskbar/desktop edge to appear at the bottom/left. This is an unreviewed **rejected candidate**, not a committed verified screenshot. Fix now resizes and repositions the real native window inside the display *working area* before capture and fails if taskbar overlap remains. Next screenshot requires fresh CI and independent visual review.
