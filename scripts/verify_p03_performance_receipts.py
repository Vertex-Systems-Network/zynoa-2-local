"""Collect measured native UI latency; not hardware-tier certification."""
import argparse
import hashlib
import json
import platform
import re
from pathlib import Path

EARLY = (
    ("chat", "chat", ("ui_create_save", "database_reopen_identity_verified"),
     ("save_to_acknowledgement_ms",)),
    ("partial", "partial", ("actual_native_stop", "nonempty_live_prefix_verified",
                            "database_reopen_identity_verified"),
     ("send_to_visible_prefix_ms", "stop_to_cancel_notice_ms")),
    ("partial", "retry", ("actual_native_retry", "retry_recovered_after_restart",
                         "database_reopen_identity_verified"),
     ("retry_to_saved_notice_ms",)),
)
INSTALLED = ("reinstall", "reinstall", ("actual_uninstall_reinstall", "active_history_preserved"),
             ("installed_startup_ms", "reinstalled_startup_ms"))

def require(value, reason):
    if not value:
        raise ValueError(reason)

def collect(root, source, executable, include_installed=False):
    require(re.fullmatch(r"[a-f0-9]{40}", source), "invalid source SHA")
    with executable.open("rb") as f:
        binary = hashlib.file_digest(f, "sha256").hexdigest()
    metrics = {}
    receipts = {}
    for folder, name, flags, keys in EARLY + ((INSTALLED,) if include_installed else ()):
        path = root / ("p03-" + folder + "-ui-proof") / ("p03-" + name + "-ui-proof.json")
        require(path.is_file() and not path.is_symlink(), "missing native timing receipt: " + name)
        raw = path.read_bytes()
        row = json.loads(raw.decode("utf-8-sig"))
        require(row.get("schema_version") == 1 and row.get("synthetic_only") is True,
                "unexpected fixture scope: " + name)
        require(row.get("source_commit_sha") == source and row.get("executable_sha256") == binary,
                "wrong source or executable: " + name)
        require(all(row.get(flag) is True for flag in flags), "unverified journey: " + name)
        for key in keys:
            value = row.get(key)
            require(type(value) is int and value >= 0, "invalid measured duration: " + key)
            metrics[key] = value
        if name == "partial":
            require(row.get("actual_model") == "qwen2.5:1.5b"
                    and type(row.get("live_prefix_chars")) is int and row["live_prefix_chars"] >= 12,
                    "unexpected streaming measurement scope")
        if name == "retry":
            require(row.get("actual_model") == "qwen2.5:1.5b", "unexpected retry model")
        if name == "reinstall":
            budget = row.get("startup_budget_ms")
            require(type(budget) is int and budget == 15000, "unexpected existing startup budget")
            observed = all(metrics[k] <= budget for k in keys)
            require(row.get("startup_within_budget") is observed, "inconsistent startup receipt")
            metrics["startup_budget_ms"] = budget
            metrics["startup_within_budget"] = observed
        receipts[name] = hashlib.sha256(raw).hexdigest()
    return {"schema_version": 1, "source_commit_sha": source, "executable_sha256": binary,
            "scope": "single-hosted-runner-native-observations",
            "os": platform.system(), "os_release": platform.release(), "architecture": platform.machine(),
            "metrics": metrics, "receipt_sha256": receipts,
            "model": "qwen2.5:1.5b", "synthetic_only": True,
            "visible_prefix_is_exact_ttft": False, "hardware_tier_certified": False,
            "full_performance_accepted": False}

def main():
    p = argparse.ArgumentParser()
    p.add_argument("--root", type=Path, required=True)
    p.add_argument("--source", required=True)
    p.add_argument("--executable", type=Path, required=True)
    p.add_argument("--output", type=Path, required=True)
    p.add_argument("--include-installed", action="store_true")
    a = p.parse_args()
    report = collect(a.root, a.source, a.executable, a.include_installed)
    with a.output.open("x", encoding="utf-8") as f:
        json.dump(report, f, indent=2)
    print("Measured native UI latency receipts reconciled; full performance acceptance pending.")

if __name__ == "__main__":
    main()
