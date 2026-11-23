"""Fail-closed verifier: three actual Windows Tauri warm-window timing observations."""
from __future__ import annotations
import argparse
import json
import re
from pathlib import Path

SHA40 = re.compile(r"^[0-9a-f]{40}$")
SHA64 = re.compile(r"^[0-9a-f]{64}$")


class InvalidRepeatedNativePerformance(ValueError):
    pass


def require(ok: bool, reason: str) -> None:
    if not ok:
        raise InvalidRepeatedNativePerformance(reason)


def verify(proof: dict, source_sha: str) -> dict:
    require(bool(SHA40.fullmatch(source_sha)), "invalid source SHA")
    require(isinstance(proof, dict) and proof.get("schema_version") == 1, "invalid receipt schema")
    require(proof.get("source_commit_sha") == source_sha, "source SHA mismatch")
    require(proof.get("target") == "Real GitHub Actions Windows Tauri native main-window UIA",
            "not native Windows UIAutomation")
    require(isinstance(proof.get("github_run_id"), str) and
            proof["github_run_id"].isdigit(), "unverified GitHub run")
    require(isinstance(proof.get("executable_sha256"), str) and
            bool(SHA64.fullmatch(proof["executable_sha256"])), "unverified executable SHA256")
    require(proof.get("measurement") ==
            "three sequential warm process launches, visible same-PID HWND and connected native IPC status in UIA",
            "wrong measurement methodology")
    require(proof.get("native_test_environment") == "GitHub-hosted Windows runner",
            "runner not authenticated")
    require(proof.get("performance_budget_approved") is False and
            proof.get("full_screen_reader_verified") is False and
            proof.get("no_user_data") is True, "false budget/a11y/privacy claim")
    samples = proof.get("samples")
    require(proof.get("sample_count") == 3 and isinstance(samples, list) and
            len(samples) == 3, "three original distinct samples are required")
    pids, ms, native_ready = [], [], []
    for i, sample in enumerate(samples, 1):
        require(isinstance(sample, dict) and sample.get("sample_index") == i,
                "sample order or identity invalid")
        pid, duration = sample.get("native_process_id"), sample.get("window_first_visible_ms")
        ready_ms = sample.get("native_handshake_ready_ms")
        require(type(pid) is int and pid > 0, "native PID missing")
        require(type(duration) is int and 0 < duration <= 60000, "native window sample invalid")
        require(type(ready_ms) is int and duration <= ready_ms <= 60000,
                "native IPC handshake timing missing or inconsistent")
        require(sample.get("real_native_ipc_status_in_uia") is True,
                "connected native IPC not observed in real UIA")
        for flag in ("real_native_visible_hwnd", "native_uia_window_pid_matches",
                     "process_alive_when_sampled"):
            require(sample.get(flag) is True, "missing real native HWND proof: " + flag)
        pids.append(pid)
        ms.append(duration)
        native_ready.append(ready_ms)
    require(len(set(pids)) == 3, "three distinct native PIDs required")
    ranked = sorted(ms)
    ready_ranked = sorted(native_ready)
    return {
        "schema_version": 1,
        "status": "THREE_WARM_NATIVE_WINDOW_OBSERVATIONS_ONLY",
        "source_commit_sha": source_sha,
        "github_run_id": proof["github_run_id"],
        "executable_sha256": proof["executable_sha256"],
        "sample_count": 3,
        "window_first_visible_ms": ms,
        "native_handshake_ready_ms": native_ready,
        "median_ms": ranked[1],
        "observed_max_ms": ranked[2],
        "native_handshake_median_ms": ready_ranked[1],
        "native_handshake_max_ms": ready_ranked[2],
        "approved_performance_budget": False,
        "cold_start_budget_verified": False,
        "screen_reader_verified": False,
        "no_user_data": True,
    }


def main(argv: list[str] | None = None) -> int:
    p = argparse.ArgumentParser(description=__doc__)
    p.add_argument("--source-sha", required=True)
    p.add_argument("--proof", type=Path, required=True)
    p.add_argument("--report", type=Path, required=True)
    args = p.parse_args(argv)
    try:
        proof = json.loads(args.proof.read_text(encoding="utf-8-sig"))
        result = verify(proof, args.source_sha)
    except (OSError, ValueError, UnicodeError, InvalidRepeatedNativePerformance) as exc:
        p.exit(1, "ZYN-PERF-010: " + str(exc) + "\n")
    args.report.parent.mkdir(parents=True, exist_ok=True)
    args.report.write_text(json.dumps(result, indent=2, sort_keys=True) + "\n",
                           encoding="utf-8")
    print(json.dumps(result, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
