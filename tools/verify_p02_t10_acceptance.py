"""P02-T10 scoped *Windows preview* acceptance: independent image, Wiki and live CI proofs.

Fail closed against missing original PNG bytes, forged visual review, stale Windows
source SHA, fake UIA/NVDA speech, or nonpassing real measured preview budgets.
P02-T11 owner review, Narrator/full-product a11y, product SLA, and protected merge
remain deliberately separate; this gate never asserts them.
"""
from __future__ import annotations

import argparse
import hashlib
import json
from pathlib import Path
import re
import struct

from tools.verify_p02_native_uia import verify as verify_uia
from tools.verify_p02_nvda_speech import verify as verify_nvda
from tools.verify_p02_native_performance import verify as verify_warm
from tools.verify_p02_t10_performance_budget import verify as verify_budget

SHA40 = re.compile(r"^[0-9a-f]{40}$")
SHA64 = re.compile(r"^[0-9a-f]{64}$")
EXPECTED = {
    **{f"M02-S{i:02d}": "M02" for i in range(1, 8)},
    **{f"M02-OPT-{i:02d}": "M02" for i in range(1, 9)},
    **{f"M19-S{i:02d}": "M19" for i in range(1, 7)},
    **{f"M19-OPT-{i:02d}": "M19" for i in range(1, 9)},
}
REVIEW_PATHS = {
    "M02": "docs/screenshots/M02/T02-final-15-native-visual.review.json",
    "M19": "docs/screenshots/M19/T10-final-14-native-visual.review.json",
}


class InvalidT10Acceptance(ValueError):
    pass


def need(ok: bool, reason: str) -> None:
    if not ok:
        raise InvalidT10Acceptance(reason)


def load(root: Path, relative: str) -> dict:
    try:
        obj = json.loads((root / relative).read_text(encoding="utf-8-sig"))
    except (OSError, ValueError) as exc:
        raise InvalidT10Acceptance("missing/invalid proof: " + relative) from exc
    need(isinstance(obj, dict), relative + " must contain JSON object")
    return obj


