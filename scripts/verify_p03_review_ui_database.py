"""Read-only proof of native review decisions and a single scoped artifact write."""
import argparse, hashlib, json, os, sqlite3
from contextlib import closing
from pathlib import Path

def sha(data):
    return hashlib.sha256(data).hexdigest()

def digest(rows):
    return sha(json.dumps(rows, ensure_ascii=False, separators=(",", ":")).encode("utf-8"))

def derive(domain, cid, source):
    return sha((domain+"\0"+cid+"\0"+source).encode("utf-8"))

def read_json(path):
    return json.loads(path.read_text(encoding="utf-8"))

def write_json(path, value):
    with path.open("x", encoding="utf-8") as out:
        json.dump(value, out, indent=2)

def main():
    assert os.environ.get("GITHUB_ACTIONS") == "true"
    p = argparse.ArgumentParser()
    p.add_argument("--stage", choices=("baseline", "denied", "approved", "reopened"), required=True)
    p.add_argument("--output", type=Path, required=True)
    p.add_argument("--artifact-proof", type=Path, required=True)
    args = p.parse_args()
    prior = read_json(args.artifact_proof / "p03-text-artifact-db-replayed.json")
    root = Path(os.environ["LOCALAPPDATA"]) / "com.zynoa.desktop" / "data"
    path = root / "state.sqlite"
    assert path.is_file()
    with closing(sqlite3.connect(path.as_uri()+"?mode=ro", uri=True, timeout=2)) as db:
        assert db.execute("PRAGMA user_version").fetchone() == (4,)
        assert db.execute("PRAGMA integrity_check").fetchone() == ("ok",)
        assert db.execute("PRAGMA foreign_key_check").fetchall() == []
        threads = db.execute("SELECT id,title,revision,created_at,updated_at FROM conversations ORDER BY id").fetchall()
        messages = db.execute("SELECT id,conversation_id,parent_id,ordinal,role,content,status,revision,created_at FROM messages ORDER BY id").fetchall()
        records = db.execute("SELECT id,class,payload,revision,created_at FROM records ORDER BY id").fetchall()
        journal = db.execute("SELECT seq,entity_type,entity_id,revision,operation,persisted_at FROM chat_change_journal ORDER BY seq").fetchall()
        artifacts = db.execute("SELECT id,conversation_id,name,sha256,bytes,created_at FROM managed_artifacts ORDER BY id").fetchall()
        links = db.execute("SELECT conversation_id,message_id,artifact_id,position FROM artifact_links ORDER BY conversation_id,message_id,position").fetchall()
        reviews = db.execute("SELECT request_id,conversation_id,turn_id,target_id,target_sha256,tool,decision,recorded_at FROM tool_review_decisions ORDER BY request_id").fetchall()
    beta = [t for t in threads if t[1] == "P03 model beta"]
    assert len(beta) == 1
    cid, title, rev, created, updated = beta[0]
    history = sorted([m for m in messages if m[1] == cid], key=lambda m:m[3])
    user, source = history[:2]
    assert user[2:5] == (None,1,"user") and source[2:5] == (user[0],2,"assistant") and source[6:8] == ("complete",1)
    content = source[5].encode("utf-8")
    assert content and source[5].strip()
    mid = derive("zynoa-text-artifact-message-v1",cid,source[0])
    aid = derive("zynoa-text-artifact-file-v1",cid,source[0])
    h = sha(content)
    attachment_threads = [t for t in threads if t[1]=="P03 attachment proof"]
    assert len(attachment_threads)==1
    attachment_cid=attachment_threads[0][0]
    attached=[a for a in artifacts if a[1]==attachment_cid and a[2]=="p03-attachment-fixture.bin"]
    assert len(attached)==1 and attached[0][4]==70000
    for row in reviews:
        assert len(row[0]) == 64 and all(c in "0123456789abcdef" for c in row[0])
        if row[5]=="local.write_artifact":
            assert row[1:6] == (cid,row[0],aid,h,"local.write_artifact")
            assert row[6] in ("approve","deny")
        else:
            assert row[1:7] == (attachment_cid,row[0],attached[0][0],attached[0][3],"local.read_attachment","approve")
        assert row[7] > 0
    fingerprint = digest([threads,messages,records,journal,artifacts,links])
    base_path = args.output / "p03-review-baseline.json"
    if args.stage == "baseline":
        assert not reviews and len(history) == 2 and fingerprint == prior["fingerprint"]
        assert not any(a[0] == aid for a in artifacts)
        proof = {"fingerprint":fingerprint,"conversation_id":cid,"source_id":source[0],"revision":rev,"updated_at":updated,"target_id":aid,"sha256":h}
        write_json(base_path,proof)
        print(json.dumps(proof))
        return
    baseline = read_json(base_path)
    assert (cid,source[0],aid,h) == (baseline["conversation_id"],baseline["source_id"],baseline["target_id"],baseline["sha256"])
    denied_path = args.output / "p03-review-db-denied.json"
    if args.stage == "denied":
        assert len(reviews) == 1 and reviews[0][6] == "deny"
        assert len(history) == 2 and fingerprint == baseline["fingerprint"] == prior["fingerprint"]
        assert not any(a[0] == aid for a in artifacts)
        proof = {"fingerprint":fingerprint,"review":list(reviews[0]),"executed":False,"synthetic_only":True}
        write_json(denied_path,proof)
        print(json.dumps(proof))
        return
    denied = read_json(denied_path)
    assert len(reviews) == 3 and list(next(r for r in reviews if r[6]=="deny")) == denied["review"]
    assert sum(r[5]=="local.write_artifact" and r[6]=="approve" for r in reviews) == 1
    assert sum(r[5]=="local.read_attachment" and r[6]=="approve" for r in reviews) == 1
    assert len(history) == 3 and rev == baseline["revision"]+1
    assert history[2][:8] == (mid,cid,source[0],3,"system","Saved assistant response as text artifact.","complete",1)
    generated = [a for a in artifacts if a[0] == aid]
    assert len(generated) == 1 and generated[0][:5] == (aid,cid,"assistant-response.txt",h,len(content))
    assert (cid,mid,aid,0) in links
    assert [row[1:5] for row in journal[-2:]] == [("message",mid,1,"insert"),("conversation",cid,rev,"message_added")]
    original = [[(t[0],t[1],baseline["revision"],t[3],baseline["updated_at"]) if t[0]==cid else t for t in threads],
        [m for m in messages if m[0]!=mid],records,journal[:-2],[a for a in artifacts if a[0]!=aid],[l for l in links if l[2]!=aid]]
    assert digest(original) == baseline["fingerprint"] == prior["fingerprint"]
    for artifact in artifacts:
        blob = root/"artifacts"/"sha256"/artifact[3][:2]/artifact[3]
        assert blob.is_file() and not blob.is_symlink()
        data = blob.read_bytes()
        assert len(data)==artifact[4] and sha(data)==artifact[3]
    stage = root/"artifacts"/"sha256"
    stages = list(stage.glob("*/.stage-1-2-3"))
    assert len(stages)==1 and stages[0].read_bytes()==b"synthetic interrupted stage"
    assert sha(stages[0].read_bytes())==prior["stage_sha256"]
    proof = {"fingerprint":fingerprint,"prior_fingerprint":baseline["fingerprint"],"reviews":[list(row) for row in reviews],"artifact_id":aid,"sha256":h,"bytes":len(content),"integrity":"ok","foreign_keys":"ok","synthetic_only":True}
    if args.stage == "reopened":
        assert read_json(args.output/"p03-review-db-approved.json") == proof
    write_json(args.output/("p03-review-db-"+args.stage+".json"),proof)
    print(json.dumps(proof))

if __name__ == "__main__":
    main()
