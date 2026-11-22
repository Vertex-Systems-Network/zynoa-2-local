# P01 authentic native Windows screenshots — reviewed subset

These PNG bytes were captured from the real Windows Tauri desktop and independently inspected for visible DWM frame, legibility, privacy, correct native navigation and checksum. [Windows CI](https://github.com/Vertex-Systems-Network/zynoa-2-local/actions/runs/45006477419) passed; [the screenshot publisher](https://github.com/Vertex-Systems-Network/zynoa-2-local/actions/runs/45007283638) accepted exactly the SHA-pinned, visual-reviewed images and [committed the original PNG bytes](https://github.com/Vertex-Systems-Network/zynoa-2-local/commit/1b582a6d5968b105de3143d3f5294aac7d4cd0de).

| Screenshot | P01 behavior genuinely shown | Original PNG SHA-256 |
|---|---|---|
| [First Boot](M01-S01.png) | Native startup, local shell, read-only handshake; upper viewport | `990ea3f00bc9129cd75fc846b9fd123c115cb6abc8bf2ad2d3499133f9dd99cf` |
| [Overview continuation](M01-S01-continued.png) | Actual PageDown, disabled workspace creation and foundation checklist | `40f8cf64be0524366f22f350d4ece5467c91dbb16c500930a3192917adff4de7` |
| [Settings](P01-Settings-preview.png) | Disabled preferences and folder selection (preview only) | `77ea700ac32a7b61515aeb40822d29d6ca9b03fcc0d943581404ae13155586e5` |
| [Recovery](P01-Recovery-preview.png) | No verified backups, disabled restore (preview only) | `621bb118615d3af7cbd547d1c2b740acd1a8b060a5358dc2a4421d6a4229d4ef` |
| [Diagnostics](P01-Diagnostics-preview.png) | Read-only diagnostic capability summary, remote reporting disabled | `c7ba39f71068ece02488f47349cf27fbedfb2bc7814aa934a476b1e981c5355e` |

**Exact built/source commit:** `f9929443740a1740b8fd904058ab0790fadb7163`. Original `.capture.json` files retain the Windows runner's honest `candidate_pending_visual_review` status; separate corresponding `.review.json` files record independent *post-capture* visual acceptance for the identical bytes. [Approval and limitations](P01_REVIEW_APPROVAL.json) and [original Windows artifact](https://github.com/Vertex-Systems-Network/zynoa-2-local/actions/runs/45006477419/artifacts/14748113338) preserve provenance. All five committed Git binary blob hashes were recomputed from downloaded original CI bytes and matched.

**Important scope limit:** This verifies the native P01 read-only foundation presentation **only**. The [full screen inventory](../../ui/SCREEN_INVENTORY.csv) remains `PENDING_IMPLEMENTATION` where future active/error/loading state coverage, project creation, Security Center, backup/restore, live diagnostics, F1 Help, publishing to GitHub Wiki or other planned option controls do not exist. Do not interpret these screenshots as those later features being complete.
