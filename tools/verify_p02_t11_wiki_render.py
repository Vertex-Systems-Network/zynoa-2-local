"""Read-only public Wiki browser DOM and source-pinned link verification for P02.

No account, credentials, Wiki writes, desktop network privilege, release or merge
authorization. Chrome runs only on a disposable GitHub-hosted CI runner.
"""
from __future__ import annotations
import argparse
import hashlib
from html.parser import HTMLParser
import json
import os
from pathlib import Path, PurePosixPath
import re
import shutil
import subprocess
import tempfile
from urllib.parse import urlsplit, unquote

REPO = "Vertex-Systems-Network/zynoa-2-local"
ORIGIN = "https://github.com/" + REPO
RECEIPT = "docs/evidence/P02_T10_WIKI_PREVIEW_PUBLISHED_20261124.json"
MODULES = ("M02", "M19")
OPTION_COUNTS = {"M02":8, "M19":8, "M26":20}
VOID = frozenset(("area","base","br","col","embed","hr","img","input","link","meta","param","source","track","wbr"))

class WikiProofError(ValueError):
    pass

def need(condition, message):
    if not condition:
        raise WikiProofError(message)

class WikiBody(HTMLParser):
    def __init__(self):
        super().__init__(convert_charrefs=True)
        self.inside = False
        self.found = False
        self.depth = 0
        self.text = []
        self.links = []

    def handle_starttag(self, tag, attrs):
        attrs = dict(attrs)
        if not self.inside and attrs.get("id") == "wiki-body":
            self.inside = self.found = True
            self.depth = 1
            return
        if self.inside:
            if tag == "a" and attrs.get("href"):
                self.links.append(attrs["href"])
            if tag not in VOID:
                self.depth += 1

    def handle_startendtag(self, tag, attrs):
        self.handle_starttag(tag, attrs)
        if tag not in VOID:
            self.handle_endtag(tag)

    def handle_endtag(self, tag):
        if self.inside and tag not in VOID:
            self.depth -= 1
            if self.depth <= 0:
                self.inside = False

    def handle_data(self, data):
        if self.inside:
            self.text.append(data)

def audit_dom(module, html, source_sha):
    need(module in OPTION_COUNTS and bool(re.fullmatch(r"[0-9a-f]{40}", source_sha)), "invalid pinned Wiki identity")
    parser = WikiBody()
    parser.feed(html)
    need(parser.found, module + ": actual rendered Wiki body not found")
    text = " ".join(parser.text)
    need("preview" in text.casefold(), module + ": preview/release scope absent")
    for i in range(1, OPTION_COUNTS[module]+1):
        option = f"{module}-OPT-{i:02d}"
        need(option in text, module + ": missing rendered " + option)
    prefix = "/" + REPO + "/blob/" + source_sha + "/"
    targets = set()
    for href in parser.links:
        link = urlsplit(href)
        path = unquote(link.path)
        if path.startswith("../") or path.startswith("./"):
            raise WikiProofError(module + ": unresolved relative source link in rendered Wiki")
        # All links into this repo's source must refer to the immutable
        # published source SHA, not a moving branch or an untrusted origin.
        if path.startswith("/" + REPO + "/blob/"):
            need(link.scheme in ("", "https") and link.netloc in ("", "github.com"), "unexpected source link origin")
            need(path.startswith(prefix), module + ": repository blob link not pinned to published source")
            rel = path[len(prefix):]
            parts = PurePosixPath(rel).parts
            need(bool(parts) and parts[0] == "docs" and ".." not in parts and "\\" not in rel,
                 module + ": invalid pinned documentation path")
            targets.add(rel)
    need(bool(targets), module + ": no immutable source links rendered")
    if module == "M26":
        need({"docs/help/articles/M26.md","docs/wiki/pages/M26.md","docs/modules/M26.md"} <= targets, "M26 exact source/Help links absent")
    return {"module":module,"rendered_option_ids":OPTION_COUNTS[module],"pinned_source_paths":sorted(targets),"rendered_preview_scope":True}

