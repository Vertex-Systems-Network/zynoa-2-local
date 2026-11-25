/** M26 P02: bundled capability facts, not a signed feed or live issue inventory. */
export type ChangeTransport = "pending" | "connected" | "unavailable" | "preview";
export type NoticeModule = "M23" | "M24" | "M25" | "M26";
export type ChangeNotice = Readonly<{id:string; module:NoticeModule; kind:"capability-limitation"; title:string; description:string}>;
export const changeNotices: readonly ChangeNotice[] = [
  {id:"backup-unavailable",module:"M23",kind:"capability-limitation",title:"Backup and restore not available",description:"The native vault foundation exists. User backup creation and verified recovery are not yet enabled."},
  {id:"relocation-unavailable",module:"M24",kind:"capability-limitation",title:"Data relocation not available",description:"Storage is managed by the local runtime. User-selected paths and move-existing operations are not enabled."},
  {id:"updates-unavailable",module:"M25",kind:"capability-limitation",title:"Signed updates not available",description:"This preview cannot check, download or install a verified update."},
  {id:"history-unavailable",module:"M26",kind:"capability-limitation",title:"Live change and release data not available",description:"Bundled notices are not a live issue tracker. No signed release cache or user-facing native change query is connected."},
];
export const noticeModules = ["All","M23","M24","M25","M26"] as const;
export type NoticeFilter = (typeof noticeModules)[number];
export function filterChangeNotices(query:string,module:NoticeFilter):ChangeNotice[] {
  const words=query.trim().slice(0,120).toLocaleLowerCase().split(/\s+/).filter(Boolean);
  return changeNotices.filter(item=>(module==="All" || item.module===module) &&
    words.every(word=>[item.module,item.title,item.description].join(" ").toLocaleLowerCase().includes(word)));
}
export function resolveNoticeSelection(matches:readonly ChangeNotice[], selected:string|null):ChangeNotice|undefined {
  return selected===null?undefined:matches.find(item=>item.id===selected);
}
export function changeAvailability(transport:ChangeTransport) {
  const status = transport==="pending" ? "Checking local runtime" : transport==="connected" ?
    "Local runtime connected" : transport==="preview" ? "Browser preview" : "Local runtime unavailable";
  const runtimeState=transport==="pending"?"loading":transport==="connected"?"active":transport==="preview"?"offline":"error";
  const guidance=transport==="pending"?"Local notices and Help remain available while the runtime is checked.":
    transport==="connected"?"Local capability notices are available; runtime connection does not verify a release.":
    transport==="preview"?"Bundled notices and Help work offline in this browser preview.":
    "The native runtime is unavailable; bundled notices and Help remain readable offline.";
  return {status,runtimeState,guidance,verifiedReleaseCount:0,liveIssuesAvailable:false,releaseFeedAvailable:false} as const;
}

/** P02 capability boundaries: descriptions are local, not simulated remote results. */
export const changeServicePanels = {
  audit: {
    title:"Technical audit timeline", heading:"Audit access is not enabled",
    description:"Native event persistence does not grant access to an audit query. No private event, technical detail or export is exposed here.",
    actions:[{label:"View technical details",reason:"Requires an authorized audience and event query."},{label:"Export change history",reason:"Requires a verified, sanitized export service."}],
  },
  preferences: {
    title:"Changelog preferences", heading:"Notification settings unavailable",
    description:"A signed release feed and verified per-device preference service are required before notification or unread settings can be changed.",
    actions:[{label:"Enable What's New notifications",reason:"No signed release notification service is connected."},{label:"Configure unread marker",reason:"No verified per-device read-state storage is connected."}],
  },
  migration: {
    title:"Release notes and migration", heading:"No verified migration notes",
    description:"No signed release manifest is connected. Backup, compatibility and recovery instructions must be matched to a verified release before they can be offered.",
    actions:[{label:"View migration notes",reason:"Requires verified release-specific migration guidance."},{label:"View rollback guidance",reason:"Requires a verified supported recovery path; no rollback will run here."}],
  },
} as const;
export type ChangeServiceSection = keyof typeof changeServicePanels;
export function isChangeServiceSection(value:string):value is ChangeServiceSection {
  return value==="audit" || value==="preferences" || value==="migration";
}
