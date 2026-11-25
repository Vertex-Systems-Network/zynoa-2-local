"""Self-contained, offline real-Windows review pack for P02's 29 final screenshot targets.

All pictures come from source-SHA-validated real Tauri PNGs, never generated
mockups. This produces REVIEW CANDIDATES, never final manifest assets or approvals.
"""
from __future__ import annotations

import argparse
import base64
from html import escape
import hashlib
import json
from pathlib import Path
import re

from tools.verify_p02_native_evidence import (
    DIRECT_CONTROL_MATRIX, OPTION_REFERENCE_MATRIX, SCREEN_IDS,
    validate_candidate, verify as verify_native,
)
from tools.verify_p02_t10_readiness import EXPECTED

_SHA = re.compile(r"^[a-f0-9]{40}$")
# These 14 IDs already have a direct running-app screenshot. The other 15
# require a new native direct-control journey; Help reference frames never count.
_EXISTING_DIRECT = frozenset({
    "M02-S03", "M02-S04", "M02-S05", "M02-S06", "M02-S07",
    "M02-OPT-03", "M02-OPT-04", "M02-OPT-07",
    *(f"M19-S{i:02d}" for i in range(1, 7)),
})


class ReviewPackError(ValueError):
    """Native source/asset mapping is not suitable for truthful review."""


def candidate_id(asset_id: str) -> str:
    if asset_id not in EXPECTED:
        raise ReviewPackError("unknown final screenshot target")
    return asset_id if asset_id in _EXISTING_DIRECT else "P02-T10-CTRL-" + asset_id


def plan(manifest: dict, machine: dict, source_sha: str) -> dict:
    if not _SHA.fullmatch(source_sha):
        raise ReviewPackError("invalid source SHA")
    if machine.get("status") != "MACHINE_METADATA_HASH_VALIDATED_ONLY" or (
        machine.get("source_commit_sha") != source_sha or
        machine.get("independent_visual_review") is not False or
        machine.get("manifest_completed") is not False
    ):
        raise ReviewPackError("native machine report invalid or claims visual approval")
    rows = [x for x in manifest.get("required", []) if x.get("module") in {"M02", "M19"}]
    targets = [row.get("asset_id") for row in rows]
    if len(rows) != 29 or set(targets) != EXPECTED or len(set(targets)) != 29:
        raise ReviewPackError("P02 final 29 screenshot inventory mismatched")
    ids = [x.get("screen_id") for x in machine.get("screens", []) if isinstance(x, dict)]
    if len(ids) != len(SCREEN_IDS) or set(ids) != set(SCREEN_IDS):
        raise ReviewPackError("real native screenshot inventory missing or duplicated")
    if len(set(ids)) != len(ids):
        raise ReviewPackError("duplicate native image ID")
    direct = machine.get("actual_screen_control_candidates", {})
    if (direct.get("status") != "MACHINE_CONTROL_CAPTURE_ONLY"
            or direct.get("ids") != list(DIRECT_CONTROL_MATRIX)
            or direct.get("count") != 15
            or direct.get("final_29_manifest_assets_verified") is not False):
        raise ReviewPackError("15 actual control proof cannot be replaced by Help reference")
    references = machine.get("option_reference_matrix", {})
    if (references.get("status") != "MACHINE_REFERENCE_CAPTURE_ONLY"
            or references.get("ids") != list(OPTION_REFERENCE_MATRIX)
            or references.get("count") != 16):
        raise ReviewPackError("separate 16-option Help references missing")
    by_id = {x["screen_id"]: x for x in machine["screens"]}
    previews = []
    for row in sorted(rows, key=lambda x: x["asset_id"]):
        asset = row["asset_id"]
        if row.get("path") != f"docs/screenshots/{row['module']}/{asset}.png":
            raise ReviewPackError("final asset path mismatch: " + asset)
        if row.get("status") not in ("PENDING", "VERIFIED"):
            raise ReviewPackError("invalid target status: " + asset)
        native_id = candidate_id(asset)
        frame = by_id.get(native_id)
        if frame is None or frame.get("source_commit_sha") != source_sha:
            raise ReviewPackError("missing source-bound real native candidate: " + asset)
        if not isinstance(frame.get("sha256"), str) or not re.fullmatch(
            r"[a-f0-9]{64}", frame["sha256"]
        ):
            raise ReviewPackError("candidate image hash missing: " + asset)
        previews.append({
            "asset_id": asset,
            "module": row["module"],
            "kind": row["kind"],
            "native_candidate_id": native_id,
            "native_path": f"docs/screenshots/_ci/{row['module']}/{native_id}.png",
            "sha256": frame["sha256"],
            "capture_class": "existing_actual_screen" if native_id == asset
                             else "new_actual_screen_or_control",
            "status": "CANDIDATE_PENDING_INDEPENDENT_FINAL_REVIEW",
            "final_manifest_verified": False,
        })
    return {
        "schema_version": 1, "phase": "P02",
        "source_commit_sha": source_sha,
        "status": "REVIEW_PACK_ONLY_NOT_FINAL",
        "final_asset_targets": 29,
        "mapped_real_native_targets": len(previews),
        "existing_direct": len(_EXISTING_DIRECT),
        "additional_direct": len(DIRECT_CONTROL_MATRIX),
        "separate_option_help_references": len(OPTION_REFERENCE_MATRIX),
        "independent_full_visual_review": False,
        "screen_reader_approved": False,
        "final_manifest_completed": False,
        "performance_budget_approved": False,
        "frames": previews,
    }


