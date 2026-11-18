# Real Screenshot Gate

`docs/screenshots/MANIFEST.json` holds every required option and screen capture. Current values are intentionally `PENDING` because no app exists. Once a phase's module is implemented, update only its captures with source build SHA, real image path/hash, tested screen/control, OS/DPI/theme and verified reviewer/automated visual test results. Docs CI must block merge if a **completed module** still has pending screenshots. Concept SVG diagrams and competitor references never satisfy the real UI proof requirement.

Sample required screenshot path: `docs/screenshots/M03/M03-S01.png`, option `docs/screenshots/M03/M03-OPT-01.png`. Screenshot guide must contain alt text, annotations and exact help link. Use reproducible seed fixture data and redact confidential content. Record baseline and actual visual-diff artifact.

## New screenshot acceptance: update, backup, model relocation

M23 (data), M24 (storage), M25 (update notifications) require actual captures for every listed screen and option in `docs/screenshots/MANIFEST.json`. Additionally, at least one verification sequence must show a recovery/error state in the user manual, with sensitive content redacted. Each image references the tested app commit SHA, OS, app version and screenshot capture test. Concept diagrams do not count as UI evidence.

## M26 changelog capture requirements

All 8 screens and all 20 M26 options have `PENDING` entries until app exists. When capturing actual UI, record build SHA, OS/theme, alt text, documentation revision and affected release. Static mockups, example versions and diagrams cannot be claimed as real screenshots.