def run(cmd, *, cwd=None, seconds=90):
    env = dict(os.environ)
    # Neither Git nor browser receives any token or persisted login.
    for name in list(env):
        if any(marker in name.upper() for marker in ("TOKEN","PASSWORD","SECRET","CREDENTIAL")):
            env.pop(name, None)
    env["GIT_TERMINAL_PROMPT"] = "0"
    env["GIT_CONFIG_NOSYSTEM"] = "1"
    result = subprocess.run(cmd, cwd=cwd, env=env, capture_output=True, timeout=seconds, check=False)
    need(result.returncode == 0, "read-only Wiki subprocess failed: " + Path(cmd[0]).name)
    return result.stdout

def verify(root, source_sha, run_id):
    need(bool(re.fullmatch(r"[0-9a-f]{40}",source_sha)) and run_id.isdigit(), "missing exact CI source/run identity")
    receipt = json.loads((root/RECEIPT).read_text(encoding="utf-8"))
    need(receipt.get("repository")==REPO and receipt.get("published_preview_not_final_release") is True
         and receipt.get("fresh_unauthenticated_git_clone_readback") is True
         and set(receipt.get("pages",{}))=={"M02.md","M19.md"}, "historical published Wiki proof absent")
    pinned = receipt["source_sha"]
    need(bool(re.fullmatch(r"[0-9a-f]{40}",pinned)), "invalid published source SHA")
    chrome = next((shutil.which(n) for n in ("google-chrome","google-chrome-stable","chromium") if shutil.which(n)), None)
    need(bool(chrome), "disposable CI Chrome unavailable")
    rows = []
    with tempfile.TemporaryDirectory(prefix="zynoa-wiki-public-") as temp:
        temp = Path(temp)
        wiki = temp/"wiki"
        run(["git","-c","credential.helper=","clone","--depth=1",ORIGIN+".wiki.git",str(wiki)])
        remote_head = run(["git","rev-parse","HEAD"],cwd=wiki).decode().strip()
        need(bool(re.fullmatch(r"[0-9a-f]{40}",remote_head)), "invalid read-only Wiki Git head")
        # Fetch a public historical commit using a fixed URL; no checkout or execution.
        run(["git","-c","credential.helper=","fetch","--no-tags","--depth=1",ORIGIN+".git",pinned],cwd=root)
        for module in MODULES:
            page = module+".md"
            raw = (wiki/page).read_bytes()
            digest = hashlib.sha256(raw).hexdigest()
            need(digest==receipt["pages"][page]["sha256"], module+": public Wiki bytes differ from verified preview")
            url = ORIGIN+"/wiki/"+module
            html = run([chrome,"--headless","--no-sandbox","--disable-dev-shm-usage",
                        "--disable-extensions","--no-first-run","--no-default-browser-check",
                        "--user-data-dir="+str(temp/("chrome-"+module)),
                        "--dump-dom","--timeout=30000",url],seconds=75)
            need(0<len(html)<=12_000_000,module+": unexpected browser DOM size")
            row = audit_dom(module,html.decode("utf-8",errors="strict"),pinned)
            for path in row["pinned_source_paths"]:
                run(["git","cat-file","-e",pinned+":"+path],cwd=root)
            row["url"]=url
            row["published_markdown_sha256"]=digest
            row["public_chrome_dom_sha256"]=hashlib.sha256(html).hexdigest()
            rows.append(row)
    return {"schema_version":1,"phase":"P02","task":"P02-T11",
            "status":"P02_PUBLIC_WIKI_CHROME_DOM_AND_PINNED_LINKS_PASS",
            "source_commit_sha":source_sha,"github_run_id":run_id,
            "published_source_sha":pinned,"observed_public_wiki_head":remote_head,
            "pages":rows,"rendered_options":16,"public_read_only":True,
            "app_external_browser_route_verified":False,
            "full_product_accessibility_approved":False,"release_approved":False,
            "protected_merge_verified":False,"no_user_data":True}

