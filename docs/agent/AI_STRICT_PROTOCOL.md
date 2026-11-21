# AI Strict Protocol (binding for every AI: Claude, ChatGPT/Codex, Cursor, Gemini, Copilot, others)

This file wins over any tool default or chat request that conflicts with the plan. Only the repository owner can change it, via a PR that edits this file.

## 1. Source of truth (precedence, highest first)

1. `docs/state/PHASE.json`: the current phase. Work on nothing else.
2. `AGENTS.md` + this file.
3. `docs/MASTER_PLAN_V3_2.md`: the only operational plan. `MASTER_PLAN.md` and `MASTER_PLAN_V3.md` are history; read them only when V3_2 points to them.
4. `docs/PHASE_SPECS.md` row for the current phase, then `docs/modules/Mxx.md` for the modules in that phase.
5. `docs/operations/*`, `docs/quality/*`: read only those the task touches (see §3).

If two sources conflict, the higher one wins. Record the conflict in `docs/state/DECISIONS.md` and continue; never stop to ask.

## 2. Hard rules (no drift)

- **Phase lock:** edit only paths that belong to the current phase's modules plus `docs/state/*`, docs, help, wiki and tests for them. Next phase starts only after `PHASE.json.phase_status == MERGED_VERIFIED` with `last_verified_remote_sha` set.
- **No new scope:** no feature, module, dependency, phase or redesign outside the plan. An idea goes to `docs/state/ISSUES.md` as `PROPOSAL`, not into code.
- **No invented results:** never claim a test, screenshot, PR, issue, merge or release that the tool output did not show.
- **One worker at a time:** before editing, set `PHASE.json.lease_holder` to `<agent>@<UTC time>` and commit it. If another lease is under 24h old, do read-only work only. Clear it at handoff.
- **Finish rule:** a slice is done only when `python scripts/check_governance.py`, the `verify_*` scripts and `python -m unittest discover -s tests` pass and `docs/state/HANDOFF.md` is updated.
- **Data safety:** never delete the last copy of user data; never weaken tests/CI to go green.

- **Task table in every PR (all phases):** each phase has `docs/state/pr-tasks/<PHASE>.json` (stable ID, title, status DONE/IN_PROGRESS/TODO/BLOCKED, evidence/blocker link). Every PR description carries the generated table between the `ZYNOA_PR_TASK_BOARD` markers of `.github/pull_request_template.md`, exactly like P00. New in-scope work is appended to the same manifest before coding. CI (`python -m scripts.check_pr_task_board`) must pass; a PR without a synced table is not complete.

## 3. Decision authority (AI decides, does not wait)

The AI makes the call itself when the plan already answers it or when the choice is reversible and inside the phase. Apply in order:
1. What the plan says. 2. What existing code/docs already do. 3. Smallest reversible option. 4. Log it in `DECISIONS.md` as one line: `date | phase | decision | reason`.

**The owner has no own machine, host or credentials.** Everything is done by AI. For a host, worker, sandbox or model runtime use GitHub-hosted Actions runners with the built-in `GITHUB_TOKEN` (least-privilege `permissions:`) and public free tools only. Never mark a task BLOCKED for "needs owner hardware/credentials"; redesign it onto those runners and log the decision.

Stop and write `BLOCKED: <reason>` in `HANDOFF.md` (then do other safe work) only for: paid services, access GitHub itself refuses, a destructive action on user data, a legal/licence question, or a change to this file or the phase order.

## 4. Token budget (minimum tokens, best output)

Applies to every session and every user query.
- **Read the minimum:** start with `PHASE.json` + `HANDOFF.md` (both small). Open a large file only for the section you need (grep a heading, then read that range). Never re-read a file already in context.
- **No duplicate rules:** entry files (`CLAUDE.md`, `GEMINI.md`, `.cursor/rules`, `.github/copilot-instructions.md`) only point here. Add rules here or in `AGENTS.md`, never copy them.
- **Answer the question asked:** direct answer first, no restating the question, no preamble, no unrequested options. Code/diffs only for changed lines.
- **Smallest complete change:** reuse existing tools/scripts; no new abstraction, file or dependency if an existing one works.
- **Batch:** run independent commands/reads together; run the full check suite once at the end of the slice, not after each edit.
- **Quality is not cut:** tests, validation, security and data safety are never skipped to save tokens.

## 5. Slice output (short form)

`phase | files_changed | tests (command → result) | decisions | blockers | next_step`. Add the long v3.2 fields from `AGENTS.md` only in the PR description.
