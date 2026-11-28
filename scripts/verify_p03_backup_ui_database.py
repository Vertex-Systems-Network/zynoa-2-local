"""Independent read-only native encrypted backup and restored profile comparison."""
import argparse, hashlib, json, os, sqlite3
from contextlib import closing
from pathlib import Path
def sha(raw):return hashlib.sha256(raw).hexdigest()
def digest(rows):return sha(json.dumps(rows,ensure_ascii=False,separators=(",",":")).encode("utf-8"))
def db_state(root):
    with closing(sqlite3.connect((root/"data"/"state.sqlite").as_uri()+"?mode=ro",uri=True,timeout=2)) as db:
        assert db.execute("PRAGMA user_version").fetchone()==(4,)
        assert db.execute("PRAGMA integrity_check").fetchone()==("ok",)
        assert db.execute("PRAGMA foreign_key_check").fetchall()==[]
        queries=[
            "SELECT id,title,revision,created_at,updated_at FROM conversations ORDER BY id",
            "SELECT id,conversation_id,parent_id,ordinal,role,content,status,revision,created_at FROM messages ORDER BY id",
            "SELECT id,class,payload,revision,created_at FROM records ORDER BY id",
            "SELECT seq,entity_type,entity_id,revision,operation,persisted_at FROM chat_change_journal ORDER BY seq",
            "SELECT id,conversation_id,name,sha256,bytes,created_at FROM managed_artifacts ORDER BY id",
            "SELECT conversation_id,message_id,artifact_id,position FROM artifact_links ORDER BY conversation_id,message_id,position",
            "SELECT request_id,conversation_id,turn_id,target_id,target_sha256,tool,decision,recorded_at FROM tool_review_decisions ORDER BY request_id",
            "SELECT * FROM schema_migrations ORDER BY version",
            "SELECT * FROM artifact_schema_migrations ORDER BY version",
            "SELECT * FROM tool_review_schema_migrations ORDER BY version"]
        return [db.execute(q).fetchall() for q in queries]
def file_state(root,rows):
    result={}
    for a in rows[4]:
        h,size=a[3:5]
        path=root/"data"/"artifacts"/"sha256"/h[:2]/h
        assert path.is_file() and not path.is_symlink()
        data=path.read_bytes()
        assert len(data)==size and sha(data)==h
        result["blob:"+h]=h
    exports=root/"data"/"exports"
    if exports.exists():
        for path in sorted(exports.glob("conversation-*.json")):
            assert path.is_file() and not path.is_symlink()
            result["export:"+path.name]=sha(path.read_bytes())
    return result
def main():
    assert os.environ.get("GITHUB_ACTIONS")=="true"
    p=argparse.ArgumentParser()
    p.add_argument("--stage",choices=("baseline","saved","wrong","restored"),required=True)
    p.add_argument("--output",type=Path,required=True)
    p.add_argument("--export-proof",type=Path,required=True)
    args=p.parse_args()
    prior=json.loads((args.export_proof/"p03-export-db-reopened.json").read_text(encoding="utf-8"))
    root=Path(os.environ["LOCALAPPDATA"])/"com.zynoa.desktop"
    rows=db_state(root);files=file_state(root,rows)
    assert digest(rows[:6])==prior["fingerprint"] and digest(rows[6])==prior["review_fingerprint"]
    assert files["export:"+Path(prior["relative_path"]).name]==prior["sha256"]
    fingerprint=digest([rows,files])
    archive_dir=root/"backups"/"portable"
    restore_dir=root/"backups"/"restored"
    archives=list(archive_dir.glob("*.awbackup")) if archive_dir.exists() else []
    restored=list(restore_dir.iterdir()) if restore_dir.exists() else []
    base={"fingerprint":fingerprint,"file_hashes":files}
    if args.stage=="baseline":
        assert not archives and not restored
        proof=base
    else:
        assert json.loads((args.output/"p03-backup-db-baseline.json").read_text(encoding="utf-8"))==base
        assert len(archives)==1 and archives[0].is_file() and not archives[0].is_symlink()
        archive=archives[0].read_bytes()
        assert archive[:8]==b"ZYNAWB01" and len(archive)==44+16+int.from_bytes(archive[36:44],"little")
        assert len(archive)<=64*1024*1024+60
        assert b"SQLite format 3" not in archive and b"Reply with a short greeting." not in archive
        receipt={"backup_id":archives[0].stem,"sha256":sha(archive),"bytes":len(archive),"fingerprint":fingerprint}
        if args.stage=="saved":
            assert not restored
            proof=receipt
        else:
            assert json.loads((args.output/"p03-backup-db-saved.json").read_text(encoding="utf-8"))==receipt
            if args.stage=="wrong":
                assert not restored
                proof={**receipt,"wrong_key_created_no_profile":True}
            else:
                assert len(restored)==1 and restored[0].is_dir() and not restored[0].is_symlink()
                marker=json.loads((restored[0]/"verified.json").read_text(encoding="utf-8"))
                profile=restored[0]/"com.zynoa.desktop"
                assert marker["backupId"]==receipt["backup_id"] and marker["activeProfileChanged"] is False
                assert marker["restoreId"]==restored[0].name
                assert marker["relativePath"]=="backups/restored/"+restored[0].name+"/com.zynoa.desktop"
                assert marker["conversationCount"]==len(rows[0])
                assert marker["itemCount"]==1+len(files)
                assert db_state(profile)==rows and file_state(profile,rows)==files
                proof={**receipt,"relative_path":marker["relativePath"],"active_profile_unchanged":True,"independent_restored_fingerprint":fingerprint,"synthetic_only":True}
    with (args.output/("p03-backup-db-"+args.stage+".json")).open("x",encoding="utf-8") as out:json.dump(proof,out,indent=2)
    print(json.dumps(proof))
if __name__=="__main__":main()