def verify_m26(root, source_sha, run_id, receipt_path):
    """Independent public readback of a guarded, unshipped M26 page."""
    need(bool(re.fullmatch(r"[0-9a-f]{40}",source_sha)) and bool(re.fullmatch(r"[1-9][0-9]*",run_id)), "invalid M26 identity")
    receipt=json.loads(receipt_path.read_text(encoding="utf-8"))
    need(receipt.get("repository")==REPO and receipt.get("source_sha")==source_sha and receipt.get("github_run_id")==run_id
         and receipt.get("published_preview_not_final_release") is True
         and receipt.get("fresh_unauthenticated_git_clone_readback") is True
         and receipt.get("existing_pages_untouched") is True and receipt.get("full_module_release_approved") is False
         and receipt.get("page")=="M26.md", "wrong guarded M26 publish receipt")
    digest=receipt.get("sha256","")
    wiki_head=receipt.get("wiki_head_after","")
    need(bool(re.fullmatch(r"[0-9a-f]{64}",digest)) and bool(re.fullmatch(r"[0-9a-f]{40}",wiki_head)), "invalid public M26 readback identity")
    chrome=next((shutil.which(n) for n in ("google-chrome","google-chrome-stable","chromium") if shutil.which(n)),None)
    need(bool(chrome),"disposable CI Chrome unavailable")
    with tempfile.TemporaryDirectory(prefix="zynoa-m26-wiki-") as name:
        temp=Path(name)
        wiki=temp/"wiki"
        run(["git","-c","credential.helper=","clone","--depth=1",ORIGIN+".wiki.git",str(wiki)])
        observed=run(["git","rev-parse","HEAD"],cwd=wiki).decode().strip()
        need(observed==wiki_head,"Wiki changed after guarded publication; reconcile before approval")
        raw=(wiki/"M26.md").read_bytes()
        need(hashlib.sha256(raw).hexdigest()==digest,"public M26 bytes differ from publish receipt")
        run(["git","-c","credential.helper=","fetch","--no-tags","--depth=1",ORIGIN+".git",source_sha],cwd=root)
        html=run([chrome,"--headless","--no-sandbox","--disable-dev-shm-usage","--disable-extensions",
                  "--no-first-run","--no-default-browser-check","--user-data-dir="+str(temp/"chrome"),
                  "--dump-dom","--timeout=30000",ORIGIN+"/wiki/M26"],seconds=75)
        need(0<len(html)<=12_000_000,"unexpected M26 browser DOM size")
        row=audit_dom("M26",html.decode("utf-8",errors="strict"),source_sha)
        for path in row["pinned_source_paths"]:
            run(["git","cat-file","-e",source_sha+":"+path],cwd=root)
    row.update(url=ORIGIN+"/wiki/M26",published_markdown_sha256=digest,
               public_chrome_dom_sha256=hashlib.sha256(html).hexdigest())
    return {"schema_version":1,"phase":"P02","task":"P02-T12","status":"M26_PUBLIC_WIKI_CHROME_DOM_AND_PINNED_LINKS_PASS",
            "source_commit_sha":source_sha,"github_run_id":run_id,"observed_public_wiki_head":observed,
            "page":row,"rendered_options":20,"public_read_only":True,"no_user_data":True,
            "full_module_release_approved":False,"protected_merge_verified":False,"app_external_browser_route_verified":False}

def main():
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--root",type=Path,default=Path("."))
    parser.add_argument("--source-sha",required=True)
    parser.add_argument("--run-id",required=True)
    parser.add_argument("--report",type=Path,required=True)
    parser.add_argument("--m26-publish-receipt",type=Path)
    args=parser.parse_args()
    try:
        if args.m26_publish_receipt:
            result=verify_m26(args.root.resolve(),args.source_sha,args.run_id,args.m26_publish_receipt)
        else:
            result=verify(args.root.resolve(),args.source_sha,args.run_id)
    except (WikiProofError,OSError,ValueError,KeyError,subprocess.TimeoutExpired) as exc:
        parser.exit(1,"ZYN-P02-T11-WIKI: "+str(exc)+"\n")
    args.report.parent.mkdir(parents=True,exist_ok=True)
    args.report.write_text(json.dumps(result,indent=2,sort_keys=True)+"\n",encoding="utf-8")
    print(json.dumps(result,sort_keys=True))
if __name__=="__main__":
    main()
