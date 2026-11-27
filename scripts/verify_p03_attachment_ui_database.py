"""Read-only verification of the actual synthetic Windows attachment journey."""
import argparse
import hashlib
import json
import os
import sqlite3
from contextlib import closing
from pathlib import Path

TITLE = "P03 attachment proof"
CONTENT = "P03 synthetic attachment message"
NAME = "p03-attachment-fixture.bin"
FIXTURE = bytes(i % 251 for i in range(70000))
SHA = hashlib.sha256(FIXTURE).hexdigest()

def digest(rows):
    return hashlib.sha256(json.dumps(rows, ensure_ascii=False, separators=(",", ":")).encode()).hexdigest()

def main():
    assert os.environ.get("GITHUB_ACTIONS") == "true"
    parser = argparse.ArgumentParser()
    parser.add_argument("--stage", choices=("baseline", "saved", "reopened"), required=True)
    parser.add_argument("--output", type=Path, required=True)
    args = parser.parse_args()
    root = Path(os.environ["LOCALAPPDATA"]) / "com.zynoa.desktop" / "data"
    path = root / "state.sqlite"
    assert path.is_file()
    with closing(sqlite3.connect(path.as_uri() + "?mode=ro", uri=True, timeout=2)) as db:
        assert db.execute("PRAGMA user_version").fetchone() == (3,)
        assert db.execute("PRAGMA integrity_check").fetchone() == ("ok",)
        assert db.execute("PRAGMA foreign_key_check").fetchall() == []
        threads = db.execute("SELECT id,title,revision,created_at,updated_at FROM conversations ORDER BY id").fetchall()
        messages = db.execute("SELECT id,conversation_id,parent_id,ordinal,role,content,status,revision,created_at FROM messages ORDER BY id").fetchall()
        records = db.execute("SELECT id,class,payload,revision,created_at FROM records ORDER BY id").fetchall()
        journal = db.execute("SELECT seq,entity_type,entity_id,revision,operation,persisted_at FROM chat_change_journal ORDER BY seq").fetchall()
        artifacts = db.execute("SELECT id,conversation_id,name,sha256,bytes,created_at FROM managed_artifacts ORDER BY id").fetchall()
        links = db.execute("SELECT conversation_id,message_id,artifact_id,position FROM artifact_links ORDER BY conversation_id,message_id,position").fetchall()
    target = [t for t in threads if t[1] == TITLE]
    target_ids = {t[0] for t in target}
    target_msgs = [m for m in messages if m[1] in target_ids]
    entity_ids = target_ids | {m[0] for m in target_msgs}
    prior = [ [t for t in threads if t[0] not in target_ids],
              [m for m in messages if m[1] not in target_ids],
              records, [j for j in journal if j[2] not in entity_ids] ]
    assert len(prior[0]) == 3 and len(prior[1]) == 5 and len(records) == 2
    assert {t[1] for t in prior[0]} == {"P03 synthetic conversation","P03 model alpha","P03 model beta"}
    baseline = args.output / "p03-attachment-baseline.json"
    prior_hash = digest(prior)
    if args.stage == "baseline":
        assert not target and not artifacts and not links
        with baseline.open("x", encoding="utf-8") as stream:
            json.dump({"prior_fingerprint":prior_hash}, stream)
        return
    assert json.loads(baseline.read_text(encoding="utf-8")) == {"prior_fingerprint":prior_hash}
    assert len(target) == len(target_msgs) == len(artifacts) == len(links) == 1
    tid, _, revision, *_ = target[0]
    mid, cid, parent, ordinal, role, content, status, mrev, _ = target_msgs[0]
    assert revision == 2 and (cid,parent,ordinal,role,content,status,mrev) == (tid,None,1,"user",CONTENT,"complete",1)
    aid, ac, name, sha, size, _ = artifacts[0]
    assert (ac,name,sha,size) == (tid,NAME,SHA,len(FIXTURE))
    assert links == [(tid,mid,aid,0)]
    assert [(j[1],j[2],j[3],j[4]) for j in journal if j[2] in entity_ids] == [
        ("conversation",tid,1,"insert"),("message",mid,1,"insert"),("conversation",tid,2,"message_added")]
    blob = root / "artifacts" / "sha256" / SHA[:2] / SHA
    assert blob.is_file() and not blob.is_symlink()
    assert blob.read_bytes() == FIXTURE
    assert hashlib.sha256(blob.read_bytes()).hexdigest() == SHA
    proof = {"prior_fingerprint":prior_hash,"fingerprint":digest([target,target_msgs,artifacts,links]),
             "thread_id":tid,"message_id":mid,"artifact_id":aid,"sha256":SHA,"bytes":size,
             "integrity":"ok","foreign_keys":"ok","synthetic_only":True}
    saved = args.output / "p03-attachment-db-saved.json"
    if args.stage == "saved":
        with saved.open("x",encoding="utf-8") as stream: json.dump(proof,stream,indent=2)
    else:
        assert not (Path(os.environ["RUNNER_TEMP"]) / NAME).exists()
        assert json.loads(saved.read_text(encoding="utf-8")) == proof
        with (args.output / "p03-attachment-db-reopened.json").open("x",encoding="utf-8") as stream: json.dump(proof,stream,indent=2)
    print("P03 attachment independent read-only database and blob proof:",args.stage)

if __name__ == "__main__":
    main()
