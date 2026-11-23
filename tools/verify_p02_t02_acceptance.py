"""P02-T02 final acceptance preflight; never close an incomplete UI task.

The task-board DONE status is checked against actual screenshot-manifest assets,
source documentation and independently reviewed evidence. All checks are local:
remote workflow success must still be separately verified on the GitHub PR.
"""
from __future__ import annotations

import argparse
import hashlib
import json
from pathlib import Path
import re
import struct


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
    if len(m02) != 15 or len(ids) != 15:
        blockers.append("M02 final screenshot inventory is not 15 unique IDs")
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
        if not isinstance(row.get("caption"), str) or len(row["caption"]) < 48 or not isinstance(row.get("alt_text"), str) or len(row["alt_text"]) < 32:
            blockers.append(row["asset_id"] + " final screenshot caption or accessible alt missing")
    if missing_png:
        blockers.append(f"{len(missing_png)} M02 final screenshot PNGs not committed")
    if pending_assets:
        blockers.append(f"{len(pending_assets)} M02 screenshot entries not VERIFIED")

    # This independently authored per-screen native visual review is separate
    # from the Windows machine's immutable candidate-only screenshot receipts.
    review_file = root / "docs/screenshots/M02/T02-final-15-native-visual.review.json"
    if not review_file.is_file():
        blockers.append("M02 independent 15-image final visual review absent")
    else:
        try:
            final_review = json.loads(review_file.read_text(encoding="utf-8"))
            reviewed_images = final_review.get("images", [])
            by_id = {entry["asset_id"]: entry for entry in reviewed_images}
            if (final_review.get("review_status") != "ACCEPTED_M02_15_NATIVE_VISUAL_ONLY"
                    or final_review.get("module") != "M02"
                    or final_review.get("screen_review_count") != 15
                    or final_review.get("independent_visual_review") is not True
                    or final_review.get("full_nvda_narrator_approved") is not False
                    or final_review.get("full_m02_module_release_approved") is not False
                    or len(reviewed_images) != 15
                    or len(by_id) != 15 or set(by_id) != REQUIRED_IDS):
                blockers.append("M02 per-image visual review incomplete or overly claims release")
            else:
                for entry in m02:
                    path = root / entry["path"]
                    if not path.is_file():
                        continue
                    image_bytes = path.read_bytes()
                    visual = by_id.get(entry["asset_id"], {})
                    git_sha = hashlib.sha1(b"blob " + str(len(image_bytes)).encode("ascii") + b"\0" + image_bytes).hexdigest()
                    valid_png = (image_bytes.startswith(b"\x89PNG\r\n\x1a\n")
                                 and len(image_bytes) >= 24)
                    width, height = struct.unpack(">II", image_bytes[16:24]) if valid_png else (0, 0)
                    if (visual.get("path") != entry["path"]
                            or visual.get("sha256") != entry.get("source_capture_sha256")
                            or visual.get("git_blob_sha") != entry.get("source_git_blob_sha")
                            or visual.get("visual_result") != "PASS_FOR_M02_SCREEN_OPTION_FRAME_ONLY"
                            or not visual.get("observations")
                            or not valid_png
                            or width != entry.get("capture_window_width")
                            or height != entry.get("capture_window_height")
                            or hashlib.sha256(image_bytes).hexdigest() != visual.get("sha256")
                            or git_sha != visual.get("git_blob_sha")):
                        blockers.append(entry["asset_id"] + " M02 independent visual/hash/geometry review mismatch")
        except (OSError, ValueError, KeyError, TypeError) as exc:
            blockers.append("M02 per-image visual review cannot be validated: " + type(exc).__name__)

    # Historical 9-frame early-foundation review is retained as provenance.
    # Its old "all assets incomplete" flag described that previous date; the
    # newer, independently reviewed 15-image final manifest supersedes it.
    review_path = root / "docs/screenshots/M02/T02-visual-foundation.review.json"
    if not review_path.is_file():
        blockers.append("T02 early native foundation review record absent")
    else:
        historic = json.loads(review_path.read_text(encoding="utf-8"))
        if (historic.get("review_status") != "ACCEPTED_SCOPED_NATIVE_FOUNDATIONS_ONLY"
                or len(historic.get("screenshots", [])) < 8):
            blockers.append("T02 historical foundational native review evidence invalid")

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
    # T02 is design tokens, keyboard-accessible primitive foundations and their
    # native image evidence. Full M02 release, all-state NVDA/Narrator,
    # cold-start performance budgets and protected P02 merge belong to T10/T11.
    # Keep the M02 module contract truthful: do NOT change NOT YET VERIFIED.
    expected_sources = {
        "apps/desktop/src/styles.css": (
            '.shell[data-theme="dark"]', '.shell[data-theme="light"]',
            '--accent:', '--outline:', '.shell .workbench-tabpanel:focus-visible',
            '@media (prefers-reduced-motion:reduce)', '@media (max-width:950px)',
        ),
        "apps/desktop/src/ui/Workbench.tsx": (
            'aria-pressed={compactProperties}', 'role="status"',
            'aria-valuetext=', 'aria-selected={active === pane.key}',
        ),
        "apps/desktop/src/App.tsx": (
            'data-density={density}', 'aria-label="Interface appearance"',
            'aria-label="Navigation density"', 'aria-live="polite"',
        ),
        "tests/test_p02_ui_contract.py": (
            'test_small_theme_labels_meet_wcag_normal_text_contrast',
            'test_workbench_focus_ring_contrast_both_themes',
            'test_workbench_keyboard_focus_visible_on_real_tabpanels',
        ),
        "tests/test_p02_m02_controls.py": (
            'test_live_session_preferences',
            'test_reduced_motion_has_distinct_focusable_read_only_status',
        ),
        "scripts/probe_p02_native_a11y.ps1": (
            'UIAutomationClient', 'keyboard_focus_enters_modal_search',
            'escape_dismisses_modal',
        ),
    }
    for relative, markers in expected_sources.items():
        source_path = root / relative
        if not source_path.is_file():
            blockers.append("T02 required source/acceptance contract missing: " + relative)
            continue
        source = source_path.read_text(encoding="utf-8")
        for marker in markers:
            if marker not in source:
                blockers.append("T02 required primitive/contrast/focus evidence missing: " + relative + " :: " + marker)
    if "NOT YET VERIFIED" not in module_text:
        blockers.append("M02 module release boundary removed or misrepresented")

    # This T02 scoped gate does NOT assert whole M02 module, full T10 screen
    # reader journeys, full performance budget, or T11 protected merge.
    # Exact-head native Windows/Governance CI is checked separately on PR #12.
    ready = not blockers
    status = "READY_FOR_T02_SCOPED_REMOTE_CI" if ready else "NOT_READY"
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
        "t02_scope_only": True,
        "m02_module_release_verified": False,
        "full_nvda_narrator_verified": False,
        "performance_budget_approved": False,
        "remote_ci_and_merge_verified": False,
        "note": "T02-local design/focus/native-image evidence preflight. Current-head GitHub Windows CI must be separately checked; full T10 NVDA/performance and T11 protected merge are not prerequisites of this narrower task.",
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
