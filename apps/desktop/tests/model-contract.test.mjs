import test from "node:test";
import assert from "node:assert/strict";
import {decodeModelEvent,decodeModelReply,modelAvailable,retryAvailable,currentContext} from "../.ui-tests/model-contract.js";
const root=(command,correlationId,data)=>({schemaVersion:1,commandId:command,correlationId,data});
test("model health accepts bounded installed inventory and rejects extra authority",()=>{
 const ok=decodeModelReply(root("inference.health","correlation-00001",{version:"0.40.18",models:[{name:"qwen2.5:0.5b",digest:"abc",size:10}]}),"inference.health","correlation-00001",{});
 assert.equal(ok.models[0].name,"qwen2.5:0.5b");
 assert.throws(()=>decodeModelReply({...root("inference.health","correlation-00001",{version:"x",models:[]}),url:"http://remote"},"inference.health","correlation-00001",{}));
});
test("settings and context require exact bounded fields",()=>{
 const settings=decodeModelReply(root("inference.settings.set","correlation-00001",{settings:{model:"qwen2.5:0.5b",contextLimit:2048,revision:2}}),"inference.settings.set","correlation-00001",{conversationId:"thread-alpha-0001",model:"qwen2.5:0.5b",contextLimit:2048});
 assert.equal(settings.settings.revision,2);
 assert.throws(()=>decodeModelReply(root("inference.settings.get","correlation-00001",{settings:{model:"qwen2.5:0.5b",contextLimit:"2048",revision:2}}),"inference.settings.get","correlation-00001",{conversationId:"thread-alpha-0001"}));
 assert.throws(()=>decodeModelReply(root("inference.settings.set","correlation-00001",{settings:{model:"https://remote",contextLimit:777,revision:2}}),"inference.settings.set","correlation-00001",{conversationId:"thread-alpha-0001",model:"https://remote",contextLimit:777}));
 for(const model of ["http://remote","https://remote","a//b","../qwen","qwen/","/qwen","qwen\n"]){
   assert.throws(()=>decodeModelReply(root("inference.settings.get","correlation-00001",{settings:{model,contextLimit:2048,revision:2}}),"inference.settings.get","correlation-00001",{conversationId:"thread-alpha-0001"}));
   assert.throws(()=>decodeModelReply(root("inference.health","correlation-00001",{version:"x",models:[{name:model,digest:"abc",size:10}]}),"inference.health","correlation-00001",{}));
 }
 const namespaced=decodeModelReply(root("inference.health","correlation-00001",{version:"x",models:[{name:"library/qwen2.5:0.5b",digest:"abc",size:10}]}),"inference.health","correlation-00001",{});
 assert.equal(namespaced.models[0].name,"library/qwen2.5:0.5b");
 const inspected=decodeModelReply(root("inference.context.inspect","correlation-00001",{estimatedTokens:300,limit:1024,includedMessages:3,omittedMessages:1}),"inference.context.inspect","correlation-00001",{conversationId:"thread-alpha-0001",draft:"next"});
 assert.equal(inspected.omittedMessages,1);
});
test("stream events reject stale, wrong-turn and oversized deltas",()=>{
 const event=decodeModelEvent({schemaVersion:1,turnId:"turn-alpha-00001",sequence:1,kind:"delta",content:"hello"},"turn-alpha-00001",0);
 assert.equal(event.content,"hello");
 assert.throws(()=>decodeModelEvent({...event,sequence:1},"turn-alpha-00001",1));
 assert.throws(()=>decodeModelEvent({...event,turnId:"turn-other-00001",sequence:2},"turn-alpha-00001",1));
 assert.throws(()=>decodeModelEvent({...event,sequence:2,content:"x".repeat(65537)},"turn-alpha-00001",1));
});
test("terminal turn requires matching durable receipt on complete",()=>{
 const payload={turnId:"turn-alpha-00001",conversationId:"thread-alpha-0001",assistantMessageId:"assistant-alpha-01",parentId:"message-user-0001"};
 const data={turnId:payload.turnId,status:"complete",receipt:{id:payload.assistantMessageId,revision:1,conversationRevision:3,ordinal:2},evalCount:12,context:{estimatedTokens:300,limit:1024,omittedMessages:0}};
 assert.equal(decodeModelReply(root("inference.turn.generate","correlation-00001",data),"inference.turn.generate","correlation-00001",payload).status,"complete");
 assert.throws(()=>decodeModelReply(root("inference.turn.generate","correlation-00001",{...data,receipt:null}),"inference.turn.generate","correlation-00001",payload));
});

test("model availability and retry are bound to the installed inventory and selected thread",()=>{
 const settings={model:"qwen2.5:0.5b",contextLimit:2048,revision:2};
 const models=[{name:settings.model,digest:"abc",size:10}];
 assert.equal(modelAvailable(settings,models,"0.40.18"),true);
 assert.equal(modelAvailable(settings,[],"0.40.18"),false);
 assert.equal(modelAvailable(settings,models,""),false);
 assert.equal(modelAvailable(null,models,"0.40.18"),false);
 const target={conversationId:"thread_alpha",parentId:"message_user_001"};
 assert.equal(retryAvailable(target,"thread_alpha",true),true);
 assert.equal(retryAvailable(target,"thread_bravo",true),false);
 assert.equal(retryAvailable(target,"thread_alpha",false),false);
});
test("context inspection belongs to exact draft, thread and settings revision",()=>{
 const settings={model:"qwen2.5:0.5b",contextLimit:2048,revision:2};
 const inspection={estimatedTokens:400,limit:2048,includedMessages:1,omittedMessages:0};
 const snapshot={conversationId:"thread_alpha",settingsRevision:2,draft:"hello",inspection};
 assert.equal(currentContext(snapshot,"thread_alpha",settings,"hello"),inspection);
 assert.equal(currentContext(snapshot,"thread_alpha",settings,"changed"),null);
 assert.equal(currentContext(snapshot,"thread_bravo",settings,"hello"),null);
 assert.equal(currentContext(snapshot,"thread_alpha",{...settings,revision:3},"hello"),null);
 assert.equal(currentContext(snapshot,"thread_alpha",{...settings,contextLimit:1024},"hello"),null);
 assert.equal(currentContext(snapshot,"thread_alpha",null,"hello"),null);
});
test("settings acknowledgement must match the requested choice and stream cannot skip sequence",()=>{
 const command="inference.settings.set",correlation="correlation-00001";
 const payload={conversationId:"thread-alpha-0001",model:"qwen2.5:0.5b",contextLimit:2048};
 const settings={model:payload.model,contextLimit:2048,revision:2};
 assert.throws(()=>decodeModelReply(root(command,correlation,{settings:{...settings,model:"another:1b"}}),command,correlation,payload));
 assert.throws(()=>decodeModelReply(root(command,correlation,{settings:{...settings,contextLimit:1024}}),command,correlation,payload));
 assert.throws(()=>decodeModelEvent({schemaVersion:1,turnId:"turn-alpha-00001",sequence:3,kind:"delta",content:"gap"},"turn-alpha-00001",1));
});
