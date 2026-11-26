# Architecture Decision Log

- ADR-0001: Windows-first local-first, modular Tauri/Rust + React/TypeScript, Rust policy broker, versioned agent sidecar. Status: proposed baseline; validate during P00.
- ADR-0002: Single active delivery phase branch and one primary PR; required checks, auto-merge subject to protection. Status: required policy.
- ADR-0003: Professional GUI shell/design system completed and tested before Chat implementation, while core interfaces remain extensible. Status: required policy.
- ADR-0004: Figma-like editor is a dedicated later module; do not conflate it with app design-system authoring. Status: required policy.
- ADR-0005: No recurring approvals for pre-authorized sandboxed tasks; all out-of-scope actions denied by broker. Status: required policy.

Record future decisions using ADR number, options considered, evidence, rationale, owner/agent, tradeoffs, tests and date.

## 2026-11-18 — v3.1 architecture additions (proposals until implemented)

- DEC-031A: Separate user vault, model binary stores, downloaded runtime payloads, caches and app executable.
- DEC-031B: Signed stable GitHub Releases; phase merge only triggers qualification, not unconditional end-user publication.
- DEC-031C: Client checks updates and notifies users; installation is their choice by default; no silent interruption of active agent work.
- DEC-031D: Mandatory verified backup before binary/schema migration; tested staged restore/rollback; OS reinstall and disk loss limitations documented.
- DEC-031E: Pluggable location adapters for Ollama/HF/ComfyUI and safe migration with checksums; do not rewrite independent third-party runtime settings silently.

## ADR-0007 — planned change intelligence architecture

