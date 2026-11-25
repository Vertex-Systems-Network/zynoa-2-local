"""T01 local-only smoke probe, synthetic prompt; not product inference."""
import argparse
import hashlib
import json
import re
import time
import urllib.request
from pathlib import Path

BASE = "http://127.0.0.1:11434"
MODEL = "qwen2.5:0.5b"

class NoRedirect(urllib.request.HTTPRedirectHandler):
    def redirect_request(self, req, fp, code, msg, headers, newurl):
        raise RuntimeError("Unexpected runtime redirect")

opener = urllib.request.build_opener(urllib.request.ProxyHandler({}), NoRedirect())

def get(path):
    with opener.open(BASE + path, timeout=10) as reply:
        return json.loads(reply.read(65536))

def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--source-sha", required=True)
    parser.add_argument("--out", type=Path, required=True)
    args = parser.parse_args()
    if not re.fullmatch(r"[0-9a-f]{40}", args.source_sha):
        raise SystemExit("Invalid source identity")
    version = get("/api/version").get("version")
    if version != "0.40.18":
        raise SystemExit("Unexpected runtime version")
    models = get("/api/tags")["models"]
    matches = [m for m in models if m.get("name") == MODEL]
    if len(matches) != 1 or not re.fullmatch(r"a8b0c5157701[0-9a-f]{52}", matches[0].get("digest", "")):
        raise SystemExit("Unexpected model identity")
    payload = {"model": MODEL, "messages": [{"role": "user", "content": "Reply with a short greeting."}],
               "stream": True, "options": {"num_predict": 32, "temperature": 0, "num_ctx": 1024}}
    request = urllib.request.Request(BASE + "/api/chat", data=json.dumps(payload).encode(),
                                     headers={"Content-Type": "application/json"}, method="POST")
    start = time.monotonic()
    first = None
    chunks = 0
    complete = None
    content_hash = hashlib.sha256()
    with opener.open(request, timeout=120) as reply:
        if reply.headers.get_content_type() != "application/x-ndjson":
            raise SystemExit("Unexpected stream content type")
        for _ in range(128):
            raw = reply.readline(65537)
            if not raw or len(raw) > 65536 or time.monotonic() - start > 150:
                raise SystemExit("Stream incomplete or oversized")
            event = json.loads(raw)
            if event.get("error"):
                raise SystemExit("Runtime returned an error")
            content = event.get("message", {}).get("content", "")
            if not isinstance(content, str):
                raise SystemExit("Invalid stream content")
            if content:
                if first is None:
                    first = int((time.monotonic() - start) * 1000)
                chunks += 1
                content_hash.update(content.encode())
            if event.get("done") is True:
                complete = event
                break
    if first is None or complete is None or type(complete.get("eval_count")) is not int or complete["eval_count"] < 1:
        raise SystemExit("No real completed model output")
    proof = {"schema_version": 1, "source_commit_sha": args.source_sha, "runtime_version": version,
             "model": MODEL, "model_digest": matches[0]["digest"], "local_only": True,
             "synthetic_prompt": True, "ttft_ms": first, "total_ms": int((time.monotonic()-start)*1000),
             "content_chunks": chunks, "eval_count": complete["eval_count"],
             "output_sha256": content_hash.hexdigest(), "done": True, "product_adapter": False}
    with args.out.open("x", encoding="utf-8") as stream:
        json.dump(proof, stream, indent=2)
    print(json.dumps(proof, sort_keys=True))

if __name__ == "__main__":
    main()
