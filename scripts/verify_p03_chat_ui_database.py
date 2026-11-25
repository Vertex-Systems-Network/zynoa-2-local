"""Read-only synthetic CI vault identity check; never modify the application database."""
import hashlib
import json
import os
import sqlite3
from contextlib import closing
from pathlib import Path

def main():
    assert os.environ.get("GITHUB_ACTIONS") == "true"
    stage=os.environ["ZYNOA_CHAT_PROOF_STAGE"]
    assert stage in {"empty","saved","reopened"}
    output=Path(os.environ["ZYNOA_CHAT_PROOF_DIR"])
    path=Path(os.environ["LOCALAPPDATA"])/"com.zynoa.desktop"/"data"/"state.sqlite"
    assert path.is_file()
    with closing(sqlite3.connect(path.as_uri()+"?mode=ro",uri=True)) as db:
        assert db.execute("PRAGMA integrity_check").fetchone()==("ok",)
        assert db.execute("PRAGMA foreign_key_check").fetchall()==[]
        assert db.execute("PRAGMA user_version").fetchone()==(2,)
        threads=db.execute("SELECT id,title,revision FROM conversations ORDER BY id").fetchall()
        messages=db.execute("SELECT id,conversation_id,parent_id,ordinal,role,content,status,revision FROM messages ORDER BY id").fetchall()
        journal=db.execute("SELECT entity_type,entity_id,revision,operation FROM chat_change_journal ORDER BY seq").fetchall()
        assert db.execute("SELECT count(*) FROM records").fetchone()==(0,)
    if stage=="empty":
        assert not threads and not messages and not journal
        return
    assert len(threads)==len(messages)==1 and len(journal)==3
    tid,title,revision=threads[0]
    mid,cid,parent,ordinal,role,content,status,mrev=messages[0]
    assert title=="P03 synthetic conversation" and revision==2
    assert (cid,parent,ordinal,role,content,status,mrev)==(tid,None,1,"user","P03 synthetic persisted message","complete",1)
    assert journal==[("conversation",tid,1,"insert"),("message",mid,1,"insert"),("conversation",tid,2,"message_added")]
    fingerprint=hashlib.sha256(json.dumps([threads,messages,journal],ensure_ascii=False,separators=(",",":")).encode()).hexdigest()
    result={"thread_id":tid,"message_id":mid,"fingerprint":fingerprint,"integrity":"ok","foreign_keys":"ok","synthetic_only":True}
    saved=output/"p03-chat-db-saved.json"
    if stage=="saved":
        with saved.open("x",encoding="utf-8") as stream: json.dump(result,stream,indent=2)
    else:
        assert json.loads(saved.read_text(encoding="utf-8"))==result
        with (output/"p03-chat-db-reopened.json").open("x",encoding="utf-8") as stream: json.dump(result,stream,indent=2)
    print("P03 read-only synthetic database verification:",stage)

if __name__=="__main__":
    main()
