/** M03 strict native response validation; no browser persistence or model calls. */
export type Thread={id:string;title:string;revision:number;createdAt:number;updatedAt:number};
export type Attachment={id:string;name:string;bytes:number;sha256:string};
export type Message={id:string;parentId:string|null;ordinal:number;role:"user"|"assistant"|"system";content:string;status:"complete"|"cancelled"|"failed";revision:number;createdAt:number;attachments:Attachment[]};
export type ThreadPage={items:Thread[];next:string|null};
export type HistoryPage={conversation:Thread;items:Message[];next:number|null};
export type WriteResult={receipt:{id:string;revision:number;conversationRevision:number;ordinal:number|null};replayed:boolean};
export type UploadChunk={conversationId:string;messageId:string;artifactId:string;name:string;total:number;offset:number;chunk:number[]};
export type UploadAck={conversationId:string;messageId:string;artifactId:string;received:number;attachment:Attachment|null};
export type DiscardDraft={conversationId:string;messageId:string};
export type ChatCommand="chat.list"|"chat.create"|"chat.history"|"chat.saveUserMessage"|"chat.attachment.chunk"|"chat.attachment.discard";
export type Payloads={
 "chat.list":{after:string|null;limit:number};
 "chat.create":{id:string;title:string};
 "chat.history":{conversationId:string;after:number;limit:number};
 "chat.saveUserMessage":{id:string;conversationId:string;parentId:string|null;content:string;attachments?:Attachment[]};
 "chat.attachment.chunk":UploadChunk;
 "chat.attachment.discard":DiscardDraft;
};
export type Replies={"chat.list":ThreadPage;"chat.create":WriteResult;"chat.history":HistoryPage;"chat.saveUserMessage":WriteResult;"chat.attachment.chunk":UploadAck;"chat.attachment.discard":DiscardDraft&{discarded:true}};
export const byteLength=(s:string)=>new TextEncoder().encode(s).length;
export const validText=(s:string,max:number)=>s.trim().length>0&&!s.includes("\0")&&byteLength(s)<=max;
function fail():never{throw new Error("ZYN-CHAT-RESPONSE");}
function object(v:unknown,keys:string[]):Record<string,unknown>{
 if(!v||typeof v!=="object"||Array.isArray(v))return fail();
 const o=v as Record<string,unknown>;
 if(Object.keys(o).length!==keys.length||keys.some(k=>!Object.prototype.hasOwnProperty.call(o,k)))return fail();
 return o;
}
function id(v:unknown):v is string{return typeof v==="string"&&/^[A-Za-z0-9_-]{8,64}$/.test(v);}
function integer(v:unknown,min=1):v is number{return typeof v==="number"&&Number.isSafeInteger(v)&&v>=min;}
function thread(v:unknown):Thread{
 const o=object(v,["id","title","revision","createdAt","updatedAt"]);
 if(!id(o.id)||typeof o.title!=="string"||!validText(o.title,512)||!integer(o.revision)||!integer(o.createdAt)||!integer(o.updatedAt))return fail();
 return o as Thread;
}
export function validAttachmentName(name:string):boolean{
 const stem=name.split(".")[0].replace(/ +$/,"");
 return byteLength(name)>0&&byteLength(name)<=160&&!/[\\/:*?"<>|\u0000-\u001f\u007f-\u009f]/u.test(name)&&!/[. ]$/.test(name)&&
 !!stem&&!/^(CON|PRN|AUX|NUL|CONIN\$|CONOUT\$|COM[1-9¹²³]|LPT[1-9¹²³])$/i.test(stem);
}
export const MAX_FILE_BYTES=25*1024*1024, MAX_DRAFT_BYTES=100*1024*1024, CHUNK_BYTES=64*1024;
export function validSelection(files:readonly {name:string;size:number}[]):boolean{
 return files.length<=8&&files.every(f=>validAttachmentName(f.name)&&integer(f.size,0)&&f.size<=MAX_FILE_BYTES)&&
 files.reduce((n,f)=>n+f.size,0)<=MAX_DRAFT_BYTES;
}
function attachment(v:unknown):Attachment{
 const o=object(v,["id","name","bytes","sha256"]);
 if(!id(o.id)||typeof o.name!=="string"||!validAttachmentName(o.name)||
 !integer(o.bytes,0)||o.bytes>MAX_FILE_BYTES||typeof o.sha256!=="string"||!/^[a-f0-9]{64}$/.test(o.sha256))return fail();
 return o as Attachment;
}
function message(v:unknown):Message{
 const o=object(v,["id","parentId","ordinal","role","content","status","revision","createdAt","attachments"]);
 if(!id(o.id)||(o.parentId!==null&&!id(o.parentId))||!integer(o.ordinal)||!["user","assistant","system"].includes(String(o.role))||
 typeof o.role!=="string"||typeof o.content!=="string"||!validText(o.content,262144)||typeof o.status!=="string"||
 !["complete","cancelled","failed"].includes(o.status)||!integer(o.revision)||!integer(o.createdAt))return fail();
 if(!Array.isArray(o.attachments)||o.attachments.length>8)return fail();
 const attachments=o.attachments.map(attachment);
 if(new Set(attachments.map(a=>a.id)).size!==attachments.length||
 attachments.reduce((sum,a)=>sum+a.bytes,0)>100*1024*1024)return fail();
 return {...o,attachments} as Message;
}
export function decodeReply<K extends ChatCommand>(raw:unknown,command:K,correlationId:string,payload:Payloads[K]):Replies[K]{
 const e=object(raw,["schemaVersion","commandId","correlationId","data"]);
 if(e.schemaVersion!==1||e.commandId!==command||e.correlationId!==correlationId)return fail();
 if(command==="chat.list"){
   const q=payload as Payloads["chat.list"],o=object(e.data,["items","next"]);
   if(!Array.isArray(o.items)||o.items.length>q.limit)return fail();
   const items=o.items.map(thread);
   let previous=q.after??"";
   for(const row of items){if(row.id<=previous)return fail();previous=row.id;}
   if(o.next!==null&&(items.length===0||o.next!==previous))return fail();
   return {items,next:o.next as string|null} as Replies[K];
 }
 if(command==="chat.history"){
   const q=payload as Payloads["chat.history"],o=object(e.data,["conversation","items","next"]);
   const conversation=thread(o.conversation);
   if(conversation.id!==q.conversationId||!Array.isArray(o.items)||o.items.length>q.limit)return fail();
   const items=o.items.map(message);let previous=q.after;const ids=new Set<string>();
   for(const row of items){if(row.ordinal<=previous||ids.has(row.id))return fail();previous=row.ordinal;ids.add(row.id);}
   if(o.next!==null&&(items.length===0||o.next!==previous))return fail();
   return {conversation,items,next:o.next as number|null} as Replies[K];
 }
 if(command==="chat.attachment.chunk"){
   const q=payload as UploadChunk,o=object(e.data,["conversationId","messageId","artifactId","received","attachment"]);
   if(o.conversationId!==q.conversationId||o.messageId!==q.messageId||o.artifactId!==q.artifactId||
     o.received!==q.offset+q.chunk.length||!integer(o.received,0)||o.received>q.total)return fail();
   if(o.received===q.total){
     const a=attachment(o.attachment);
     if(a.id!==q.artifactId||a.name!==q.name||a.bytes!==q.total)return fail();
     return {...o,attachment:a} as Replies[K];
   }
   if(o.attachment!==null)return fail();
   return o as Replies[K];
 }
 if(command==="chat.attachment.discard"){
   const q=payload as DiscardDraft,o=object(e.data,["conversationId","messageId","discarded"]);
   if(o.conversationId!==q.conversationId||o.messageId!==q.messageId||o.discarded!==true)return fail();
   return o as Replies[K];
 }
 const q=payload as Payloads["chat.create"]|Payloads["chat.saveUserMessage"];
 const o=object(e.data,["receipt","replayed"]),a=object(o.receipt,["id","revision","conversationRevision","ordinal"]);
 if(a.id!==q.id||!integer(a.revision)||!integer(a.conversationRevision)||typeof o.replayed!=="boolean"||
 (command==="chat.create"?a.ordinal!==null:!integer(a.ordinal)))return fail();
 return o as Replies[K];
}