M26 uses append-only event ledger, per-PR change records, verified-release manifest, product changelog projections and versioned Help/Wiki. Unreleased issue history stays separate from user-visible shipped releases. See `docs/adr/0007-change-intelligence-and-changelog.md`. No implementation yet.
2026-11-21 | P00 | Added AI_STRICT_PROTOCOL; V3_2 is sole operational plan | removes plan conflict and agent drift
2026-11-21 | P00 | Owner has no hardware/credentials: T17/T19/T21-T24 to be redesigned on GitHub-hosted runners + GITHUB_TOKEN | only AI-executable path; no user infrastructure
2026-11-21 | P00 | T22 live acceptance (workflow_run listener must be on main) moves to the first step after P00 merge; T24 merge no longer waits on it | breaks T22<->T24 circular dependency
2026-11-22 | P01 | ADR-0025 selects Tauri 2/Rust + React/TypeScript/Vite for native capability-scoped P01 foundation; Electron and Wails 3 retained as researched alternatives | matches master plan and keeps policy/vault in Rust; version pin and Windows proof deferred to T03
2026-11-22 | P01 | Interpret P01-T04 typed IPC as M01/M16 workspace transport while M16 remains Project & Workspace Manager; include M23/M24/M26 only for their explicit P01 foundation tasks | reconciles task-label discrepancy with module dossiers and preserves phase scope
2026-11-22 | P01 | T02 observer must bind phase/branch/PR and never journal invalid phase as P00 | prevents stale P00 identity from contaminating P01 evidence
2026-11-22 | P01 | P00 Issue #3 applies only to P00; P01 observer reports blocker policy UNKNOWN and cannot authorize phase transition/merge without separately configured blocker scope | prevents inheriting irrelevant P00 blocker and protects owner-only merge policy
2026-11-22 | P01 | Keep scripts/runner_worker.py and its heavy rootless/Ollama workflow phase-locked to the P00-T20 disposable fixture; use tools.phase_worker active-phase read-only observer for P01 | fixture model execution grants cannot be promoted to P01 source editing
2026-11-22 | P01 | T02 runner dispatch reads active phase plus trusted Actions branch/PR; P01 permits only read-only observer while P00 fixture Docker/Ollama and bot-branch publishing remain P00-only | prevents permission carryover and limits expensive jobs to relevant code changes
2026-11-22 | P01 | T03: create offline Tauri 2 + React/TypeScript/Vite minimal native shell with no privileged JS grants; Windows runner checks build and executable boot; no persistence or IPC claim | stays within M01 and avoids unverified user-data authority
2026-11-22 | P01 | T03 native Windows unsigned executable compiled and survived 8-second cold-boot process test in run 44972395326; no claim of WebView2 visible-window/screenshot, signed installer or checked-in dependency locks | T03 bootable process gate met; interactive GUI/screenshot and reproducibility remain later evidence gates
2026-11-22 | P01 | T04 M16 refers to Project & Workspace Manager; implement only M01/M16 read-only workspace.status typed handshake as P01 transport, and restrict custom Tauri command to main window using AppManifest ACL | avoid module reclassification or premature filesystem permissions
2026-11-22 | P01 | T05: use Windows-native Credential Manager via pinned keyring 3.6.3 and zeroize native-secret buffers; keep all credential operations private to Rust (no IPC grant), model a deny-first capability broker and revoke locally | avoids webview secret exposure and plain-text storage; CI cannot attest production code-signing identity
2026-11-22 | P01 | T05 accepts only native-only security foundation on Windows CI #44973840898; maintain signing/installer trust and user-facing permission-grant UI as unfulfilled P01 exit gates | do not confuse passing testable native adapter with signed release or finished security center
2026-11-22 | P01 | Start T06 with allowlisted native-only diagnostic spool and Windows Rust fixture tests, not WebView or remote reports | prevents uncontrolled diagnostics leaking user information before M24 storage grants
2026-11-22 | P01 | Wire M18 native-only startup, sanitized panic and denial-class event capture to Tauri's OS-resolved app-local data root, refuse symlinked/corrupt existing locations and fail startup with static code on unavailable store | makes diagnostic spine real without granting WebView arbitrary path or remote telemetry access; multi-process locking and retention remain pending
2026-11-22 | P01 | Prevent multiple Windows app instances from appending to one M18 spool by holding a kernel-exclusive local writer guard; never delete stale marker or log and test immediate crash release | protects replay counts and data integrity without a mutable lockfile lease or auto-destructive recovery
2026-11-22 | P01 | Accept P01-T06 as tested native diagnostic-spine sub-scope on Windows #44980027777 and Governance #44980027876; keep the broader M18 UI/remote issue reporting/screenshots/signing explicitly incomplete | task-scope evidence is not evidence of a shipped full module
2026-11-22 | P01 | Start T07 native-only M23 SQLite WAL vault with pinned rusqlite 0.43.0 bundled+backup, transaction-after-commit receipts and isolated online-backup restore tests; no frontend commands or preexisting file replacement | aligns with M23 data safety and avoids premature exposure of untested user-data writes
2026-11-22 | P01 | Wire private M23 SQLite vault to trusted Tauri startup OS app-local data directory; no frontend vault commands and no user data on first boot; refuse nonregular WAL sidecars and existing restore destination | verifies native persistence outside app binary while preventing premature user-data mutations and overwrite
2026-11-22 | P01 | Accept T07 M23 native transactional core after Windows #44981325644 real app-local boot/schema integrity and Rust WAL/online-backup/restore tests; full M23 UI/encrypted portable backup and post-reinstall recovery remain gated | distinguish tested native storage foundation from finished end-user backup and release
2026-11-22 | P01 | Start T08 M24 with native-only versioned relative storage class registry, OS-root binding, read-only unresolved external runtimes and explicitly denied migrations | separates app-owned data, backups, cache and models without silent ownership transfer or data deletion
2026-11-22 | P01 | Fix concurrent Windows Rust fixture collisions using process-atomic sequence in M18/M23/M24 tests; retain all negative tests | CI #44981878863 proved coarse timestamp caused same-path AlreadyExists with parallel tests
2026-11-22 | P01 | Gate native Windows cold boot on three actual OS-local artifacts with bounded 45s startup wait rather than a fixed 8s process-alive check | T08 CI showed process survival without the required diagnostics file; keep strict schema and privacy checks enabled
2026-11-22 | P01 | Accept T08 only as Windows-tested native M24 relative location/ownership registry on CI #44986611731, keep user-selected relocation and external-runtime operations disabled | gate required real registry, SQLite vault, diagnostics readback and full Governance; no destructive migration permissions were added
2026-11-22 | P01 | Start M26/T09 as a standalone native SQLite WAL append-only audit ledger under app-local data with unique stream sequences, strict idempotency and fixed privacy categories; no UI, network, user payload or release markers | preserves release truth and avoids schema migration of existing M23 vault while enabling restart-safe native audit events
2026-11-22 | P01 | Serialize native M26 SQLite first-open schema discovery/creation within a process with fail-closed mutex while keeping WAL/IMMEDIATE concurrent event append | Windows CI #44987500956 showed a real race (30 passed, 1 failed); never weaken parallel writer tests or overwrite event history
2026-11-22 | P01 | Start T10 with Windows native Tauri window screenshot evidence only; candidate image and SHA/alt metadata remain unverified until actual visual review; reject blank/hidden windows | prevents fabricated browser/mock images from passing P01 real-screenshot documentation gate
2026-11-22 | P01 | Reject first native M01 screenshot as acceptance evidence because CI display taskbar and desktop overlap actual app bounds; resize/reposition Tauri native HWND into verified Windows working area before recapture; correct stale shell copy to reflect verified native storage but disabled user features | preserve real Windows provenance and avoid falsely accepting clipped or occluded screenshots
2026-11-22 | P01 | Keep M01 native screenshot candidate #14741119290 unverified despite green Windows CI: resize fixed taskbar overlap but DWM invisible borders reveal surrounding desktop pixels; require DWM extended-frame crop or documented pixel-only crop, SHA, alt review before committing PNG | visual acceptance is stricter than successful screenshot creation, no screenshots may be fabricated
2026-11-22 | P01 | Fix M01 CI screenshot native visible bounds using DwmGetWindowAttribute extended frame (9) and fail closed on DWM error or out-of-display bounds | GetWindowRect included invisible resize margins exposing underlying CI desktop; screenshots must be genuine Tauri pixels
2026-11-22 | P01 | Fix PowerShell Marshal.SizeOf DWM RECT by passing boxed value instance instead of type object | Windows CI #44990920037 had all 32 Rust tests pass but capture script marshaling failed; preserve fail-closed capture on DWM failure

