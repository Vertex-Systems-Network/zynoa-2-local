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
export function changeAvailability(transport:ChangeTransport) {
  const status = transport==="pending" ? "Checking local runtime" : transport==="connected" ?
    "Local runtime connected" : transport==="preview" ? "Browser preview" : "Local runtime unavailable";
  return {status,verifiedReleaseCount:0,liveIssuesAvailable:false,releaseFeedAvailable:false} as const;
}
