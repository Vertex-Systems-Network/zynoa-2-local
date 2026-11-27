import test from "node:test";
import assert from "node:assert/strict";
import {decodeModelEvent,decodeModelReply,modelAvailable,modelSelectValue,retryAvailable,recoverRetryTarget,currentContext} from "../.ui-tests/model-contract.js";
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
 const snapshot={conversationId:"thread_alpha",conversationRevision:5,settingsRevision:2,draft:"hello",inspection};
 assert.equal(currentContext(snapshot,"thread_alpha",5,settings,"hello"),inspection);
 assert.equal(currentContext(snapshot,"thread_alpha",5,settings,"changed"),null);
 assert.equal(currentContext(snapshot,"thread_alpha",6,settings,"hello"),null);
 assert.equal(currentContext(snapshot,"thread_alpha",null,settings,"hello"),null);
 assert.equal(currentContext(snapshot,"thread_bravo",5,settings,"hello"),null);
 assert.equal(currentContext(snapshot,"thread_alpha",5,{...settings,revision:3},"hello"),null);
 assert.equal(currentContext(snapshot,"thread_alpha",5,{...settings,contextLimit:1024},"hello"),null);
 assert.equal(currentContext(snapshot,"thread_alpha",5,null,"hello"),null);
});
test("settings acknowledgement must match the requested choice and stream cannot skip sequence",()=>{
 const command="inference.settings.set",correlation="correlation-00001";
 const payload={conversationId:"thread-alpha-0001",model:"qwen2.5:0.5b",contextLimit:2048};
 const settings={model:payload.model,contextLimit:2048,revision:2};
 assert.throws(()=>decodeModelReply(root(command,correlation,{settings:{...settings,model:"another:1b"}}),command,correlation,payload));
 assert.throws(()=>decodeModelReply(root(command,correlation,{settings:{...settings,contextLimit:1024}}),command,correlation,payload));
 assert.throws(()=>decodeModelEvent({schemaVersion:1,turnId:"turn-alpha-00001",sequence:3,kind:"delta",content:"gap"},"turn-alpha-00001",1));
});

test("recover retry from final cancelled or failed history without stale or save-only targets",()=>{
 const cid="thread_alpha",other="thread_bravo";
 const row=(id,ordinal,role,status,parentId=null,attachments=[])=>({id,ordinal,role,status,parentId,attachments,content:"synthetic",revision:1,createdAt:1});
 const user=row("user_001",1,"user","complete");
 const stopped=row("asst_001",2,"assistant","cancelled",user.id);
 const failed=row("asst_002",3,"assistant","failed",user.id);
 const done=row("asst_003",4,"assistant","complete",user.id);
 const target={conversationId:cid,parentId:user.id};
 assert.deepEqual(recoverRetryTarget([user,stopped],null,cid,null),target);
 assert.deepEqual(recoverRetryTarget([user,stopped,failed],null,cid,null),target);
 assert.equal(recoverRetryTarget([user,stopped],2,cid,null),null);
 assert.equal(recoverRetryTarget([stopped],null,cid,null),null);
 assert.equal(recoverRetryTarget([user,stopped,failed,done],null,cid,target),null);
 assert.equal(recoverRetryTarget([user,stopped,row("user_002",3,"user","complete")],null,cid,target),null);
 assert.equal(recoverRetryTarget([user,stopped,row("asst_999",3,"assistant","failed","other_user")],null,cid,null),null);
 assert.equal(recoverRetryTarget([user],null,cid,null),null);
 assert.deepEqual(recoverRetryTarget([user],null,cid,target),target);
 assert.equal(recoverRetryTarget([user],null,other,target),null);
 assert.equal(recoverRetryTarget([user,stopped],null,null,target),null);
 assert.equal(recoverRetryTarget([{...user,attachments:[{id:"artifact_1"}]},stopped],null,cid,target),null);
 assert.equal(recoverRetryTarget([user,done,failed],null,cid,target),null);
});

test("model selector never displays an unacknowledged replacement",()=>{
 const saved={model:"qwen2.5:0.5b",contextLimit:2048,revision:2};
 const original={name:saved.model,digest:"original",size:10};
 const alternative={name:"qwen2.5:1.5b",digest:"alternative",size:20};
 assert.equal(modelSelectValue(saved,[original,alternative],"0.40.18"),saved.model);
 assert.equal(modelSelectValue(saved,[alternative],"0.40.18"),"");
 assert.equal(modelAvailable(saved,[alternative],"0.40.18"),false);
 assert.equal(modelSelectValue(saved,[],"0.40.18"),"");
 assert.equal(modelSelectValue(saved,[original],""),"");
 assert.equal(modelSelectValue(null,[alternative],"0.40.18"),"");
 assert.equal(modelSelectValue({...saved,model:alternative.name,revision:3},[alternative],"0.40.18"),alternative.name);
 assert.equal(modelSelectValue(saved,[original],"0.40.18"),saved.model);
});

test("native artifact receipts do not mask a later interrupted turn",()=>{
 const cid="thread-alpha-0001";
 const row=(id,ordinal,role,status,parentId=null)=>({id,ordinal,role,status,parentId,attachments:[],content:"synthetic",revision:1,createdAt:1});
 const first=row("user-first-0001",1,"user","complete");
 const done=row("assistant-done-0001",2,"assistant","complete",first.id);
 const latest=row("user-latest-0001",3,"user","complete");
 const stopped=row("assistant-stop-0001",4,"assistant","cancelled",latest.id);
 const receipt={...row("a".repeat(64),5,"system","complete",done.id),content:"Saved assistant response as text artifact.",attachments:[{id:"b".repeat(64),name:"assistant-response.txt",bytes:9,sha256:"c".repeat(64)}]};
 const history=[first,done,latest,stopped,receipt];
 assert.deepEqual(recoverRetryTarget(history,null,cid,null),{conversationId:cid,parentId:latest.id});
 assert.equal(recoverRetryTarget(history,5,cid,null),null);
 assert.equal(recoverRetryTarget([...history.slice(0,-1),{...receipt,parentId:stopped.id}],null,cid,null),null);
 assert.equal(recoverRetryTarget([first,done,receipt],null,cid,null),null);
});


test("durable zero-output terminal notice restores only exact original retry parent",()=>{
 const cid="thread_alpha";
 const row=(id,ordinal,role,status,parentId=null)=>({id,ordinal,role,status,parentId,attachments:[],content:"synthetic",revision:1,createdAt:1});
 const user=row("user_001",1,"user","complete");
 const stopped={...row("attempt_001",2,"system","cancelled",user.id),content:"No assistant text was produced before this turn ended."};
 const failed={...stopped,id:"attempt_002",ordinal:3,status:"failed"};
 const target={conversationId:cid,parentId:user.id};
 assert.deepEqual(recoverRetryTarget([user,stopped],null,cid,null),target);
 assert.deepEqual(recoverRetryTarget([user,stopped,failed],null,cid,null),target);
 assert.equal(recoverRetryTarget([user,stopped],2,cid,null),null);
 assert.equal(recoverRetryTarget([user,{...stopped,content:"other system notice"}],null,cid,null),null);
 assert.equal(recoverRetryTarget([user,{...stopped,parentId:"other_user"}],null,cid,null),null);
 assert.equal(recoverRetryTarget([user,{...stopped,attachments:[{id:"unexpected"}]}],null,cid,null),null);
 assert.equal(recoverRetryTarget([user,stopped,row("assistant_003",3,"assistant","complete",user.id)],null,cid,null),null);
});
