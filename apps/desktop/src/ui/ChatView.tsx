import { useEffect, useRef, useState, type FormEvent } from "react";
import { chatRequest, chatError, mutationId, uploadSelectedFiles, type SelectedFile } from "../chat-transport";
import {modelRequest,modelError} from "../model-transport";
import { byteLength, validText, validSelection, recoveryRows, isTextArtifactReceipt, type ExportReceipt, type ReviewPreview, type ReviewTrace, type ReviewChoice, type TextArtifactPreview, type RecoveryInventory, type Thread, type Message, type Payloads } from "./chat-contract";
import {modelAvailable,modelSelectValue,retryAvailable,recoverRetryTarget,currentContext,type InstalledModel,type ModelSettings,type ContextSnapshot,type RetryTarget} from "./model-contract";
type Transport="pending"|"connected"|"unavailable"|"preview";
type Pending={command:"chat.create";payload:Payloads["chat.create"]}|{command:"chat.saveUserMessage";payload:Payloads["chat.saveUserMessage"]}|{command:"attachment-upload";payload:Payloads["chat.saveUserMessage"];files:SelectedFile[]};
export function ChatView({active,transport,onHelp}:{active:boolean;transport:Transport;onHelp:()=>void}){
 const [threads,setThreads]=useState<Thread[]>([]);
 const [threadCursor,setThreadCursor]=useState<string|null>(null);
 const [selected,setSelected]=useState<Thread|null>(null);
 const [messages,setMessages]=useState<Message[]>([]);
 const [historyCursor,setHistoryCursor]=useState<number|null>(null);
 const [title,setTitle]=useState("");
 const [draft,setDraft]=useState("");
 const [files,setFiles]=useState<SelectedFile[]>([]);
 const [uploadProgress,setUploadProgress]=useState<{received:number;total:number}|null>(null);
 const [busy,setBusy]=useState(false);
 const [pending,setPending]=useState<Pending|null>(null);
 const [notice,setNotice]=useState("");
 const [recovery,setRecovery]=useState<RecoveryInventory|null>(null);
 const [artifactPreview,setArtifactPreview]=useState<TextArtifactPreview|null>(null);
 const [exportConfirmed,setExportConfirmed]=useState(false);
 const [exportReceipt,setExportReceipt]=useState<ExportReceipt|null>(null);
 const [review,setReview]=useState<ReviewPreview|null>(null);
 const [trace,setTrace]=useState<ReviewTrace[]>([]);
 const [traceCursor,setTraceCursor]=useState<string|null>(null);
 const [traceLoaded,setTraceLoaded]=useState(false);
 const [error,setError]=useState("");
 const [models,setModels]=useState<InstalledModel[]>([]);
 const [runtimeVersion,setRuntimeVersion]=useState("");
 const [settings,setSettings]=useState<ModelSettings|null>(null);
 const [contextSnapshot,setContext]=useState<ContextSnapshot|null>(null);
 const [live,setLive]=useState("");
 const [activeTurn,setActiveTurn]=useState<{turnId:string;conversationId:string;parentId:string}|null>(null);
 const [sessionRetry,setRetryTarget]=useState<RetryTarget|null>(null);
 const activeTurnRef=useRef<string|null>(null);
 const reviewDenyRef=useRef<HTMLButtonElement>(null);
 const focusedReviewRequest=useRef<string|null>(null);
 const lock=useRef(false), pendingRef=useRef<Pending|null>(null), started=useRef(false);
 const titleRef=useRef<HTMLInputElement>(null),composerRef=useRef<HTMLTextAreaElement>(null),fileRef=useRef<HTMLInputElement>(null);
 const online=transport==="connected";
 const canEdit=online&&!busy&&!pending;
 // Move focus only once per newly opened review, after native loading has
 // finished and the decision buttons are enabled. Default to denial.
 useEffect(()=>{
   if(!active||!canEdit||activeTurn||!review||review.conversationId!==selected?.id||focusedReviewRequest.current===review.requestId)return;
   const button=reviewDenyRef.current;
   if(!button||button.disabled)return;
   focusedReviewRequest.current=review.requestId;
   button.focus();
 },[active,canEdit,activeTurn,review,selected?.id]);
 const installed=modelAvailable(settings,models,runtimeVersion);
 const retryTarget=recoverRetryTarget(messages,historyCursor,selected?.id??null,sessionRetry);
 const canRetry=retryAvailable(retryTarget,selected?.id??null,installed);
 const context=currentContext(contextSnapshot,selected?.id??null,selected?.revision??null,settings,draft);
 function invalidateInventory(){setModels([]);setRuntimeVersion("");setContext(null);}
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
   // Never combine pages across conversation revisions.
   if(after!==0&&(!selected||selected.id!==id||selected.revision!==page.conversation.revision)){
     await history(id);return;
   }
   // A new history read must not expose another conversation's preference
   // if its native settings lookup fails.
   if(after===0){setSettings(null);setContext(null);setArtifactPreview(null);setExportConfirmed(false);setExportReceipt(null);setReview(null);setTrace([]);setTraceCursor(null);setTraceLoaded(false);}
   setSelected(page.conversation);
   setMessages(old=>after===0?page.items:[...old,...page.items.filter(m=>!old.some(x=>x.id===m.id))]);
   setHistoryCursor(page.next);
   if(after===0){
     const configured=await modelRequest("inference.settings.get",{conversationId:id});let next=configured.settings;
     if(!next){
       const health=await modelRequest("inference.health",{});
       const available=[...health.models].sort((a,b)=>a.name<b.name?-1:a.name>b.name?1:0);
       setModels(available);setRuntimeVersion(health.version);
       if(available[0]){const reply=await modelRequest("inference.settings.set",{conversationId:id,model:available[0].name,contextLimit:2048});next=reply.settings;}
     }
     setSettings(next);setContext(null);
   }
 }
 async function modelHealth(){invalidateInventory();const health=await modelRequest("inference.health",{});
  const available=[...health.models].sort((a,b)=>a.name<b.name?-1:a.name>b.name?1:0);
  setModels(available);setRuntimeVersion(health.version);
  // Complete bootstrap in the same refresh transaction so WebView2 never
  // observes an enabled selector with only its disabled placeholder.
  if(selected){
   // Re-read durable settings; an earlier settings lookup may have failed.
   // Never overwrite a saved preference solely because the model disappeared.
   setSettings(null);
   const configured=await modelRequest("inference.settings.get",{conversationId:selected.id});
   if(configured.settings){setSettings(configured.settings);}
   else if(available[0]){
     const reply=await modelRequest("inference.settings.set",{conversationId:selected.id,model:available[0].name,contextLimit:2048});
     setSettings(reply.settings);
   }
  }
 }
 useEffect(()=>{
   if(!active||!online||started.current)return;
   started.current=true;void run(async()=>{await Promise.all([list(),modelHealth()]);});
 },[active,online]);
 function choose(id:string){
   if(draft||files.length||pendingRef.current||lock.current)return;
   setNotice("");setRetryTarget(null);setContext(null);void run(()=>history(id));
 }
 async function perform(request:Pending){
   setRecovery(null);
   if(request.command==="attachment-upload"){
      const attachments=await uploadSelectedFiles(request.payload.conversationId,request.payload.id,request.files,
        (received,total)=>setUploadProgress({received,total}));
      // Persist the exact manifest in the retry state BEFORE the first save.
      // An uncertain save acknowledgement must never restart file upload.
      const commit:Pending={command:"chat.saveUserMessage",payload:{...request.payload,attachments}};
      pendingRef.current=commit;setPending(commit);
      await perform(commit);return;
   }
   if(request.command==="chat.create"){
      await chatRequest(request.command,request.payload);
      pendingRef.current=null;setPending(null);setTitle("");setRetryTarget(null);
      setNotice("Conversation saved locally.");
      await history(request.payload.id);await list();
   }else{
      await chatRequest(request.command,request.payload);
      pendingRef.current=null;setPending(null);setDraft("");setFiles([]);setUploadProgress(null);setContext(null);setRetryTarget(null);
      setNotice(request.payload.attachments?.length?"Message and attachments saved locally. No model response was requested.":"Message saved locally.");
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
   if(!canEdit||draft||files.length||!validText(title,512))return;
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
   if(!canEdit||!selected||!installed||files.length||!validText(draft,262144))return;
   try{const id=mutationId();const request:Pending={command:"chat.saveUserMessage",payload:{id,conversationId:selected.id,parentId:null,content:draft}};
    pendingRef.current=request;setPending(request);setNotice("");void run(async()=>{await perform(request);await generate(selected.id,id);});}
   catch(e){setError(chatError(e));}
 }
 function selectFiles(incoming:FileList|null){
   if(!canEdit||!selected||!incoming||lock.current||pendingRef.current)return;
   const selectedFiles=Array.from(incoming);
   if(!validSelection([...files.map(x=>x.file),...selectedFiles])){setError("Select up to 8 portable filenames, 25 MiB per file and 100 MiB total.");return;}
   try{const additions=selectedFiles.map(file=>({id:mutationId(),file}));setFiles(old=>[...old,...additions]);setError("");setNotice("");}
   catch(e){setError(chatError(e));}
 }
 function saveOnly(){if(!canEdit||!selected||!validText(draft,262144))return;try{
   const payload={id:mutationId(),conversationId:selected.id,parentId:null,content:draft};
   const request:Pending=files.length?{command:"attachment-upload",payload,files:[...files]}:{command:"chat.saveUserMessage",payload};
   start(request);
  }catch(e){setError(chatError(e));}}
 function discardUpload(){const q=pendingRef.current;if(q?.command!=="attachment-upload"||lock.current)return;
   void run(async()=>{await chatRequest("chat.attachment.discard",{conversationId:q.payload.conversationId,messageId:q.payload.id});
     pendingRef.current=null;setPending(null);setUploadProgress(null);setNotice("Upload discarded. Selected files and message text are still in this draft.");});
 }
  async function stop(){const turn=activeTurn;if(!turn)return;try{const reply=await modelRequest("inference.turn.cancel",{turnId:turn.turnId,conversationId:turn.conversationId});if(activeTurnRef.current===turn.turnId)setNotice(reply.stopped?"Stop requested; waiting for the local runtime to reach a safe boundary.":"Stop was not accepted; the turn may have already ended or may not have started yet.");}catch(e){if(activeTurnRef.current===turn.turnId)setError(modelError(e));}}
 function retry(){if(!canEdit||!canRetry||!retryTarget||activeTurn||lock.current||draft||files.length)return;const target=retryTarget;void run(()=>generate(target.conversationId,target.parentId));}
 function chooseModel(model:string){if(!selected||!canEdit||activeTurn||!runtimeVersion||!models.some(item=>item.name===model))return;void run(async()=>{const reply=await modelRequest("inference.settings.set",{conversationId:selected.id,model,contextLimit:settings?.contextLimit??2048});setSettings(reply.settings);setContext(null);});}
 function chooseContext(contextLimit:number){if(!selected||!settings||!installed||!canEdit||activeTurn)return;void run(async()=>{const reply=await modelRequest("inference.settings.set",{conversationId:selected.id,model:settings.model,contextLimit});setSettings(reply.settings);setContext(null);});}
 function createArtifact(source:Message){
   if(!selected||!canEdit||lock.current||pendingRef.current||activeTurn||
      source.role!=="assistant"||source.status!=="complete"||!messages.some(m=>m.id===source.id))return;
   const q={conversationId:selected.id,sourceId:source.id};
   setArtifactPreview(null);setRecovery(null);setContext(null);
   void run(async()=>{
     const saved=await chatRequest("chat.artifact.createText",q);
     setNotice(saved.replayed?"Existing text artifact verified.":"Text artifact saved locally.");
     await history(q.conversationId);await list();
     setArtifactPreview(await chatRequest("chat.artifact.previewText",q));
   });
 }
 function previewArtifact(receipt:Message){
   if(!selected||!canEdit||lock.current||pendingRef.current||activeTurn||!isTextArtifactReceipt(receipt)||!receipt.parentId||
      !messages.some(m=>m.id===receipt.id))return;
   const q={conversationId:selected.id,sourceId:receipt.parentId};
   setArtifactPreview(null);
   void run(async()=>setArtifactPreview(await chatRequest("chat.artifact.previewText",q)));
 }
 async function loadReviewTrace(conversationId:string,after:string|null=null){
   const page=await chatRequest("chat.review.list",{conversationId,after,limit:50});
   setTrace(old=>after===null?page.items:[...old,...page.items.filter(item=>!old.some(x=>x.requestId===item.requestId))]);
   setTraceCursor(page.next);setTraceLoaded(true);
 }
 function beginReview(source:Message,attachmentId:string|null){
   if(!selected||!canEdit||lock.current||pendingRef.current||activeTurn||!messages.some(m=>m.id===source.id))return;
   const conversationId=selected.id;
   setReview(null);setNotice("");
   void run(async()=>setReview(await chatRequest("chat.review.begin",{conversationId,sourceId:source.id,attachmentId})));
 }
 function finishReview(decision:ReviewChoice){
   if(!review||!selected||selected.id!==review.conversationId||!canEdit||lock.current||activeTurn)return;
   const current=review;setReview(null);
   void run(async()=>{
     try{
       const result=await chatRequest("chat.review.finish",{conversationId:current.conversationId,requestId:current.requestId,decision});
       setNotice(result.executed?"Reviewed local tool completed.":"Reviewed local tool denied; no action executed.");
       if(result.executed&&current.tool==="local.write_artifact"){await history(current.conversationId);await list();}
     }finally{await loadReviewTrace(current.conversationId);}
   });
 }
 function exportConversation(){
   if(!selected||!exportConfirmed||!canEdit||lock.current||activeTurn)return;
   const conversationId=selected.id,revision=selected.revision;
   setExportConfirmed(false);setExportReceipt(null);
   void run(async()=>{
     const receipt=await chatRequest("chat.export.conversation",{conversationId,revision,exportId:mutationId(),destination:"local-data-exports"});
     setExportReceipt(receipt);setNotice("Full conversation exported locally.");
   });
 }
 function inspectRecovery(){
   if(!canEdit||lock.current||pendingRef.current)return;
   setRecovery(null);
   void run(async()=>setRecovery(await chatRequest("chat.recovery.inspect",{})));
 }
 function inspectContext(){if(!selected||!settings||!canEdit)return;const conversationId=selected.id,conversationRevision=selected.revision,settingsRevision=settings.revision;setContext(null);void run(async()=>setContext({conversationId,conversationRevision,settingsRevision,draft,inspection:await modelRequest("inference.context.inspect",{conversationId,draft})}));}
 return <section className="studio-page" aria-labelledby="chat-heading" data-testid="chat-view">
   <div className="section-heading"><div><p className="eyebrow">M03 / LOCAL CONVERSATIONS</p>
   <h1 id="chat-heading">Local AI chat</h1><p className="lead">Create durable conversations and run installed models through the fixed local Ollama service.</p></div>
   <button className="subtle-action" type="button" onClick={onHelp}>Chat help</button></div>
   <p className="chat-notice" role="status">{transport==="preview"?"Browser preview: local inference is unavailable.":transport==="pending"?"Connecting to the native desktop…":!online?"Native service unavailable. Reopen the desktop application.":activeTurn?"Local model is generating…":busy?"Working with local services…":notice||`Ollama ${runtimeVersion||"not checked"} · ${models.length} installed model${models.length===1?"":"s"}.`}</p>
   {error&&<p role="alert" className="chat-notice">{error}</p>}
   {pending&&<div className="chat-actions"><p className="chat-notice">A save has not been confirmed. Retry the original request to avoid duplicates.</p><button type="button" className="subtle-action" disabled={!online||busy} onClick={()=>{const q=pendingRef.current;if(q)void run(()=>perform(q));}}>Retry same request</button>{pending.command==="attachment-upload"&&<button type="button" className="subtle-action" disabled={!online||busy} onClick={discardUpload}>Discard unfinished upload</button>}</div>}
   <div className="chat-layout" aria-busy={busy}>
   <section className="chat-pane" aria-labelledby="chat-threads">
    <h2 id="chat-threads">Conversations</h2>
    <form onSubmit={create}><label htmlFor="chat-title">Conversation title</label>
     <input id="chat-title" data-testid="chat-title" ref={titleRef} value={title} maxLength={512} disabled={!canEdit||!!draft||files.length>0} onChange={e=>setTitle(e.target.value)}/>
     <button type="submit" className="subtle-action" disabled={!canEdit||!!draft||files.length>0||!validText(title,512)}>Create conversation</button>
    </form>
    <button type="button" className="subtle-action" disabled={!canEdit} onClick={()=>void run(()=>list())}>Refresh conversations</button>
    {threads.length===0&&!busy&&<p className="chat-notice">{online?"No saved conversations.":"History unavailable."}</p>}
    <ul className="chat-list">{threads.map(t=><li key={t.id}><button type="button" aria-pressed={selected?.id===t.id} disabled={!canEdit||!!draft||files.length>0} onClick={()=>choose(t.id)}>{t.title}</button></li>)}</ul>
    {threadCursor!==null&&<button className="subtle-action" type="button" disabled={!canEdit} onClick={()=>void run(()=>list(threadCursor))}>More conversations</button>}
   </section>
   <section className="chat-pane" aria-labelledby="chat-detail">
    <h2 id="chat-detail">{selected?.title??"Select a conversation"}</h2>
    {selected&&<><div className="chat-actions"><button type="button" className="subtle-action" disabled={!canEdit} onClick={()=>void run(()=>history(selected.id))}>Refresh history</button><button type="button" className="subtle-action" disabled={busy||activeTurn!==null} onClick={()=>void run(()=>modelHealth())}>Refresh local models</button></div>
    <div className="chat-model-controls" role="group" aria-label="Local model and context settings">
     <label htmlFor="chat-model">Model</label><select id="chat-model" value={modelSelectValue(settings,models,runtimeVersion)} disabled={!canEdit||!runtimeVersion||models.length===0||activeTurn!==null} onChange={e=>chooseModel(e.target.value)}>
      <option value="" disabled>{settings&&!installed?"Previously selected model unavailable":models.length===0?"No installed models":"Choose an installed model"}</option>{models.map(model=><option key={model.name} value={model.name}>{model.name}</option>)}</select>
     {settings&&!installed&&<p className="chat-notice" role="status">The saved model is unavailable. Refresh local models or choose an installed model. Your saved messages are unchanged.</p>}
     <label htmlFor="chat-context">Context budget</label><select id="chat-context" value={settings?.contextLimit??2048} disabled={!installed||!canEdit||activeTurn!==null} onChange={e=>chooseContext(Number(e.target.value))}>
      {[512,1024,2048,4096,8192,16384,32768].map(value=><option key={value} value={value}>{value} tokens</option>)}</select>
     <button type="button" className="subtle-action" disabled={!settings||busy||activeTurn!==null} onClick={inspectContext}>Inspect context</button>
     {context&&<output aria-live="polite" aria-label={`Estimated ${context.estimatedTokens} / ${context.limit} tokens · ${context.includedMessages} included · ${context.omittedMessages} omitted`}>{`Estimated ${context.estimatedTokens} / ${context.limit} tokens · ${context.includedMessages} included · ${context.omittedMessages} omitted`}</output>}
    </div>
    {messages.length===0&&!busy&&<p className="chat-notice">No saved messages.</p>}
    <ol className="chat-history" aria-label="Saved messages" tabIndex={0}>{messages.map(m=><li key={m.id}><strong>{m.role==="user"?"You":m.role==="assistant"?"Assistant":"System"}</strong><p>{m.content}</p>{m.attachments.length>0&&<ul aria-label="Saved attachments">{m.attachments.map(a=><li key={a.id} aria-label={`Saved attachment: ${a.name}, ${a.bytes} bytes`}><span>{a.name}</span> <small>({a.bytes.toLocaleString()} bytes · stored metadata)</small> <button type="button" className="subtle-action" disabled={!canEdit||activeTurn!==null} aria-label={`Review attachment tool ${a.name}`} onClick={()=>beginReview(m,a.id)}>Review attachment tool</button></li>)}</ul>}<small>{m.status==="complete"?"Saved":m.status}</small>
    {m.role==="assistant"&&m.status==="complete"&&<button type="button" className="subtle-action" disabled={!canEdit||activeTurn!==null} aria-label={`Generate text artifact from message ${m.ordinal}`} onClick={()=>createArtifact(m)}>Generate text artifact</button>}
    {m.role==="assistant"&&m.status==="complete"&&<button type="button" className="subtle-action" disabled={!canEdit||activeTurn!==null} aria-label={`Review text artifact tool from message ${m.ordinal}`} onClick={()=>beginReview(m,null)}>Review text artifact tool</button>}
    {isTextArtifactReceipt(m)&&<button type="button" className="subtle-action" disabled={!canEdit||activeTurn!==null} aria-label={`Preview text artifact from receipt ${m.ordinal}`} onClick={()=>previewArtifact(m)}>Preview text artifact</button>}
    </li>)}{live&&<li aria-live="polite" aria-label="Streaming assistant response"><strong>Assistant</strong><p>{live}</p><small>Generating locally</small></li>}</ol>
    {historyCursor!==null&&<button type="button" className="subtle-action" disabled={!canEdit} onClick={()=>void run(()=>history(selected.id,historyCursor))}>Load more messages</button>}
    {artifactPreview&&artifactPreview.conversationId===selected.id&&<section role="group" aria-label="Verified text artifact preview" className="chat-artifact-preview">
     <h3>Verified text artifact preview</h3>
     <p className="chat-notice">assistant-response.txt · {byteLength(artifactPreview.content).toLocaleString()} bytes · verified local plain text</p>
     <textarea readOnly aria-label="Verified artifact text" value={artifactPreview.content} rows={5} spellCheck={false}/>
     <button type="button" className="subtle-action" onClick={()=>setArtifactPreview(null)}>Close artifact preview</button>
    </section>}
    <form onSubmit={save}><label htmlFor="chat-message">Message</label><textarea id="chat-message" data-testid="chat-message" ref={composerRef} value={draft} maxLength={262144} disabled={!canEdit} onChange={e=>{setDraft(e.target.value);setContext(null);}} aria-describedby="chat-draft-info"/>
    <p id="chat-draft-info" className="chat-notice">{byteLength(draft)} / 262144 bytes · Drafts are session-only.</p>
    <div role="group" aria-label="Draft attachments">
     <button type="button" className="subtle-action" disabled={!canEdit||files.length>=8} onClick={()=>fileRef.current?.click()} aria-describedby="chat-attachment-info">Attach local files</button>
     <input ref={fileRef} type="file" id="chat-attachments" data-testid="chat-attachments" multiple hidden disabled={!canEdit||files.length>=8} onChange={e=>{selectFiles(e.currentTarget.files);e.currentTarget.value="";}}/>
     <p id="chat-attachment-info" className="chat-notice">Up to 8 files · 25 MiB each · 100 MiB total. Select files and enter message text, then Save message. File contents are not sent to the model.</p>
     {files.length>0&&<ul aria-label="Selected attachments">{files.map(a=><li key={a.id}><span>{a.file.name} · {a.file.size.toLocaleString()} bytes</span> <button type="button" className="subtle-action" disabled={!canEdit} onClick={()=>setFiles(old=>old.filter(x=>x.id!==a.id))} aria-label={`Remove ${a.file.name}`}>Remove</button></li>)}</ul>}
     {uploadProgress&&<div><progress aria-label="Attachment upload progress" value={uploadProgress.received} max={Math.max(1,uploadProgress.total)}/><span role="status">{uploadProgress.received.toLocaleString()} / {uploadProgress.total.toLocaleString()} bytes transferred to local service; save not yet confirmed.</span></div>}
    </div>
    <div className="chat-actions"><button type="submit" className="gold-action" disabled={!canEdit||!installed||files.length>0||!validText(draft,262144)}>Send</button><button type="button" className="subtle-action" disabled={!canEdit||!validText(draft,262144)} onClick={saveOnly}>Save message</button><button type="button" className="subtle-action" disabled={!activeTurn} onClick={()=>void stop()}>Stop</button><button type="button" className="subtle-action" disabled={!canEdit||!canRetry||activeTurn!==null||!!draft||files.length>0} onClick={retry}>Retry turn</button><button type="button" className="subtle-action" disabled={!canEdit||(!draft&&!files.length)} onClick={()=>{setDraft("");setFiles([]);setContext(null);composerRef.current?.focus();}}>Clear draft</button></div>
    </form></>}
    <section aria-label="Managed file recovery" className="chat-recovery">
     <h3>Managed file recovery</h3>
     <p className="chat-notice">Check local managed files across conversations. This is a bounded read-only inspection, not a repair or deletion. Unreferenced files may still be needed.</p>
     <button type="button" className="subtle-action" disabled={!canEdit||activeTurn!==null} onClick={inspectRecovery}>Check managed files</button>
     {recovery&&<div role="group" aria-label="Managed file check result" className="chat-recovery-result">
      <p role="status" className="chat-notice">Managed file check complete. Point-in-time result; no files were changed.</p>
      <ul aria-label="Managed file counts">{recoveryRows(recovery).map(row=><li key={row} aria-label={row} tabIndex={-1}>{row}</li>)}</ul>
     </div>}
    </section>
    {selected&&<section className="chat-recovery" aria-label="Tool trace and permission review">
     <h3>Tool trace and permission review</h3>
     <p className="chat-notice">Only explicitly reviewed local attachment verification and fixed text artifact actions are supported. Model-requested tools remain blocked.</p>
     {review&&review.conversationId===selected.id&&<div role="group" aria-label="Pending local tool review">
      <p>{review.tool==="local.read_attachment"?"Verify saved attachment":"Generate fixed text artifact"}</p>
      <p className="chat-notice">Target ID: {review.targetId}</p>
      <p className="chat-notice">SHA-256: {review.targetSha256}</p>
      <p>Review expires after two minutes. Approval applies only to this action.</p>
      <div className="chat-actions"><button data-testid="chat-review-approve" type="button" className="gold-action" disabled={!canEdit||activeTurn!==null} onClick={()=>finishReview("approve")}>Approve local tool</button><button ref={reviewDenyRef} data-testid="chat-review-deny" type="button" className="subtle-action" disabled={!canEdit||activeTurn!==null} onClick={()=>finishReview("deny")}>Deny local tool</button></div>
     </div>}
     <button type="button" className="subtle-action" disabled={!canEdit||activeTurn!==null} onClick={()=>void run(()=>loadReviewTrace(selected.id))}>Refresh tool trace</button>
     {traceLoaded&&trace.length===0&&<p className="chat-notice">No recorded tool decisions in this conversation.</p>}
     <ul aria-label="Recorded tool decisions">{trace.map(row=><li key={row.requestId} aria-label={`Tool decision: ${row.decision} ${row.tool}`} tabIndex={-1}><strong>{row.decision==="approve"?"Approved":"Denied"} · {row.tool}</strong><p className="chat-notice">Request: {row.requestId} · target: {row.targetId} · SHA-256: {row.targetSha256}</p><small>Historical decision, not an execution receipt or reusable permission.</small></li>)}</ul>
     {traceCursor!==null&&<button type="button" className="subtle-action" disabled={!canEdit} onClick={()=>void run(()=>loadReviewTrace(selected.id,traceCursor))}>More tool decisions</button>}
    </section>}
    {selected&&<section className="chat-recovery" aria-label="Conversation export">
     <h3>Conversation export</h3>
     <p className="chat-notice">Export all saved messages and linked files in this conversation as a plaintext JSON file (up to 32 MiB). No model, account or other conversation data is exported. Destination: the local application data folder, data/exports. Anyone with access to this file may read its contents.</p>
     <label className="local-consent"><input data-testid="chat-export-consent" type="checkbox" checked={exportConfirmed} disabled={!canEdit||activeTurn!==null} onChange={e=>setExportConfirmed(e.target.checked)}/> I understand the export is unencrypted and choose the local exports folder</label>
     <button data-testid="chat-export-confirmed" type="button" className="subtle-action" disabled={!canEdit||activeTurn!==null||!exportConfirmed} onClick={exportConversation}>Export full conversation</button>
     {exportReceipt&&exportReceipt.conversationId===selected.id&&<div role="group" aria-label="Conversation export receipt">
      <p>Export verified: {exportReceipt.messageCount} messages · {exportReceipt.attachmentCount} linked files · {exportReceipt.bytes.toLocaleString()} bytes</p>
      <label>Relative export path<input readOnly aria-label="Relative export path" value={exportReceipt.relativePath}/></label>
      <label>Export SHA-256<input readOnly aria-label="Export SHA-256" value={exportReceipt.sha256}/></label>
     </div>}
    </section>}
    <p className="chat-notice">Inference stays on fixed loopback. Files can be saved with a message. Complete assistant responses can be saved and previewed as verified text artifacts. Opening imported files, model file consumption, and model-requested tools are not available in this slice. Saved metadata does not grant arbitrary file access.</p>
   </section>
   </div>
 </section>;
}
