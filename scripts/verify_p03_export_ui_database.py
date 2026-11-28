"""Read-only native full conversation export verification; synthetic disposable CI only."""
import argparse, hashlib, json, os, sqlite3
from contextlib import closing
from pathlib import Path

def sha(data):
    return hashlib.sha256(data).hexdigest()

def digest(rows):
    return sha(json.dumps(rows, ensure_ascii=False, separators=(",", ":")).encode("utf-8"))

def main():
    assert os.environ.get("GITHUB_ACTIONS")=="true"
    p=argparse.ArgumentParser()
    p.add_argument("--stage",choices=("baseline","saved","reopened"),required=True)
    p.add_argument("--output",type=Path,required=True)
    p.add_argument("--review-proof",type=Path,required=True)
    args=p.parse_args()
    prior=json.loads((args.review_proof/"p03-review-db-reopened.json").read_text(encoding="utf-8"))
    root=Path(os.environ["LOCALAPPDATA"])/"com.zynoa.desktop"/"data"
    with closing(sqlite3.connect((root/"state.sqlite").as_uri()+"?mode=ro",uri=True,timeout=2)) as db:
        assert db.execute("PRAGMA user_version").fetchone()==(4,)
        assert db.execute("PRAGMA integrity_check").fetchone()==("ok",)
        assert db.execute("PRAGMA foreign_key_check").fetchall()==[]
        threads=db.execute("SELECT id,title,revision,created_at,updated_at FROM conversations ORDER BY id").fetchall()
        messages=db.execute("SELECT id,conversation_id,parent_id,ordinal,role,content,status,revision,created_at FROM messages ORDER BY id").fetchall()
        records=db.execute("SELECT id,class,payload,revision,created_at FROM records ORDER BY id").fetchall()
        journal=db.execute("SELECT seq,entity_type,entity_id,revision,operation,persisted_at FROM chat_change_journal ORDER BY seq").fetchall()
        artifacts=db.execute("SELECT id,conversation_id,name,sha256,bytes,created_at FROM managed_artifacts ORDER BY id").fetchall()
        links=db.execute("SELECT conversation_id,message_id,artifact_id,position FROM artifact_links ORDER BY conversation_id,message_id,position").fetchall()
        reviews=db.execute("SELECT request_id,conversation_id,turn_id,target_id,target_sha256,tool,decision,recorded_at FROM tool_review_decisions ORDER BY request_id").fetchall()
    fp=digest([threads,messages,records,journal,artifacts,links])
    assert fp==prior["fingerprint"]
    assert [list(row) for row in reviews]==prior["reviews"]
    directory=root/"exports"
    files=list(directory.glob("conversation-*.json")) if directory.exists() else []
    if args.stage=="baseline":
        assert not files
        proof={"fingerprint":fp,"review_fingerprint":digest(reviews)}
    else:
        assert len(files)==1 and files[0].is_file() and not files[0].is_symlink()
        raw=files[0].read_bytes()
        assert len(raw)<=32*1024*1024
        doc=json.loads(raw)
        assert set(doc)=={"schemaVersion","kind","conversation","messages"}
        assert doc["schemaVersion"]==1 and doc["kind"]=="zynoa-conversation-export"
        selected=[row for row in threads if row[1]=="P03 attachment proof"]
        assert len(selected)==1
        cid,title,revision,created,updated=selected[0]
        assert doc["conversation"]=={"id":cid,"title":title,"revision":revision,"createdAt":created,"updatedAt":updated}
        expected=sorted([m for m in messages if m[1]==cid],key=lambda m:m[3])
        assert len(doc["messages"])==len(expected)
        count=0
        for row,msg in zip(expected,doc["messages"]):
            mid,_,parent,ordinal,role,content,status,rev,stamp=row
            assert {k:v for k,v in msg.items() if k!="attachments"}=={"id":mid,"parentId":parent,"ordinal":ordinal,"role":role,"content":content,"contentSha256":sha(content.encode("utf-8")),"status":status,"revision":rev,"createdAt":stamp}
            linked=sorted([l for l in links if l[:2]==(cid,mid)],key=lambda l:l[3])
            assert len(msg["attachments"])==len(linked)
            for link,item in zip(linked,msg["attachments"]):
                aid,_,name,h,size,_=next(a for a in artifacts if a[0]==link[2] and a[1]==cid)
                assert set(item)=={"id","name","bytes","sha256","dataHex"}
                assert (item["id"],item["name"],item["sha256"],item["bytes"])==(aid,name,h,size)
                data=bytes.fromhex(item["dataHex"])
                assert len(data)==size and sha(data)==h
                assert data==(root/"artifacts"/"sha256"/h[:2]/h).read_bytes()
                count+=1
        assert count==1
        proof={"fingerprint":fp,"review_fingerprint":digest(reviews),"relative_path":"data/exports/"+files[0].name,"sha256":sha(raw),"bytes":len(raw),"message_count":len(expected),"attachment_count":count,"synthetic_only":True}
        if args.stage=="reopened":
            assert json.loads((args.output/"p03-export-db-saved.json").read_text(encoding="utf-8"))==proof
    with (args.output/("p03-export-db-"+args.stage+".json")).open("x",encoding="utf-8") as out:
        json.dump(proof,out,indent=2)
    print(json.dumps(proof))

if __name__=="__main__":
    main()
