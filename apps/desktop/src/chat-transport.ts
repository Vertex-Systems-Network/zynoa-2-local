import { invoke } from "@tauri-apps/api/core";
import { decodeReply, type ChatCommand, type Payloads, type Replies } from "./ui/chat-contract";
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
export function chatError(error:unknown):string{
 const code=error instanceof Error?error.message:typeof error==="object"&&error!==null&&"code" in error?error.code:null;
 switch(code){
  case "ZYN-CHAT-INPUT":return "The native service rejected the input. Check the title or message length.";
  case "ZYN-CHAT-CONFLICT":return "A saved ID conflicts with this request. Refresh history before creating another.";
  case "ZYN-CHAT-NOT-FOUND":return "This conversation is unavailable. Refresh the conversation list.";
  case "ZYN-CHAT-TIMEOUT":return "The response timed out. The save may have committed; retry the same request.";
  case "ZYN-CHAT-RESPONSE":return "The native response could not be verified. Retry the same request before creating another.";
  default:return "The local chat service is unavailable. No successful save can be confirmed.";
 }
}
