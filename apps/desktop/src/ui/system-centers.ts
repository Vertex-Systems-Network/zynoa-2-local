/** P02 scoped system centers; no native mutation authority. */
export type CenterModule="M23"|"M24"|"M25";
export type CenterView="backup"|"locations"|"updates";
export type CenterTransport="pending"|"connected"|"unavailable"|"preview";
export type CenterOption=Readonly<{id:string;title:string;kind:"blocked"|"toggle"|"select";reason:string;choices?:readonly string[]}>;
export type CenterScreen=Readonly<{id:string;title:string;status:string;description:string;options:readonly string[]}>;
export type CenterDefinition=Readonly<{module:CenterModule;view:CenterView;title:string;article:string;phase:string;description:string;screens:readonly CenterScreen[];options:readonly CenterOption[]}>;
export const systemCenters:readonly CenterDefinition[]=[
  {
    "module": "M23",
    "view": "backup",
    "title": "Backup Center",
    "article": "backup-center",
    "phase": "P03",
    "description": "Understand data coverage, prepare a backup plan and review safe recovery steps without touching existing files.",
    "screens": [
      {
        "id": "M23-S01",
        "title": "Data & Privacy Overview",
        "status": "Data ownership",
        "description": "Native vault foundation exists; no authorized chat or managed-file inventory is exposed.",
        "options": [
          "M23-OPT-13",
          "M23-OPT-17"
        ]
      },
      {
        "id": "M23-S02",
        "title": "Chat History Browser",
        "status": "No accessible chat history",
        "description": "No chat records are exposed. A native handshake does not prove committed conversations.",
        "options": [
          "M23-OPT-01"
        ]
      },
      {
        "id": "M23-S03",
        "title": "Backup Dashboard",
        "status": "No verified backup catalog",
        "description": "Review backup planning and pre-update protection; no snapshot has been created here.",
        "options": [
          "M23-OPT-07",
          "M23-OPT-15"
        ]
      },
      {
        "id": "M23-S04",
        "title": "Create Backup Wizard",
        "status": "Draft backup plan",
        "description": "Choose intended coverage, frequency and retention; native destination and encryption remain unavailable.",
        "options": [
          "M23-OPT-02",
          "M23-OPT-03",
          "M23-OPT-04",
          "M23-OPT-05",
          "M23-OPT-06",
          "M23-OPT-14"
        ]
      },
      {
        "id": "M23-S05",
        "title": "Backup History & Verification",
        "status": "No verified backup entries",
        "description": "A backup is not restorable until manifest and integrity checks are independently verified.",
        "options": [
          "M23-OPT-08"
        ]
      },
      {
        "id": "M23-S06",
        "title": "Restore Preview",
        "status": "No verified restore source",
        "description": "Plan restoration into a new profile; never overwrite the only copy.",
        "options": [
          "M23-OPT-09",
          "M23-OPT-10"
        ]
      },
      {
        "id": "M23-S07",
        "title": "Restore Progress & Results",
        "status": "No restore job running",
        "description": "No progress percentage, completed record or audit entry is fabricated.",
        "options": [
          "M23-OPT-16"
        ]
      },
      {
        "id": "M23-S08",
        "title": "Data Export/Import",
        "status": "Export and import unavailable",
        "description": "Portable exports and import validation require typed authorization and data-integrity checks.",
        "options": [
          "M23-OPT-11",
          "M23-OPT-12"
        ]
      },
      {
        "id": "M23-S09",
        "title": "Recovery Mode",
        "status": "Keep original data intact",
        "description": "Do not delete the vault. Verified compatible recovery source required.",
        "options": [
          "M23-OPT-18"
        ]
      }
    ],
    "options": [
      {
        "id": "M23-OPT-01",
        "title": "Auto-save acknowledged chats",
        "kind": "blocked",
        "reason": "Chat transaction acknowledgement belongs to P03; no chat state is claimed."
      },
      {
        "id": "M23-OPT-02",
        "title": "Select backup categories",
        "kind": "select",
        "reason": "Draft coverage only; external originals, secrets and caches are excluded unless explicitly authorized.",
        "choices": [
          "Chats, projects and managed files",
          "Chats and settings",
          "Managed files only"
        ]
      },
      {
        "id": "M23-OPT-03",
        "title": "Choose backup destination",
        "kind": "blocked",
        "reason": "Native independent-disk validation and destination picker required; no path is collected."
      },
      {
        "id": "M23-OPT-04",
        "title": "Enable scheduled backups",
        "kind": "toggle",
        "reason": "Session scheduling intention only; no scheduler is enabled."
      },
      {
        "id": "M23-OPT-05",
        "title": "Backup frequency & retention",
        "kind": "select",
        "reason": "Session retention plan; no files are pruned.",
        "choices": [
          "Daily · keep 7",
          "Weekly · keep 4",
          "Monthly · keep 3"
        ]
      },
      {
        "id": "M23-OPT-06",
        "title": "Encrypt backup with passphrase",
        "kind": "blocked",
        "reason": "Verified encrypted backup service required. Do not enter a passphrase."
      },
      {
        "id": "M23-OPT-07",
        "title": "Create backup now",
        "kind": "blocked",
        "reason": "No authorized backup job endpoint; no snapshot is created."
      },
      {
        "id": "M23-OPT-08",
        "title": "Verify existing backup",
        "kind": "blocked",
        "reason": "Verified backup catalog and checksum reader required."
      },
      {
        "id": "M23-OPT-09",
        "title": "Restore to new profile",
        "kind": "blocked",
        "reason": "Compatible backup and isolated new-profile restore required."
      },
      {
        "id": "M23-OPT-10",
        "title": "Selective restore or merge",
        "kind": "select",
        "reason": "Draft restore strategy; no record is merged or overwritten.",
        "choices": [
          "New profile only",
          "Selective restore preview"
        ]
      },
      {
        "id": "M23-OPT-11",
        "title": "Export chat history",
        "kind": "blocked",
        "reason": "No authorized conversation export; no chat data is read."
      },
      {
        "id": "M23-OPT-12",
        "title": "Export all managed files",
        "kind": "blocked",
        "reason": "No authorized managed-file export; no file is copied."
      },
      {
        "id": "M23-OPT-13",
        "title": "Open managed data folder",
        "kind": "blocked",
        "reason": "No approved native folder-open command; paths are not exposed."
      },
      {
        "id": "M23-OPT-14",
        "title": "Include external project files (explicit)",
        "kind": "toggle",
        "reason": "Explicit inclusion intention only; no external path is requested or copied."
      },
      {
        "id": "M23-OPT-15",
        "title": "Protect before update",
        "kind": "toggle",
        "reason": "Pre-update protection intention; no checkpoint is created."
      },
      {
        "id": "M23-OPT-16",
        "title": "View restore audit & logs",
        "kind": "blocked",
        "reason": "No authorized restore audit query; no private event is exposed."
      },
      {
        "id": "M23-OPT-17",
        "title": "Data retention & deletion policy",
        "kind": "select",
        "reason": "Draft retention preference; no deletion.",
        "choices": [
          "Keep until explicitly deleted",
          "Review retention before deletion"
        ]
      },
      {
        "id": "M23-OPT-18",
        "title": "Recovery key assistance",
        "kind": "blocked",
        "reason": "No recovery key workflow; keep secrets outside this interface."
      }
    ]
  },
  {
    "module": "M24",
    "view": "locations",
    "title": "Data Locations",
    "article": "data-locations",
    "phase": "P05",
    "description": "Review ownership boundaries, plan storage categories and inspect relocation safeguards.",
    "screens": [
      {
        "id": "M24-S01",
        "title": "Storage Overview",
        "status": "Storage classes, not measured usage",
        "description": "Native location registry foundation exists. No storage paths, byte counts or free-space measurements exposed.",
        "options": [
          "M24-OPT-01",
          "M24-OPT-14"
        ]
      },
      {
        "id": "M24-S02",
        "title": "Custom Download Locations",
        "status": "No writable location adapter",
        "description": "Runtime paths require native owner validation. No path entry or picker is active.",
        "options": [
          "M24-OPT-02",
          "M24-OPT-03",
          "M24-OPT-04",
          "M24-OPT-05",
          "M24-OPT-08",
          "M24-OPT-09"
        ]
      },
      {
        "id": "M24-S03",
        "title": "Model Storage Manager",
        "status": "No verified model inventory",
        "description": "Managed and external models have different ownership. Do not delete unidentified files.",
        "options": [
          "M24-OPT-18"
        ]
      },
      {
        "id": "M24-S04",
        "title": "Installed Runtime Locations",
        "status": "No verified runtime inventory",
        "description": "Externally installed runtimes must not be treated as app-managed.",
        "options": [
          "M24-OPT-06",
          "M24-OPT-07"
        ]
      },
      {
        "id": "M24-S05",
        "title": "Relocation Wizard",
        "status": "Draft relocation strategy",
        "description": "Inventory, free-space check, quiesce and staged validation must precede an actual move.",
        "options": [
          "M24-OPT-10"
        ]
      },
      {
        "id": "M24-S06",
        "title": "Relocation Progress & Recovery",
        "status": "No relocation running",
        "description": "Original copy remains authoritative until verified activation and rollback checkpoint exist.",
        "options": [
          "M24-OPT-11",
          "M24-OPT-12",
          "M24-OPT-13"
        ]
      },
      {
        "id": "M24-S07",
        "title": "Cleanup & Quotas",
        "status": "No cleanup authorization",
        "description": "Quota preference is a draft. No deletion or free-space claim.",
        "options": [
          "M24-OPT-15",
          "M24-OPT-16"
        ]
      },
      {
        "id": "M24-S08",
        "title": "Storage Diagnostics",
        "status": "No live paths exposed",
        "description": "Native path disclosure requires explicitly authorized endpoint.",
        "options": [
          "M24-OPT-17"
        ]
      }
    ],
    "options": [
      {
        "id": "M24-OPT-01",
        "title": "Browse current locations",
        "kind": "blocked",
        "reason": "Read-only native registry exists but no frontend path inventory endpoint is authorized."
      },
      {
        "id": "M24-OPT-02",
        "title": "Set Ollama model path",
        "kind": "blocked",
        "reason": "Ollama path changes require ownership detection and runtime-aware restart."
      },
      {
        "id": "M24-OPT-03",
        "title": "Set Hugging Face cache path",
        "kind": "blocked",
        "reason": "Hugging Face cache needs validated per-process adapter configuration."
      },
      {
        "id": "M24-OPT-04",
        "title": "Set llama.cpp GGUF path",
        "kind": "blocked",
        "reason": "GGUF movement needs managed inventory and checksum validation."
      },
      {
        "id": "M24-OPT-05",
        "title": "Set ComfyUI models path",
        "kind": "blocked",
        "reason": "ComfyUI needs compatible runtime adapter configuration."
      },
      {
        "id": "M24-OPT-06",
        "title": "Set optional module install root",
        "kind": "blocked",
        "reason": "Managed runtime root needs native ownership and installer compatibility checks."
      },
      {
        "id": "M24-OPT-07",
        "title": "Set user data location (advanced)",
        "kind": "blocked",
        "reason": "Vault relocation requires recoverable transaction and verified original copy."
      },
      {
        "id": "M24-OPT-08",
        "title": "Set backup destination",
        "kind": "blocked",
        "reason": "Native destination selection requires independent-storage checks."
      },
      {
        "id": "M24-OPT-09",
        "title": "Set download staging location",
        "kind": "blocked",
        "reason": "Staging changes require volume and resumable-download validation."
      },
      {
        "id": "M24-OPT-10",
        "title": "Choose move vs new-downloads-only",
        "kind": "select",
        "reason": "Draft move policy; no existing file or future download location is changed.",
        "choices": [
          "New downloads only",
          "Move existing after verification"
        ]
      },
      {
        "id": "M24-OPT-11",
        "title": "Pause and resume relocation",
        "kind": "blocked",
        "reason": "No active relocation job; pause and resume unavailable."
      },
      {
        "id": "M24-OPT-12",
        "title": "Verify moved files by checksum",
        "kind": "blocked",
        "reason": "No native inventory or staged move for checksum verification."
      },
      {
        "id": "M24-OPT-13",
        "title": "Rollback failed relocation",
        "kind": "blocked",
        "reason": "No relocation transaction or rollback receipt."
      },
      {
        "id": "M24-OPT-14",
        "title": "Storage free-space warning",
        "kind": "blocked",
        "reason": "Free-space measurement requires authorized native query."
      },
      {
        "id": "M24-OPT-15",
        "title": "Set per-category storage quotas",
        "kind": "select",
        "reason": "Draft quota only; no limit enforced.",
        "choices": [
          "No draft limit",
          "25 GB",
          "100 GB",
          "250 GB"
        ]
      },
      {
        "id": "M24-OPT-16",
        "title": "Cleanup unused models safely",
        "kind": "blocked",
        "reason": "No verified ownership or unused-model inventory; deletion denied."
      },
      {
        "id": "M24-OPT-17",
        "title": "Open data and model folders",
        "kind": "blocked",
        "reason": "No approved native folder-open action or path."
      },
      {
        "id": "M24-OPT-18",
        "title": "Detect external/shared runtime ownership",
        "kind": "blocked",
        "reason": "External/shared ownership must be detected by verified adapter."
      }
    ]
  },
  {
    "module": "M25",
    "view": "updates",
    "title": "Update Center",
    "article": "update-center",
    "phase": "P11",
    "description": "Review signed-update safety and draft channel preferences. Nothing is downloaded or installed.",
    "screens": [
      {
        "id": "M25-S01",
        "title": "Update Center Overview",
        "status": "No verified release feed",
        "description": "Development foundation; no availability or published version inferred.",
        "options": [
          "M25-OPT-05"
        ]
      },
      {
        "id": "M25-S02",
        "title": "New Update Notification",
        "status": "No signed update notification",
        "description": "No verified release received; no reminder or notification scheduled.",
        "options": [
          "M25-OPT-04",
          "M25-OPT-09"
        ]
      },
      {
        "id": "M25-S03",
        "title": "Update Release Notes",
        "status": "No verified release notes",
        "description": "Only a signed verified release can have installable release notes.",
        "options": [
          "M25-OPT-06",
          "M25-OPT-12"
        ]
      },
      {
        "id": "M25-S04",
        "title": "Download & Installation Progress",
        "status": "No update job running",
        "description": "Download, signature verification and pre-update checkpoint must precede installation.",
        "options": [
          "M25-OPT-07",
          "M25-OPT-11"
        ]
      },
      {
        "id": "M25-S05",
        "title": "Update History & Recovery",
        "status": "No verified update history",
        "description": "No installation history or rollback target fabricated.",
        "options": [
          "M25-OPT-13",
          "M25-OPT-14"
        ]
      },
      {
        "id": "M25-S06",
        "title": "Update Preferences",
        "status": "Draft update preferences",
        "description": "Session-only preferences are not applied to an updater or OS notification service.",
        "options": [
          "M25-OPT-01",
          "M25-OPT-02",
          "M25-OPT-03",
          "M25-OPT-08",
          "M25-OPT-10"
        ]
      },
      {
        "id": "M25-S07",
        "title": "Update Failure Troubleshooting",
        "status": "Keep current build and data",
        "description": "Do not install unsigned artifacts or delete data. Preserve actual recovery checkpoints.",
        "options": []
      }
    ],
    "options": [
      {
        "id": "M25-OPT-01",
        "title": "Check updates at startup",
        "kind": "toggle",
        "reason": "Session intention only; no startup request."
      },
      {
        "id": "M25-OPT-02",
        "title": "Periodic update checks",
        "kind": "select",
        "reason": "Session interval intention; no timer or request.",
        "choices": [
          "Manual only",
          "Daily",
          "Weekly"
        ]
      },
      {
        "id": "M25-OPT-03",
        "title": "Release channel Stable/Beta/Nightly",
        "kind": "select",
        "reason": "Draft channel; no feed or release selected.",
        "choices": [
          "Stable",
          "Beta",
          "Nightly"
        ]
      },
      {
        "id": "M25-OPT-04",
        "title": "Show desktop update notifications",
        "kind": "toggle",
        "reason": "Draft notification preference; no OS permission requested."
      },
      {
        "id": "M25-OPT-05",
        "title": "Check now",
        "kind": "blocked",
        "reason": "No signed feed endpoint; no network request."
      },
      {
        "id": "M25-OPT-06",
        "title": "View release notes",
        "kind": "blocked",
        "reason": "No verified signed release notes."
      },
      {
        "id": "M25-OPT-07",
        "title": "Download update now",
        "kind": "blocked",
        "reason": "No authenticated artifact or download service."
      },
      {
        "id": "M25-OPT-08",
        "title": "Enable optional auto-download",
        "kind": "toggle",
        "reason": "Draft opt-in; no automatic download enabled."
      },
      {
        "id": "M25-OPT-09",
        "title": "Defer or remind later",
        "kind": "blocked",
        "reason": "No verified update event to defer."
      },
      {
        "id": "M25-OPT-10",
        "title": "Set metered/bandwidth policy",
        "kind": "select",
        "reason": "Draft bandwidth policy; no network access.",
        "choices": [
          "Manual on metered network",
          "Ask before downloading",
          "Unmetered only"
        ]
      },
      {
        "id": "M25-OPT-11",
        "title": "Install update and restart",
        "kind": "blocked",
        "reason": "No verified download, signature or checkpoint; installation disabled."
      },
      {
        "id": "M25-OPT-12",
        "title": "View signature verification",
        "kind": "blocked",
        "reason": "No authenticated artifact or signature receipt."
      },
      {
        "id": "M25-OPT-13",
        "title": "View update history",
        "kind": "blocked",
        "reason": "No verified installation history endpoint."
      },
      {
        "id": "M25-OPT-14",
        "title": "Restore compatible previous build",
        "kind": "blocked",
        "reason": "No compatible signed rollback build or recovery receipt."
      }
    ]
  }
];
export function getSystemCenter(view:CenterView):CenterDefinition {
  const found=systemCenters.find(center=>center.view===view);
  if(!found) throw new Error("Unknown system center");
  return found;
}
export function centerAvailability(transport:CenterTransport):{state:"loading"|"active"|"error"|"offline";label:string;detail:string} {
  switch(transport){
    case "pending":return {state:"loading",label:"Checking native connection",detail:"Local guidance is available while the read-only handshake completes."};
    case "connected":return {state:"active",label:"Native bridge connected · planning only",detail:"The handshake grants no backup, move, updater or data-inventory authority."};
    case "unavailable":return {state:"error",label:"Native connection unavailable",detail:"Open Diagnostics or Help; preserve existing files. No privileged operation is attempted."};
    case "preview":return {state:"offline",label:"Offline/browser preview · planning only",detail:"No native service, network request or data path is available."};
  }
}
export function initialCenterDraft(center:CenterDefinition):Record<string,boolean|string>{
  const draft:Record<string,boolean|string>={};
  for(const option of center.options){
    if(option.kind==="toggle")draft[option.id]=false;
    if(option.kind==="select")draft[option.id]=option.choices?.[0]??"";
  }
  return draft;
}
export function updateCenterDraft(center:CenterDefinition,current:Readonly<Record<string,boolean|string>>,id:string,value:boolean|string):Record<string,boolean|string>{
  const option=center.options.find(item=>item.id===id);
  if(!option||option.kind==="blocked"||(option.kind==="toggle"&&typeof value!=="boolean")||
     (option.kind==="select"&&(typeof value!=="string"||!option.choices?.includes(value))))return {...current};
  return {...current,[id]:value};
}

/** Local all-word search across canonical screen and option labels, bounded like the command palette. */
export function filterCenterScreens(center:CenterDefinition,query:string):readonly CenterScreen[]{
  const words=query.trim().slice(0,100).toLowerCase().split(/\s+/).filter(Boolean);
  return center.screens.filter(screen=>{
    const haystack=[screen.id,screen.title,screen.description,screen.status,...center.options.filter(o=>screen.options.includes(o.id)).flatMap(o=>[o.id,o.title,o.reason])].join(" ").toLowerCase();
    return words.every(word=>haystack.includes(word));
  });
}
