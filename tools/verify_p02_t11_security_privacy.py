"""Fail-closed P02-T11 source security and privacy review (NOT merge authorization).

Validate effective local Tauri privilege scope, content security policy, typed
native handshake, and no active M02/M19 network/telemetry/browser storage hooks.
All results describe current P02 preview code only.
"""
from __future__ import annotations
import argparse
import json
from pathlib import Path

class P02SecurityViolation(ValueError): pass

FRONTEND = (
    "apps/desktop/src/App.tsx",
    "apps/desktop/src/ui/HelpCenter.tsx",
    "apps/desktop/src/ui/HelpWorkflows.tsx",
    "apps/desktop/src/ui/CommandPalette.tsx",
    "apps/desktop/src/ui/help-catalog.ts",
    "apps/desktop/src/ui/help-options.ts",
    "apps/desktop/src/ui/help-workflows.ts",
    "apps/desktop/src/ui/unified-search.ts",
    "apps/desktop/src/ui/commands.ts",
    "apps/desktop/src/ui/shortcut-map.ts",
    "apps/desktop/src/ui/ChangeCenter.tsx",
    "apps/desktop/src/ui/change-center.ts",
)
DENIED = (
    "fetch(", "XMLHttpRequest", "new WebSocket(", "new EventSource(",
    "sendBeacon(", "localStorage.", "sessionStorage.",
    "dangerouslySetInnerHTML", ".innerHTML =", "eval(",
    "new Function(", "window.open(", "document.write(",
)
def require(cond, msg):
    if not cond: raise P02SecurityViolation(msg)

def audit_source_contract(config, capability, ipc, frontend, workflow, *, chat_capability=None):
    """Check the P02 source contract, without inferring lifecycle or merge state."""
    require(isinstance(config,dict) and isinstance(capability,dict), "missing Tauri security sources")
    security=config.get("app",{}).get("security",{})
    # Historical P02 calls remain strict. Later-phase regression tests may
    # explicitly supply the separate, precisely scoped P03 capability.
    expected=["main-readonly"] if chat_capability is None else ["main-readonly","main-chat"]
    require(security.get("capabilities")==expected, "Tauri capability broadened")
    if chat_capability is not None:
        require(isinstance(chat_capability,dict) and chat_capability.get("identifier")=="main-chat"
                and chat_capability.get("windows")==["main"] and chat_capability.get("local") is True
                and chat_capability.get("permissions")==["allow-chat-request"]
                and "remote" not in chat_capability
                and set(chat_capability)=={"identifier","description","windows","local","permissions"},
                "unexpected P03 chat grant")
    csp=security.get("csp","")
    for directive in (
        "default-src 'self'", "script-src 'self'", "style-src 'self'",
        "connect-src 'self'", "object-src 'none'", "frame-src 'none'",
        "base-uri 'none'", "form-action 'none'",
    ):
        require(directive in csp, "CSP missing: "+directive)
    for unsafe in ("'unsafe-eval'", "'unsafe-inline'", "https:", "http:"):
        require(unsafe not in csp, "unsafe CSP option: "+unsafe)
    require(config.get("bundle",{}).get("active") is False, "unexpected signed/release bundle enabled")
    require(capability.get("identifier")=="main-readonly" and
            capability.get("windows")==["main"] and
            capability.get("permissions")==["allow-workspace-handshake"],
            "unexpected native privilege grant")
    for fragment in (
        "const MAX_ENVELOPE_BYTES: usize = 1024",
        "deny_unknown_fields",
        "window.label() != \"main\"",
        "allow_local_workspace_handshake",
        "request.command_id != \"workspace.status\"",
        "request.workspace_scope != \"local\"",
        "writable: false",
    ):
        require(fragment in ipc, "read-only native IPC boundary missing: "+fragment)
    require(set(frontend)==set(FRONTEND), "M02/M19 frontend audit inventory incomplete")
    for path,src in frontend.items():
        require(isinstance(src,str) and len(src)>100, "missing UI source: "+path)
        for needle in DENIED:
            require(needle not in src, "network/browser storage/code execution in "+path+": "+needle)
    help_ui=frontend["apps/desktop/src/ui/HelpWorkflows.tsx"]
    require("navigator.clipboard.writeText(content)" in help_ui
            and "onClick={() => void copy()}" in help_ui
            and "Nothing was sent to a server" in help_ui,
            "local report clipboard must be explicit and manual")
    help_core=frontend["apps/desktop/src/ui/help-workflows.ts"]
    require("offline_only: true" in help_core
            and "requestOfflineHelp(request: unknown)" in help_core
            and "value.query.length > 120" in help_core,
            "bounded local Help lookup contract missing")
    require(workflow.startswith("name: P01 Desktop Foundation")
            and "permissions:\n  contents: read" in workflow
            and "pull_request:" in workflow and "cancel-in-progress: true" in workflow,
            "untrusted PR workflow privilege or concurrency changed")
    for grant in ("pull-requests: write","contents: write","issues: write","actions: write"):
        require(grant not in workflow, "untrusted PR workflow has GitHub write scope: "+grant)
    return {
        "schema_version":1,
        "phase":"P02",
        "task_id":"P02-T11",
        "status":"P02_SCOPED_SOURCE_SECURITY_PRIVACY_PASS_NOT_MERGE_APPROVAL",
        "frontend_files_reviewed":len(frontend),
        "tauri_readonly_capability_verified":True,
        "native_typed_ipc_scope_verified":True,
        "local_only_help_and_clipboard_verified":True,
        "strict_content_security_policy_verified":True,
        "untrusted_pr_workflow_readonly_verified":True,
        "source_side_no_unapproved_network_or_storage_verified":True,
        "github_ruleset_checked_by_this_static_gate":False,
        "independent_owner_approval_verified":False,
        "full_narrator_certified":False,
        "product_cold_start_sla_approved":False,
        "protected_merge_verified":False,
        "release_published":False
    }