def audit_static(root: Path) -> dict:
    """Trust only source-bound committed PNGs and separately reviewed originals."""
    task_board = load(root, "docs/state/pr-tasks/P02.json")
    tasks = {x["id"]: x for x in task_board["tasks"]}
    need(tasks["P02-T10"]["status"] in ("IN_PROGRESS", "DONE"), "invalid T10 board status")
    need(tasks["P02-T11"]["status"] == "IN_PROGRESS", "T11 must remain unmerged")
    phase = load(root, "docs/state/PHASE.json")
    need(phase.get("phase") == "P02" and phase.get("phase_status") == "IN_PROGRESS",
         "P02 phase advanced without protected merge")
    manifest = load(root, "docs/screenshots/MANIFEST.json")
    rows = [x for x in manifest.get("required", []) if x.get("module") in ("M02", "M19")]
    ids = [x.get("asset_id") for x in rows]
    need(len(rows) == len(EXPECTED) == len(set(ids)) and set(ids) == set(EXPECTED),
         "29 native image inventory absent or duplicated")
    final = load(root, "docs/evidence/P02_T10_FINAL_29_NATIVE_SCREENSHOTS_20261124.json")
    need(final.get("status") == "ALL_29_NATIVE_PNG_SCREEN_OPTION_VISUALS_VERIFIED_ONLY"
         and final.get("total") == 29 and final.get("m02_verified") == 15
         and final.get("m19_verified") == 14
         and final.get("independent_per_image_visual_review") is True
         and final.get("image_caption_alt_metadata_complete") is True
         and final.get("protected_main_merged") is False
         and final.get("phase_verified_complete") is False,
         "complete 29 source image proof missing or falsely claiming release")
    final_images = {x["asset_id"]: x for x in final.get("assets", [])}
    need(len(final_images) == 29 and set(final_images) == set(EXPECTED),
         "independent final image list incomplete")
    reviewed = {}
    for module, file in REVIEW_PATHS.items():
        review = load(root, file)
        number = 15 if module == "M02" else 14
        desired = ("ACCEPTED_M02_15_NATIVE_VISUAL_ONLY" if module == "M02"
                   else "ACCEPTED_M19_14_OF_14_NATIVE_VISUAL_ONLY")
        need(review.get("module") == module and review.get("review_status") == desired
             and review.get("full_nvda_narrator_approved") is False,
             module + " review is untrusted or claims full Narrator")
        count = review.get("screen_review_count") if module == "M02" else review.get("complete_reviewed_count")
        need(count == number and len(review.get("images", [])) == number,
             module + " independent per-image visual review incomplete")
        if module == "M02":
            need(review.get("independent_visual_review") is True, "M02 reviewer was not independent")
        else:
            need(review.get("all_committed_native_screen_option_pngs_accepted_for_visual_identity_only") is True
                 and review.get("pending_final_png_ids") == [], "M19 original visual signoff incomplete")
        for image in review["images"]:
            ident = image["asset_id"]
            need(ident not in reviewed and EXPECTED.get(ident) == module,
                 "review image identity wrong or duplicated")
            reviewed[ident] = image
    need(set(reviewed) == set(EXPECTED), "29 independent image-specific reviews missing")
    for row in rows:
        ident = row["asset_id"]
        module = EXPECTED[ident]
        path = f"docs/screenshots/{module}/{ident}.png"
        need(row.get("path") == path and row.get("status") == "VERIFIED",
             ident + " original PNG not verified in final manifest")
        try:
            payload = (root / path).read_bytes()
        except OSError as exc:
            raise InvalidT10Acceptance(ident + " original PNG absent") from exc
        need(len(payload) >= 24 and payload.startswith(b"\x89PNG\r\n\x1a\n"),
             ident + " original native PNG invalid")
        width, height = struct.unpack(">II", payload[16:24])
        source_hash = hashlib.sha256(payload).hexdigest()
        git_hash = hashlib.sha1(f"blob {len(payload)}\0".encode("ascii") + payload).hexdigest()
        item, review = final_images[ident], reviewed[ident]
        need(row.get("source_capture_sha256") == source_hash
             and row.get("source_git_blob_sha") == git_hash
             and item.get("source_sha256") == source_hash
             and item.get("git_blob_sha") == git_hash
             and review.get("sha256") == source_hash
             and review.get("git_blob_sha") == git_hash,
             ident + " original PNG or review hash mismatch")
        need(row.get("capture_window_width") == width and row.get("capture_window_height") == height
             and item.get("window_width") == width and item.get("window_height") == height,
             ident + " native image dimensions mismatch")
        need(item.get("path") == path and review.get("path") == path
             and item.get("status") == "VERIFIED"
             and review.get("visual_result") == f"PASS_FOR_{module}_SCREEN_OPTION_FRAME_ONLY"
             and len(review.get("observations", "")) >= 20,
             ident + " image-specific visual review not accepted")
        need(len(row.get("alt_text", "")) >= 32 and len(row.get("caption", "")) >= 48
             and row.get("alt_text") == item.get("alt_text")
             and row.get("caption") == item.get("caption")
             and row.get("review_scope") == "VERIFIED_NATIVE_PNG_IMAGE_ONLY_NOT_MODULE_RELEASE",
             ident + " caption/alt/privacy/scope metadata incomplete")
    wiki = load(root, "docs/evidence/P02_T10_WIKI_PREVIEW_PUBLISHED_20261124.json")
    need(wiki.get("status") == "WIKI_TWO_PREVIEW_PAGES_REMOTELY_PUBLISHED_AND_READ_BACK"
         and wiki.get("fresh_unauthenticated_git_clone_readback") is True
         and wiki.get("existing_home_untouched") is True
         and wiki.get("published_preview_not_final_release") is True
         and wiki.get("protected_pr_merged") is False
         and wiki.get("publish_run") == 45284338605,
         "hosted Wiki preview remote readback absent")
    pages = wiki.get("pages", {})
    need(set(pages) == {"M02.md", "M19.md"} and all(
        page.get("preview") is True and bool(SHA64.fullmatch(page.get("sha256", "")))
        for page in pages.values()), "hosted Wiki SHA-bound two-page preview missing")
    for mod in ("M02", "M19"):
        help_text = (root / f"docs/help/articles/{mod}.md").read_text(encoding="utf-8")
        wiki_text = (root / f"docs/wiki/pages/{mod}.md").read_text(encoding="utf-8")
        for i in range(1, 9):
            option = f"{mod}-OPT-{i:02d}"
            need(option in help_text and option in wiki_text,
                 option + " Help/Wiki mapping missing")
    return {"native_images_verified": 29, "m02_images": 15, "m19_images": 14,
            "independent_image_reviews": 29, "help_wiki_options": 16,
            "remote_wiki_preview_readback": True}


