import { useId, useLayoutEffect, useRef, useState } from "react";
import { changeAvailability, filterChangeNotices, noticeModules, resolveNoticeSelection, changeServicePanels, isChangeServiceSection, type ChangeTransport, type NoticeFilter } from "./change-center";

const sections = [
  {key:"releases", label:"What's New"},
  {key:"issues", label:"Known Issues"},
  {key:"versions", label:"Version History"},
  {key:"modules", label:"Module Changes"},
  {key:"audit", label:"Audit Timeline"},
  {key:"preferences", label:"Notifications"},
  {key:"migration", label:"Migration Notes"},
] as const;
type Section = (typeof sections)[number]["key"];

function UnavailableAction({label,reason}:{label:string;reason:string}) {
  const reasonId=useId();
  return <div className="change-unavailable-action" role="group" aria-label={label+" unavailable"} aria-describedby={reasonId} tabIndex={0}>
    <button type="button" disabled aria-describedby={reasonId}>{label}</button>
    <p id={reasonId}>{reason}</p>
  </div>;
}

function ServiceBoundary({section,onHelp}:{section:keyof typeof changeServicePanels;onHelp:()=>void}) {
  const panel=changeServicePanels[section];
  return <article className="panel wide">
    <div className="panel-head">{panel.title}<span className="status-muted">Unavailable</span></div>
    <h2 tabIndex={-1}>{panel.heading}</h2>
    <p>{panel.description}</p>
    <div className="change-unavailable-actions">
      {panel.actions.map(action=><UnavailableAction key={action.label} label={action.label} reason={action.reason}/>)}
    </div>
    <button type="button" className="subtle-action" onClick={onHelp}>Read contextual guidance</button>
  </article>;
}