2026-11-22 | P01 | Bind screenshot evidence to the actual checked-out PR HEAD and fail fast on PowerShell parser errors; keep unreviewed native PNG as candidate only | prior synthetic-merge SHA ambiguity and Windows parser failure needed explicit reproducible proof and no premature visual acceptance

2026-11-22 | P01 | Source-control only authentic SHA-pinned and independently reviewed native CI PNGs; keep all unimplemented full-module option screens explicitly pending | preserves exact source/visual provenance without falsely claiming P02 Help/UI or production features

2026-11-22 | P01 | Record T11 separately as IN_PROGRESS; preserve draft/no-merge owner constraint while confirming effective trusted main ruleset #27593065 via rulesets API | a green CI/task board and `protected=true` do not imply permission to merge; blocker scope and post-merge SHA must be independently verified

2026-11-22 | P01 | Permit only authenticated exact-target active non-bypass repository ruleset readback if the classic effective-rules endpoint is inaccessible; fail closed on ambiguity and preserve independent issue-scope/owner authorization gates | the real main ruleset is independently readable and trusted but legacy branch-rules access can be denied to integrations

2026-11-22 | P01 | Strengthen guarded premerge with explicit independent blocker-policy completeness, an exact integer zero count and verified GitHub Actions provenance | a zero count or green check alone can be fabricated/incomplete and must never authorize protected merge

2026-11-22 | P01 | For P01+ independently classify exhaustively paginated real GitHub open issues by explicit phase + merge-disposition labels and reject arbitrary supplied blocker tuples, including empty | zero issues cannot be self-certified by a caller; unknown/unlabelled issues must fail closed rather than allow a merge

2026-11-22 | P01 | Maintain an evidence-backed issue-by-issue triage dossier instead of silently marking legacy open P00/M22 incidents nonblocking after PR #1 merged | issue #3 still explicitly claims P00 premerge blocker and issue #7 has actual P01-era Governance CI failures; only independent maintainer can resolve relevance, not the branch author

2026-11-22 | P01 | Require two matching authenticated GitHub premerge observations plus SHA-256 of exhaustive independently classified open-issue IDs/labels, refusing changed issue, PR, CI or main evidence | prevents time-of-check/time-of-use acceptance of stale blockers or PR state between initial preflight and protected merge attempt

2026-11-22 | P01 | Verify governance.yml exact GitHub blob equality between pinned protected main and PR head before accepting trusted governance check; require it again in the second merge preflight | the real Actions app and workflow path do not by themselves prove that PR-authored workflow instructions were not weakened

2026-11-22 | P01 | Require a separate explicit owner-merge operator confirmation tied to immutable phase/PR/head before any GitHub write-merge call, on top of trusted branch/CI/issue evidence | a green CI and configured write token do not themselves establish user authorization; current do-not-merge instruction remains binding

2026-11-22 | P01 | Record each actual M22 Governance failure's root cause and independently verified default-branch incident publisher job/Issue #7 readback; revisit historical Issue #5 "manual-only" evidence boundary without altering issue states | five real CI failures reduce to three remediated classes while successful protected-main workflow_run jobs prove auto dedup updates; independent maintainers still own phase/severity/acceptance classification

2026-11-22 | P01 | Fail-close pure next-phase policy against bool/float false-zero and absent P01+ independent GitHub issue inventory, without changing the merge executor | Existing authorize_next_phase permitted false==0 and did not require complete authenticated phase-scoped issue labels; scoped tests added before phase advancement (no merge or phase change)

2026-11-22 | P01 | Add strict host-local verified-transition SQLite journal receipt with replay/readback and collision denial; never backfill P00 history | Issue #4 requires a separate persisted transition event, while actual P00 code only logged remote observations. Explicit external publication is required because GitHub Actions workers are ephemeral; no merge, P02 or historical proof invented.

2026-11-22 | P01 | Prefer a trusted-main-only bot PR-comment external phase-journal receipt with exact GitHub readback and replay dedup, not a new archive branch | GitHub runner SQLite is ephemeral; the primary PR already exists and persists after merge. This is not immutable or retroactive P00 evidence, and it cannot execute on draft PR #10.

2026-11-22 | P01 | Finalized T11 after owner-requested protected PR #10 merge with exact GitHub SHA readback; retain truthful phase-specific issue blockers | GitHub squash SHA c5fca7106942e96be2c6d07ff9938a61e7854780; main governance and Windows passed, open #3 remains P00 blocking, future #2 remains P08I blocking, P01 #7 historical CI regressions now nonblocking after verified repairs; T11 11/11 closeout needs its own protected PR before P02.
2026-11-22 | P01 | Skip trusted-main receipt publishing on IN_PROGRESS phase snapshots, while retaining strict MERGED_VERIFIED verification | first post-primary-merge receipt #45065695769 failed closed as P01 remained IN_PROGRESS, a false-negative workflow result rather than evidence of a successful event publication; closeout adds explicit status gate and test.

