import { useEffect, useRef, useState, type FormEvent } from "react";
import { chatRequest, chatError, mutationId } from "../chat-transport";
import {modelRequest,modelError} from "../model-transport";
import { byteLength, validText, type Thread, type Message, type Payloads } from "./chat-contract";
import {modelAvailable,retryAvailable,currentContext,type InstalledModel,type ModelSettings,type ContextSnapshot,type RetryTarget} from "./model-contract";
type Transport="pending"|"connected"|"unavailable"|"preview";
type Pending={command:"chat.create";payload:Payloads["chat.create"]}|{command:"chat.saveUserMessage";payload:Payloads["chat.saveUserMessage"]};
export function ChatView({active,transport,onHelp}:{active:boolean;transport:Transport;onHelp:()=>void}){
 const [threads,setThreads]=useState<Thread[]>([]);
 const [threadCursor,setThreadCursor]=useState<string|null>(null);
 const [selected,setSelected]=useState<Thread|null>(null);
 const [messages,setMessages]=useState<Message[]>([]);
 const [historyCursor,setHistoryCursor]=useState<number|null>(null);
 const [title,setTitle]=useState("");
 const [draft,setDraft]=useState("");
 const [busy,setBusy]=useState(false);
 const [pending,setPending]=useState<Pending|null>(null);
 const [notice,setNotice]=useState("");
 const [error,setError]=useState("");
 const [models,setModels]=useState<InstalledModel[]>([]);
 const [runtimeVersion,setRuntimeVersion]=useState("");
 const [settings,setSettings]=useState<ModelSettings|null>(null);
 const [contextSnapshot,setContext]=useState<ContextSnapshot|null>(null);
 const [live,setLive]=useState("");
 const [activeTurn,setActiveTurn]=useState<{turnId:string;conversationId:string;parentId:string}|null>(null);
 const [retryTarget,setRetryTarget]=useState<RetryTarget|null>(null);
 const activeTurnRef=useRef<string|null>(null);
 const lock=useRef(false), pendingRef=useRef<Pending|null>(null), started=useRef(false);
 const titleRef=useRef<HTMLInputElement>(null),composerRef=useRef<HTMLTextAreaElement>(null);
 const online=transport==="connected";
 const canEdit=online&&!busy&&!pending;
 const installed=modelAvailable(settings,models,runtimeVersion);
 const canRetry=retryAvailable(retryTarget,selected?.id??null,installed);
 const context=currentContext(contextSnapshot,selected?.id??null,settings,draft);
 function invalidateInventory(){setModels([]);setRuntimeVersion("");}
 async function run(work:()=>Promise<void>){
   if(lock.current||!online)return;
   lock.current=true;setBusy(true);setError("");
   try{await work();}catch(e){const code=e instanceof Error?e.message:typeof e==="object"&&e!==null&&"code" in e?String(e.code):"";setError(code.startsWith("ZYN-MODEL")?modelError(e):chatError(e));}
   finally{lock.current=false;setBusy(false);}
 }
 async function list(after:string|null=null){
   const page=await chatRequest("chat.list",{after,limit:50});
   setThreads(old=>after===null?page.items:[...old,...page.items.filter(t=>!old.some(x=>x.id===t.id))]);
   setThreadCursor(page.next);
 }
 async function history(id:string,after=0){
   const page=await chatRequest("chat.history",{conversationId:id,after,limit:4});
   setSelected(page.conversation);
   setMessages(old=>after===0?page.items:[...old,...page.items.filter(m=>!old.some(x=>x.id===m.id))]);
   setHistoryCursor(page.next);
   if(after===0){const configured=await modelRequest("inference.settings.get",{conversationId:id});let next= configured.settings;if(!next){const health=await modelRequest("inference.health",{});const first=[...health.models].sort((a,b)=>a.name<b.name?-1:a.name>b.name?1:0)[0];if(first){const reply=await modelRequest("inference.settings.set",{conversationId:id,model:first.name,contextLimit:2048});next=reply.settings;}}setSettings(next);setContext(null);}
 }
 async function modelHealth(){invalidateInventory();const health=await modelRequest("inference.health",{});setModels([...health.models].sort((a,b)=>a.name<b.name?-1:a.name>b.name?1:0));setRuntimeVersion(health.version);}
 useEffect(()=>{
   if(!active||!online||started.current)return;
   started.current=true;void run(async()=>{await Promise.all([list(),modelHealth()]);});
 },[active,online]);
 useEffect(()=>{
   if(!selected||settings||!runtimeVersion||!models[0])return;
   let live=true;
   void modelRequest("inference.settings.set",{conversationId:selected.id,model:models[0].name,contextLimit:2048})
     .then(reply=>{if(live)setSettings(reply.settings);})
     .catch(()=>undefined);
   return()=>{live=false;};
 },[selected,settings,runtimeVersion,models]);
 function choose(id:string){
   if(draft||pendingRef.current||lock.current)return;
   setNotice("");setRetryTarget(null);setContext(null);void run(()=>history(id));
 }
 async function perform(request:Pending){
   if(request.command==="chat.create"){
      await chatRequest(request.command,request.payload);
      pendingRef.current=null;setPending(null);setTitle("");setRetryTarget(null);
      setNotice("Conversation saved locally.");
      await history(request.payload.id);await list();
   }else{
      await chatRequest(request.command,request.payload);
      pendingRef.current=null;setPending(null);setDraft("");setContext(null);setRetryTarget(null);
      setNotice("Message saved locally.");
      await history(request.payload.conversationId);await list();
   }
 }
 function start(request:Pending){
   if(lock.current||pendingRef.current||!online)return;
   pendingRef.current=request;setPending(request);setNotice("");
   void run(()=>perform(request));
 }
 function create(event:FormEvent){
   event.preventDefault();
   if(!canEdit||draft||!validText(title,512))return;
   try{start({command:"chat.create",payload:{id:mutationId(),title:title.trim()}});}
   catch(e){setError(chatError(e));}
 }
 async function generate(conversationId:string,parentId:string){
   const turnId=mutationId(),assistantMessageId=mutationId();setLive("");setRetryTarget(null);setContext(null);
   activeTurnRef.current=turnId;setActiveTurn({turnId,conversationId,parentId});
   try{const result=await modelRequest("inference.turn.generate",{turnId,conversationId,assistantMessageId,parentId},event=>{
     if(activeTurnRef.current===turnId&&event.kind==="delta")setLive(old=>old+event.content);
   });
    setNotice(result.status==="complete"?"Local model response completed and saved.":result.status==="cancelled"?"Turn stopped; any partial response was saved as cancelled.":"The local turn failed; any partial response was saved.");
    if(result.status!=="complete")setRetryTarget({conversationId,parentId});
   }catch(e){const code=e instanceof Error?e.message:typeof e==="object"&&e!==null&&"code" in e?String(e.code):"";
     if(code==="ZYN-MODEL-OFFLINE"||code==="ZYN-MODEL-MISSING")invalidateInventory();
     setError(modelError(e));setRetryTarget({conversationId,parentId});}
   finally{activeTurnRef.current=null;setActiveTurn(null);setLive("");await history(conversationId);await list();}
 }
 function save(event:FormEvent){
   event.preventDefault();
   if(!canEdit||!selected||!installed||!validText(draft,262144))return;
   try{const id=mutationId();const request:Pending={command:"chat.saveUserMessage",payload:{id,conversationId:selected.id,parentId:null,content:draft}};
    pendingRef.current=request;setPending(request);setNotice("");void run(async()=>{await perform(request);await generate(selected.id,id);});}
   catch(e){setError(chatError(e));}
 }
 function saveOnly(){if(!canEdit||!selected||!validText(draft,262144))return;try{const request:Pending={command:"chat.saveUserMessage",payload:{id:mutationId(),conversationId:selected.id,parentId:null,content:draft}};
   pendingRef.current=request;setPending(request);setNotice("");void run(async()=>{await perform(request);setNotice("Message saved locally. No model response was requested.");});
  }catch(e){setError(chatError(e));}}
  async function stop(){const turn=activeTurn;if(!turn)return;try{const reply=await modelRequest("inference.turn.cancel",{turnId:turn.turnId,conversationId:turn.conversationId});if(activeTurnRef.current===turn.turnId)setNotice(reply.stopped?"Stop requested; waiting for the local runtime to reach a safe boundary.":"Stop was not accepted; the turn may have already ended or may not have started yet.");}catch(e){if(activeTurnRef.current===turn.turnId)setError(modelError(e));}}
 function retry(){if(!canEdit||!canRetry||!retryTarget||activeTurn)return;const target=retryTarget;void run(()=>generate(target.conversationId,target.parentId));}
 function chooseModel(model:string){if(!selected||!canEdit||activeTurn||!runtimeVersion||!models.some(item=>item.name===model))return;void run(async()=>{const reply=await modelRequest("inference.settings.set",{conversationId:selected.id,model,contextLimit:settings?.contextLimit??2048});setSettings(reply.settings);setContext(null);});}
 function chooseContext(contextLimit:number){if(!selected||!settings||!installed||!canEdit||activeTurn)return;void run(async()=>{const reply=await modelRequest("inference.settings.set",{conversationId:selected.id,model:settings.model,contextLimit});setSettings(reply.settings);setContext(null);});}
 function inspectContext(){if(!selected||!settings||!canEdit)return;const conversationId=selected.id,settingsRevision=settings.revision;setContext(null);void run(async()=>setContext({conversationId,settingsRevision,draft,inspection:await modelRequest("inference.context.inspect",{conversationId,draft})}));}
 return <section className="studio-page" aria-labelledby="chat-heading" data-testid="chat-view">
   <div className="section-heading"><div><p className="eyebrow">M03 / LOCAL CONVERSATIONS</p>
   <h1 id="chat-heading">Local AI chat</h1><p className="lead">Create durable conversations and run installed models through the fixed local Ollama service.</p></div>
   <button className="subtle-action" type="button" onClick={onHelp}>Chat help</button></div>
   <p className="chat-notice" role="status">{transport==="preview"?"Browser preview: local inference is unavailable.":transport==="pending"?"Connecting to the native desktop…":!online?"Native service unavailable. Reopen the desktop application.":activeTurn?"Local model is generating…":busy?"Working with local services…":notice||`Ollama ${runtimeVersion||"not checked"} · ${models.length} installed model${models.length===1?"":"s"}.`}</p>
   {error&&<p role="alert" className="chat-notice">{error}</p>}
   {pending&&<div className="chat-actions"><p className="chat-notice">A save has not been confirmed. Retry the original request to avoid duplicates.</p><button type="button" className="subtle-action" disabled={!online||busy} onClick={()=>{const q=pendingRef.current;if(q)void run(()=>perform(q));}}>Retry same request</button></div>}
   <div className="chat-layout" aria-busy={busy}>
   <section className="chat-pane" aria-labelledby="chat-threads">
    <h2 id="chat-threads">Conversations</h2>
    <form onSubmit={create}><label htmlFor="chat-title">Conversation title</label>
     <input id="chat-title" data-testid="chat-title" ref={titleRef} value={title} maxLength={512} disabled={!canEdit||!!draft} onChange={e=>setTitle(e.target.value)}/>
     <button type="submit" className="subtle-action" disabled={!canEdit||!!draft||!validText(title,512)}>Create conversation</button>
    </form>
    <button type="button" className="subtle-action" disabled={!canEdit} onClick={()=>void run(()=>list())}>Refresh conversations</button>
    {threads.length===0&&!busy&&<p className="chat-notice">{online?"No saved conversations.":"History unavailable."}</p>}
    <ul className="chat-list">{threads.map(t=><li key={t.id}><button type="button" aria-pressed={selected?.id===t.id} disabled={!canEdit||!!draft} onClick={()=>choose(t.id)}>{t.title}</button></li>)}</ul>
    {threadCursor!==null&&<button className="subtle-action" type="button" disabled={!canEdit} onClick={()=>void run(()=>list(threadCursor))}>More conversations</button>}
   </section>
   <section className="chat-pane" aria-labelledby="chat-detail">
    <h2 id="chat-detail">{selected?.title??"Select a conversation"}</h2>
    {selected&&<><div className="chat-actions"><button type="button" className="subtle-action" disabled={!canEdit} onClick={()=>void run(()=>history(selected.id))}>Refresh history</button><button type="button" className="subtle-action" disabled={busy||activeTurn!==null} onClick={()=>void run(()=>modelHealth())}>Refresh local models</button></div>
    <div className="chat-model-controls" role="group" aria-label="Local model and context settings">
     <label htmlFor="chat-model">Model</label><select id="chat-model" value={installed?settings!.model:""} disabled={!canEdit||!runtimeVersion||activeTurn!==null} onChange={e=>chooseModel(e.target.value)}>
      <option value="" disabled>{settings&&!installed?"Previously selected model unavailable":"Choose an installed model"}</option>{models.map(model=><option key={model.name} value={model.name}>{model.name}</option>)}</select>
     {settings&&!installed&&<p className="chat-notice" role="status">The saved model is unavailable. Refresh local models or choose an installed model. Your saved messages are unchanged.</p>}
     <label htmlFor="chat-context">Context budget</label><select id="chat-context" value={settings?.contextLimit??2048} disabled={!installed||!canEdit||activeTurn!==null} onChange={e=>chooseContext(Number(e.target.value))}>
      {[512,1024,2048,4096,8192,16384,32768].map(value=><option key={value} value={value}>{value} tokens</option>)}</select>
     <button type="button" className="subtle-action" disabled={!settings||busy||activeTurn!==null} onClick={inspectContext}>Inspect context</button>
     {context&&<output aria-live="polite">Estimated {context.estimatedTokens} / {context.limit} tokens · {context.includedMessages} included · {context.omittedMessages} omitted</output>}
    </div>
    {messages.length===0&&!busy&&<p className="chat-notice">No saved messages.</p>}
    <ol className="chat-history" aria-label="Saved messages" tabIndex={0}>{messages.map(m=><li key={m.id}><strong>{m.role==="user"?"You":m.role==="assistant"?"Assistant":"System"}</strong><p>{m.content}</p><small>{m.status==="complete"?"Saved":m.status}</small></li>)}{live&&<li aria-live="polite"><strong>Assistant</strong><p>{live}</p><small>Generating locally</small></li>}</ol>
    {historyCursor!==null&&<button type="button" className="subtle-action" disabled={!canEdit} onClick={()=>void run(()=>history(selected.id,historyCursor))}>Load more messages</button>}
    <form onSubmit={save}><label htmlFor="chat-message">Message</label><textarea id="chat-message" data-testid="chat-message" ref={composerRef} value={draft} maxLength={262144} disabled={!canEdit} onChange={e=>{setDraft(e.target.value);setContext(null);}} aria-describedby="chat-draft-info"/>
    <p id="chat-draft-info" className="chat-notice">{byteLength(draft)} / 262144 bytes · Drafts are session-only.</p>
    <div className="chat-actions"><button type="submit" className="gold-action" disabled={!canEdit||!installed||!validText(draft,262144)}>Send</button><button type="button" className="subtle-action" disabled={!canEdit||!validText(draft,262144)} onClick={saveOnly}>Save message</button><button type="button" className="subtle-action" disabled={!activeTurn} onClick={()=>void stop()}>Stop</button><button type="button" className="subtle-action" disabled={!canEdit||!canRetry||activeTurn!==null} onClick={retry}>Retry turn</button><button type="button" className="subtle-action" disabled={!canEdit||!draft} onClick={()=>{setDraft("");setContext(null);composerRef.current?.focus();}}>Clear draft</button></div>
    </form></>}
    <p className="chat-notice">Inference stays on fixed loopback. Attachments, tools and export are not available in this slice.</p>
   </section>
   </div>
 </section>;
}
