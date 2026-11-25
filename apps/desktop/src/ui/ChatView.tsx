import { useEffect, useRef, useState, type FormEvent } from "react";
import { chatRequest, chatError, mutationId } from "../chat-transport";
import { byteLength, validText, type Thread, type Message, type Payloads } from "./chat-contract";
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
 const lock=useRef(false), pendingRef=useRef<Pending|null>(null), started=useRef(false);
 const titleRef=useRef<HTMLInputElement>(null),composerRef=useRef<HTMLTextAreaElement>(null);
 const online=transport==="connected";
 const canEdit=online&&!busy&&!pending;
 async function run(work:()=>Promise<void>){
   if(lock.current||!online)return;
   lock.current=true;setBusy(true);setError("");
   try{await work();}catch(e){setError(chatError(e));}
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
 }
 useEffect(()=>{
   if(!active||!online||started.current)return;
   started.current=true;void run(()=>list());
 },[active,online]);
 function choose(id:string){
   if(draft||pendingRef.current||lock.current)return;
   setNotice("");void run(()=>history(id));
 }
 async function perform(request:Pending){
   if(request.command==="chat.create"){
      await chatRequest(request.command,request.payload);
      pendingRef.current=null;setPending(null);setTitle("");
      setNotice("Conversation saved locally.");
      await history(request.payload.id);await list();
   }else{
      await chatRequest(request.command,request.payload);
      pendingRef.current=null;setPending(null);setDraft("");
      setNotice("Message saved locally. No model response was requested.");
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
 function save(event:FormEvent){
   event.preventDefault();
   if(!canEdit||!selected||!validText(draft,262144))return;
   try{start({command:"chat.saveUserMessage",payload:{id:mutationId(),conversationId:selected.id,parentId:null,content:draft}});}
   catch(e){setError(chatError(e));}
 }
 return <section className="studio-page" aria-labelledby="chat-heading" data-testid="chat-view">
   <div className="section-heading"><div><p className="eyebrow">M03 / LOCAL CONVERSATIONS</p>
   <h1 id="chat-heading">Chat history</h1><p className="lead">Create conversations and store messages in your local native vault.</p></div>
   <button className="subtle-action" type="button" onClick={onHelp}>Chat help</button></div>
   <p className="chat-notice" role="status">{transport==="preview"?"Browser preview: saving is unavailable.":transport==="pending"?"Connecting to the native desktop…":!online?"Native service unavailable. Reopen the desktop application.":busy?"Working with local storage…":notice||"Save-only mode · Model inference is not available yet."}</p>
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
    {selected&&<><div className="chat-actions"><button type="button" className="subtle-action" disabled={!canEdit} onClick={()=>void run(()=>history(selected.id))}>Refresh history</button></div>
    {messages.length===0&&!busy&&<p className="chat-notice">No saved messages.</p>}
    <ol className="chat-history" aria-label="Saved messages" tabIndex={0}>{messages.map(m=><li key={m.id}><strong>{m.role==="user"?"You":m.role==="assistant"?"Assistant":"System"}</strong><p>{m.content}</p><small>{m.status==="complete"?"Saved":m.status}</small></li>)}</ol>
    {historyCursor!==null&&<button type="button" className="subtle-action" disabled={!canEdit} onClick={()=>void run(()=>history(selected.id,historyCursor))}>Load more messages</button>}
    <form onSubmit={save}><label htmlFor="chat-message">Message</label><textarea id="chat-message" data-testid="chat-message" ref={composerRef} value={draft} maxLength={262144} disabled={!canEdit} onChange={e=>setDraft(e.target.value)} aria-describedby="chat-draft-info"/>
    <p id="chat-draft-info" className="chat-notice">{byteLength(draft)} / 262144 bytes · Drafts are session-only.</p>
    <div className="chat-actions"><button type="submit" className="gold-action" disabled={!canEdit||!validText(draft,262144)}>Save message</button><button type="button" className="subtle-action" disabled={!canEdit||!draft} onClick={()=>{setDraft("");composerRef.current?.focus();}}>Clear draft</button></div>
    </form></>}
    <p className="chat-notice">Model responses, attachments and exports are not available in this slice.</p>
   </section>
   </div>
 </section>;
}
