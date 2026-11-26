import { invoke } from "@tauri-apps/api/core";
import { decodeReply, CHUNK_BYTES, validSelection, type Attachment, type ChatCommand, type Payloads, type Replies } from "./ui/chat-contract";
export function mutationId():string {
 const id=globalThis.crypto?.randomUUID?.();
 if(!id)throw new Error("ZYN-CHAT-UNAVAILABLE");
 return id;
}
export async function chatRequest<K extends ChatCommand>(command:K,payload:Payloads[K]):Promise<Replies[K]>{
 const correlationId=mutationId();
 const request={schemaVersion:1,commandId:command,correlationId,workspaceScope:"local",payload};
 let timer:ReturnType<typeof setTimeout>|undefined;
 try{
   const reply=await Promise.race([
     invoke<unknown>("chat_request",{request}),
     new Promise<never>((_,reject)=>{timer=setTimeout(()=>reject(new Error("ZYN-CHAT-TIMEOUT")),15000);}),
   ]);
   return decodeReply(reply,command,correlationId,payload);
 }finally{if(timer!==undefined)clearTimeout(timer);}
}
// Only browser File objects from the explicit picker are accepted. No OS paths.
export type SelectedFile={id:string;file:File};
export async function uploadSelectedFiles(conversationId:string,messageId:string,files:readonly SelectedFile[],
 onProgress:(received:number,total:number)=>void):Promise<Attachment[]>{
 if(!validSelection(files.map(x=>x.file)))throw new Error("ZYN-CHAT-FILE");
 const total=files.reduce((n,x)=>n+x.file.size,0), result:Attachment[]=[];
 let received=0;onProgress(0,total);
 for(const {id,file} of files){
   let offset=0, final:Attachment|null=null;
   do{
     const buffer=await file.slice(offset,offset+CHUNK_BYTES).arrayBuffer();
     const chunk=Array.from(new Uint8Array(buffer));
     if(chunk.length!==Math.min(CHUNK_BYTES,file.size-offset))throw new Error("ZYN-CHAT-FILE");
     const ack=await chatRequest("chat.attachment.chunk",{conversationId,messageId,artifactId:id,name:file.name,total:file.size,offset,chunk});
     offset=ack.received;received+=chunk.length;onProgress(received,total);final=ack.attachment;
   }while(offset<file.size);
   if(!final)throw new Error("ZYN-CHAT-RESPONSE");
   result.push(final);
 }
 return result;
}
export function chatError(error:unknown):string{
 const code=error instanceof Error?error.message:typeof error==="object"&&error!==null&&"code" in error?error.code:null;
 switch(code){
  case "ZYN-CHAT-FILE":return "The selected files could not be read or exceed attachment limits.";
  case "ZYN-CHAT-INPUT":return "The native service rejected the input. Check text and attachment limits.";
  case "ZYN-CHAT-CONFLICT":return "A saved ID conflicts with this request. Refresh history before creating another.";
  case "ZYN-CHAT-NOT-FOUND":return "This conversation is unavailable. Refresh the conversation list.";
  case "ZYN-CHAT-TIMEOUT":return "The response timed out. The save may have committed; retry the same request.";
  case "ZYN-CHAT-RESPONSE":return "The native response could not be verified. Retry the same request before creating another.";
  default:return "The local chat service is unavailable. No successful save can be confirmed.";
 }
}
