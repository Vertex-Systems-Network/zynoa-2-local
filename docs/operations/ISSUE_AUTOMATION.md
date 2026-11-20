# Autonomous Error → GitHub Issue Architecture

## Requirements

A. **Development agent:** all actionable build failures, unexpected warnings, test breaks, reproducible exceptions and regressions route automatically to a tracked incident. Duplicate signatures update the same GitHub issue. Silent ignored warnings are disallowed.

B. **Installed end-user client:** locally captures minimal crash envelopes. User-facing Privacy/Diagnostics setting controls any remote reporting; initial consent can establish persistent opt-in, with no repeated confirmations. The desktop app cannot contain repository write credentials. For opt-in mode, reports go to authenticated ingestion relay; the relay uses a short-lived GitHub App installation token and repo-scoped Issues permission. Raw user source/prompt/logs do not go to GitHub.

C. **Security-sensitive:** never publish exploit details, credential strings or sensitive content in public tickets. Private security report/maintainer-only queue with separate policy. Always keep local report available when remote route disallowed.

## Incident state machine

`CAPTURED → SANITIZED → FINGERPRINTED → CLASSIFIED → LOCAL_SPOOL → (REMOTE_ALLOWED?) → DEDUP_LOOKUP → CREATE/UPDATE → TRACKED → FIX_PR_LINKED → REGRESSION_VERIFIED → RELEASE_VERIFIED → RESOLVED`

If remote disabled: `LOCAL_SPOOL → LOCAL_ONLY`; if offline: `RETRY_WAIT` with backoff; if privacy redaction fails: `QUARANTINE_NO_UPLOAD`; if rate-limited: `RETRY_WAIT`; if P0 security: `PRIVATE_SECURITY_ROUTE`.

## Envelope minimum

```json
{
  "schema_version": 1,
  "fingerprint": "sha256(module|error_code|normalized_stack|major_minor_version)",
  "source": "developer-ci|desktop-client",
  "app_version": "<version>",
  "platform": "Windows|macOS|Linux",
  "module": "Mxx",
  "error_code": "ERR_STABLE_CODE",
  "severity": "P0|P1|P2|P3",
  "first_seen": "UTC ISO8601",
  "last_seen": "UTC ISO8601",
  "occurrence_count": 1,
  "safe_reproduction": "optional manually verified safe steps",
  "privacy_audit": "redaction_policy_version"
}
```

**Never include:** raw model chats, API keys, credentials, local absolute paths, IP addresses, emails, documents, source code, full stacks with content, browser history, personal identifiers or filenames from private projects. Avoid putting identifiable stable hardware IDs into fingerprints.

## Fingerprinting / dedupe

Normalize stack to module, exception type, symbol/frame *names* and app version band; replace line numbers/volatile addresses. Hash stable fields. Maintain local `incidents` SQLite table with fingerprint, seen count, issue URL, first/last seen, severity and retry state. Relay checks GitHub existing issue by fingerprint label/hidden marker and searches known open/closed records; update existing ticket with summary/version delta or create one. Secondary GitHub API limits require throttling; do not produce one issue per event.

## Decision policy

- P0 security/credential leak → private security queue, avoid public issue.
- P1 deterministic app crash → developer issue immediately in authorized CI; user incident only via opt-in relay and rate controls.
- P2 reproducible task malfunction → issue after local repro or multiple signals; attach sanitized test evidence.
- P3 warnings → incident group and prioritized issue when persistent/new in CI; network timeouts may be grouped into provider outage without duplicate issue storms.
- Known fixed version → link change, do not close until verified actual deployment/upgrade tests.

## GitHub API security

Use a GitHub App installation token, required scoped `Issues:write` permission on specific repo; CI can use a suitable `GITHUB_TOKEN` and restricted workflow permissions. Do not write personal access tokens into app/source. User client sends reports to a relay with abuse prevention, not direct GitHub; local-only mode is viable. Request quotas, retry backoff, authentication, TLS, and end-user deletions/retention obeyed.

Official: https://docs.github.com/en/rest/issues/issues — issues must be enabled and write permission granted. API creates notifications and has secondary rate limits.

## Developer workflow after issue

Issue template includes module, phase, stable fingerprint, affected versions, severity, sanitized stack class, deterministic steps, expected/actual, test command, baseline, screenshot only from synthetic fixtures, linked PR and acceptance evidence. Fix on active phase branch or a policy-authorized separate hotfix; leave open until regression suite passes and release target verified. Documentation/help error code link should be updated.

## Starter demo

`python tools/incident_router.py --event tests/fixtures/incident.json --db <local-db> --dry-run` processes locally, redacts and stores fingerprint without publishing. `--publish` requires explicit configured repository/token policy; production relay, telemetry UI and GitHub remote integration remain future implementation tasks.

### Release, backup and relocation issues

Classify update failures by `UPD-*`, backup corruption and data loss by `DAT-*`/`BKP-*`, runtime relocation failures by `STO-*`. Deduplicate by version + error code + safe stack fingerprint. Bugs with potential data loss are high priority and block stable promotion until fixed/isolated. Do not attach original chat messages, raw backup contents, file paths with usernames, encryption keys or private code to public GitHub issues. CI-side failures can open/update issues with sanitized build logs; end-user remote reporting follows opt-in policy.

## v3.2 incident-to-change-event route

Upon issue report: write privacy-scoped event with stable fingerprint and GitHub URL if report succeeds; don't imply fix. Upon approved enhancement: record planned scope and evidence. Upon fix PR: link the change ID, tests, documentation and screenshots. Upon verified release: mark as shipped in release-specific feed and only then show Fixed to installed users. Keep issue state, implementation state and release state independent. See [M26](CHANGE_INTELLIGENCE_CHANGELOG.md).


## P00 Developer CI bridge status — 2026-11-18

The repo contains `tools/github_issue_bridge.py` with developer-ci-only allowlisting, `tools/incident_router.py` sanitization, P0 public-report block, remote fingerprint dedup and 4-page fail-closed pagination. Direct issue publishing is OFF without separate `ZYNOA_ISSUE_TOKEN` and explicit publish authorization. A trusted-default-branch `.github/workflows/developer-incident.yml` triggers for failed governance runs; it **does not activate until merged to main**, and does not checkout untrusted PR code. No installed client/user incident relay has been deployed, and no actual automatic issue generation has yet been proven on a failing workflow. See [P00 runbook](P00_WORKER_RUNBOOK.md) and [Issue #3](https://github.com/Vertex-Systems-Network/zynoa-2-local/issues/3).


## P00 CI run readback and bounded dedup update (2026-11-20)

The existing trusted-default-branch `developer-incident.yml` reporter now passes the failed `workflow_run` ID and full HEAD SHA to `DeveloperIssueBridge`. The bridge independently GETs the GitHub Actions run and requires completed failure, exact `Governance v3.2` workflow, same head repository and matching ID/SHA before public Issues operations. It uses a restricted `issues:write` token and allows only canonical create/dedup/patch for a matching `github-actions[bot]` Issue title/fingerprint, rebuilding a source-free body with up to five verified run links, no old text or job logs. The same event is idempotent; ambiguous results deny. Read [P00 operator delivery runbook](P00_VERIFIED_CI_ISSUE_DELIVERY.md) and [ADR-0023](../adr/0023-ci-run-verified-sanitized-issue-delivery.md). **Not live on current draft branch:** GitHub `workflow_run` listener must exist on default branch, so a genuine postmerge failed-run → authenticated issue readback is required to finish P00-T22. CI mocks and optional manual connector write proof are distinct.
