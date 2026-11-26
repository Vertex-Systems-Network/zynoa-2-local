"""Independent read-only checks for the synthetic real-model UI journey."""
import argparse
import hashlib
import json
import os
import sqlite3
from contextlib import closing
from pathlib import Path

BASELINE = "P03 synthetic conversation"
CASES = {
    "P03 model alpha": ("qwen2.5:0.5b", 512, "Reply with a short greeting."),
    "P03 model beta": ("qwen2.5:1.5b", 2048, "Say hello in three words."),
}


def main():
    assert os.environ.get("GITHUB_ACTIONS") == "true"
    parser = argparse.ArgumentParser()
    parser.add_argument("--stage", choices=["baseline", "settings", "turn", "saved", "reopened"], required=True)
    parser.add_argument("--output", type=Path, required=True)
    parser.add_argument("--title", default="")
    parser.add_argument("--model", default="")
    parser.add_argument("--budget", type=int, default=0)
    args = parser.parse_args()
    path = Path(os.environ["LOCALAPPDATA"]) / "com.zynoa.desktop" / "data" / "state.sqlite"
    assert path.is_file()
    with closing(sqlite3.connect(path.as_uri() + "?mode=ro", uri=True, timeout=2)) as db:
        assert db.execute("PRAGMA integrity_check").fetchone() == ("ok",)
        assert db.execute("PRAGMA foreign_key_check").fetchall() == []
        assert db.execute("PRAGMA user_version").fetchone() == (3,)
        threads = db.execute("SELECT id,title,revision FROM conversations ORDER BY id").fetchall()
        messages = db.execute("SELECT id,conversation_id,parent_id,ordinal,role,content,status,revision FROM messages ORDER BY id").fetchall()
        records = db.execute("SELECT id,class,payload,revision FROM records ORDER BY id").fetchall()
        journal = db.execute("SELECT entity_type,entity_id,revision,operation FROM chat_change_journal ORDER BY seq").fetchall()
    assert len({title for _, title, _ in threads}) == len(threads)
    by_title = {title: (tid, revision) for tid, title, revision in threads}
    assert BASELINE in by_title
    baseline_id, baseline_revision = by_title[BASELINE]
    baseline_messages = [m for m in messages if m[1] == baseline_id]
    assert baseline_revision == 2 and len(baseline_messages) == 1
    assert baseline_messages[0][2:] == (None, 1, "user", "P03 synthetic persisted message", "complete", 1)
    assert set(by_title) <= {BASELINE, *CASES}
    settings = {}
    for tid, kind, payload, revision in records:
        assert kind == "preference" and tid in {v[0] for v in by_title.values()}
        data = json.loads(payload)
        assert set(data) == {"model", "context_limit", "revision"}
        assert data["revision"] == revision
        settings[tid] = data
    assert baseline_id not in settings

    def check_settings(title, model, budget):
        tid, _ = by_title[title]
        assert tid in settings, 'expected model preference not committed'
        data = settings[tid]
        assert data["model"] == model and data["context_limit"] == budget
        assert data["revision"] >= 1
        return tid

    def check_turn(title):
        model, budget, prompt = CASES[title]
        tid = check_settings(title, model, budget)
        rows = sorted((m for m in messages if m[1] == tid), key=lambda m: m[3])
        assert len(rows) == 2
        user, assistant = rows
        assert user[2:] == (None, 1, "user", prompt, "complete", 1)
        assert assistant[2:5] == (user[0], 2, "assistant")
        assert assistant[6:] == ("complete", 1)
        assert assistant[5].strip()
        return assistant[5]

    if args.stage == "baseline":
        assert set(by_title) == {BASELINE} and len(messages) == 1 and not records
        # Bind this journey to the previously accepted T03 fixture, not a reset.
        assert journal == [("conversation", baseline_id, 1, "insert"),
                           ("message", baseline_messages[0][0], 1, "insert"),
                           ("conversation", baseline_id, 2, "message_added")]
        print(json.dumps({"baseline": True}))
    elif args.stage == "settings":
        assert args.title in CASES
        check_settings(args.title, args.model, args.budget)
        print(json.dumps({"settings_match": True}))
    elif args.stage == "turn":
        assert args.title in CASES
        # Text is passed only to the in-process UIA comparison; not written to proof.
        print(json.dumps({"assistant_text": check_turn(args.title)}, ensure_ascii=True))
    else:
        assert set(by_title) == {BASELINE, *CASES} and len(messages) == 5 and len(records) == 2
        for title in CASES:
            check_turn(title)
        fingerprint = hashlib.sha256(json.dumps([threads, messages, records, journal],
            ensure_ascii=False, separators=(",", ":")).encode()).hexdigest()
        proof = {"fingerprint": fingerprint, "thread_count": 3, "message_count": 5,
                 "settings_count": 2, "integrity": "ok", "foreign_keys": "ok",
                 "synthetic_only": True}
        saved = args.output / "p03-model-db-saved.json"
        if args.stage == "saved":
            with saved.open("x", encoding="utf-8") as stream:
                json.dump(proof, stream, indent=2)
        else:
            assert json.loads(saved.read_text(encoding="utf-8")) == proof
            with (args.output / "p03-model-db-reopened.json").open("x", encoding="utf-8") as stream:
                json.dump(proof, stream, indent=2)
        print(json.dumps(proof))


if __name__ == "__main__":
    main()