def audit(root: Path, runtime: Path, source_sha: str, run_id: str) -> dict:
    need(bool(SHA40.fullmatch(source_sha)), "invalid source SHA")
    need(run_id.isdigit(), "missing exact Windows CI run ID")
    static = audit_static(root)
    subdir = "docs/screenshots/_ci/M02/"
    uia_raw = load(runtime, subdir + "P02-native-uia.capture.json")
    nvda_raw = load(runtime, subdir + "P02-nvda-speech.capture.json")
    warm_raw = load(runtime, subdir + "P02-native-startup-repeat.capture.json")
    cold_raw = load(runtime, subdir + "P02-native-performance.json")
    budget = load(root, "docs/quality/P02_T10_PERFORMANCE_BUDGET.json")
    try:
        uia = verify_uia(uia_raw, source_sha)
        nvda = verify_nvda(nvda_raw, source_sha)
        warm = verify_warm(warm_raw, source_sha)
        perf = verify_budget(budget, cold_raw, warm, source_sha)
    except ValueError as exc:
        raise InvalidT10Acceptance("native Windows proof failed: " + str(exc)) from exc
    need(uia["native_aria_checks"] == 9
         and uia["native_keyboard_journey_verified"] is True,
         "native keyboard UIA journey failed")
    need(nvda["status"] == "SCOPED_LIVE_NVDA_SPEECH_PASS"
         and nvda.get("narrator_verified") is False,
         "live native NVDA three-stage speech scope failed")
    need(perf["status"] == "P02_CI_PREVIEW_PERFORMANCE_GUARDRAIL_PASS"
         and perf.get("product_performance_sla_approved") is False
         and perf.get("historical_outlier_not_waived") is True,
         "native preview performance gate invalid")
    need(warm.get("github_run_id") == nvda.get("github_run_id") == run_id
         and warm.get("executable_sha256") == nvda_raw.get("app_executable_sha256"),
         "NVDA and performance are not from the same exact-head native executable/run")
    return {
        "schema_version": 1, "phase": "P02", "task_id": "P02-T10",
        "status": "READY_FOR_T10_SCOPED_WINDOWS_PREVIEW_ACCEPTANCE",
        "source_commit_sha": source_sha, "github_run_id": run_id,
        **static,
        "native_uia_checks": 9, "nvda_live_spoken_journeys": 3,
        "warm_ipc_ms": perf["native_warm_ipc_ms"],
        "cold_native_metadata_ms": perf["native_cold_metadata_ready_ms"],
        "ci_preview_budget_enforced": True,
        "full_narrator_certified": False, "full_product_a11y_certified": False,
        "product_performance_sla_approved": False, "protected_merge_verified": False,
        "t11_pending": True, "no_user_data": True,
    }


def main(argv=None) -> int:
    p = argparse.ArgumentParser(description=__doc__)
    p.add_argument("--root", type=Path, default=Path("."))
    p.add_argument("--runtime", type=Path, default=Path("."))
    p.add_argument("--source-sha", required=True)
    p.add_argument("--run-id", required=True)
    p.add_argument("--report", type=Path, required=True)
    a = p.parse_args(argv)
    try:
        output = audit(a.root, a.runtime, a.source_sha, a.run_id)
    except (InvalidT10Acceptance, OSError, KeyError, TypeError, ValueError) as exc:
        p.exit(1, "ZYN-P02-T10-020: " + str(exc) + "\n")
    a.report.parent.mkdir(parents=True, exist_ok=True)
    a.report.write_text(json.dumps(output, sort_keys=True, indent=2) + "\n", encoding="utf-8")
    print(json.dumps(output, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