def verify_premerge_state(phase, tasks):
    require(phase.get("phase")=="P02" and phase.get("phase_status")=="IN_PROGRESS",
            "phase lock or premerge state bypassed")
    item={x["id"]:x["status"] for x in tasks.get("tasks",[])}
    require(item.get("P02-T10")=="DONE" and item.get("P02-T11")=="IN_PROGRESS",
            "premerge task table claims falsely completed T11")


def audit_sources(config, capability, ipc, frontend, workflow, phase, tasks):
    # Live acceptance remains strictly premerge-only.
    verify_premerge_state(phase, tasks)
    return audit_source_contract(config, capability, ipc, frontend, workflow)

def audit(root:Path):
    def contents(path):return (root/path).read_text(encoding="utf-8-sig")
    try:
        return audit_sources(
            json.loads(contents("apps/desktop/src-tauri/tauri.conf.json")),
            json.loads(contents("apps/desktop/src-tauri/capabilities/main-readonly.json")),
            contents("apps/desktop/src-tauri/src/ipc.rs"),
            {name:contents(name) for name in FRONTEND},
            contents(".github/workflows/p01-desktop.yml"),
            json.loads(contents("docs/state/PHASE.json")),
            json.loads(contents("docs/state/pr-tasks/P02.json")),
        )
    except (OSError, ValueError, TypeError, KeyError, AttributeError) as exc:
        raise P02SecurityViolation("source read/security audit rejected: "+str(exc)) from exc

def main(argv=None):
    a=argparse.ArgumentParser(description=__doc__)
    a.add_argument("--root",type=Path,default=Path("."))
    a.add_argument("--report",type=Path,required=True)
    args=a.parse_args(argv)
    try: result=audit(args.root)
    except P02SecurityViolation as exc: a.exit(1,"ZYN-P02-T11-SEC: "+str(exc)+"\n")
    args.report.parent.mkdir(parents=True,exist_ok=True)
    args.report.write_text(json.dumps(result,sort_keys=True,indent=2)+"\n",encoding="utf-8")
    print(json.dumps(result,sort_keys=True))
    return 0
if __name__=="__main__":raise SystemExit(main())
