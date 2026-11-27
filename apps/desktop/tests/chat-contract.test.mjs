import test from "node:test";
import assert from "node:assert/strict";
import { decodeReply,validText,byteLength,validSelection,validAttachmentName,recoveryRows } from "../.ui-tests/chat-contract.js";
const thread={id:"thread-alpha-001",title:"Saved",revision:2,createdAt:1,updatedAt:2};
const msg={id:"message-alpha-001",parentId:null,ordinal:1,role:"user",content:"<script>plain text</script>",status:"complete",revision:1,createdAt:1,attachments:[]};
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
test("attachment metadata is bounded, validated and never grants path authority",()=>{
 const q={conversationId:thread.id,after:0,limit:1};
 const a={id:"artifact-alpha-001",name:"note.txt",bytes:23,sha256:"a".repeat(64)};
 const withAttachments=attachments=>({conversation:thread,items:[{...msg,attachments}],next:null});
 assert.deepEqual(decode("chat.history",withAttachments([a]),q).items[0].attachments,[a]);
 for(const invalid of [[{...a,name:"../outside"}],[{...a,name:"NUL.txt"}],[{...a,bytes:-1}],[{...a,bytes:25*1024*1024+1}],[{...a,sha256:"bad"}],[{...a,path:"outside"}],[a,a],Array.from({length:5},(_,i)=>({...a,id:"artifact-alpha-00"+i,bytes:25*1024*1024}))]){
  assert.throws(()=>decode("chat.history",withAttachments(invalid),q),/ZYN-CHAT-RESPONSE/);
 }
});
test("stale correlation and unverified acknowledgement rejected",()=>{
 const q={id:msg.id,conversationId:thread.id,parentId:null,content:msg.content};
 const ack={receipt:{id:msg.id,revision:1,conversationRevision:2,ordinal:1},replayed:true};
 assert.deepEqual(decode("chat.saveUserMessage",ack,q),ack);
 assert.throws(()=>decodeReply(wrap("chat.saveUserMessage",ack),"chat.saveUserMessage","different-correlation",q),/ZYN-CHAT-RESPONSE/);
 assert.throws(()=>decode("chat.saveUserMessage",{...ack,receipt:{...ack.receipt,id:"wrong-message-001"}},q),/ZYN-CHAT-RESPONSE/);
 assert.throws(()=>decode("chat.saveUserMessage",{...ack,receipt:{...ack.receipt,ordinal:null}},q),/ZYN-CHAT-RESPONSE/);
});

test("file selection limits and names match native policy",()=>{
 assert.equal(validSelection([{name:"résumé.txt",size:0},{name:"note.txt",size:25*1024*1024}]),true);
 for(const name of ["../x","NUL.txt","COM1 .txt","a.","a ",".hidden","x:y"])assert.equal(validAttachmentName(name),false);
 assert.equal(validSelection(Array.from({length:9},()=>({name:"x",size:0}))),false);
 assert.equal(validSelection(Array.from({length:5},()=>({name:"x",size:25*1024*1024}))),false);
 assert.equal(validSelection([{name:"x",size:25*1024*1024+1}]),false);
});
test("upload acknowledgements bind exact scope, offset and final manifest",()=>{
 const q={conversationId:thread.id,messageId:msg.id,artifactId:"artifact-alpha-001",name:"note.txt",total:2,offset:0,chunk:[1,2]};
 const a={id:q.artifactId,name:q.name,bytes:2,sha256:"a".repeat(64)};
 const ack={conversationId:q.conversationId,messageId:q.messageId,artifactId:q.artifactId,received:2,attachment:a};
 assert.deepEqual(decode("chat.attachment.chunk",ack,q),ack);
 for(const bad of [{...ack,received:1},{...ack,messageId:"wrong-message-001"},{...ack,attachment:null},{...ack,attachment:{...a,bytes:3}},{...ack,attachment:{...a,name:"other.txt"}}])assert.throws(()=>decode("chat.attachment.chunk",bad,q),/ZYN-CHAT-RESPONSE/);
 const partial={...q,total:3};
 assert.equal(decode("chat.attachment.chunk",{...ack,attachment:null},partial).attachment,null);
 assert.throws(()=>decode("chat.attachment.chunk",ack,partial),/ZYN-CHAT-RESPONSE/);
 const discard={conversationId:q.conversationId,messageId:q.messageId};
 assert.deepEqual(decode("chat.attachment.discard",{...discard,discarded:true},discard),{...discard,discarded:true});
 assert.throws(()=>decode("chat.attachment.discard",{...discard,discarded:false},discard),/ZYN-CHAT-RESPONSE/);
});

test("managed recovery inventory exposes counts only, with consistent bounded totals",()=>{
 const report={referencedHashes:2,verifiedReferenced:1,verifiedUnreferenced:1,unavailableReferenced:1,damagedOrUnreadable:1,interruptedStages:1,unexpectedEntries:0,unlinkedMetadata:0};
 assert.deepEqual(decode("chat.recovery.inspect",report,{}),report);
 assert.deepEqual(recoveryRows(report),["Referenced hashes: 2","Verified referenced: 1","Unavailable referenced: 1","Verified unreferenced: 1","Damaged or unreadable: 1","Interrupted stages: 1","Unexpected entries: 0","Unlinked metadata: 0"]);
 for(const invalid of [{...report,path:"outside"},{...report,referencedHashes:1},{...report,verifiedReferenced:-1},{...report,interruptedStages:4097},{...report,unexpectedEntries:0.5},{...report,unlinkedMetadata:"0"}]){
  assert.throws(()=>decode("chat.recovery.inspect",invalid,{}),/ZYN-CHAT-RESPONSE/);
 }
});
