export type InstalledModel={name:string;digest:string;size:number};
export type ModelSettings={model:string;contextLimit:number;revision:number};
export type ContextInspection={estimatedTokens:number;limit:number;includedMessages:number;omittedMessages:number};
export type TurnReceipt={id:string;revision:number;conversationRevision:number;ordinal:number};
export type TurnResult={turnId:string;status:"complete"|"cancelled"|"failed";receipt:TurnReceipt|null;evalCount:number;context:{estimatedTokens:number;limit:number;omittedMessages:number}};
export type ModelEvent={schemaVersion:1;turnId:string;sequence:number;kind:"delta"|"terminal";content:string};
export type ModelCommand="inference.health"|"inference.settings.get"|"inference.settings.set"|"inference.context.inspect"|"inference.turn.generate"|"inference.turn.cancel";
export type ModelPayloads={
 "inference.health":Record<string,never>;
 "inference.settings.get":{conversationId:string};
 "inference.settings.set":{conversationId:string;model:string;contextLimit:number};
 "inference.context.inspect":{conversationId:string;draft:string};
 "inference.turn.generate":{turnId:string;conversationId:string;assistantMessageId:string;parentId:string};
 "inference.turn.cancel":{turnId:string;conversationId:string};
};
export type ModelReplies={
 "inference.health":{version:string;models:InstalledModel[]};
 "inference.settings.get":{settings:ModelSettings|null};
 "inference.settings.set":{settings:ModelSettings};
 "inference.context.inspect":ContextInspection;
 "inference.turn.generate":TurnResult;
 "inference.turn.cancel":{turnId:string;stopped:boolean};
};
const modelName=(x:unknown):x is string=>typeof x==="string"&&/^[A-Za-z0-9._:/-]{1,128}$/.test(x);
const id=(x:unknown):x is string=>typeof x==="string"&&/^[A-Za-z0-9_-]{8,64}$/.test(x);
const integer=(x:unknown,min=0):x is number=>typeof x==="number"&&Number.isSafeInteger(x)&&x>=min;
function fail():never{throw new Error("ZYN-MODEL-RESPONSE");}
function object(x:unknown,keys:string[]):Record<string,unknown>{if(!x||typeof x!=="object"||Array.isArray(x))return fail();const o=x as Record<string,unknown>;
 if(Object.keys(o).length!==keys.length||keys.some(k=>!Object.prototype.hasOwnProperty.call(o,k)))return fail();return o;}
function settings(x:unknown):ModelSettings{const o=object(x,["model","contextLimit","revision"]);
 if(!modelName(o.model)||![512,1024,2048,4096,8192,16384,32768].includes(Number(o.contextLimit))||!integer(o.revision,1))return fail();return o as unknown as ModelSettings;}
function inspection(x:unknown):ContextInspection{const o=object(x,["estimatedTokens","limit","includedMessages","omittedMessages"]);
 if(!integer(o.estimatedTokens)||!integer(o.limit,512)||!integer(o.includedMessages)||!integer(o.omittedMessages)||Number(o.estimatedTokens)>Number(o.limit))return fail();return o as unknown as ContextInspection;}
export function decodeModelEvent(raw:unknown,turnId:string,lastSequence:number):ModelEvent{
 const o=object(raw,["schemaVersion","turnId","sequence","kind","content"]);
 if(o.schemaVersion!==1||o.turnId!==turnId||!integer(o.sequence,1)||Number(o.sequence)<=lastSequence||
   !["delta","terminal"].includes(String(o.kind))||typeof o.content!=="string"||new TextEncoder().encode(o.content).length>65536||
   (o.kind==="terminal"&&o.content!==""))return fail();
 return o as unknown as ModelEvent;
}
export function decodeModelReply<K extends ModelCommand>(raw:unknown,command:K,correlationId:string,payload:ModelPayloads[K]):ModelReplies[K]{
 const root=object(raw,["schemaVersion","commandId","correlationId","data"]);if(root.schemaVersion!==1||root.commandId!==command||root.correlationId!==correlationId)return fail();
 if(command==="inference.health"){const o=object(root.data,["version","models"]);if(typeof o.version!=="string"||!o.version||o.version.length>64||!Array.isArray(o.models)||o.models.length>128)return fail();
   const models=o.models.map(row=>{const m=object(row,["name","digest","size"]);if(!modelName(m.name)||typeof m.digest!=="string"||m.digest.length>128||!integer(m.size))return fail();return m as unknown as InstalledModel;});
   return {version:o.version,models} as ModelReplies[K];}
 if(command==="inference.settings.get"){const o=object(root.data,["settings"]);return {settings:o.settings===null?null:settings(o.settings)} as ModelReplies[K];}
 if(command==="inference.settings.set"){const o=object(root.data,["settings"]);return {settings:settings(o.settings)} as ModelReplies[K];}
 if(command==="inference.context.inspect")return inspection(root.data) as ModelReplies[K];
 if(command==="inference.turn.cancel"){const o=object(root.data,["turnId","stopped"]);if(o.turnId!==(payload as ModelPayloads["inference.turn.cancel"]).turnId||typeof o.stopped!=="boolean")return fail();return o as ModelReplies[K];}
 const q=payload as ModelPayloads["inference.turn.generate"],o=object(root.data,["turnId","status","receipt","evalCount","context"]);
 if(o.turnId!==q.turnId||!["complete","cancelled","failed"].includes(String(o.status))||!integer(o.evalCount))return fail();
 const context=object(o.context,["estimatedTokens","limit","omittedMessages"]);if(!integer(context.estimatedTokens)||!integer(context.limit,512)||!integer(context.omittedMessages)||Number(context.estimatedTokens)>Number(context.limit))return fail();
 let receipt:TurnReceipt|null=null;if(o.receipt!==null){const r=object(o.receipt,["id","revision","conversationRevision","ordinal"]);if(r.id!==q.assistantMessageId||!integer(r.revision,1)||!integer(r.conversationRevision,1)||!integer(r.ordinal,1))return fail();receipt=r as unknown as TurnReceipt;}
 if(o.status==="complete"&&receipt===null)return fail();
 return {turnId:o.turnId,status:o.status,receipt,evalCount:o.evalCount,context} as ModelReplies[K];
}