2026-11-22 | P02 | Build session-scoped semantic React/CSS tokens and keyboard-accessible command/navigation plus offline Help search with pinned native source and no dependency additions | M02/M19 need real working UI, but native persistence/wiki publishing are not yet authorized services; choose typed allowlisted local behavior over decorative/remote controls. VS Code/Figma/Penpot/WAI references in ADR-0026. CI/screenshot proof pending.

2026-11-23 | P02 | Keep P02-T02 at IN_PROGRESS until all 15 final M02 screenshots, implemented option contracts and complete native visual/performance evidence pass; add fail-closed acceptance guard and explicit Light/Dark/Keyboard-guide candidate capture | Prior CI-green source slices and nine real Tauri screenshots prove only scoped foundations, while M02-OPT-03/04 and final manifest remain incomplete; preventing false closure is safer than marking DONE without release-quality proof.

2026-11-23 | P02 | Add Reviewdog as a same-repo-only PR comment/annotation layer with read-only UI scanning before token injection; implement M02-OPT-03 as session-only compact properties layout preview | The Marketplace setup action alone does not provide code review; source lint cannot replace native CI, and preview UI must not imply an operational saved project inspector.

2026-11-23 | P02 | Implement M02-OPT-04 as in-app session-only Ctrl+1..6 shortcut remapping via swap-on-collision, with F1/Ctrl+Shift+P reserved; keep P03 locked | Uses a reversible, typed allowlist without native global hooks or persistent preferences. Existing source CI and real Windows Tauri visual evidence verify changed navigation labels, while phase protocol forbids P03 implementation before P02 verified merge.

2026-11-23 | P02 | Complete official P02-T04 functional command-palette/shortcut/focus work on exact-source Windows CI and independent nine-image native review while keeping M02/M19 final screenshot-manifest under P02-T10 | Five source-SHA workflows passed, no-match/Escape/Enter and shortcut-swap views were inspected; full released module screenshots and screen-reader certification remain separate evidence gates, so P02 phase cannot advance.

2026-11-23 | P02 | T03 adaptive desktop sidebar uses a 78px rail automatically at <=1000px with an explicit session-only expand/collapse button and Alt+N; keep named split preview regions | Compared permanent 222px sidebar (insufficient main content at 900px native width) with overlay drawer (harder keyboard/focus management). A persistent accessible icon rail preserves navigation and content without new storage or native permission. Require real Windows narrow viewport screenshot review and full CI before DONE.

2026-11-23 | P02 | Replace preview-only M19 Help with versioned offline search and guided recovery, FAQ/glossary, local Wiki mapping and sanitized reports; do not publish or auto-upload | A bundled typed catalog and finite-step wizard give real user value without introducing network, storage or unsafe GitHub ticket actions. Hosted Wiki publication and screenshot tours remain explicit later gates.

2026-11-23 | P02 | Unify local M02 view commands with M19 articles and option references behind one bounded keyboard palette; route only allowlisted local targets | Delivers an end-to-end discoverability workflow across current-phase modules without new dependency, storage, network, native privilege or P03 scope. Preserve real Windows/native/screenshot gates and release worker lease at handoff.

2026-11-23 | P02 | Implement 16-option actual Windows Tauri Help-reference matrix with exact SHA/identity validation and an honest T10 29-image readiness gate | Native UI screenshots, unlike browser mocks, supply reviewable evidence without extra app dependencies; the Help references do not replace actual option-control screenshots or screen-reader/performance acceptance.

2026-11-23 | P02 | Add Microsoft UIAutomationClient read-only inspection of actual Windows Tauri WebView2 HWND, with required accessible labels, modal keyboard focus and Escape evidence, separate from screen-reader approval | Alternatives: DOM-only/source inspection cannot prove OS accessibility tree, screenshot pixels cannot prove accessible labels; Windows built-in UIAutomation needs no runtime dependency or network and fail-closes on missing real tree. Revert only this bounded CI proof if incompatible; P02 stays active.

2026-11-23 | P02 | Replace brittle Windows WebView2 UIA focus-name assertion with real typed-input ValuePattern, result filtering and Enter/Escape modal journey; retain fail-closed source-SHA and privacy checks | ARIA active-descendant can transfer accessibility focus to a list item even when DOM focus remains on a named combobox; real keyboard typing plus exact local result and Help navigation are stronger functional evidence without weakening accessibility checks.

2026-11-23 | P02 | Focus/scroll the semantic selected-option heading after M19 command-palette Help deep navigation; let the destination own focus instead of the generic scroll pane | Real Windows UIA proved the option filter and Enter close the modal but its detail was outside the visible viewport. Double requestAnimationFrame settles palette focus recovery; no fake browser captures or relaxed native acceptance tests.