def render_html(pack: dict, root: Path) -> str:
    """Embed original PNG bytes. No internet/JS/remote image dependency."""
    head = [
        "<!doctype html><html lang='en'><head><meta charset='utf-8'>",
        "<meta name='viewport' content='width=device-width,initial-scale=1'>",
        "<title>P02 native screenshot review — not final</title>",
        "<style>body{margin:0;background:#141820;color:#eee;font:15px Segoe UI,Arial,sans-serif}"
        "header{padding:32px;max-width:1250px;margin:auto}h1{margin:0 0 12px}p{line-height:1.6}"
        ".warning{border-left:4px solid #e8b76b;padding:10px 14px;background:#27231e}"
        ".grid{display:grid;grid-template-columns:repeat(auto-fit,minmax(380px,1fr));gap:20px;"
        "max-width:1320px;margin:auto;padding:24px}.item{background:#1c2430;border:1px solid #44505e;"
        "border-radius:12px;padding:16px;min-width:0}.item img{max-width:100%;width:100%;height:auto;"
        "border:1px solid #515c6b}.meta{overflow-wrap:anywhere;font-size:11px;color:#acb9c5}"
        "h2{font-size:18px}.ref{background:#26303b}</style></head><body><header>",
        "<h1>P02 — actual Windows Tauri screenshot review</h1>",
        f"<p>Exact source SHA: <code>{escape(pack['source_commit_sha'])}</code>. "
        "Twenty-nine required screen/control targets have **candidate images**, "
        "plus sixteen separately classified Help references.</p>",
        "<p class='warning'><strong>NOT FINAL:</strong> no image is approved or committed "
        "to the final screenshot manifest. An independent complete visual review, "
        "NVDA/Narrator, performance budgets and protected PR merge remain required.</p>",
        "</header><main class='grid'>",
    ]
    for record in pack["frames"]:
        path = root / record["native_path"]
        png = path.read_bytes()
        if hashlib.sha256(png).hexdigest() != record["sha256"]:
            raise ReviewPackError("embedded image SHA does not match native report: " + record["asset_id"])
        img = base64.b64encode(png).decode("ascii")
        title = escape(record["asset_id"])
        actual = escape(record["native_candidate_id"])
        category = escape(record["capture_class"])
        head.extend([
            "<article class='item'>",
            f"<h2>{title}</h2><p class='meta'>Real candidate {actual} — {category}</p>",
            f"<img loading='lazy' alt='Windows Tauri native review candidate {title}' "
            f"src='data:image/png;base64,{img}'>",
            f"<p class='meta'>SHA256 {escape(record['sha256'])}</p>",
            "</article>",
        ])
    head.append("</main><header><h2>Separate option Help references (NOT control screenshots)</h2>")
    head.append("<p>The following 16 captures document bundled Help details only. They cannot be "
                "used to approve a required actual control screenshot.</p></header><section class='grid'>")
    for candidate in OPTION_REFERENCE_MATRIX:
        module = candidate[:3]
        path = root / f"docs/screenshots/_ci/{module}/{candidate}.png"
        png = path.read_bytes()
        name = escape(candidate)
        head.extend([
            "<article class='item ref'>",
            f"<h2>Help only — {name}</h2>",
            f"<img loading='lazy' alt='Native offline Help reference {name}, not final control' "
            f"src='data:image/png;base64,{base64.b64encode(png).decode('ascii')}'>",
            "</article>",
        ])
    head.append("</section></body></html>")
    return "".join(head)


def build(root: Path, source_sha: str, output: Path) -> dict:
    machine = verify_native(root / "docs/screenshots/_ci", source_sha)
    manifest = json.loads((root / "docs/screenshots/MANIFEST.json").read_text(encoding="utf-8"))
    report = plan(manifest, machine, source_sha)
    # A validated PNG/receipt pair must exist for every frame, including
    # the 16 Help references. verify_native has already checked all 69 pairs.
    output.mkdir(parents=True, exist_ok=True)
    html = render_html(report, root)
    index = output / "P02-T10-69-native-review.html"
    metadata = output / "P02-T10-29-review-index.json"
    if index.exists() or metadata.exists():
        raise ReviewPackError("refuse overwriting a prior review artifact")
    index.write_text(html, encoding="utf-8")
    metadata.write_text(json.dumps(report, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    return report


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--root", type=Path, default=Path("."))
    parser.add_argument("--source-sha", required=True)
    parser.add_argument("--out", type=Path, required=True)
    args = parser.parse_args()
    try:
        result = build(args.root, args.source_sha, args.out)
    except (ReviewPackError, OSError, ValueError, KeyError) as exc:
        parser.exit(1, "ZYN-P02-REVIEW-001: " + str(exc) + "\n")
    print(json.dumps({
        "status": result["status"], "final_targets_with_native_candidates":
        result["mapped_real_native_targets"], "real_control_candidates":
        result["additional_direct"], "help_only_references":
        result["separate_option_help_references"],
    }))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
