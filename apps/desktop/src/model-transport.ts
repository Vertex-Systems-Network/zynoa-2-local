import {Channel,invoke} from "@tauri-apps/api/core";
import {mutationId} from "./chat-transport";
import {decodeModelEvent,decodeModelReply,type ModelCommand,type ModelEvent,type ModelPayloads,type ModelReplies} from "./ui/model-contract";
export async function modelRequest<K extends ModelCommand>(command:K,payload:ModelPayloads[K],onEvent?:(event:ModelEvent)=>void):Promise<ModelReplies[K]>{
 const correlationId=mutationId(),channel=new Channel<unknown>();let sequence=0,channelError:unknown=null;
 channel.onmessage=raw=>{if(!onEvent||channelError)return;try{const event=decodeModelEvent(raw,(payload as {turnId?:string}).turnId??"",sequence);sequence=event.sequence;onEvent(event);}catch(error){channelError=error;}};
 const request={schemaVersion:1,commandId:command,correlationId,workspaceScope:"local",payload};
 const timeout=command==="inference.turn.generate"?180000:15000;let timer:ReturnType<typeof setTimeout>|undefined;
 try{const raw=await Promise.race([invoke<unknown>("model_request",{request,onEvent:channel}),new Promise<never>((_,reject)=>{timer=setTimeout(()=>reject(new Error("ZYN-MODEL-TIMEOUT")),timeout);})]);
   if(channelError)throw channelError;return decodeModelReply(raw,command,correlationId,payload);
 }finally{if(timer!==undefined)clearTimeout(timer);}
}
export function modelError(error:unknown):string{const code=error instanceof Error?error.message:typeof error==="object"&&error!==null&&"code" in error?String(error.code):"";
 switch(code){case "ZYN-MODEL-OFFLINE":return "Ollama is not available at the local loopback service.";case "ZYN-MODEL-MISSING":return "The selected model is no longer installed. Refresh local models.";
 case "ZYN-MODEL-BUSY":return "This conversation already has an active local turn.";case "ZYN-MODEL-CONTEXT":return "The selected context budget cannot contain the latest message.";
 case "ZYN-MODEL-SETTINGS":return "Choose an installed model before sending.";case "ZYN-MODEL-TIMEOUT":return "The local model did not finish in time. Stop the turn or retry explicitly.";
 case "ZYN-MODEL-RESPONSE":return "The local model response failed validation.";default:return "Local inference failed. Your saved messages remain available.";}}