2026-11-23 | P02 | Capture 15 missing M02/M19 actual UI/control candidates in real Windows Tauri, keep 16 option Help-reference candidates separate, and assemble a 29-target offline review bundle | Real option Help documentation is not proof that a corresponding UI control was captured. Source-SHA, native window, keyboard UI Automation, per-frame hash and visual review are independent gates; retaining 29 final statuses PENDING is mandatory until assets are committed and independently approved.

2026-11-23 | P02 | Start P02-T11 protected-merge/issue/security closeout audit but do not promote PR #12 or P03 until all T02/T05/T06/T08/T10 acceptance evidence is actually final | Main SHA and protected ruleset verified; no current P02-scoped open issues, but required signed reviewer and final docs/screenshot/reader/performance/Wiki gates still missing. A green Windows candidate CI alone is not full phase completion.

2026-11-23 | P02 | Expose a focusable, read-only Windows reduced-motion status separate from theme selector and capture its real keyboard focus on Windows | Actual 69-frame native artifact showed theme and reduced motion PNGs identical, a failed control evidence gate; retain strict uniqueness and no fake toggle/persistence.

2026-11-23 | P02 | Export 29 actual source-hashed Tauri screenshot candidates under exact final-path names only inside a review-only ZIP; never auto-commit or mark manifest VERIFIED | GitHub connector supports text commits but not binary source artifact writeback; staged images must retain reviewer/OS/contrast/screen-reader acceptance before protected merge. CI verifies native receipts and rejects Help substitutions, duplicates and false approval.

2026-11-24 | P02 | Publish only missing source-SHA-pinned M02/M19 preview pages to initialized GitHub Wiki through one-shot guarded GitHub Actions and independently clone/read back every byte; remove privileged workflow after success | Actual Wiki HEAD, two page SHA256 values and unchanged Home.md are evidenced by successful run #45284338605. No module release or protected PR merge is inferred.

2026-11-24 | P02 | Distinguish three sequential native Windows *visible HWND* launch samples from actually interactive native IPC readiness; require named `Typed native handshake connected` in the same-PID WebView2 UIAutomation tree before computing the new readiness metric | Passing #45286192929 produced valid OS-visible HWND 250/133/139 ms but cannot establish UX responsiveness, and previous cold local metadata outlier was 42.6 seconds. The stronger source and negative tests are committed, exact-head Windows sample still requires independent CI proof. No artificial P95 or budget approval.

2026-11-24 | P02 | Close only P02-T02 design-token/accessibility-primitive/native-visual *task*, not entire M02 module or T10/T11 | Original 15/15 M02 screenshots passed per-byte SHA256 and Git blob/geometry + independent per-image visual review; 8 option docs/source and focus/contrast/reduced-motion/responsive primitives pass the exact-source T02 Windows acceptance step and same-head governance. Historical scoped nine-frame pending flag cannot override later final screenshot acceptance. Current branch full native job outcome is separately checked, not implied. All-state NVDA/Narrator, budget and main merge remain P02-T10/T11. Board set T02 DONE with stricter fail-closed regression retained, lease null.

2026-11-24 | P02 | Add read-only public hosted Wiki Chrome DOM verification, published-page SHA readback and immutable linked source-file validation; reconcile current canonical guide status | Prior remote Git byte proof does not verify rendered content; use an isolated GitHub-hosted runner, no auth, no Wiki publishing or app network grant, keep exact-head merge and release gates separate.

2026-11-24 | P02 | Add actual installed Microsoft Narrator three-stage speech clipboard probe and read-only cold metadata timing decomposition | Fail closed on unsupported host or absent speech; keep unchanged performance limits and preserve no-user-data policy; do not infer full release/merge certification.

2026-11-24 | P02 | Reconcile existing cross-phase requirements: T12 M26 UI and T13 M23–M25 UI; retain T11 final merge gate | Original PHASE_SPECS and PHASES.json require these; source inventory and board omit them. Issues #16/#17 remain blockers. No new product scope or silent deferral.

2026-11-24 | P02 | Separate pure source/visual regression tests from strict current-phase premerge predicates; repair two mechanical warning sources and move in-scope evidence actions to Node24 | Avoid circular failure after protected closeout; strict live CLI and negative tests retained. New CI required. Existing dead-code contracts remain tracked, not suppressed. P03 must have own exact-head native CI/security baseline at preflight.

2026-11-24 | P02 | T12 reuse shared design tokens and four integrated Change Center tabs, reserve existing six remappable shortcuts, bundle only actual known capability limitations | Alternative full native event/feed query would broaden read-only IPC and need separate P03/P11 service/security proof. No release/status claims; real capture and remaining scope required before issue #16 closure.

2026-11-24 | P02 | Add three navigable M26 service-boundary panels and disabled controls with explicit reasons | Reuse existing WAI-ARIA tab pattern and theme tokens; no synthetic release/event data, persistence, network, privileges or dependencies; native capture and spoken evidence remain required.

2026-11-24 | P02 | Repair native Help mode activation and submit one complete module-select keyboard gesture | Exact-head Windows failed native activation and foreground; keep strict foreground, actual UIA state and image checks, no runtime or privilege changes.

