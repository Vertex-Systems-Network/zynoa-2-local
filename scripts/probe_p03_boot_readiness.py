"""Read-only readiness check for the disposable native Windows CI process.

This is a readiness predicate, not acceptance evidence. The separate native
audit validation still checks integrity, version, WAL and zero fabricated events.
"""
import argparse
from contextlib import closing
from pathlib import Path
import sqlite3


def ledger_ready(path: Path) -> bool:
    if not path.is_file():
        return False
    try:
        uri = path.resolve().as_uri() + "?mode=ro"
        with closing(sqlite3.connect(uri, uri=True, timeout=0.2)) as db:
            version = db.execute("PRAGMA user_version").fetchone()[0]
            mode = db.execute("PRAGMA journal_mode").fetchone()[0]
            objects = set(db.execute(
                "SELECT type, name FROM sqlite_master WHERE tbl_name='audit_events'"
            ))
            return version == 1 and mode.lower() == "wal" and {
                ("table", "audit_events"),
                ("trigger", "audit_events_no_update"),
                ("trigger", "audit_events_no_delete"),
            } <= objects
    except (OSError, sqlite3.Error):
        # A native bootstrap transaction may still be in progress.
        # The caller has a fixed deadline; no writes or initialization here.
        return False


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("ledger", type=Path)
    args = parser.parse_args()
    print("ready" if ledger_ready(args.ledger) else "pending")


if __name__ == "__main__":
    main()