export function ChangeCenter({transport,onHelp}:{transport:ChangeTransport;onHelp:()=>void}) {
  const [active,setActive]=useState<Section>("releases");
  const [query,setQuery]=useState("");
  const [module,setModule]=useState<NoticeFilter>("All");
  const [selected,setSelected]=useState<string|null>(null);
  const tabs=useRef<(HTMLButtonElement|null)[]>([]);
  const pendingTabFocus=useRef<number|null>(null);
  const searchInput=useRef<HTMLInputElement|null>(null);
  const detailHeading=useRef<HTMLHeadingElement|null>(null);
  const noticeButtons=useRef(new Map<string,HTMLButtonElement>());
  const pendingNoticeFocus=useRef<string|null>(null);
  const returnToNotice=()=>{
    if(selected)noticeButtons.current.get(selected)?.focus();
  };
  const resetFilters=()=>{
    pendingNoticeFocus.current=null;
    setQuery("");setModule("All");setSelected(null);
    searchInput.current?.focus();
  };
  useLayoutEffect(()=>{
    const index=pendingTabFocus.current;
    pendingTabFocus.current=null;
    if(index!==null)tabs.current[index]?.focus();
  },[active]);
  const availability=changeAvailability(transport);
  const matches=filterChangeNotices(query,module);
  const current=resolveNoticeSelection(matches,selected);
  useLayoutEffect(()=>{
    if(current && pendingNoticeFocus.current===current.id){
      pendingNoticeFocus.current=null;
      detailHeading.current?.focus();
    }
  },[current]);
  const select=(index:number,focus=false)=>{
    const next=sections[index].key;
    if(focus && next===active)tabs.current[index]?.focus();
    else if(focus)pendingTabFocus.current=index;
    else pendingTabFocus.current=null;
    pendingNoticeFocus.current=null;
    setActive(next);setSelected(null);
  };
  const filterable=active==="issues" || active==="modules";
  return <section className="studio-page change-center" aria-labelledby="change-title">
    <div className="section-heading">
      <div><p className="eyebrow">M26 / RELEASE TRACEABILITY</p>
        <h1 id="change-title">Change <em>history.</em></h1>
        <p className="lead">Understand what is shipped, what is unavailable and where to find local guidance. Unreleased work is never presented as an installed fix.</p></div>
      <div className="heading-actions"><button type="button" className="subtle-action" onClick={onHelp}>Changelog help</button></div>
    </div>
    <div className="notice change-runtime-status" role="status" data-runtime-state={availability.runtimeState}>
      <span className="change-runtime-label">{availability.status}</span>
      <span>{availability.guidance} Signed release feed and live issue inventory are unavailable. No network request has been made.</span>
    </div>
    <div className="change-tabs" role="tablist" aria-label="Change history views">
      {sections.map((item,index)=><button key={item.key} type="button" role="tab" id={"change-tab-"+item.key}
        aria-selected={active===item.key} aria-controls={"change-panel-"+item.key} tabIndex={active===item.key?0:-1}
        ref={node=>{tabs.current[index]=node;}} onClick={()=>select(index)}
        onKeyDown={event=>{
          if(!["ArrowLeft","ArrowRight","Home","End"].includes(event.key))return;
          event.preventDefault();
          select(event.key==="Home"?0:event.key==="End"?sections.length-1:
            (index+(event.key==="ArrowRight"?1:-1)+sections.length)%sections.length,true);
        }}>{item.label}</button>)}
    </div>
    {sections.map(item=><div key={item.key} role="tabpanel" id={"change-panel-"+item.key}
      aria-labelledby={"change-tab-"+item.key} hidden={active!==item.key} tabIndex={active===item.key?0:-1}>
      {active!==item.key?null:isChangeServiceSection(item.key)?<ServiceBoundary section={item.key} onHelp={onHelp}/>:filterable?
      <>
        <div className="change-filters">
          <label className="help-tool-field">Search bundled notices
            <input ref={searchInput} aria-label="Search bundled notices" value={query} maxLength={120} onChange={event=>{pendingNoticeFocus.current=null;setQuery(event.target.value);setSelected(null);}} placeholder="Search backup, updates or history" /></label>
          <label className="help-tool-field">Module
            <select aria-label="Module" value={module} onChange={event=>{const value=noticeModules.find(x=>x===event.target.value);if(value){pendingNoticeFocus.current=null;setModule(value);setSelected(null);}}}>
              {noticeModules.map(value=><option key={value} value={value}>{value==="All"?"All modules":value}</option>)}
            </select></label>
          <button type="button" className="subtle-action" onClick={resetFilters}>Reset filters</button>
        </div>
        <p className="help-tool-muted" role="status">{matches.length} bundled capability {matches.length===1?"notice":"notices"}. Not live GitHub issues or release entries.</p>
        <div className="help-option-layout">
          <div className="help-option-list" role="group" aria-label="Bundled capability notices">
            {matches.map(notice=><button key={notice.id} type="button" aria-pressed={current?.id===notice.id}
              aria-controls="change-notice-detail" ref={node=>{if(node)noticeButtons.current.set(notice.id,node);else noticeButtons.current.delete(notice.id);}}
              onClick={event=>{
                pendingNoticeFocus.current=event.detail===0?notice.id:null;
                if(current?.id===notice.id && event.detail===0){pendingNoticeFocus.current=null;detailHeading.current?.focus();}
                else setSelected(notice.id);
              }}><code>{notice.module}</code><span>{notice.title}</span></button>)}
            {!matches.length&&<button type="button" className="change-empty-reset" onClick={resetFilters}>No matching notices. Reset filters to view all.</button>}
          </div>
          <article id="change-notice-detail" className="help-option-detail" aria-label="Capability notice detail">
            {current?<><span className="small-caps">{current.module} / CAPABILITY LIMITATION</span>
              <h3 ref={detailHeading} tabIndex={-1}>{current.title}</h3><p>{current.description}</p><p tabIndex={-1}>Not a released fix or live issue status.</p>
              <div className="change-detail-navigation">
                <button type="button" className="subtle-action" onClick={returnToNotice}>Back to notice list</button>
                <button type="button" className="subtle-action" onClick={onHelp}>Read contextual guidance</button>
              </div>
              <div className="change-unavailable-actions">
                <UnavailableAction label="Open linked issue" reason="No verified issue link is attached to this bundled notice."/>
                <UnavailableAction label="Open linked pull request" reason="No verified merge receipt is attached to this bundled notice."/>
                <UnavailableAction label="Report problem from change" reason="No authorized change-reporting service is connected."/>
              </div>
              </>:
              <><h3 tabIndex={-1}>Select a capability notice</h3><p>Details are bundled and can be read offline.</p></>}
          </article>
        </div>
      </>:
      <article className="panel wide">
        <div className="panel-head">{active==="releases"?"Verified release feed":"Verified version history"}<span className="status-muted">Not configured</span></div>
        <h2 tabIndex={-1}>{active==="releases"?"No verified releases":"No verified versions"}</h2>
        <p>{active==="releases"?"No signed release manifest or verified cached entries are connected to this preview.":"Version comparison requires two verified released versions. No release dates or version badges are inferred."}</p>
        <div className="change-unavailable-actions">
          {active==="releases"?<>
            <UnavailableAction label="Check release feed" reason="No signed feed is configured."/>
            <UnavailableAction label="Filter release channel or version" reason="No verified release channel or version data is available."/>
            <UnavailableAction label="Filter change category" reason="No verified release entries are available."/>
            <UnavailableAction label="View fixed problems" reason="Only verified published fixes may appear here."/>
          </>:<UnavailableAction label="Compare versions" reason="Two verified released versions are required."/>}
        </div>
      </article>}
    </div>)}
    <p className="help-tool-muted">Read-only preview. Notification preferences, signed feed, technical audit query and export require their separately verified services.</p>
  </section>;
}