2026-11-24 | P02 | Align inherited glossary static contract with actual keyboard-driven activation | Prior CI stopped before native build on obsolete substring and InvokePattern assertion; retain stronger PID/focus/foreground/panel/visibility gates. No runtime or verifier changes.

2026-11-24 | P02 | Verify disposable Narrator process exit and bound M26 foreground recovery to intentional focus boundaries | Actual M26 foreground interruption after search-empty; preserve strict input/capture validation, no synthetic data or privileges.

2026-11-24 | P02 | Reconcile Narrator script-tail contract with strict process cleanup guard | Both CI jobs stopped before native acceptance on obsolete ending assertion; verify unique fail-closed guard and exit checks, retain all runtime evidence.

2026-11-24 | P02 | Isolate M26 capture before live screen readers and diagnose foreground loss by allowlisted owner/stage | Repeated exact-head loss after search-empty despite successful recovery earlier; cause unconfirmed, no skipped acceptance gates.

2026-11-25 | P02 | Add M26-specific actual NVDA speech gate after successful isolated candidate journey | All seven workflows passed; ten source-bound native frames reviewed; existing general speech evidence does not establish M26. Require actual tab/search/no-match speech and exact binary/run; lower option and Wiki evidence remain pending.

2026-11-25 | P02 | Add dedicated 20-option native evidence, M26-specific Narrator and scoped new Wiki preview | Previously verified ten native frames insufficient for below-fold and option acceptance; keep disabled services nonoperational and separate write-once Wiki publication from read-only browser verification. Existing gates unchanged.

2026-11-25 | P02 | Accept actual hosted M26 Wiki preview and remove temporary writer | Independent public Git clone and Chrome readback passed for all twenty option IDs and exact pinned source; keep only read-only PR verification and original receipts. No release or native approval inferred.

2026-11-25 | P02 | Retry only a foreground-invalidated native journey on a fresh process; repair actual reader navigation/input | Original M26 NVDA three-stage proof passed; observed WebView2 foreground loss, baseline palette value mismatch and Narrator entry failure; keep every actual state, speech and provenance requirement.

2026-11-25 | P02 | Improve real M26 keyboard workflow and responsive UI before further acceptance | Empty-state reset, notice detail focus/return, disabled reason Tab navigation and actual transport guidance solve user-facing gaps; preserve strict source/runtime evidence and phase order.

2026-11-25 | P02 | Preserve actual input accessibility focus and decouple native option verification from screen failure | Both M26 live screen-reader gates passed; option journey previously skipped, legacy default active descendant can report result rather than edit, strict aggregate CI remains fail closed.

2026-11-25 | P02 | Synchronize T04 source assertions with deliberate palette result navigation | Same inherited assertion blocked Windows and Governance before native execution; preserve modal isolation, keyboard movement, default Enter and focus return requirements.

2026-11-25 | P02 | Record all 30 native candidates, reject OPT-13 visible focus gap, request genuine empty reset speech | Native screen/option gates passed but independent review finds focus ring missing and live NVDA empty speech absent; do not treat machine receipt as final visual or speech approval.

2026-11-25 | P02 | Preserve independently reviewed original PNGs from successful capture run rather than restart entire evidence set | 27 scoped targets reviewed, OPT-13 excluded; read-only pinned transport and original blob verification required; exact-head gate remains mandatory.

2026-11-25 | P02 | Commit 27 verified native M26 images to canonical paths | Original a45ab65 run receipts, independent pixel review and seven read-only transfer batches match; leave OPT-13 pending and retain final exact-head acceptance.

2026-11-25 | P02 | Accept corrected OPT-13 visual candidate from exact-source fully passing scoped M26 run | Actual visible focus, disabled control and explanation confirmed on original 998x701 PNG; one-shot original transfer before manifest finalization; legacy Help speech remains separate blocker.

2026-11-25 | P02 | Owner-directed automation pilot on existing GitHub-hosted Windows CI dependency, no paid host or secrets | Read-only model candidate and static check are permitted, PR code cannot receive protected writer authority; no persistent worker claim, keep phase order and #3 open. Also publish final independently reviewed OPT-13 original.

2026-11-25 | P02 | Scope screenshot checkout contract to native prerequisites; deny mixed/unknown model failure routing | First real continuation job passed 4 contracts and selected T12 automatically; unrelated global checkout count failed native/governance; retain exact checkout and no credentials in each native job, no product test relaxation.

2026-11-25 | P02 | Process one known failure group per continuation, preserve deferred failures; verify real legacy Help heading and request current focus speech | Prior native mixed failures prevented inference; no unknown-step permissions, no bypass of speech verifier or native focus. Trusted publisher absent on protected main; no automatic write yet.

2026-11-25 | P02 | Consolidated T13 UI implementation on active PR after owner explicitly prioritized phase completion | Existing P02 scope includes three system centers; preserve six shortcuts, use session-only drafts and actual disabled service controls; native 74-candidate verifier; no premature task DONE or backend mutation.

2026-11-25 | P02 | Preserve Help category correctness under expanded T13 catalog, improve screen search and keyboard return | First TypeScript and six companion gates passed; fixed inherited exact-count assumption without weakening membership checks; no native or release acceptance claim.

