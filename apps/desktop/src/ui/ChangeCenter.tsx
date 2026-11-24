import { useRef, useState } from "react";
import { changeAvailability, filterChangeNotices, noticeModules, type ChangeTransport, type NoticeFilter } from "./change-center";

const sections = [
  {key:"releases", label:"What's New"},
  {key:"issues", label:"Known Issues"},
  {key:"versions", label:"Version History"},
  {key:"modules", label:"Module Changes"},
] as const;
type Section = (typeof sections)[number]["key"];

export function ChangeCenter({transport,onHelp}:{transport:ChangeTransport;onHelp:()=>void}) {
  const [active,setActive]=useState<Section>("releases");
  const [query,setQuery]=useState("");
  const [module,setModule]=useState<NoticeFilter>("All");
  const [selected,setSelected]=useState<string|null>(null);
  const tabs=useRef<(HTMLButtonElement|null)[]>([]);
  const availability=changeAvailability(transport);
  const matches=filterChangeNotices(query,module);
  const current=matches.find(item=>item.id===selected);
  const select=(index:number,focus=false)=>{
    setActive(sections[index].key);setSelected(null);
    if(focus)tabs.current[index]?.focus();
  };
  const filterable=active==="issues" || active==="modules";
  return <section className="studio-page change-center" aria-labelledby="change-title">
    <div className="section-heading">
      <div><p className="eyebrow">M26 / RELEASE TRACEABILITY</p>
        <h1 id="change-title">Change <em>history.</em></h1>
        <p className="lead">Understand what is shipped, what is unavailable and where to find local guidance. Unreleased work is never presented as an installed fix.</p></div>
      <div className="heading-actions"><button type="button" className="subtle-action" onClick={onHelp}>Changelog help</button></div>
    </div>
    <div className="notice" role="status">{availability.status}. Signed release feed and live issue inventory are unavailable. No network request has been made.</div>
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
      aria-labelledby={"change-tab-"+item.key} hidden={active!==item.key} tabIndex={0}>
      {active!==item.key?null:filterable?
      <>
        <div className="change-filters">
          <label className="help-tool-field">Search bundled notices
            <input value={query} maxLength={120} onChange={event=>{setQuery(event.target.value);setSelected(null);}} placeholder="Search backup, updates or history" /></label>
          <label className="help-tool-field">Module
            <select value={module} onChange={event=>{const value=noticeModules.find(x=>x===event.target.value);if(value){setModule(value);setSelected(null);}}}>
              {noticeModules.map(value=><option key={value} value={value}>{value==="All"?"All modules":value}</option>)}
            </select></label>
          <button type="button" className="subtle-action" onClick={()=>{setQuery("");setModule("All");setSelected(null);}}>Reset filters</button>
        </div>
        <p className="help-tool-muted" role="status">{matches.length} bundled capability notices. Not live GitHub issues or release entries.</p>
        <div className="help-option-layout">
          <div className="help-option-list" role="group" aria-label="Bundled capability notices">
            {matches.map(notice=><button key={notice.id} type="button" aria-pressed={current?.id===notice.id}
              onClick={()=>setSelected(notice.id)}><code>{notice.module}</code><span>{notice.title}</span></button>)}
            {!matches.length&&<p role="status">No matching notices. Reset filters to view all.</p>}
          </div>
          <article className="help-option-detail" aria-label="Capability notice detail">
            {current?<><span className="small-caps">{current.module} / CAPABILITY LIMITATION</span>
              <h3>{current.title}</h3><p>{current.description}</p><p>Not a released fix or live issue status.</p></>:
              <><h3>Select a capability notice</h3><p>Details are bundled and can be read offline.</p></>}
          </article>
        </div>
      </>:
      <article className="panel wide">
        <div className="panel-head">{active==="releases"?"Verified release feed":"Verified version history"}<span className="status-muted">Not configured</span></div>
        <h2>{active==="releases"?"No verified releases":"No verified versions"}</h2>
        <p>{active==="releases"?"No signed release manifest or verified cached entries are connected to this preview.":"Version comparison requires two verified released versions. No release dates or version badges are inferred."}</p>
        <button type="button" disabled>{active==="releases"?"Check release feed":"Compare versions"}</button>
      </article>}
    </div>)}
    <p className="help-tool-muted">Read-only preview. Notification preferences, signed feed, technical audit query and export require their separately verified services.</p>
  </section>;
}
