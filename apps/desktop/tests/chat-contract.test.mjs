import test from "node:test";
import assert from "node:assert/strict";
import { decodeReply,validText,byteLength } from "../.ui-tests/chat-contract.js";
const thread={id:"thread-alpha-001",title:"Saved",revision:2,createdAt:1,updatedAt:2};
const msg={id:"message-alpha-001",parentId:null,ordinal:1,role:"user",content:"<script>plain text</script>",status:"complete",revision:1,createdAt:1};
const wrap=(commandId,data)=>({schemaVersion:1,commandId,correlationId:"correlation-00001",data});
const decode=(cmd,data,payload)=>decodeReply(wrap(cmd,data),cmd,"correlation-00001",payload);
test("UTF-8 byte bounds and NUL/whitespace rejection",()=>{
 assert.equal(byteLength("é"),2);
 assert.equal(validText("é".repeat(256),512),true);
 assert.equal(validText("é".repeat(257),512),false);
 assert.equal(validText("  ",512),false);
 assert.equal(validText("x\0y",512),false);
});
test("list and history are scoped, ordered and bounded",()=>{
 assert.deepEqual(decode("chat.list",{items:[thread],next:null},{after:null,limit:1}).items,[thread]);
 const q={conversationId:thread.id,after:0,limit:1};
 assert.deepEqual(decode("chat.history",{conversation:thread,items:[msg],next:null},q).items,[msg]);
 for(const data of [{conversation:{...thread,id:"other-thread-001"},items:[msg],next:null},{conversation:thread,items:[msg,msg],next:null},{conversation:thread,items:[msg],next:99},{conversation:thread,items:[{...msg,role:"tool"}],next:null}]){
  assert.throws(()=>decode("chat.history",data,q),/ZYN-CHAT-RESPONSE/);
 }
 assert.throws(()=>decode("chat.list",{items:[thread],next:"other-thread-001"},{after:null,limit:1}),/ZYN-CHAT-RESPONSE/);
});
test("stale correlation and unverified acknowledgement rejected",()=>{
 const q={id:msg.id,conversationId:thread.id,parentId:null,content:msg.content};
 const ack={receipt:{id:msg.id,revision:1,conversationRevision:2,ordinal:1},replayed:true};
 assert.deepEqual(decode("chat.saveUserMessage",ack,q),ack);
 assert.throws(()=>decodeReply(wrap("chat.saveUserMessage",ack),"chat.saveUserMessage","different-correlation",q),/ZYN-CHAT-RESPONSE/);
 assert.throws(()=>decode("chat.saveUserMessage",{...ack,receipt:{...ack.receipt,id:"wrong-message-001"}},q),/ZYN-CHAT-RESPONSE/);
 assert.throws(()=>decode("chat.saveUserMessage",{...ack,receipt:{...ack.receipt,ordinal:null}},q),/ZYN-CHAT-RESPONSE/);
});
