# Illustrated Documentation + Help + Wiki System

## Document architecture

Canonical content under `docs/help/articles/Mxx.md` and `docs/wiki/pages/Mxx.md`, checked into same phase branch. End-user app consumes versioned Help bundle generated from canonical markdown, indexed locally by keyword + FTS, and supports context `help://Mxx/option-id`. Online Wiki mirrors relevant pages from `<repo>.wiki.git`. Never point to guessed remote links until repository owner/name and enabled Wiki are verified.

## Required per-option article template

- Stable option ID and screen ID; exact label, purpose, ideal user and behavior.
- Screenshot of **running app** for active state, focus/hover when meaningful and error state, with annotation and descriptive alt text.
- Control type, allowed values, default, saved scope, prerequisites, dependency warnings and disabled state.
- Step-by-step working example plus alternative/undo and advanced use.
- Offline/slow hardware behavior, permissions, privacy, storage cost and limitations.
- Common errors and stable error codes with self-service recovery link and diagnostics issue details.
- Keyboard shortcut, accessibility expectations, related options and exact tested app version.

## User Help interface

Help home → search → category → article → contextual screenshot/diagram → task steps → troubleshooting → 'show in app' → report problem. App opens local embedded docs without browser/network; external Wiki is opt-in link. `F1` invokes current screen help, and `?` on settings opens precise option topic. First launch offers tour; experts can disable onboarding.

## Screenshot capture and review

A running desktop E2E harness sets deterministic theme, density, viewport, locale, pixel scale, seeded fixture data and phase build version; captures screenshot from actual feature and state. Each screenshot has ID, source commit, SHA256, test name, OS/DPI, human-readable caption, alt text, sensitive-data check and 'verified' state. Baseline review rejects clipping, empty/placeholder controls, low contrast, unreadable metadata, wrong labels and competitor imagery. Generated diagrams are tagged `conceptual` and don't satisfy screenshot requirements.

## Wiki publishing

GitHub Wiki is separate Git repo `https://github.com/OWNER/REPO.wiki.git`, availability depends on repo settings/plan. A guarded job copies Wiki sources and image assets, rewrites verified links, validates anchors, computes diff, commits/pushes with least privilege and then checks public/private resulting pages. Treat Wiki publish as a separate deployment job with retry and reconciliation; do not confuse a local docs source with a published Wiki URL. Build a static docs-site mirror if Wiki unavailable, with explicit requirement deviation.

## Documentation Done gate

All changed screens/options have updated versioned help, actual screenshots, valid alt/captions, working local links, correct Wiki mapping, issue/error guidance, release notes, and test evidence. Any missing captured screenshot makes a *completed* module fail. P00 planning templates are permitted to remain pending and cannot be reported as finished user manuals.

Official Wiki publishing guide: https://docs.github.com/en/communities/documenting-your-project-with-wikis/adding-or-editing-wiki-pages

## v3.2 documentation changes must be traceable

Any released UI change updates module dossier, option explanation, screenshot/alt text, offline Help and Wiki source. New feature/issue/change event links those revisions; release manifest references the version-matched documentation. Missing docs or screenshot proof blocks phase completion. Publishing an issue or merged PR is not proof the behavior is available to a user.