2026-11-25 | P02 | Close scoped T12 only after all dedicated exact-source native/speech gates, 28 final images and Wiki proof | Overall Windows still failed T13 and legacy M19; retain T11/T13 merge blockers. Retry M23 real keyboard button once and pass actual Enter through NVDA; verifier unchanged.

2026-11-25 | P02 | Capture T13 option focus after real Tab and Shift+Tab; target the actual Help result in Narrator | The Windows run passed all 74 candidate contracts, but M24-OPT-13 lacked a visible outline and the Narrator receipt captured the edit label for the result. Preserve the original focus, speech and source identity checks.

2026-11-25 | P02 | Preserve 74 reviewed Windows frames from two runs with identical desktop source and exact per-asset provenance | The earlier M24 rollback option image shows visible keyboard focus. Keep the latest candidate finding and the separate full-CI gate.

2026-11-25 | P02 | Record completion in a postmerge closeout | PR #12 merged at `115b6c79fece26b5e4ec58ef8ad2364d7a77d244` and matched the protected remote `main` readback after all phase checks passed.

2026-11-25 | P02 | Add fixed receipt denial codes and trusted-main path trigger for postmerge repair | Issue #22: do not guess root cause or relax any required proof; no P03 until actual receipt; maintenance snapshot unchanged.

2026-11-25 | P02 | Use PR write scope rather than general issue write for main-only receipt and allowlisted HTTP status diagnostics | #22 confirmed POST-stage denial; https://docs.github.com/en/rest/issues/comments#create-an-issue-comment documents PR write; test actual publication before transition.

2026-11-25 | P03 | Activate phase only after independent P02 bot receipt; use separate read-only exact-head Windows baseline workflow | Preserve P02 evidence and gates, avoid changing P01/P02 workflow scope. Real native baseline pending before feature code.

2026-11-25 | P03 | Fix inherited SQLite connection lifetime as a minimal preflight regression repair | #26, full Windows suite failed with 31 leaked-handle cleanup errors. Explicit contextlib.closing preserves transactions and all tests; no P00 behavior expansion. Use pinned actual local Ollama probe and existing Rust SQLite vault; see P03 preflight ADR. T02 code waits for baseline.

2026-11-25 | P03 | Move model cache location into runtime shell environment | Initial workflow failed before job creation; runner.temp is not available in job-level env. No tests or verification gates changed.

2026-11-25 | P03 | Accept T01 scoped baseline and proceed to T02 | Native and local-model artifact readback and exact-head CI verified; inherited warnings recorded. T02 additive v2 migration and real Rust tests first.

2026-11-25 | P03 | Implement additive native v2 normalized chat tables and pre-migration verified SQLite backup under reserved writer lock | Preserve v1 opaque records, no inferred history conversion. Typed postcommit receipts, journal atomicity, parent FK and bounded ordinal paging; no UI or portable encryption in T02. Native tests/boot proof pending.

2026-11-25 | P03 | Accept T02 native storage scope from exact-source Windows CI and independently hash-verified original proof | Nine focused real SQLite tests, 41 total Rust tests, native boot/schema v2 and all regression checks passed. T03 next; 8 new dead-code warnings tracked for wiring and T14. No UI or encrypted backup claim.

2026-11-25 | P03 | Accept T03 local conversation UI and durable restart scope from exact-source Windows proof | Real keyboard create/save, process restart, UI readback and independent SQLite identity passed; original artifact and PNG hashes independently verified and visually reviewed. T04 inference remains separate.

2026-11-25 | P03 | T03 dedicated Chat view with bounded typed native domain commands, no generic SQL/FS/network grant | Official Tauri v2 command/capability docs; preserve old workspace handshake and P02 shell. Main-local scoped capability and explicit allowlist planned; no product authority expanded in preflight. Real UI create/restart/readback required before DONE.

2026-11-25 | P03 | Split T03 into native thread query then bounded IPC/UI slices | Existing P01/P02 exact privilege allowlists require explicit scoped migration and new negative tests; preserve historical checks. Add metadata-only queries and same-thread reconciliation lookup first; no authority expansion yet.

2026-11-25 | P03 | Implement scoped chat_request domain command and separate local capability | Keep workspace handshake unchanged, no arbitrary host authority; stable mutation ID replay, bounded reads, typed errors. Retain historical P02 strict gate and test current exact grant. Native and UI proof pending.

2026-11-25 | P03 | Wire dedicated save-only Chat UI to native typed domain service | Preserve local-only capability and existing shortcuts; strict correlated response validation, stable ID retry and session drafts. Fix missed P02 exact capability assertion by validating both explicitly scoped local grants; no arbitrary privilege or weakened deny tests. Native interaction proof pending.

2026-11-25 | P03 | Add real Windows UIA create/save/restart proof after existing empty-vault assertions | Reuse disposable runner and current read-only workflow; compare DB identities and journal before/after restart, no test injection or data reset. Screenshots candidate only until independent review. Fresh exact-head CI required.

