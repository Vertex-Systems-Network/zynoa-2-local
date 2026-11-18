#!/usr/bin/env python3
"""Local-only Ollama bootstrap readiness probe (NO model execution).

P00 development worker prerequisite: discover whether Ollama is actually
available on THIS host, not on a transient CI runner. The probe sends no user
prompts or repository content. It cannot accept arbitrary URLs or remote model
endpoints. It never pretends that an observed model implies a deployed worker.
"""
from __future__ import annotations

import argparse
import json
import re
import urllib.error
import urllib.parse
import urllib.request
from typing import Callable


class LocalModelUnavailable(RuntimeError):
    pass


class _NoRedirect(urllib.request.HTTPRedirectHandler):
    def redirect_request(self, req, fp, code, msg, headers, newurl):
        raise LocalModelUnavailable("redirect refused")


def validate_local_base(url: str) -> str:
    if not isinstance(url, str) or len(url) > 200:
        raise LocalModelUnavailable("endpoint is invalid")
    try:
        parsed = urllib.parse.urlsplit(url)
        port = parsed.port
    except ValueError:
        raise LocalModelUnavailable("endpoint port invalid") from None
    if (
        parsed.scheme != "http" or
        parsed.hostname not in ("127.0.0.1", "::1") or
        parsed.username is not None or parsed.password is not None or
        parsed.path not in ("", "/") or parsed.query or parsed.fragment or
        port is None or port < 1 or port > 65535
    ):
        raise LocalModelUnavailable("only explicit loopback Ollama endpoint is allowed")
    if parsed.hostname == "::1":
        return "http://[::1]:" + str(port)
    return "http://127.0.0.1:" + str(port)


def _read_local_json(base: str, endpoint: str, timeout: float = 4.0) -> dict:
    if endpoint not in ("/api/version", "/api/tags"):
        raise LocalModelUnavailable("local endpoint not allowlisted")
    req = urllib.request.Request(
        base + endpoint,
        headers={"Accept": "application/json", "User-Agent": "Zynoa-Local-Probe/1"},
    )
    try:
        # Disable HTTP(S) proxies; a local health probe must not leak metadata
        # to a corporate proxy or accidentally access the public internet.
        opener = urllib.request.build_opener(urllib.request.ProxyHandler({}), _NoRedirect)
        with opener.open(req, timeout=timeout) as response:
            if response.status != 200:
                raise LocalModelUnavailable("unexpected Ollama status")
            raw = response.read(256_001)
        if len(raw) > 256_000:
            raise LocalModelUnavailable("Ollama response too large")
        data = json.loads(raw)
    except (urllib.error.URLError, OSError, TimeoutError, UnicodeError, ValueError):
        raise LocalModelUnavailable("Ollama endpoint not responsive or response invalid") from None
    if not isinstance(data, dict):
        raise LocalModelUnavailable("Ollama JSON shape invalid")
    return data


def probe_local_ollama(base_url: str = "http://127.0.0.1:11434",
                       transport: Callable | None = None) -> dict:
    base = validate_local_base(base_url)
    reader = transport or _read_local_json
    version = reader(base, "/api/version")
    tags = reader(base, "/api/tags")
    if not isinstance(version, dict) or not isinstance(tags, dict):
        raise LocalModelUnavailable("invalid model server metadata")
    raw_version = version.get("version")
    if not isinstance(raw_version, str) or not re.fullmatch(r"[a-zA-Z0-9._+\-]{1,45}", raw_version):
        raise LocalModelUnavailable("missing trustworthy local Ollama version")
    raw_models = tags.get("models")
    if not isinstance(raw_models, list) or len(raw_models) > 1000:
        raise LocalModelUnavailable("invalid Ollama model inventory")
    names = []
    for model in raw_models:
        if not isinstance(model, dict):
            raise LocalModelUnavailable("invalid Ollama model item")
        name = model.get("name")
        if not isinstance(name, str) or not re.fullmatch(r"[a-zA-Z0-9._/+:\-]{1,128}", name):
            raise LocalModelUnavailable("invalid Ollama model identifier")
        if any(part in ("", ".", "..") for part in name.split("/")):
            raise LocalModelUnavailable("unsafe local model identifier")
        names.append(name)
    return {
        "status": "LOCAL_MODEL_PRESENT" if names else "OLLAMA_RUNNING_NO_MODELS",
        "provider": "ollama",
        "version": raw_version,
        "model_count": len(names),
        "model_names": sorted(set(names))[:30],
        "model_ready_for_coding": bool(names),
        "coding_agent_deployed": False,
        "os_sandbox_verified": False,
        "github_writes": 0,
        "prompts_sent": 0,
    }


def main() -> int:
    parser = argparse.ArgumentParser(description="Probe local Ollama without prompts or writes")
    parser.add_argument("--endpoint", default="http://127.0.0.1:11434")
    args = parser.parse_args()
    try:
        print(json.dumps(probe_local_ollama(args.endpoint), indent=2, sort_keys=True))
        return 0
    except LocalModelUnavailable:
        print(json.dumps({
            "status": "LOCAL_MODEL_UNAVAILABLE",
            "coding_agent_deployed": False,
            "github_writes": 0,
            "prompts_sent": 0,
        }))
        return 2


if __name__ == "__main__":
    raise SystemExit(main())
