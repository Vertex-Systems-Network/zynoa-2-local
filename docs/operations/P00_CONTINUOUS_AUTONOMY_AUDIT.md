# P00 Continuous-Autonomy Blocker Audit — 2026-11-18

**Repository:** [Vertex-Systems-Network/zynoa-2-local](https://github.com/Vertex-Systems-Network/zynoa-2-local)
**Scope:** Existing P00, branch `phase/00-governance`, draft [PR #1](https://github.com/Vertex-Systems-Network/zynoa-2-local/pull/1). **This audit is diagnostic and does not deploy or authorize a privileged agent.** All prior decisions, code and one-branch/one-PR sequencing are preserved.

## Executive finding

The user's requested "non-stop, phase-by-phase AI development" is **not running** because there is no continuously deployed, model-backed autonomous developer. The existing ChatGPT session implements bounded increments only while the user has requested work. The repository contains an observer, durable READ-ONLY queue, dependency DAG, scope validator and worktree *planner*, but **not an always-on AI coding process**.

The policy also mixes P00 bootstrap readiness with future product requirements, and conflates pre-merge issues with post-merge verification. Repeated manual "Continue" prompts are therefore an expected result of the present execution architecture, not evidence the CI tests are malfunctioning.

## Evidence verified from actual GitHub

| Evidence | Observed fact | Authority |
|---|---|---|
| `docs/state/PHASE.json` | `phase=P00`, `IN_PROGRESS`, `worker_running=false`, PR=1 | Repo code state, not an independent heartbeat |
| [P00 PR #1](https://github.com/Vertex-Systems-Network/zynoa-2-local/pull/1) | OPEN, DRAFT, not merged | GitHub remote |
| `main` branch | SHA `8dcb546828a8fdeef40dfaa250ac8f6b8639025d`, `protected=false`; 0 repository rulesets | GitHub remote |
| [P00 GitHub Actions 44224825917](https://github.com/Vertex-Systems-Network/zynoa-2-local/actions/runs/44224825917) | SUCCESS on SHA `6b600a358f50cc960008ec018c0c9edd2cb1f9b1`; governance/unit/Windows tests only | GitHub remote |
| `.github/workflows/governance.yml` | `on: pull_request` and `on: push` to main; tests, `phase_worker --once`, `phase_merge_guard` dry-run, read-only queue `--smoke` | Versioned workflow |
| `tools/phase_worker.py` | Docstring states read-only P00 observer, no coding model or GitHub mutation; no deployed service evidence | Source code |
| `tools/dev_job_runner.py` | Exactly three hard-coded read-only checks; never invokes coding agent or write tool | Source code |
| `tools/worktree_plan.py` | Only constructs argv; integration creates worktree against disposable fixture | Source/tests |
| `tools/phase_merge_guard.py` | Merge default disabled; requires non-draft, protected main, pinned CI checks, no blockers | Source code |
| `.github/workflows/developer-incident.yml` | `workflow_run` reporter lives only on PR branch; not active as trusted main code until merge | Versioned workflow |
| [Infrastructure Issue #3](https://github.com/Vertex-Systems-Network/zynoa-2-local/issues/3) | OPEN; host, credentials, repo rules, write integrations remain unresolved | GitHub remote |
| M22 module | P00-only controller prototype while full GUI and screenshot obligations remain pending | `docs/modules/M22.md` |

**Passing governance tests are genuine, but they do not prove autonomous model execution or uninterrupted development.**

## Root causes (ranked)

### RC-01 — No autonomous execution process (P0, primary)

ChatGPT conversation is not a persistent deployed operating-system service. Existing `phase_worker.py` can poll remote facts only **if externally installed and started**, but is not installed, and lacks the model-backed code-writing/repair pipeline. Nothing currently requests the next permitted coding task without another human-initiated conversation/tool session.

**Necessary fix:** a separately deployed, supervised host-side developer worker using a local/free Ollama model or other authorized model runtime; durable queue, tool gateway, GitHub identity, restart/heartbeat and no-bypass policy. Verify host evidence from actual process/supervisor, not from a JSON flag.

### RC-02 — GitHub Actions is a test pipeline, not a self-scheduling developer (P0)

Current workflow triggers only after PR updates or `main` pushes. `phase_worker --once` exits after one observation. `dev_job_runner --smoke` executes three static checks and exits. There is no `schedule`, `repository_dispatch`, persistent runner or active agent-model invocation that would generate subsequent code changes. GitHub-hosted jobs have finite execution limits, and scheduled runs can be delayed and only use default-branch workflows; do not describe them as guaranteed 24/7 agents.

**Necessary fix:** separate persistent developer executor. GitHub Actions stays an independent evaluator; optionally use a watchdog/scheduled *wake-up* workflow from trusted main after deployment, not as a fake continuously running coding model.

### RC-03 — Hard GitHub readiness blockers (P0)

Main protection is absent and no effective rules are installed, while merge gate explicitly requires a protected main with trusted pinned required check. PR #1 is DRAFT. The merge executor is disabled by default and no trusted write identity/host runs it. `allow_auto_merge=true` is a repository preference, **not an enabled auto-merge instruction for the current draft PR**.

**Necessary fix:** authorized GitHub admin provisions actual ruleset from the existing `deploy/github/main-ruleset.json`, verifies applied rules via API and configures least-privilege GitHub App. Complete acceptance evidence, convert PR out of draft when ready, then permit guarded merge and verify remote SHA.

### RC-04 — Circular pre-merge/post-merge issue lifecycle (P1)

The GitHub reader treats OPEN Issue #3 as a critical blocking issue. The merge guard forbids any open critical issue. The issue's narrative also says do not close it until P00 merge is verified, which would require a merge while issue is open. **This is a dependency cycle even after the infrastructure is repaired.**

**Necessary fix:** classify blocker checks by lifecycle. A pre-merge blocker may close only after *independently verified* pre-merge deployment/security facts, never as a workaround. Separately track the actual post-merge SHA verification and next-phase handoff in PHASE.json / audit record (or a distinct non-premerge-blocking tracker). Do not weaken the protected-branch/CI gate or silently ignore open true blockers.

### RC-05 — P00 scope creep and acceptance ambiguity (P1)

`docs/PHASE_SPECS.md` says P00 exit is constitution, PR policy, source bank, controller contract and test harness; P01 builds desktop core, P02 builds shared GUI, P04 builds the *product's* coding module, and P10 builds advanced *product* autonomy. Later P00 acceptance addenda require production OS execution and all downstream M22 UI screenshots, without clearly distinguishing the **external developer bootstrap** from shipped product features.

**Necessary fix:** define two distinct outcomes:
1. P00 **developer-autonomy bootstrap**: actual supervised host, safe pre-authorized development task executor, GitHub read/write integration with independent gates, checked retries/restarts and phase-truth chain. This must work if the user expects no repeat prompts from P01 onward.
2. Future **product feature maturity**: polished in-app M22 dashboard/screenshots (when UI platform exists), Chat (P03), Coding (P04), advanced in-app agents (P10), Designer interop (P08I).

P00 shall not be called complete without its declared bootstrap/security evidence. P00 shall also not be held hostage by *future module features/screenshots that cannot exist before the shared UI platform*. P02 captures graphical screenshots as features become executable. No screenshot may be fabricated.

### RC-06 — No full closed-loop planner/test/repair/docs/merge/next-phase handoff (P1)

Existing queue/DAG persist **read-only checks**, not independent model tasks. There is no trusted coding-agent service that turns a failed CI result into a scoped patch/test/regression loop, updates the same PR, reconciles blocked issues and moves to the next phase. The `GuardedMerger` can execute only with separately configured authority and does not itself create P01; the observer likewise has no phase transition write action.

**Necessary fix:** explicit immutable development-task records and a bounded state machine on the deployed host; independent evaluator and remote write receipts; after guarded merge, require server-verified commit and new branch/primary PR creation in the correct order.

## Required architecture to satisfy user intent

```text
Dedicated 24/7 developer host (actual OS service + watchdog + secure identity)
  -> GitHub readback: actual phase/PR/checks/issues
  -> Persistent SQLite queue + DAG + task lease
  -> Local authorized model router (Ollama etc.) and planner
  -> Restricted OS sandbox / capability broker / isolated Git worktree
  -> Code changes + test runner + bounded error repair
  -> Documentation, Help/Wiki source, changelog record, incident dedup
  -> Commit/push to EXISTING phase branch/PR only
  -> GitHub independent CI + corrections until eligible
  -> Guarded non-bypass merge + independent remote merge SHA verification
  -> Durable PHASE/STATUS/HANDOFF transition
  -> Exactly ONE next-phase branch/primary PR
  -> Repeat while active; on true blocker, continue independent safe tasks
```

No "run forever regardless of conditions": permanent failure must enter `BLOCKED_WAIT_EVENT`, open a sanitized issue/notify, and retry only after a relevant event/authorized remediation. Never bypass security or invent green CI.

## Correct acceptance/lifecycle separation (do not silently waive gates)

| Lifecycle | Verifiable contract | Current result |
|---|---|---|
| P00 pre-development | Constitution, master plan, research, module contracts, issue inventory | Partial, largely documented |
| P00 bootstrap readiness | Actually installed supervised developer worker; heartbeat, usable local model, sandboxed tool execution; durable queue and restart/backup proof | **BLOCKED** |
| P00 GitHub pre-merge | Protected main with pinned required CI; scoped GitHub App; CI green at exact HEAD; pre-merge blockers resolved with evidence; PR not draft | **BLOCKED** |
| P00 merge | Policy-compliant actual GitHub PR merge | **NOT DONE** |
| P00 post-merge | Verify resulting main merge SHA and commit/check; record status and create P01 branch/PR only after that proof | **NOT DONE** |
| P02 UI | Running UI, real screenshot-backed Help/Wiki for M22 graphical options | **FUTURE** |
| P04/P10 product | Coding editor and advanced in-app autonomy as products | **FUTURE** |

## Immediate priorities (not generic documentation polish)

1. **Provision the actual persistent execution host** (Windows service or Linux systemd; dedicated user and credentials vault). Without that, every chat remains a bounded manual kick-off.
2. Integrate real model-backed scoped developer tasks with sandboxed tooling, CI troubleshooting, test fix and checkpoint recovery; prove a fully unattended *single safe test-repo task*.
3. Provision and verify the GitHub protected-main ruleset and independent narrowly scoped write identity.
4. Fix Issue #3 lifecycle cycle, add premerge/postmerge event gates and test them without ever merging before true eligibility.
5. Prove P00 on the current branch/PR, merge via validated rules, verify SHA and only then create P01. Deploy the host BEFORE claiming automatic P01–P12 progression.

**Cannot be solved by:** more aggressive `AGENTS.md` prompts, repeated "continue" messages, a SQLite table alone, an Actions test success, auto-merge preference alone, or an uninstalled service template.

## Technical references checked 2026-11-18

- GitHub Actions triggering and default-branch schedule constraints: https://docs.github.com/en/actions/reference/workflows-and-actions/events-that-trigger-workflows
- GitHub Actions hosted job limits: https://docs.github.com/en/actions/reference/limits
- GitHub auto-merge prerequisites: https://docs.github.com/en/repositories/configuring-branches-and-merges-in-your-repository/configuring-pull-request-merges/managing-auto-merge-for-pull-requests-in-your-repository
- GitHub drafts cannot merge: https://docs.github.com/en/pull-requests/how-tos/merge-and-close-pull-requests/merging-a-pull-request
- Existing project [Autonomous Loop](AUTONOMOUS_LOOP.md), [Worker runbook](P00_WORKER_RUNBOOK.md), [Release gates](../quality/RELEASE_GATES.md), [Phase specs](../PHASE_SPECS.md).

**Audit is evidence-only:** actual repo protection is still off, controller host not deployed, PR #1 draft, no merge and no next phase. All original security requirements stay in force.
