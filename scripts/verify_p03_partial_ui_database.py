"""Independent read-only proof of actual native Stop after nonempty real-model output."""
import argparse
import hashlib
import json
import os
import sqlite3
from contextlib import closing
from pathlib import Path

TITLE = "P03 partial persistence"
PROMPT = "List the numbers from one to one thousand in words. Use one line for every number. Do not summarize or stop early."

def digest(value):
    return hashlib.sha256(json.dumps(value, ensure_ascii=False, separators=(",", ":")).encode()).hexdigest()

def main():
    assert os.environ.get("GITHUB_ACTIONS") == "true"
    parser = argparse.ArgumentParser()
    parser.add_argument("--stage", choices=("baseline", "saved", "reopened"), required=True)
    parser.add_argument("--output", type=Path, required=True)
    parser.add_argument("--prior", type=Path, required=True)
    args = parser.parse_args()
    previous = json.loads((args.prior / "p03-model-db-reopened.json").read_text(encoding="utf-8"))
    assert previous["thread_count"] == 3 and previous["message_count"] == 5 and previous["settings_count"] == 2
    path = Path(os.environ["LOCALAPPDATA"]) / "com.zynoa.desktop" / "data" / "state.sqlite"
    assert path.is_file()
    with closing(sqlite3.connect(path.as_uri() + "?mode=ro", uri=True, timeout=2)) as db:
        assert db.execute("PRAGMA user_version").fetchone() == (3,)
        assert db.execute("PRAGMA integrity_check").fetchone() == ("ok",)
        assert db.execute("PRAGMA foreign_key_check").fetchall() == []
        threads = db.execute("SELECT id,title,revision FROM conversations ORDER BY id").fetchall()
        messages = db.execute("SELECT id,conversation_id,parent_id,ordinal,role,content,status,revision FROM messages ORDER BY id").fetchall()
        records = db.execute("SELECT id,class,payload,revision FROM records ORDER BY id").fetchall()
        journal = db.execute("SELECT entity_type,entity_id,revision,operation FROM chat_change_journal ORDER BY seq").fetchall()
        assert db.execute("SELECT count(*) FROM managed_artifacts").fetchone() == (0,)
        assert db.execute("SELECT count(*) FROM artifact_links").fetchone() == (0,)
    target = [t for t in threads if t[1] == TITLE]
    ids = {t[0] for t in target}
    target_messages = [m for m in messages if m[1] in ids]
    entities = ids | {m[0] for m in target_messages}
    prior = [[t for t in threads if t[0] not in ids],
             [m for m in messages if m[1] not in ids],
             [r for r in records if r[0] not in ids],
             [j for j in journal if j[1] not in entities]]
    assert [len(prior[i]) for i in range(3)] == [3, 5, 2]
    assert digest(prior) == previous["fingerprint"], "previous real chat/model fixture changed"
    if args.stage == "baseline":
        assert not target and not target_messages
        print(json.dumps({"baseline": True}))
        return
    assert len(target) == 1 and len(target_messages) == 2
    tid, _, revision = target[0]
    assert revision == 3
    user, assistant = sorted(target_messages, key=lambda m: m[3])
    assert user[2:] == (None, 1, "user", PROMPT, "complete", 1)
    assert assistant[0] != user[0]
    assert assistant[2:5] == (user[0], 2, "assistant")
    assert assistant[6:] == ("cancelled", 1), "real Stop did not persist cancelled status"
    partial = assistant[5]
    assert partial.strip() and len(partial.encode("utf-8")) <= 262144
    settings = [r for r in records if r[0] == tid]
    assert len(settings) == 1 and settings[0][1] == "preference"
    config = json.loads(settings[0][2])
    assert config["model"] == "qwen2.5:1.5b" and config["context_limit"] == 8192
    assert config["revision"] == settings[0][3]
    assert [j for j in journal if j[1] in entities] == [
        ("conversation", tid, 1, "insert"),
        ("message", user[0], 1, "insert"),
        ("conversation", tid, 2, "message_added"),
        ("message", assistant[0], 1, "insert"),
        ("conversation", tid, 3, "message_added")]
    proof = {"prior_fingerprint": previous["fingerprint"],
             "fingerprint": digest([threads, messages, records, journal]),
             "thread_id": tid, "user_id": user[0], "assistant_id": assistant[0],
             "assistant_status": "cancelled", "partial_bytes": len(partial.encode("utf-8")),
             "partial_sha256": hashlib.sha256(partial.encode("utf-8")).hexdigest(),
             "thread_count": 4, "message_count": 7, "settings_count": 3,
             "integrity": "ok", "foreign_keys": "ok", "synthetic_only": True}
    saved = args.output / "p03-partial-db-saved.json"
    if args.stage == "saved":
        with saved.open("x", encoding="utf-8") as stream:
            json.dump(proof, stream, indent=2)
        # Synthetic text passed only to the native probe's in-process comparison.
        print(json.dumps({"assistant_text": partial}, ensure_ascii=True))
    else:
        assert json.loads(saved.read_text(encoding="utf-8")) == proof
        with (args.output / "p03-partial-db-reopened.json").open("x", encoding="utf-8") as stream:
            json.dump(proof, stream, indent=2)
        print(json.dumps(proof))

if __name__ == "__main__":
    main()
