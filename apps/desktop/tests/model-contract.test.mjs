import test from "node:test";
import assert from "node:assert/strict";
import {decodeModelEvent,decodeModelReply} from "../.ui-tests/model-contract.js";
const root=(command,correlationId,data)=>({schemaVersion:1,commandId:command,correlationId,data});
test("model health accepts bounded installed inventory and rejects extra authority",()=>{
 const ok=decodeModelReply(root("inference.health","correlation-00001",{version:"0.40.18",models:[{name:"qwen2.5:0.5b",digest:"abc",size:10}]}),"inference.health","correlation-00001",{});
 assert.equal(ok.models[0].name,"qwen2.5:0.5b");
 assert.throws(()=>decodeModelReply({...root("inference.health","correlation-00001",{version:"x",models:[]}),url:"http://remote"},"inference.health","correlation-00001",{}));
});
test("settings and context require exact bounded fields",()=>{
 const settings=decodeModelReply(root("inference.settings.set","correlation-00001",{settings:{model:"qwen2.5:0.5b",contextLimit:2048,revision:2}}),"inference.settings.set","correlation-00001",{conversationId:"thread-alpha-0001",model:"qwen2.5:0.5b",contextLimit:2048});
 assert.equal(settings.settings.revision,2);
 assert.throws(()=>decodeModelReply(root("inference.settings.set","correlation-00001",{settings:{model:"https://remote",contextLimit:777,revision:2}}),"inference.settings.set","correlation-00001",{conversationId:"thread-alpha-0001",model:"https://remote",contextLimit:777}));
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
