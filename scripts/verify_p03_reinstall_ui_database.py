"""Read-only exact-state checks at every T13 synthetic desktop recovery boundary."""
import argparse
import json
import os
from pathlib import Path
from verify_p03_backup_ui_database import db_state, file_state, digest, sha

def main():
    assert os.environ.get("GITHUB_ACTIONS") == "true"
    assert os.environ.get("RUNNER_ENVIRONMENT") == "github-hosted"
    p = argparse.ArgumentParser()
    p.add_argument("--stage", choices=("baseline", "crashed", "restarted", "uninstalled", "reinstalled"), required=True)
    p.add_argument("--output", type=Path, required=True)
    p.add_argument("--backup-proof", type=Path, required=True)
    a = p.parse_args()
    prior = json.loads((a.backup_proof / "p03-backup-db-restored.json").read_text(encoding="utf-8"))
    root = Path(os.environ["LOCALAPPDATA"]) / "com.zynoa.desktop"
    rows = db_state(root)
    files = file_state(root, rows)
    fingerprint = digest([rows, files])
    assert prior["synthetic_only"] is True and prior["active_profile_unchanged"] is True
    assert fingerprint == prior["fingerprint"] == prior["independent_restored_fingerprint"]
    archive = root / "backups" / "portable" / (prior["backup_id"] + ".awbackup")
    assert archive.is_file() and not archive.is_symlink()
    assert sha(archive.read_bytes()) == prior["sha256"]
    restored = root / prior["relative_path"]
    assert db_state(restored) == rows and file_state(restored, rows) == files
    marker = restored.parent / "verified.json"
    assert marker.is_file() and not marker.is_symlink()
    stages = list((root / "data" / "artifacts" / "sha256").glob("*/.stage-1-2-3"))
    assert len(stages) == 1 and stages[0].is_file() and not stages[0].is_symlink()
    assert stages[0].read_bytes() == b"synthetic interrupted stage"
    proof = {"fingerprint": fingerprint, "backup_sha256": prior["sha256"],
             "restore_marker_sha256": sha(marker.read_bytes()),
             "interrupted_stage_sha256": sha(stages[0].read_bytes()), "file_hashes": files,
             "conversation_count": len(rows[0]), "message_count": len(rows[1]),
             "synthetic_only": True}
    if a.stage != "baseline":
        assert json.loads((a.output / "p03-reinstall-db-baseline.json").read_text(encoding="utf-8")) == proof
    with (a.output / ("p03-reinstall-db-" + a.stage + ".json")).open("x", encoding="utf-8") as out:
        json.dump(proof, out, indent=2)
    print(json.dumps(proof))

if __name__ == "__main__":
    main()
