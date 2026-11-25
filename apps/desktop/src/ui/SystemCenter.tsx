import {useEffect,useRef,useState} from "react";
import {centerAvailability,getSystemCenter,initialCenterDraft,updateCenterDraft,type CenterTransport,type CenterView} from "./system-centers";
export function SystemCenter({view,transport,onHelp,onDiagnostics}:{view:CenterView;transport:CenterTransport;onHelp:()=>void;onDiagnostics:()=>void}){
  const center=getSystemCenter(view);
  const [selected,setSelected]=useState(center.screens[0].id);
  const [draft,setDraft]=useState(()=>initialCenterDraft(center));
  const [query,setQuery]=useState("");
  const heading=useRef<HTMLHeadingElement>(null);
  const nav=useRef<Record<string,HTMLButtonElement|null>>({});
  const requested=useRef(false);
  const screen=center.screens.find(s=>s.id===selected)??center.screens[0];
  const availability=centerAvailability(transport);
  const visible=center.screens.filter(s=>[s.id,s.title,s.description,...s.options].join(" ").toLowerCase().includes(query.trim().toLowerCase()));
  const optionItems=center.options.filter(o=>screen.options.includes(o.id));
  const choose=(id:string)=>{if(id===screen.id){heading.current?.focus();return;}requested.current=true;setSelected(id);};
  useEffect(()=>{if(requested.current){requested.current=false;heading.current?.focus({preventScroll:false});}},[selected]);
  return <section className="system-center" aria-labelledby="system-center-title">
    <div className="system-center-header"><div><p className="eyebrow">{center.module} / LOCAL SYSTEM</p><h1 id="system-center-title">{center.title}</h1><p className="lead">{center.description}</p></div><button type="button" className="subtle-action" onClick={onHelp}>Open bundled Help (F1)</button></div>
    <div className="system-center-status" role="status" data-runtime-state={availability.state}><strong>{availability.label}</strong><span>{availability.detail}</span>{transport==="unavailable"&&<button type="button" className="subtle-action" onClick={onDiagnostics}>Open Diagnostics</button>}</div>
    <div className="system-center-layout"><nav className="system-center-nav" aria-label={center.title+" screens"}>
      <label className="help-tool-field"><span>Find a screen</span><input type="search" maxLength={100} value={query} onChange={event=>setQuery(event.target.value)} placeholder="Search screen or option ID"/></label>
      <div className="system-center-screen-list">{visible.map(s=><button key={s.id} type="button" ref={node=>{nav.current[s.id]=node;}} aria-label={"Open "+s.id+" "+s.title} aria-current={s.id===screen.id?"page":undefined} onClick={()=>choose(s.id)}><small>{s.id}</small><span>{s.title}</span></button>)}
      {!visible.length&&<div role="status"><p>No matching screens.</p><button type="button" className="subtle-action" onClick={()=>setQuery("")}>Clear screen search</button></div>}</div></nav>
      <article className="system-center-detail" aria-labelledby="system-screen-heading">
        <div className="system-screen-heading"><span className="small-caps">{screen.id} · UI FOUNDATION</span><h2 tabIndex={-1} ref={heading} id="system-screen-heading" aria-label={screen.id+" "+screen.title}>{screen.title}</h2><p>{screen.description}</p></div>
        <div className="system-center-empty" role="status"><strong>{screen.status}</strong><p>Service operations remain gated to {center.phase}. No simulated history, job progress or successful mutation.</p></div>
        {optionItems.length>0&&<div className="system-center-options" aria-label="Screen options">{optionItems.map(option=><section key={option.id} className="system-center-option" role="group" tabIndex={0} aria-label={option.id+" "+option.title} aria-describedby={option.id+"-reason"}>
          <div className="system-option-top"><small>{option.id}</small><span>{option.kind==="blocked"?"Unavailable":"Session draft"}</span></div><h3>{option.title}</h3><p id={option.id+"-reason"}>{option.reason}</p>
          {option.kind==="blocked"?<button type="button" className="subtle-action" disabled aria-label={option.id+" action unavailable"}>Unavailable</button>:
          option.kind==="toggle"?<label className="system-draft-toggle"><input type="checkbox" aria-label={option.id+" draft preference"} checked={draft[option.id]===true} onChange={event=>setDraft(current=>updateCenterDraft(center,current,option.id,event.target.checked))}/><span>Include in session plan</span></label>:
          <label className="help-tool-field"><span>Draft selection</span><select aria-label={option.id+" draft preference"} value={String(draft[option.id]??"")} onChange={event=>setDraft(current=>updateCenterDraft(center,current,option.id,event.target.value))}>{option.choices?.map(choice=><option key={choice}>{choice}</option>)}</select></label>}
        </section>)}</div>}
        <div className="system-center-actions"><button type="button" className="subtle-action" onClick={()=>{if(nav.current[screen.id])nav.current[screen.id]?.focus();else setQuery("");}}>Back to screen list</button><button type="button" className="subtle-action" onClick={()=>setDraft(initialCenterDraft(center))}>Reset session drafts</button></div>
        <p className="help-tool-muted">Drafts reset when you leave this center. No path, credential, backup, download or persistent setting is changed.</p>
      </article></div>
  </section>;
}
