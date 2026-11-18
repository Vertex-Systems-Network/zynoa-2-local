# P00 — Required GitHub Protected Main Ruleset Provisioning

**Status: DECLARATIVE TEMPLATE PREPARED; NOT INSTALLED ON GITHUB.** The repository's actual `main` remains unprotected at last authenticated audit. Related [Issue #3](https://github.com/Vertex-Systems-Network/zynoa-2-local/issues/3). The ruleset must be provisioned through a repository-admin identity and independently verified before guarded auto-merge may run.

## Desired policy and evidence

Manifest: [deploy/github/main-ruleset.json](../../deploy/github/main-ruleset.json).

- Exactly targets `refs/heads/main` and uses `enforcement=active`.
- Requires a pull request (no direct pushes).
- Prevents branch deletion and non-fast-forward pushes.
- Requires `governance-lint` from GitHub Actions App ID **15368**, pinned to the CI provider (verified via real check-run readback at P00 PR HEAD SHA `50c478659e3c34050635615028c4b19af407c46e` on 2026-11-18).
- Requires strict status checks on current main.
- No bypass actors declared in this template.
- Sets required approving reviews to **0**, consistent with user's authorized no-repetitive-confirmation workflow; required CI and security policies still apply and GitHub-level required reviews (if later set) must never be bypassed.
- Review discussion resolution is required; unattended PRs with unresolved comments remain blocked.

**Security warning:** With zero human approvals, required CI is a critical trust boundary. Do not grant AI models access to modify GitHub protection, CI expected sources, or merge policy without independent permission. Governance CI code itself can change in PRs; future strengthening may require separate security/owner-controlled workflow source and policy review.

## Provisioning options

1. **Authorized repository admin UI:** Repository → Settings → Rules → Rulesets → New branch ruleset. Select active, target `main`, require PR, disallow deletion and force pushes, require `governance-lint` status from GitHub Actions, enable strict checks. Record actual ruleset ID and effective branch rules after saving.
2. **GitHub REST Admin API (future delegated operator):** `POST /repos/Vertex-Systems-Network/zynoa-2-local/rulesets` with the JSON manifest, using a separate short-lived token/GitHub App granted repository **Administration: write**. Do not store token in this repository, Actions PR checkout, desktop app or issue. No provisioning call is made by this documentation, CI, or the current assistant connector.
3. Verify `GET /repos/Vertex-Systems-Network/zynoa-2-local/rules/branches/main` returns the active `pull_request` and pinned `required_status_checks` rules, and `GET /branches/main` returns `protected: true`. Recheck the expected check app ID on live latest PR HEAD and ensure required GitHub CI names match.
4. Only after real GitHub readback and other P00 acceptance gates (host/worker, tests, no critical blocker, non-draft verified PR) may the separate guarded merge controller evaluate remote merge eligibility. Main branch protection is necessary but alone insufficient.

## Observable current status

- `main` protected: **false** in GitHub API at last audited checkpoint.
- Repository auto-merge setting: **true**, which does not imply protected branch or allow a safe merge.
- P00 PR #1: **open draft**. Do not force merge or create P01.
- Current connector exposes repository read + content/PR/Issue actions but not ruleset administrative writes. Do not claim the manifest was installed.
- CI static tests validate manifest schema/invariants but do not prove GitHub configuration.

## Official references

- [GitHub REST repository rulesets](https://docs.github.com/en/rest/repos/rules)
- [Rulesets management](https://docs.github.com/en/repositories/configuring-branches-and-merges-in-your-repository/managing-rulesets)
- [Branch rules applied REST endpoint](https://docs.github.com/en/rest/repos/rules#get-rules-for-a-branch)
- [Ruleset rule options](https://docs.github.com/en/repositories/configuring-branches-and-merges-in-your-repository/managing-rulesets/available-rules-for-rulesets)

**P00 exit gate:** Readback of actual protected main, actual trusted check provider, verified CI, functioning supervised worker and authenticated write-controller tests. Documentation does not waive these requirements.


## P00 trusted policy readback hardening — 2026-11-19 (pre-merge source)

The read-only GitHub phase observer now compares the effective `main` required-status-check integration to the independently approved **GitHub Actions App ID 15368**, not merely to the check-run's self-consistent provider ID. It also requires the applied rule to specify `strict_required_status_checks_policy=true` and the pull-request rule to specify `required_review_thread_resolution=true`. A missing, substituted, non-strict, or incomplete rule is **NOT merge-ready**, even if an unrelated CI run reports success. Tests use the real approved provider ID and cover an internally matching but unapproved app, disabled strict mode, and missing review-thread resolution.

The actual remote `main` still has `protected=false` and **zero installed rulesets** at this checkpoint. This is fail-closed source verification, **not branch-protection provisioning** and not proof that GitHub ruleset bypass actors or host privileges have been independently audited. A privileged, operator-owned ruleset deployment and live GitHub readback remain required under Issue #3. P00 PR #1 remains draft; no next phase or release is authorized.

Primary reference: https://docs.github.com/en/rest/repos/rules?apiVersion=2022-11-28


## Required Actions workflow-run and job provenance (P00 in progress — 2026-11-19)

GitHub Actions App ID `15368` identifies the application, **not the exact workflow**. A second workflow could produce a same-named check, so the P00 gateway must correlate required `governance-lint` to GitHub's check-run `details_url`, authenticated `GET /actions/runs/{run_id}` and `GET /actions/jobs/{job_id}`. Require consistent run/job IDs, suite ID, completed success, exact PR HEAD SHA, P00 branch, repo/head repo, PR #1 association, workflow name and `.github/workflows/governance.yml` path. Missing `actions:read`, stale or incomplete API evidence fails closed. This verifies **source provenance**, not that a PR-editable workflow's commands have been security reviewed. Actual protected-main ruleset remains absent; no host deployment/merge is implied.

Official references: https://docs.github.com/en/rest/actions/workflow-runs#get-a-workflow-run and https://docs.github.com/en/rest/actions/workflow-jobs#get-a-job-for-a-workflow-run.
