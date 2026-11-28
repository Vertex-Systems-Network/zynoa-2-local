"""Verify all original P03 native screenshot candidates; not visual acceptance."""
import argparse
import hashlib
import json
import re
import struct
import zlib
from pathlib import Path

# Fixed expected inventory; a missing receipt or image is a failed gate.
EXPECTED = {
    ("chat", "chat"): ("M03-S01-candidate.png", "M03-S02-candidate.png"),
    ("model", "model"): ("M03-OPT-01-candidate.png", "M03-OPT-03-candidate.png", "M03-OPT-02-candidate.png", "M03-S04-candidate.png"),
    ("partial", "partial"): ("M03-OPT-02-stopped-candidate.png", "M03-OPT-02-partial-reopened-candidate.png"),
    ("partial", "retry"): ("M03-OPT-06-retry-ready-candidate.png", "M03-OPT-06-retry-completed-candidate.png", "M03-OPT-06-retry-reopened-candidate.png"),
    ("partial", "model-availability"): ("M03-OPT-01-missing-model-candidate.png", "M03-OPT-01-restored-model-candidate.png"),
    ("attachment", "attachment"): ("M03-S03-candidate.png", "M03-OPT-04-candidate.png", "M03-managed-recovery-candidate.png"),
    ("text-artifact", "text-artifact"): ("M03-OPT-05-candidate.png", "M03-OPT-05-reopened-candidate.png", "M03-OPT-05-replayed-candidate.png"),
    ("review", "review"): ("M03-S05-review-pending-candidate.png", "M03-OPT-08-denied-candidate.png", "M03-OPT-08-approved-candidate.png", "M03-OPT-08-reopened-candidate.png", "M03-OPT-08-attachment-approved-candidate.png", "M03-OPT-08-attachment-reopened-candidate.png"),
    ("export", "export"): ("M03-S06-export-consent-candidate.png", "M03-OPT-07-export-candidate.png"),
    ("backup", "backup"): ("M23-OPT-07-encrypted-backup-candidate.png", "M23-OPT-09-restore-preview-candidate.png"),
    ("reinstall", "reinstall"): ("M23-installed-history-candidate.png", "M23-reinstalled-history-candidate.png"),
}

def require(condition, reason):
    if not condition:
        raise ValueError(reason)

def sha(path):
    with path.open("rb") as f:
        return hashlib.file_digest(f, "sha256").hexdigest()

def png_receipt(path, expected):
    require(path.is_file() and not path.is_symlink(), "missing original PNG")
    require(re.fullmatch(r"[a-f0-9]{64}", expected or ""), "invalid image digest")
    require(sha(path) == expected, "image digest mismatch")
    require(45 <= path.stat().st_size <= 64 * 1024 * 1024, "invalid capture size")
    raw = path.read_bytes()
    require(raw[:8] == b"\x89PNG\r\n\x1a\n", "invalid PNG signature")
    pos = 8
    width = height = 0
    seen_data = seen_end = False
    while pos < len(raw):
        require(pos + 12 <= len(raw), "truncated PNG chunk")
        size = struct.unpack_from(">I", raw, pos)[0]
        end = pos + 12 + size
        require(end <= len(raw), "truncated PNG payload")
        kind = raw[pos+4:pos+8]
        payload = raw[pos+8:end-4]
        crc = struct.unpack_from(">I", raw, end-4)[0]
        require(zlib.crc32(raw[pos+4:end-4]) == crc, "PNG CRC mismatch")
        if pos == 8:
            require(kind == b"IHDR" and size == 13, "invalid PNG header")
            width, height = struct.unpack_from(">II", payload)
            require(800 <= width <= 16384 and 500 <= height <= 16384, "capture dimensions outside bounds")
        else:
            require(kind != b"IHDR", "duplicate PNG header")
        if kind == b"IDAT":
            seen_data = True
        if kind == b"IEND":
            require(size == 0 and seen_data and end == len(raw), "invalid PNG termination")
            seen_end = True
        pos = end
    require(seen_end, "missing PNG termination")
    return {"sha256": expected, "width": width, "height": height}

def verify(root, source, executable):
    require(re.fullmatch(r"[a-f0-9]{40}", source), "invalid source SHA")
    binary = sha(executable)
    entries = {}
    for (directory, receipt), names in EXPECTED.items():
        folder = root / ("p03-" + directory + "-ui-proof")
        proof = folder / ("p03-" + receipt + "-ui-proof.json")
        require(proof.is_file() and not proof.is_symlink(), "missing native proof")
        row = json.loads(proof.read_text(encoding="utf-8-sig"))
        require(row.get("schema_version") == 1 and row.get("synthetic_only") is True, "wrong proof scope")
        require(row.get("source_commit_sha") == source and row.get("executable_sha256") == binary, "source or executable mismatch")
        images = row.get("images")
        require(isinstance(images, dict) and set(images) == set(names), "unexpected screenshot inventory")
        for name in names:
            require(name not in entries, "duplicate screenshot identity")
            entries[name] = {"proof": proof.name, **png_receipt(folder / name, images[name])}
    return {"schema_version": 1, "source_commit_sha": source, "executable_sha256": binary,
            "proof_count": len(EXPECTED), "image_count": len(entries), "images": entries,
            "integrity_verified": True, "visual_review": "pending", "full_accessibility_certified": False,
            "hosted_wiki_verified": False, "synthetic_only": True}

def main():
    p = argparse.ArgumentParser()
    p.add_argument("--root", type=Path, required=True)
    p.add_argument("--source", required=True)
    p.add_argument("--executable", type=Path, required=True)
    p.add_argument("--output", type=Path, required=True)
    a = p.parse_args()
    report = verify(a.root, a.source, a.executable)
    with a.output.open("x", encoding="utf-8") as f:
        json.dump(report, f, indent=2)
    print("P03 native screenshot integrity verified; visual and hosted Wiki review pending")

if __name__ == "__main__":
    main()