2026-11-25 | P03 | Repair native keyboard probe without weakening acceptance | Run 45629508632 passed 47 real Rust tests and build, failed exact keyboard readback; root cause unknown. Two bounded real keyboard attempts, UIA focus then actual pointer focus, exact ValuePattern comparison retained; preserve separate failure artifacts. Issue #27 open.

2026-11-25 | P03 | Repair native ARIA pressed button activation and responsive conversation layout | Run 45632415583 independently confirmed real keyboard input and saved data; reopen list visible, provider InvokePattern unsupported for pressed button. Use actual supported Invoke/Toggle pattern or bounded physical click, retain postrestart exact UI+database proof. Review native screenshot showed unnecessary stacked pane at 1024 width; use content container breakpoint. No completion claim.

2026-11-25 | P03 | Apply reviewed F01/F02/F04/F05 repair candidate plus F03 acknowledgement/status consistency; preserve active task status | Failed exact-head native assertion, bounded standard I/O, shared conservative draft-aware context and strict validation; interruptible transport and exact-head acceptance remain pending.

2026-11-25 | P03 | Interruptible async loopback transport using pinned reqwest and a latched wakeable cancellation state | Prior Windows baseline passed; preserve byte limits and terminal persistence, no new dependency/schema/capability. Candidate tests require fresh exact-head native CI and real model UI proof.

2026-11-25 | P03 | Expand cancellation acceptance without depending on installed runtime | Prior exact-head Windows baseline 45660752755 passed 57 native and 9 focused vault tests. Add bounded deterministic loopback stall/retry and terminal race fixtures; preserve real Ollama and native UI acceptance gates.

2026-11-25 | P03 | Gate startup teardown on committed native audit ledger schema | Run 45664948466 passed 59 native / 9 focused vault tests but audit DB absent. Issue #28: probable early-stop race, not proven. Read-only readiness predicate, unchanged deadline and independent ledger validation; no app or data schema changes.

2026-11-25 | P03 | Verify actual product adapter against pinned CPU Ollama in existing same-repository read-only preflight | Windows startup regression repaired and verified by 45667552634; issue #28 closed. Explicit ignored integration test only, synthetic disposable vault, no new app capability, no runtime installation in product, no output text in evidence. Existing smoke and new adapter proof remain separately labeled. Linux native build prerequisites added; exact-head CI, native model UI and actual token calibration pending.

2026-11-25 | P03 | Accept T04 minimal fixed-loopback product adapter, calibrate T07 separately | Exact c1a79a1 Linux real gateway and Windows baseline passed, original product evidence independently inspected. No universal tokenizer claim; native-only prompt usage metric with existing IPC shape and pinned-model multilingual test. T05–T07 retain acceptance gates.

2026-11-25 | P03 | Bind model controls to installed inventory, thread, settings revision and current draft | Verified a2dbceb calibration and baseline; avoid stale UI estimate or cross-thread retry and late stream state updates. Existing IPC/storage/dependencies retained; exact-head native/UI acceptance pending.

2026-11-25 | P03 | Add real Windows model interaction after unchanged T03 baseline | Official runtime asset digest pinned, isolated CI-only two model inventory, keyboard selection and independent SQLite readback; no product capability or schema change. Actual proof and visual review pending.

2026-11-25 | P03 | Require exact native dropdown acknowledgement before independent database readback | Windows run 45682806417 failed first model selection; original screenshot shows placeholder. Prefer actual provider selection, fallback to real physical click and bounded keyboard attempts; no direct state/DB injection or relaxed assertions. Issue #29 remains open.

2026-11-26 | P03 | Align existing T05–T16 dependency order; share portable managed-name validation between attachment and restore candidates | Exact-head model UI candidate passed but independent proof pending; source-only contracts are not storage or encryption. No dependency, scope or gate expansion. See docs/evidence/P03_PLAN_ALIGNMENT_AUDIT_20261126.md.

2026-11-26 | P03 | Repair confirmed CI regressions without weakening prior-phase checks | Issue #30: keep exact Wiki screen/option anchor inventory, explicitly decode UTF-8 Rust test sources. New-head verification required.

2026-11-26 | P03 | Stage managed content under the existing vault by hash before adding DB links | Reuse existing SHA-256, create-new staging and no-replace publication; preserve source/occupied data; explicit native-only and durability/race limitations. Prior exact CI green; no new gate waived.

2026-11-26 | P03 | Add V3 attachment schema with separate migration receipt and atomic message links | Existing V2 source snapshot mandatory before upgrade; preserve V2 history and all previous data assertions. No new dependencies or renderer authority. Fresh CI pending.

2026-11-26 | P03 | Read SQLite attachment lengths as signed INTEGER and validate before conversion | Reject negative, oversized and aggregate-overflow metadata; maintain existing native acceptance gates. Issue #31.

2026-11-26 | P03 | Expose scoped attachment metadata through existing bounded history only | Strict decoder, text-only replay conflict; no arbitrary file authority or model ingestion. #31 verified; new exact CI pending.
