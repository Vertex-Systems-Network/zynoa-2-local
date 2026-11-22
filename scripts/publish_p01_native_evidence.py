"""Publish only explicitly reviewed, SHA-pinned native Windows CI screenshot bytes.

No synthetic image generation, no arbitrary archive extraction, no user data.
Run from the same-repository phase branch with a short-lived GitHub Actions token.
"""
from __future__ import annotations
import hashlib
import io
import json
import os
from pathlib import Path
import re
import struct
import subprocess
import urllib.request
import urllib.error
import urllib.parse
import zipfile

REPO = "Vertex-Systems-Network/zynoa-2-local"
APPROVAL_FILE = Path("docs/screenshots/M01/P01_REVIEW_APPROVAL.json")
REVIEWED_IDS = frozenset((
    "M01-S01", "M01-S01-continued", "P01-Settings-preview",
    "P01-Recovery-preview", "P01-Diagnostics-preview",
))
HEX40 = re.compile(r"^[0-9a-f]{40}$")
HEX64 = re.compile(r"^[0-9a-f]{64}$")
MAX_ZIP_BYTES = 20 * 1024 * 1024


def require(condition: bool, message: str) -> None:
    if not condition:
        raise ValueError("ZYN-REVIEW: " + message)


def validate_approval(approval: dict) -> None:
    require(approval.get("schema_version") == 1 and approval.get("phase") == "P01",
            "wrong manifest schema/phase")
    require(approval.get("decision") == "ACCEPTED_NATIVE_FOUNDATION_ONLY",
            "explicit independent image review absent")
    require(approval.get("reviewer") == "ChatGPT independent visual inspection",
            "reviewer evidence missing")
    require(isinstance(approval.get("review_notes"), str) and len(approval["review_notes"]) >= 50,
            "detailed privacy/frame/legibility review missing")
    require(isinstance(approval.get("run_id"), int) and approval["run_id"] > 0,
            "invalid Windows run")
    require(isinstance(approval.get("artifact_id"), int) and approval["artifact_id"] > 0,
            "invalid artifact")
    require(bool(HEX40.fullmatch(str(approval.get("source_commit_sha", "")))),
            "invalid source commit")
    sha_map = approval.get("sha256_by_screenshot")
    require(isinstance(sha_map, dict) and set(sha_map) == REVIEWED_IDS,
            "approved screenshot list differs from the fixed P01 subset")
    require(all(isinstance(sha, str) and HEX64.fullmatch(sha) for sha in sha_map.values()),
            "invalid approved PNG hash")


def validate_png_and_capture(png: bytes, metadata: dict, screenshot_id: str,
                             expected_sha: str, expected_source: str) -> None:
    require(1000 < len(png) < 5 * 1024 * 1024, "unexpected PNG byte size: " + screenshot_id)
    require(png[:8] == b"\x89PNG\r\n\x1a\n" and png[12:16] == b"IHDR",
            "not a native PNG with IHDR")
    width, height = struct.unpack(">II", png[16:24])
    require(880 <= width <= 2400 and 600 <= height <= 1800, "invalid native window dimensions")
    real_sha = hashlib.sha256(png).hexdigest()
    require(real_sha == expected_sha == metadata.get("sha256"), "reviewed screenshot hash changed")
    require(metadata.get("screenshot_id") == screenshot_id, "screenshot ID mismatch")
    require(metadata.get("source_commit_sha") == expected_source
            and metadata.get("built_commit_sha") == expected_source,
            "source/build provenance mismatch")
    require(metadata.get("source") == "GitHub Windows Actions actual Tauri process",
            "image is not from actual native Tauri source")
    require(metadata.get("capture_verified") is False
            and metadata.get("capture_status") == "candidate_pending_visual_review",
            "raw runner metadata should remain a candidate")
    require(metadata.get("window_fully_visible") is True
            and "DwmGetWindowAttribute" in metadata.get("frame_bounds_source", ""),
            "native visible-frame proof missing")
    require(metadata.get("window_width") == width and metadata.get("window_height") == height,
            "captured bitmap dimensions disagree with metadata")
    require(isinstance(metadata.get("alt_text"), str) and len(metadata["alt_text"]) > 25,
            "alt text missing")
    require("Disposable CI fixture" in metadata.get("privacy", ""),
            "disposable privacy fixture unverified")


def github_get(path: str, *, as_bytes: bool = False):
    token = os.environ.get("GITHUB_TOKEN", "")
    require(bool(token), "GitHub token unavailable")
    req = urllib.request.Request(
        "https://api.github.com/repos/" + REPO + path,
        headers={"Authorization": "Bearer " + token,
                 "Accept": "application/vnd.github+json",
                 "X-GitHub-Api-Version": "2022-11-28",
                 "User-Agent": "Zynoa-P01-approved-evidence"},
    )
    with urllib.request.urlopen(req, timeout=60) as response:
        payload = response.read(MAX_ZIP_BYTES + 1)
    require(len(payload) <= MAX_ZIP_BYTES, "GitHub artifact exceeds size cap")
    return payload if as_bytes else json.loads(payload)



