"""Read-only proof of actual Windows text artifact creation, preview and replay."""
import argparse
import hashlib
import json
import os
import sqlite3
from contextlib import closing
from pathlib import Path

def digest(rows):
    return hashlib.sha256(json.dumps(rows, ensure_ascii=False, separators=(",", ":")).encode("utf-8")).hexdigest()

def sha(data):
    return hashlib.sha256(data).hexdigest()

def derived(domain, cid, source):
    return sha((domain + "\0" + cid + "\0" + source).encode("utf-8"))

def main():
    assert os.environ.get("GITHUB_ACTIONS") == "true"
    parser = argparse.ArgumentParser()
    parser.add_argument("--stage", choices=("baseline", "saved", "reopened", "replayed"), required=True)
    parser.add_argument("--output", type=Path, required=True)
    parser.add_argument("--attachment-proof", type=Path, required=True)
    args = parser.parse_args()
    prior = json.loads((args.attachment_proof / "p03-attachment-recovery-db.json").read_text(encoding="utf-8"))
    prior_attachment = prior["attachment"]
    assert prior["stage_preserved"] is True
    root = Path(os.environ["LOCALAPPDATA"]) / "com.zynoa.desktop" / "data"
    path = root / "state.sqlite"
    assert path.is_file()
    with closing(sqlite3.connect(path.as_uri() + "?mode=ro", uri=True, timeout=2)) as db:
        assert db.execute("PRAGMA user_version").fetchone() == (4,)
        assert db.execute("SELECT count(*) FROM tool_review_decisions").fetchone() == (0,)
        assert db.execute("PRAGMA integrity_check").fetchone() == ("ok",)
        assert db.execute("PRAGMA foreign_key_check").fetchall() == []
        threads = db.execute("SELECT id,title,revision,created_at,updated_at FROM conversations ORDER BY id").fetchall()
        messages = db.execute("SELECT id,conversation_id,parent_id,ordinal,role,content,status,revision,created_at FROM messages ORDER BY id").fetchall()
        records = db.execute("SELECT id,class,payload,revision,created_at FROM records ORDER BY id").fetchall()
        journal = db.execute("SELECT seq,entity_type,entity_id,revision,operation,persisted_at FROM chat_change_journal ORDER BY seq").fetchall()
        artifacts = db.execute("SELECT id,conversation_id,name,sha256,bytes,created_at FROM managed_artifacts ORDER BY id").fetchall()
        links = db.execute("SELECT conversation_id,message_id,artifact_id,position FROM artifact_links ORDER BY conversation_id,message_id,position").fetchall()
    # Preserve the previously accepted attachment and interrupted-stage fixtures.
    old_thread = [t for t in threads if t[0] == prior_attachment["thread_id"]]
    old_messages = [m for m in messages if m[1] == prior_attachment["thread_id"]]
    old_artifacts = [a for a in artifacts if a[1] == prior_attachment["thread_id"]]
    old_links = [l for l in links if l[0] == prior_attachment["thread_id"]]
    assert digest([old_thread, old_messages, old_artifacts, old_links]) == prior_attachment["fingerprint"]
    old_hash = prior_attachment["sha256"]
    assert len(old_hash) == 64 and all(c in "0123456789abcdef" for c in old_hash)
    old_blob = root / "artifacts" / "sha256" / old_hash[:2] / old_hash
    assert old_blob.is_file() and not old_blob.is_symlink()
    assert old_blob.read_bytes() == bytes(i % 251 for i in range(70000))
    stage = old_blob.parent / ".stage-1-2-3"
    assert stage.is_file() and not stage.is_symlink()
    assert stage.read_bytes() == b"synthetic interrupted stage"
    assert sha(stage.read_bytes()) == prior["stage_sha256"]
    alpha = [t for t in threads if t[1] == "P03 model alpha"]
    assert len(alpha) == 1
    cid, title, rev, created, updated = alpha[0]
    history = sorted([m for m in messages if m[1] == cid], key=lambda m:m[3])
    user, source = history[:2]
    assert user[2:5] == (None, 1, "user") and user[5] == "Reply with a short greeting."
    assert user[6:8] == ("complete", 1)
    assert source[2:5] == (user[0], 2, "assistant") and source[6:8] == ("complete", 1)
    data = source[5].encode("utf-8")
    assert 0 < len(data) <= 262144 and source[5].strip()
    mid = derived("zynoa-text-artifact-message-v1", cid, source[0])
    aid = derived("zynoa-text-artifact-file-v1", cid, source[0])
    fingerprint = digest([threads, messages, records, journal, artifacts, links])
    baseline_path = args.output / "p03-text-artifact-baseline.json"
    if args.stage == "baseline":
        assert (len(threads), len(messages), len(records), len(artifacts), len(links)) == (5, 9, 3, 1, 1)
        assert len(history) == 2 and rev == 3
        assert all(m[0] != mid for m in messages) and all(a[0] != aid for a in artifacts)
        baseline = {"fingerprint": fingerprint, "conversation_id":cid, "source_id":source[0],
                    "source_sha256":sha(data), "revision":rev, "updated_at":updated}
        with baseline_path.open("x",encoding="utf-8") as stream:
            json.dump(baseline, stream, indent=2)
        # Synthetic source text is passed in-process to the UI comparison only.
        print(json.dumps({"assistant_text":source[5]}, ensure_ascii=True))
        return
    baseline = json.loads(baseline_path.read_text(encoding="utf-8"))
    assert baseline["conversation_id"] == cid and baseline["source_id"] == source[0]
    assert baseline["source_sha256"] == sha(data)
    assert (len(threads), len(messages), len(records), len(artifacts), len(links)) == (5, 10, 3, 2, 2)
    assert len(history) == 3 and rev == baseline["revision"] + 1
    receipt = history[2]
    assert receipt[:8] == (mid,cid,source[0],3,"system","Saved assistant response as text artifact.","complete",1)
    generated = [a for a in artifacts if a[0] == aid]
    assert len(generated) == 1 and generated[0][:5] == (aid,cid,"assistant-response.txt",sha(data),len(data))
    assert (cid,mid,aid,0) in links
    assert [row[1:5] for row in journal[-2:]] == [("message",mid,1,"insert"),("conversation",cid,rev,"message_added")]
    original_rows = [
        [(t[0],t[1],baseline["revision"],t[3],baseline["updated_at"]) if t[0] == cid else t for t in threads],
        [m for m in messages if m[0] != mid], records, journal[:-2],
        [a for a in artifacts if a[0] != aid], [l for l in links if l[2] != aid],
    ]
    assert digest(original_rows) == baseline["fingerprint"], "previous durable records changed"
    blob = root / "artifacts" / "sha256" / sha(data)[:2] / sha(data)
    assert blob.is_file() and not blob.is_symlink()
    assert blob.read_bytes() == data
    proof = {"fingerprint":fingerprint,"prior_fingerprint":baseline["fingerprint"],
             "conversation_id":cid,"source_id":source[0],"message_id":mid,"artifact_id":aid,
             "sha256":sha(data),"bytes":len(data),"receipt_count":1,"artifact_count":2,
             "message_count":10,"prior_attachment_fingerprint":prior_attachment["fingerprint"],
             "stage_sha256":prior["stage_sha256"],"integrity":"ok","foreign_keys":"ok","synthetic_only":True}
    saved = args.output / "p03-text-artifact-db-saved.json"
    if args.stage != "saved":
        assert json.loads(saved.read_text(encoding="utf-8")) == proof
    out = args.output / ("p03-text-artifact-db-" + args.stage + ".json")
    with out.open("x",encoding="utf-8") as stream:
        json.dump(proof,stream,indent=2)
    print(json.dumps(proof))

if __name__ == "__main__":
    main()
