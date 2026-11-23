"""P02-T02 final acceptance preflight; never close an incomplete UI task.

The task-board DONE status is checked against actual screenshot-manifest assets,
source documentation and independently reviewed evidence. All checks are local:
remote workflow success must still be separately verified on the GitHub PR.
"""
from __future__ import annotations

import argparse
import json
from pathlib import Path


SCREEN_IDS = tuple(f"M02-S{i:02d}" for i in range(1, 8))
OPTION_IDS = tuple(f"M02-OPT-{i:02d}" for i in range(1, 9))
REQUIRED_IDS = frozenset(SCREEN_IDS + OPTION_IDS)


class PrematureT02Closure(ValueError):
    """Task status claims DONE while required evidence is still absent."""


def audit(root: Path) -> dict:
    tasks = json.loads((root / "docs/state/pr-tasks/P02.json").read_text(encoding="utf-8"))
    screenshot_manifest = json.loads((root / "docs/screenshots/MANIFEST.json").read_text(encoding="utf-8"))
    help_text = (root / "docs/help/articles/M02.md").read_text(encoding="utf-8")
    wiki_text = (root / "docs/wiki/pages/M02.md").read_text(encoding="utf-8")
    module_text = (root / "docs/modules/M02.md").read_text(encoding="utf-8")
    t02 = next((row for row in tasks["tasks"] if row["id"] == "P02-T02"), None)
    if t02 is None:
        raise PrematureT02Closure("P02-T02 missing from official task board")
    m02 = [row for row in screenshot_manifest["required"] if row["module"] == "M02"]
    ids = {row["asset_id"] for row in m02}
    blockers: list[str] = []
    missing_ids = sorted(REQUIRED_IDS - ids)
    if missing_ids:
        blockers.append("M02 missing required screenshot IDs: " + ", ".join(missing_ids))
    missing_png: list[str] = []
    pending_assets: list[str] = []
    for row in m02:
        if row["asset_id"] not in REQUIRED_IDS:
            blockers.append("unexpected M02 screenshot ID: " + row["asset_id"])
        if not (root / row["path"]).is_file():
            missing_png.append(row["asset_id"])
        if row["status"] != "VERIFIED":
            pending_assets.append(row["asset_id"])
    if missing_png:
        blockers.append(f"{len(missing_png)} M02 final screenshot PNGs not committed")
    if pending_assets:
        blockers.append(f"{len(pending_assets)} M02 screenshot entries not VERIFIED")

    # A scoped screenshot review is not a full module-wide visual review.
    review_path = root / "docs/screenshots/M02/T02-visual-foundation.review.json"
    if review_path.is_file():
        review = json.loads(review_path.read_text(encoding="utf-8"))
        boundaries = review.get("status_boundary", {})
        if boundaries.get("all_M02_M19_screenshot_gates_complete") is False:
            blockers.append("scoped native visual review explicitly excludes final module screenshots")
    else:
        blockers.append("T02 native visual review record absent")

    for option in OPTION_IDS:
        if f"### {option} " not in help_text:
            blockers.append(f"{option} detailed Help section missing")
        if option not in wiki_text:
            blockers.append(f"{option} Wiki source mapping missing")
    # These planned controls remain unavailable in the P02 preview. Their
    # successful implementation must replace these honest unavailable labels.
    for option in ("M02-OPT-03", "M02-OPT-04"):
        start = help_text.find(f"### {option} ")
        end = help_text.find("### M02-OPT-", start + 5)
        segment = help_text[start:end if end != -1 else None] if start >= 0 else ""
        if "not implemented" in segment.lower():
            blockers.append(f"{option} functionality explicitly not implemented")
    if "NOT YET VERIFIED" in module_text:
        blockers.append("M02 module contract still marks completion NOT YET VERIFIED")

    # Final acceptance requires the real implementation, screenshots, all
    # options, accessibility and manual review. No all-green current source CI
    # substitutes for the future exact-head module delivery gates.
    ready = not blockers
    status = "READY_FOR_FINAL_REMOTE_REVIEW" if ready else "NOT_READY"
    if t02["status"] == "DONE" and not ready:
        raise PrematureT02Closure(
            "P02-T02 falsely marked DONE: " + "; ".join(blockers))
    return {
        "schema_version": 1,
        "task_id": "P02-T02",
        "official_task_status": t02["status"],
        "acceptance": status,
        "module": "M02",
        "expected_final_screenshot_count": len(REQUIRED_IDS),
        "verified_manifest_screenshot_count": sum(
            row["status"] == "VERIFIED" and (root / row["path"]).is_file()
            for row in m02 if row["asset_id"] in REQUIRED_IDS
        ),
        "blockers": blockers,
        "remote_ci_and_merge_verified": False,
        "note": "Automated local preflight only. Remote GitHub checks, full visual/a11y review and PR merge require independent proof.",
    }


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--root", type=Path, default=Path(__file__).resolve().parents[1])
    parser.add_argument("--report", type=Path)
    args = parser.parse_args(argv)
    try:
        result = audit(args.root)
    except (OSError, KeyError, ValueError, PrematureT02Closure) as exc:
        parser.exit(1, f"ZYN-P02-T02-012: {exc}\n")
    if args.report:
        args.report.parent.mkdir(parents=True, exist_ok=True)
        args.report.write_text(json.dumps(result, indent=2, sort_keys=True) + "\n",
                               encoding="utf-8")
    print(json.dumps({"task": result["task_id"],
                      "official_status": result["official_task_status"],
                      "acceptance": result["acceptance"],
                      "verified_screenshots": result["verified_manifest_screenshot_count"],
                      "blockers": result["blockers"]}, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