def trusted_redirect_target(url: str) -> None:
    parsed = urllib.parse.urlsplit(url)
    host = (parsed.hostname or "").lower()
    require(parsed.scheme == "https"
            and (host.endswith(".blob.core.windows.net")
                 or host.endswith(".githubusercontent.com")
                 or host.endswith(".actions.githubusercontent.com")),
            "artifact redirect left GitHub-managed HTTPS storage")


class NoAutomaticRedirect(urllib.request.HTTPRedirectHandler):
    """Avoid forwarding the GitHub bearer token to signed artifact storage."""
    def redirect_request(self, req, fp, code, msg, headers, newurl):
        return None


def download_approved_artifact(artifact_id: int) -> bytes:
    token = os.environ.get("GITHUB_TOKEN", "")
    require(bool(token), "GitHub token unavailable")
    req = urllib.request.Request(
        f"https://api.github.com/repos/{REPO}/actions/artifacts/{artifact_id}/zip",
        headers={"Authorization": "Bearer " + token,
                 "Accept": "application/vnd.github+json",
                 "User-Agent": "Zynoa-P01-approved-evidence"},
    )
    try:
        with urllib.request.build_opener(NoAutomaticRedirect).open(req, timeout=60) as r:
            data = r.read(MAX_ZIP_BYTES + 1)
    except urllib.error.HTTPError as error:
        if error.code not in (301, 302, 303, 307, 308):
            raise
        location = error.headers.get("Location", "")
        trusted_redirect_target(location)
        # Signed Azure/GitHub artifact URLs must NEVER see the GitHub bearer token.
        with urllib.request.urlopen(urllib.request.Request(
                location, headers={"User-Agent": "Zynoa-P01-approved-evidence"}),
                timeout=60) as r:
            data = r.read(MAX_ZIP_BYTES + 1)
    require(len(data) <= MAX_ZIP_BYTES, "GitHub artifact exceeds size cap")
    return data


def main() -> None:
    require(os.environ.get("GITHUB_REPOSITORY") == REPO, "wrong repository")
    require(os.environ.get("GITHUB_REF") == "refs/heads/phase/01-foundation",
            "reviewed branch required")
    manifest = json.loads(APPROVAL_FILE.read_text(encoding="utf-8"))
    validate_approval(manifest)
    source = manifest["source_commit_sha"]
    subprocess.run(["git", "merge-base", "--is-ancestor", source, "HEAD"], check=True)
    changed = subprocess.check_output(["git", "diff", "--name-only", source, "HEAD"], text=True)
    for path in changed.splitlines():
        require(not (path.startswith("apps/desktop/")
                     or path in ("scripts/capture_p01_desktop.ps1",
                                 ".github/workflows/p01-desktop.yml")),
                "application/capture sources changed after reviewed build: " + path)
    run = github_get("/actions/runs/" + str(manifest["run_id"]))
    require(run.get("name") == "P01 Desktop Foundation"
            and run.get("conclusion") == "success"
            and run.get("event") == "pull_request"
            and run.get("head_sha") == source,
            "screenshot source must be a successful real native Windows PR build")
    artifacts = github_get("/actions/runs/" + str(manifest["run_id"]) + "/artifacts?per_page=100")
    selected = [a for a in artifacts["artifacts"]
                if a["id"] == manifest["artifact_id"]
                and a["name"] == "p01-desktop-windows-build-evidence"
                and not a["expired"]]
    require(len(selected) == 1, "reviewed artifact absent from successful run")
    blob = download_approved_artifact(manifest["artifact_id"])
    planned = []
    with zipfile.ZipFile(io.BytesIO(blob)) as archive:
        for shot in sorted(REVIEWED_IDS):
            path = "docs/screenshots/M01/" + shot
            png = archive.read(path + ".png")
            raw_meta = archive.read(path + ".capture.json")
            meta = json.loads(raw_meta.decode("utf-8-sig"))
            validate_png_and_capture(png, meta, shot, manifest["sha256_by_screenshot"][shot], source)
            review_meta = {
                "screenshot_id": shot,
                "review_status": "ACCEPTED_NATIVE_FOUNDATION_ONLY",
                "verified_for": "Actual P01 read-only/disabled shell states; not planned feature completion",
                "reviewer": manifest["reviewer"],
                "reviewed_at": manifest["reviewed_at"],
                "review_notes": manifest["review_notes"],
                "source_commit_sha": source,
                "source_run_id": manifest["run_id"],
                "source_artifact_id": manifest["artifact_id"],
                "png_sha256": hashlib.sha256(png).hexdigest(),
            }
            planned.extend((
                (Path(path + ".png"), png),
                (Path(path + ".capture.json"), raw_meta),
                (Path(path + ".review.json"), (json.dumps(review_meta, indent=2) + "\n").encode()),
            ))
    for path, _ in planned:
        require(not path.exists(), "would overwrite existing reviewed evidence: " + str(path))
    for path, payload in planned:
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_bytes(payload)
    print(f"Verified and materialized {len(REVIEWED_IDS)} actual reviewed screenshots "
          f"from run {manifest['run_id']}; no feature completion implied")


if __name__ == "__main__":
    main()
