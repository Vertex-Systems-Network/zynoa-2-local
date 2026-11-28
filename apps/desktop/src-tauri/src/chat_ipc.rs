//! M03 fixed local-domain commands. No generic SQL, path, tool or network authority.
use crate::vault::{NativeVault, VaultFault, ChatMessageInput, ChatRole, ChatStatus, ConversationSummary, StoredChatMessage, ChatWriteReceipt, LinkedAttachment};
use serde::{Deserialize, Serialize};
use serde_json::{Value, json};

const MAX_REQUEST_BYTES: usize = 1_600_000;
const MAX_RESPONSE_BYTES: usize = 1_600_000;
const MAX_THREADS: u32 = 50;
const MAX_MESSAGES: u32 = 4;

#[derive(Deserialize)]
#[serde(rename_all="camelCase", deny_unknown_fields)]
pub struct ChatRequest {
    schema_version: u8,
    command_id: String,
    correlation_id: String,
    workspace_scope: String,
    payload: Value,
}
#[derive(Serialize, Debug)]
#[serde(rename_all="camelCase")]
pub struct ChatError { code: &'static str, recovery_action: &'static str }
fn error(code: &'static str) -> ChatError {
    ChatError { code, recovery_action: "Refresh local history; preserve your draft and retry only the same ID." }
}
impl From<VaultFault> for ChatError {
    fn from(fault: VaultFault) -> Self {
        error(match fault {
            VaultFault::InvalidRecord => "ZYN-CHAT-INPUT",
            VaultFault::Conflict => "ZYN-CHAT-CONFLICT",
            _ => "ZYN-CHAT-STORAGE",
        })
    }
}
#[derive(Serialize)]
#[serde(rename_all="camelCase")]
pub struct ChatReply {
    schema_version: u8, command_id: String, correlation_id: String, data: Value,
}
#[derive(Deserialize)]
#[serde(rename_all="camelCase",deny_unknown_fields)]
struct ListPayload { after: Option<String>, limit: u32 }
#[derive(Deserialize)]
#[serde(deny_unknown_fields)]
struct RecoveryPayload {}
#[derive(Deserialize)]
#[serde(rename_all="camelCase",deny_unknown_fields)]
struct TextArtifactPayload { conversation_id:String, source_id:String }
#[derive(Deserialize)]
#[serde(rename_all="camelCase",deny_unknown_fields)]
struct ReviewBeginPayload { conversation_id:String, source_id:String, attachment_id:Option<String> }
#[derive(Deserialize)]
#[serde(rename_all="camelCase",deny_unknown_fields)]
struct ReviewFinishPayload { conversation_id:String, request_id:String, decision:String }
#[derive(Deserialize)]
#[serde(rename_all="camelCase",deny_unknown_fields)]
struct ReviewListPayload { conversation_id:String, after:Option<String>,limit:u32 }
#[derive(Deserialize)]
#[serde(rename_all="camelCase",deny_unknown_fields)]
struct ExportPayload { conversation_id:String, revision:i64, export_id:String, destination:String }
#[derive(Deserialize)]
#[serde(rename_all="camelCase",deny_unknown_fields)]
struct CreatePayload { id: String, title: String }
#[derive(Deserialize)]
#[serde(rename_all="camelCase",deny_unknown_fields)]
struct HistoryPayload { conversation_id: String, after: i64, limit: u32 }
#[derive(Deserialize)]
#[serde(rename_all="camelCase",deny_unknown_fields)]
struct SavePayload { id: String, conversation_id: String, parent_id: Option<String>, content: String,
    #[serde(default)] attachments: Vec<AttachmentManifest> }
#[derive(Deserialize)]
#[serde(rename_all="camelCase",deny_unknown_fields)]
struct AttachmentManifest { id:String, name:String, bytes:u64, sha256:String }
#[derive(Deserialize)]
#[serde(rename_all="camelCase",deny_unknown_fields)]
struct UploadPayload { conversation_id:String, message_id:String, artifact_id:String,
    name:String,total:u64,offset:u64,chunk:Vec<u8> }
#[derive(Deserialize)]
#[serde(rename_all="camelCase",deny_unknown_fields)]
struct DiscardPayload { conversation_id:String,message_id:String }

fn manifest(items: Vec<AttachmentManifest>) -> Result<Vec<LinkedAttachment>,ChatError> {
    if items.len()>8 { return Err(error("ZYN-CHAT-INPUT")); }
    let mut ids=std::collections::HashSet::new();
    let mut total=0u64;
    let mut result=Vec::new();
    for a in items {
        total=total.checked_add(a.bytes).ok_or_else(||error("ZYN-CHAT-INPUT"))?;
        if !token(&a.id)||!ids.insert(a.id.clone())
            || !crate::artifact_contracts::valid_managed_basename(&a.name)
            || a.bytes>crate::artifact_contracts::MAX_ATTACHMENT||total>100*1024*1024
            || a.sha256.len()!=64||!a.sha256.bytes().all(|b|b.is_ascii_digit()||(b'a'..=b'f').contains(&b)) {
            return Err(error("ZYN-CHAT-INPUT"));
        }
        result.push(LinkedAttachment{id:a.id,receipt:crate::artifact_contracts::AttachmentReceipt{
            name:a.name,bytes:a.bytes,sha256:a.sha256}});
    }
    Ok(result)
}
fn same_attachments(a:&[LinkedAttachment],b:&[LinkedAttachment])->bool {
    a.len()==b.len()&&a.iter().zip(b).all(|(x,y)|x.id==y.id&&x.receipt==y.receipt)
}

fn summary(row:&ConversationSummary)->Value {
    json!({"id":row.id,"title":row.title,"revision":row.revision,"createdAt":row.created_at,"updatedAt":row.updated_at})
}
fn message(vault:&NativeVault,conversation_id:&str,row:&StoredChatMessage)->Result<Value,ChatError> {
    let attachments=vault.list_message_attachments(conversation_id,&row.id)?;
    // Metadata only: no original path, bytes, preview URL or filesystem authority.
    let attachments=attachments.iter().map(|a|json!({
        "id":a.id,"name":a.receipt.name,"bytes":a.receipt.bytes,"sha256":a.receipt.sha256
    })).collect::<Vec<_>>();
    Ok(json!({"id":row.id,"parentId":row.parent_id,"ordinal":row.ordinal,"role":row.role,"content":row.content,
        "status":row.status,"revision":row.revision,"createdAt":row.created_at,"attachments":attachments}))
}
fn receipt(row:&ChatWriteReceipt)->Value {
    json!({"id":row.id,"revision":row.revision,"conversationRevision":row.conversation_revision,"ordinal":row.ordinal})
}
fn parse<T: serde::de::DeserializeOwned>(value: Value) -> Result<T,ChatError> {
    serde_json::from_value(value).map_err(|_|error("ZYN-CHAT-INPUT"))
}
fn token(value:&str) -> bool {
    (16..=64).contains(&value.len()) && value.bytes().all(|b| b.is_ascii_alphanumeric() || b==b'-')
}
fn authorize_request(label:&str, request:&ChatRequest) -> Result<(),ChatError> {
    crate::security::allow_local_chat(label).map_err(|_|error("ZYN-CHAT-DENIED"))?;
    if request.schema_version!=1 || request.workspace_scope!="local" || !token(&request.correlation_id) {
        return Err(error("ZYN-CHAT-INPUT"));
    }
    if !matches!(request.command_id.as_str(),"chat.list"|"chat.create"|"chat.history"|"chat.saveUserMessage"|"chat.attachment.chunk"|"chat.attachment.discard"|"chat.recovery.inspect"|"chat.artifact.createText"|"chat.artifact.previewText"|"chat.review.begin"|"chat.review.finish"|"chat.review.list"|"chat.export.conversation") {
        return Err(error("ZYN-CHAT-DENIED"));
    }
    if serde_json::to_vec(&request.payload).map_err(|_|error("ZYN-CHAT-INPUT"))?.len()>MAX_REQUEST_BYTES {
        return Err(error("ZYN-CHAT-INPUT"));
    }
    Ok(())
}
fn execute(vault:&mut NativeVault, request:ChatRequest) -> Result<ChatReply,ChatError> {
    let data=match request.command_id.as_str() {
        "chat.export.conversation" => {
            let q:ExportPayload=parse(request.payload)?;
            if !token(&q.conversation_id)||!token(&q.export_id)||q.revision<=0||q.destination!="local-data-exports" {
                return Err(error("ZYN-CHAT-INPUT"));
            }
            serde_json::to_value(vault.export_conversation(&q.conversation_id,q.revision,&q.export_id)?)
                .map_err(|_|error("ZYN-CHAT-STORAGE"))?
        },
        "chat.review.begin" => {
            let q:ReviewBeginPayload=parse(request.payload)?;
            if !token(&q.conversation_id)||!token(&q.source_id)||q.attachment_id.as_ref().is_some_and(|id|!token(id)) {
                return Err(error("ZYN-CHAT-INPUT"));
            }
            serde_json::to_value(vault.begin_tool_review(&q.conversation_id,&q.source_id,q.attachment_id.as_deref())?)
                .map_err(|_|error("ZYN-CHAT-STORAGE"))?
        },
        "chat.review.finish" => {
            let q:ReviewFinishPayload=parse(request.payload)?;
            if !token(&q.conversation_id)||!token(&q.request_id) {return Err(error("ZYN-CHAT-INPUT"));}
            use crate::artifact_contracts::ReviewChoice;
            let choice=match q.decision.as_str(){"approve"=>ReviewChoice::Approve,"deny"=>ReviewChoice::Deny,
                _=>return Err(error("ZYN-CHAT-INPUT"))};
            let executed=vault.finish_tool_review(&q.conversation_id,&q.request_id,choice)?;
            json!({"conversationId":q.conversation_id,"requestId":q.request_id,"decision":q.decision,"executed":executed})
        },
        "chat.review.list" => {
            let q:ReviewListPayload=parse(request.payload)?;
            if !token(&q.conversation_id)||q.after.as_ref().is_some_and(|id|!token(id))||!(1..=50).contains(&q.limit) {
                return Err(error("ZYN-CHAT-INPUT"));
            }
            let mut items=vault.list_tool_reviews(&q.conversation_id,q.after.as_deref(),q.limit+1)?;
            let more=items.len()>q.limit as usize;items.truncate(q.limit as usize);
            let items=serde_json::to_value(items).map_err(|_|error("ZYN-CHAT-STORAGE"))?;
            let next=if more {items.as_array().and_then(|a|a.last()).and_then(|a|a.get("requestId")).cloned().ok_or_else(||error("ZYN-CHAT-STORAGE"))?}else{Value::Null};
            json!({"conversationId":q.conversation_id,"items":items,"next":next})
        },
        "chat.artifact.createText" => {
            let q:TextArtifactPayload=parse(request.payload)?;
            if !token(&q.conversation_id)||!token(&q.source_id) {return Err(error("ZYN-CHAT-INPUT"));}
            let saved=vault.create_text_artifact(&q.conversation_id,&q.source_id)?;
            let a=&saved.attachment;
            json!({"conversationId":q.conversation_id,"sourceId":saved.source_id,"messageId":saved.message_id,
                "attachment":{"id":a.id,"name":a.receipt.name,"bytes":a.receipt.bytes,"sha256":a.receipt.sha256},
                "replayed":saved.replayed})
        },
        "chat.artifact.previewText" => {
            let q:TextArtifactPayload=parse(request.payload)?;
            if !token(&q.conversation_id)||!token(&q.source_id) {return Err(error("ZYN-CHAT-INPUT"));}
            let content=vault.preview_text_artifact(&q.conversation_id,&q.source_id)?;
            json!({"conversationId":q.conversation_id,"sourceId":q.source_id,"content":content})
        },
        "chat.recovery.inspect" => {
            if !request.payload.is_object() {return Err(error("ZYN-CHAT-INPUT"));}
            let _:RecoveryPayload=parse(request.payload)?;
            let report=vault.inspect_managed_recovery()?;
            // Counts only: no paths, content, file access or mutation authority.
            json!({"referencedHashes":report.referenced_hashes,
                "verifiedReferenced":report.verified_referenced,
                "verifiedUnreferenced":report.verified_unreferenced,
                "unavailableReferenced":report.unavailable_referenced,
                "damagedOrUnreadable":report.damaged_or_unreadable,
                "interruptedStages":report.interrupted_stages,
                "unexpectedEntries":report.unexpected_entries,
                "unlinkedMetadata":report.unlinked_metadata})
        },
        "chat.list" => {
            let q:ListPayload=parse(request.payload)?;
            if !(1..=MAX_THREADS).contains(&q.limit) { return Err(error("ZYN-CHAT-INPUT")); }
            let mut items=vault.list_conversations(q.after.as_deref(),q.limit+1)?;
            let more=items.len()>q.limit as usize;
            items.truncate(q.limit as usize);
            let next=if more {items.last().map(|x| x.id.clone())} else {None};
            json!({"items":items.iter().map(summary).collect::<Vec<_>>(),"next":next})
        },
        "chat.create" => {
            let q:CreatePayload=parse(request.payload)?;
            if !token(&q.id) {return Err(error("ZYN-CHAT-INPUT"));}
            match vault.create_conversation(&q.id,&q.title) {
                Ok(row)=>json!({"receipt":receipt(&row),"replayed":false}),
                Err(VaultFault::Conflict)=>{
                    let row=vault.get_conversation(&q.id)?.ok_or_else(||error("ZYN-CHAT-CONFLICT"))?;
                    if row.title!=q.title {return Err(error("ZYN-CHAT-CONFLICT"));}
                    json!({"receipt":{"id":row.id,"revision":1,"conversationRevision":row.revision,"ordinal":null},"replayed":true})
                },
                Err(e)=>return Err(e.into()),
            }
        },
        "chat.history" => {
            let q:HistoryPayload=parse(request.payload)?;
            if !(1..=MAX_MESSAGES).contains(&q.limit) || q.after<0 {return Err(error("ZYN-CHAT-INPUT"));}
            let thread=vault.get_conversation(&q.conversation_id)?.ok_or_else(||error("ZYN-CHAT-NOT-FOUND"))?;
            let mut items=vault.list_chat_messages(&q.conversation_id,q.after,q.limit+1)?;
            let mut more=items.len()>q.limit as usize;
            items.truncate(q.limit as usize);
            loop {
                let next=if more {items.last().map(|x| x.ordinal)} else {None};
                let history=items.iter().map(|row|message(vault,&q.conversation_id,row))
                    .collect::<Result<Vec<_>,ChatError>>()?;
                let candidate=json!({"conversation":summary(&thread),"items":history,"next":next});
                if serde_json::to_vec(&candidate).map_err(|_|error("ZYN-CHAT-STORAGE"))?.len()<=MAX_RESPONSE_BYTES {break candidate;}
                if items.len()<=1 {return Err(error("ZYN-CHAT-STORAGE"));}
                items.pop(); more=true;
            }
        },
        "chat.attachment.chunk" => {
            let q:UploadPayload=parse(request.payload)?;
            if !token(&q.message_id)||!token(&q.artifact_id) {return Err(error("ZYN-CHAT-INPUT"));}
            let end=q.offset.checked_add(q.chunk.len() as u64).ok_or_else(||error("ZYN-CHAT-INPUT"))?;
            let complete=vault.upload_attachment_chunk(&q.conversation_id,&q.message_id,&q.artifact_id,
                &q.name,q.total,q.offset,&q.chunk)?;
            let attachment=complete.map(|a|json!({"id":q.artifact_id,"name":a.name,"bytes":a.bytes,"sha256":a.sha256}));
            json!({"conversationId":q.conversation_id,"messageId":q.message_id,"artifactId":q.artifact_id,
                "received":end,"attachment":attachment})
        },
        "chat.attachment.discard" => {
            let q:DiscardPayload=parse(request.payload)?;
            if !token(&q.message_id) {return Err(error("ZYN-CHAT-INPUT"));}
            vault.discard_attachment_draft(&q.conversation_id,&q.message_id)?;
            json!({"conversationId":q.conversation_id,"messageId":q.message_id,"discarded":true})
        },
        "chat.saveUserMessage" => {
            let q:SavePayload=parse(request.payload)?;
            if !token(&q.id) {return Err(error("ZYN-CHAT-INPUT"));}
            let expected=manifest(q.attachments)?;
            // Reconcile an already committed ID before resolving ephemeral upload
            // bytes. This also supports replay after a native restart.
            if let Some(row)=vault.get_chat_message(&q.conversation_id,&q.id)? {
                let stored=vault.list_message_attachments(&q.conversation_id,&q.id)?;
                if row.content!=q.content || row.parent_id!=q.parent_id || row.role!="user" || row.status!="complete"
                    || !same_attachments(&stored,&expected) {
                    return Err(error("ZYN-CHAT-CONFLICT"));
                }
                for a in &stored {vault.read_managed_blob(&a.receipt)?;}
                let thread=vault.get_conversation(&q.conversation_id)?.ok_or_else(||error("ZYN-CHAT-CONFLICT"))?;
                json!({"receipt":{"id":row.id,"revision":row.revision,"conversationRevision":thread.revision,"ordinal":row.ordinal},"replayed":true})
            } else {
                let input=ChatMessageInput {id:&q.id,conversation_id:&q.conversation_id,parent_id:q.parent_id.as_deref(),
                    content:&q.content,role:ChatRole::User,status:ChatStatus::Complete};
                let row=vault.append_uploaded_message(input,&expected)?;
                json!({"receipt":receipt(&row),"replayed":false})
            }
        },
        _=>return Err(error("ZYN-CHAT-DENIED")),
    };
    if serde_json::to_vec(&data).map_err(|_|error("ZYN-CHAT-STORAGE"))?.len()>MAX_RESPONSE_BYTES {
        return Err(error("ZYN-CHAT-STORAGE"));
    }
    Ok(ChatReply {schema_version:1,command_id:request.command_id,correlation_id:request.correlation_id,data})
}

// Async Tauri dispatch runs off the GUI thread; no await with a vault lock held.
#[tauri::command]
pub async fn chat_request(window:tauri::Window, storage:tauri::State<'_,std::sync::Arc<std::sync::Mutex<NativeVault>>>,
    diagnostics:tauri::State<'_,crate::diagnostics::NativeDiagnostics>,request:ChatRequest)
    -> Result<ChatReply,ChatError>
{
    if let Err(e)=authorize_request(window.label(),&request) {diagnostics.record_denied_ipc();return Err(e);}
    let mut vault=storage.lock().map_err(|_|error("ZYN-CHAT-STORAGE"))?;
    execute(&mut vault,request)
}

#[cfg(test)]
mod tests {
    use super::*;
    const A:&str="thread-alpha-00001";
    const B:&str="thread-other-00001";
    const M:&str="message-alpha-0001";
    struct Fixture(std::path::PathBuf);
    impl Fixture {
        fn new()->Self {
            let stamp=std::time::SystemTime::now().duration_since(std::time::UNIX_EPOCH).unwrap().as_nanos();
            let root=std::env::temp_dir().join(format!("zynoa-chat-{}-{stamp}",std::process::id())).join("com.zynoa.desktop");
            std::fs::create_dir_all(&root).unwrap();Self(root)
        }
    }
    impl Drop for Fixture {fn drop(&mut self){let _=std::fs::remove_dir_all(self.0.parent().unwrap());}}
    fn request(command:&str,payload:Value)->ChatRequest {
        ChatRequest {schema_version:1,command_id:command.into(),correlation_id:"correlation-00001".into(),workspace_scope:"local".into(),payload}
    }
    fn call(v:&mut NativeVault,command:&str,payload:Value)->Result<Value,ChatError> {
        let req=request(command,payload);authorize_request("main",&req)?;Ok(execute(v,req)?.data)
    }
    #[test]
    fn chat_ipc_export_is_local_and_has_no_arbitrary_path_authority() {
        let f=Fixture::new();let mut v=NativeVault::open(&f.0).unwrap();
        call(&mut v,"chat.create",json!({"id":A,"title":"Synthetic"})).unwrap();
        call(&mut v,"chat.saveUserMessage",json!({"id":M,"conversationId":A,"content":"Prompt"})).unwrap();
        let q=json!({"conversationId":A,"revision":2,"exportId":"export-alpha-00001","destination":"local-data-exports"});
        assert!(authorize_request("remote",&request("chat.export.conversation",q.clone())).is_err());
        let mut bad=q.clone();bad["path"]=json!("outside");
        assert!(call(&mut v,"chat.export.conversation",bad).is_err());
        let mut bad=q.clone();bad["destination"]=json!("outside");
        assert!(call(&mut v,"chat.export.conversation",bad).is_err());
        let ack=call(&mut v,"chat.export.conversation",q.clone()).unwrap();
        assert_eq!(ack["messageCount"],1);
        assert_eq!(ack["relativePath"],"data/exports/conversation-export-alpha-00001.json");
        assert!(call(&mut v,"chat.export.conversation",q).is_err());
    }

    #[test]
    fn chat_ipc_review_is_local_scoped_single_use_and_strict() {
        let f=Fixture::new();let mut v=NativeVault::open(&f.0).unwrap();
        for id in [A,B] {call(&mut v,"chat.create",json!({"id":id,"title":"Synthetic"})).unwrap();}
        call(&mut v,"chat.saveUserMessage",json!({"id":M,"conversationId":A,"content":"Prompt"})).unwrap();
        let source="assistant-alpha-01";
        v.append_chat_message(ChatMessageInput{id:source,conversation_id:A,parent_id:Some(M),role:ChatRole::Assistant,
            content:"Synthetic answer",status:ChatStatus::Complete}).unwrap();
        let q=json!({"conversationId":A,"sourceId":source,"attachmentId":null});
        assert!(authorize_request("remote",&request("chat.review.begin",q.clone())).is_err());
        assert!(call(&mut v,"chat.review.begin",json!({"conversationId":A,"sourceId":source,"path":"outside"})).is_err());
        assert!(call(&mut v,"chat.review.begin",json!({"conversationId":B,"sourceId":source})).is_err());
        let p=call(&mut v,"chat.review.begin",q.clone()).unwrap();
        assert_eq!(p["tool"],"local.write_artifact");
        assert_eq!(p["sourceId"],source);
        let id=p["requestId"].as_str().unwrap();
        assert!(call(&mut v,"chat.review.finish",json!({"conversationId":B,"requestId":id,"decision":"approve"})).is_err());
        assert!(call(&mut v,"chat.review.finish",json!({"conversationId":A,"requestId":id,"decision":"allow"})).is_err());
        let deny=json!({"conversationId":A,"requestId":id,"decision":"deny"});
        assert_eq!(call(&mut v,"chat.review.finish",deny.clone()).unwrap()["executed"],false);
        assert!(call(&mut v,"chat.review.finish",deny).is_err());
        let p=call(&mut v,"chat.review.begin",q).unwrap();
        let approve=json!({"conversationId":A,"requestId":p["requestId"],"decision":"approve"});
        assert_eq!(call(&mut v,"chat.review.finish",approve.clone()).unwrap()["executed"],true);
        assert!(call(&mut v,"chat.review.finish",approve).is_err());
        drop(v);let mut v=NativeVault::open(&f.0).unwrap();
        let trace=call(&mut v,"chat.review.list",json!({"conversationId":A,"limit":50,"after":null})).unwrap();
        assert_eq!(trace["items"].as_array().unwrap().len(),2);
        assert_eq!(call(&mut v,"chat.review.list",json!({"conversationId":B,"limit":50})).unwrap()["items"],json!([]));
        assert!(call(&mut v,"chat.review.list",json!({"conversationId":A,"limit":51})).is_err());
    }

    #[test]
    fn chat_ipc_denies_wrong_window_scope_version_and_unknown_fields() {
        let mut req=request("chat.list",json!({"limit":1}));
        assert!(authorize_request("remote",&req).is_err());
        req.workspace_scope="external".into();assert!(authorize_request("main",&req).is_err());
        req.workspace_scope="local".into();req.schema_version=2;assert!(authorize_request("main",&req).is_err());
        req.schema_version=1;req.command_id="chat.delete".into();assert!(authorize_request("main",&req).is_err());
        assert!(parse::<SavePayload>(json!({"id":M,"conversationId":A,"content":"x","role":"assistant"})).is_err());
        assert!(parse::<CreatePayload>(json!({"id":A,"title":"x","path":"outside"})).is_err());
        assert!(serde_json::from_value::<ChatRequest>(json!({"schemaVersion":1,"commandId":"chat.list","correlationId":"correlation-00001","workspaceScope":"local","payload":{},"authority":true})).is_err());
        assert!(authorize_request("main",&request("chat.create",json!({"id":A,"title":"x".repeat(MAX_REQUEST_BYTES+1)}))).is_err());
    }
    #[test]
    fn chat_ipc_replay_conflict_and_reopen() {
        let f=Fixture::new();let mut v=NativeVault::open(&f.0).unwrap();
        let create=json!({"id":A,"title":"Synthetic thread"});
        assert_eq!(call(&mut v,"chat.create",create.clone()).unwrap()["replayed"],false);
        assert_eq!(call(&mut v,"chat.create",create).unwrap()["replayed"],true);
        assert!(call(&mut v,"chat.create",json!({"id":A,"title":"overwrite"})).is_err());
        let save=json!({"id":M,"conversationId":A,"parentId":null,"content":"Synthetic persisted message"});
        assert_eq!(call(&mut v,"chat.saveUserMessage",save.clone()).unwrap()["replayed"],false);
        drop(v);let mut v=NativeVault::open(&f.0).unwrap();
        assert_eq!(call(&mut v,"chat.saveUserMessage",save).unwrap()["replayed"],true);
        assert!(call(&mut v,"chat.saveUserMessage",json!({"id":M,"conversationId":A,"content":"wrong"})).is_err());
        let h=call(&mut v,"chat.history",json!({"conversationId":A,"after":0,"limit":4})).unwrap();
        assert_eq!(h["items"].as_array().unwrap().len(),1);
        assert_eq!(h["items"][0]["content"],"Synthetic persisted message");
        assert_eq!(h["items"][0]["role"],"user");assert_eq!(h["conversation"]["revision"],2);
    }
    #[test]
    fn chat_ipc_scopes_history_and_bounds_pagination() {
        let f=Fixture::new();let mut v=NativeVault::open(&f.0).unwrap();
        for id in [B,A] {call(&mut v,"chat.create",json!({"id":id,"title":"Synthetic"})).unwrap();}
        let list=call(&mut v,"chat.list",json!({"limit":1})).unwrap();
        assert_eq!(list["items"][0]["id"],A);assert_eq!(list["next"],A);
        let next=call(&mut v,"chat.list",json!({"limit":1,"after":A})).unwrap();
        assert_eq!(next["items"][0]["id"],B);assert!(next["next"].is_null());
        call(&mut v,"chat.saveUserMessage",json!({"id":M,"conversationId":A,"content":"One"})).unwrap();
        assert!(call(&mut v,"chat.saveUserMessage",json!({"id":"message-other-0001","conversationId":B,"parentId":M,"content":"Invalid"})).is_err());
        assert_eq!(call(&mut v,"chat.history",json!({"conversationId":B,"after":0,"limit":1})).unwrap()["items"].as_array().unwrap().len(),0);
        assert!(call(&mut v,"chat.history",json!({"conversationId":"missing-thread-001","after":0,"limit":1})).is_err());
        assert!(call(&mut v,"chat.list",json!({"limit":51})).is_err());
        assert!(call(&mut v,"chat.history",json!({"conversationId":A,"after":0,"limit":5})).is_err());
    }
    #[test]
    fn chat_ipc_attachment_history_is_scoped_and_plain_replay_cannot_drop_links() {
        let f=Fixture::new();let mut v=NativeVault::open(&f.0).unwrap();
        for id in [A,B] {call(&mut v,"chat.create",json!({"id":id,"title":"Synthetic"})).unwrap();}
        let a=crate::vault::LinkedAttachment {id:"artifact-alpha-001".into(),
            receipt:v.stage_managed_blob("note.txt",b"private synthetic bytes").unwrap()};
        let hash=a.receipt.sha256.clone();
        v.append_chat_message_with_attachments(ChatMessageInput {id:M,conversation_id:A,parent_id:None,
            content:"One",role:ChatRole::User,status:ChatStatus::Complete},&[a]).unwrap();
        drop(v);let mut v=NativeVault::open(&f.0).unwrap();
        let h=call(&mut v,"chat.history",json!({"conversationId":A,"after":0,"limit":1})).unwrap();
        assert_eq!(h["items"][0]["attachments"],json!([{"id":"artifact-alpha-001","name":"note.txt","bytes":23,"sha256":hash}]));
        assert!(!h.to_string().contains("private synthetic bytes"));
        assert_eq!(call(&mut v,"chat.history",json!({"conversationId":B,"after":0,"limit":1})).unwrap()["items"],json!([]));
        let err=call(&mut v,"chat.saveUserMessage",json!({"id":M,"conversationId":A,"content":"One"})).unwrap_err();
        assert_eq!(err.code,"ZYN-CHAT-CONFLICT");
        let h=call(&mut v,"chat.history",json!({"conversationId":A,"after":0,"limit":1})).unwrap();
        assert_eq!(h["items"][0]["attachments"].as_array().unwrap().len(),1);
    }
    #[test]
    fn chat_ipc_chunked_attachment_upload_commit_and_exact_replay() {
        let f=Fixture::new();let mut v=NativeVault::open(&f.0).unwrap();
        for id in [A,B] {call(&mut v,"chat.create",json!({"id":id,"title":"Synthetic"})).unwrap();}
        let id="artifact-alpha-001";
        let chunk=|scope:&str,offset:u64,data:Vec<u8>|json!({"conversationId":scope,"messageId":M,
            "artifactId":id,"name":"note.txt","total":4,"offset":offset,"chunk":data});
        assert!(call(&mut v,"chat.attachment.chunk",chunk(A,2,vec![3,4])).is_err());
        let first=chunk(A,0,vec![1,2]);
        assert_eq!(call(&mut v,"chat.attachment.chunk",first.clone()).unwrap()["received"],2);
        assert_eq!(call(&mut v,"chat.attachment.chunk",first).unwrap()["attachment"],Value::Null);
        assert!(call(&mut v,"chat.attachment.chunk",chunk(A,0,vec![9,2])).is_err());
        assert!(call(&mut v,"chat.attachment.chunk",chunk(B,0,vec![1,2])).is_err());
        assert!(call(&mut v,"chat.attachment.discard",json!({"conversationId":B,"messageId":M})).is_err());
        let plain=json!({"id":M,"conversationId":A,"content":"One"});
        assert!(call(&mut v,"chat.saveUserMessage",plain.clone()).is_err());
        let final_chunk=chunk(A,2,vec![3,4]);
        let a=call(&mut v,"chat.attachment.chunk",final_chunk.clone()).unwrap()["attachment"].clone();
        assert_eq!(call(&mut v,"chat.attachment.chunk",final_chunk).unwrap()["attachment"],a);
        let mut save=plain.clone();save["attachments"]=json!([a]);
        let mut wrong=save.clone();wrong["attachments"][0]["sha256"]=json!("a".repeat(64));
        assert!(call(&mut v,"chat.saveUserMessage",wrong.clone()).is_err());
        assert_eq!(call(&mut v,"chat.saveUserMessage",save.clone()).unwrap()["replayed"],false);
        drop(v);let mut v=NativeVault::open(&f.0).unwrap();
        assert_eq!(call(&mut v,"chat.saveUserMessage",save).unwrap()["replayed"],true);
        assert!(call(&mut v,"chat.saveUserMessage",wrong).is_err());
        assert!(call(&mut v,"chat.saveUserMessage",plain).is_err());
        let stored=v.list_message_attachments(A,M).unwrap();
        assert_eq!(v.read_managed_blob(&stored[0].receipt).unwrap(),vec![1,2,3,4]);
    }

    #[test]
    fn chat_ipc_chunked_upload_discard_and_limits_are_fail_closed() {
        let f=Fixture::new();let mut v=NativeVault::open(&f.0).unwrap();
        call(&mut v,"chat.create",json!({"id":A,"title":"Synthetic"})).unwrap();
        let request=json!({"conversationId":A,"messageId":M,"artifactId":"artifact-alpha-001",
            "name":"empty.txt","total":0,"offset":0,"chunk":[]});
        let mut oversized=request.clone();oversized["total"]=json!(25*1024*1024+1);
        assert!(call(&mut v,"chat.attachment.chunk",oversized).is_err());
        let mut bad=request.clone();bad["path"]=json!("outside");
        assert!(call(&mut v,"chat.attachment.chunk",bad).is_err());
        let mut huge=request.clone();huge["total"]=json!(65537);huge["chunk"]=json!(vec![0u8;65537]);
        assert!(call(&mut v,"chat.attachment.chunk",huge).is_err());
        let result=call(&mut v,"chat.attachment.chunk",request.clone()).unwrap();
        assert_eq!(result["attachment"]["bytes"],0);
        let mut save=json!({"id":M,"conversationId":A,"content":"One","attachments":[result["attachment"].clone()]});
        call(&mut v,"chat.attachment.discard",json!({"conversationId":A,"messageId":M})).unwrap();
        assert!(call(&mut v,"chat.attachment.chunk",request).is_err());
        assert!(call(&mut v,"chat.saveUserMessage",save.clone()).is_err());
        save["attachments"]=json!([]);
        assert_eq!(call(&mut v,"chat.saveUserMessage",save).unwrap()["replayed"],false);
    }

    #[test]
    fn chat_ipc_recovery_is_bounded_read_only_and_rejects_authority() {
        let f=Fixture::new();let mut v=NativeVault::open(&f.0).unwrap();
        assert!(authorize_request("remote",&request("chat.recovery.inspect",json!({}))).is_err());
        for bad in [json!({"path":"outside"}),json!({"delete":true}),json!(null),json!([])] {
            assert!(call(&mut v,"chat.recovery.inspect",bad).is_err());
        }
        let empty=json!({"referencedHashes":0,"verifiedReferenced":0,"verifiedUnreferenced":0,
            "unavailableReferenced":0,"damagedOrUnreadable":0,"interruptedStages":0,
            "unexpectedEntries":0,"unlinkedMetadata":0});
        assert_eq!(call(&mut v,"chat.recovery.inspect",json!({})).unwrap(),empty);
        call(&mut v,"chat.create",json!({"id":A,"title":"Synthetic"})).unwrap();
        let receipt=v.stage_managed_blob("keep.txt",b"sole synthetic copy").unwrap();
        let hash=receipt.sha256.clone();
        let directory=f.0.join("data").join("artifacts").join("sha256").join(&hash[..2]);
        let stage=directory.join(".stage-1-2-3");
        std::fs::write(&stage,b"interrupted synthetic bytes").unwrap();
        let mut expected=empty.clone();
        expected["verifiedUnreferenced"]=json!(1);
        expected["interruptedStages"]=json!(1);
        assert_eq!(call(&mut v,"chat.recovery.inspect",json!({})).unwrap(),expected);
        let a=LinkedAttachment{id:"artifact-alpha-001".into(),receipt:receipt.clone()};
        v.append_chat_message_with_attachments(ChatMessageInput{id:M,conversation_id:A,parent_id:None,
            content:"One",role:ChatRole::User,status:ChatStatus::Complete},&[a]).unwrap();
        let history=call(&mut v,"chat.history",json!({"conversationId":A,"after":0,"limit":4})).unwrap();
        drop(v);let mut v=NativeVault::open(&f.0).unwrap();
        expected["referencedHashes"]=json!(1);expected["verifiedReferenced"]=json!(1);
        expected["verifiedUnreferenced"]=json!(0);
        assert_eq!(call(&mut v,"chat.recovery.inspect",json!({})).unwrap(),expected);
        assert_eq!(call(&mut v,"chat.history",json!({"conversationId":A,"after":0,"limit":4})).unwrap(),history);
        assert_eq!(v.read_managed_blob(&receipt).unwrap(),b"sole synthetic copy");
        assert_eq!(std::fs::read(&stage).unwrap(),b"interrupted synthetic bytes");
        std::fs::write(directory.join(&hash),b"corrupted").unwrap();
        expected["verifiedReferenced"]=json!(0);expected["unavailableReferenced"]=json!(1);
        expected["damagedOrUnreadable"]=json!(1);
        assert_eq!(call(&mut v,"chat.recovery.inspect",json!({})).unwrap(),expected);
        assert_eq!(std::fs::read(directory.join(&hash)).unwrap(),b"corrupted");
        assert_eq!(std::fs::read(stage).unwrap(),b"interrupted synthetic bytes");
    }

    #[test]
    fn chat_ipc_text_artifact_create_preview_is_scoped_and_replayable() {
        let f=Fixture::new();let mut v=NativeVault::open(&f.0).unwrap();
        for id in [A,B] {call(&mut v,"chat.create",json!({"id":id,"title":"Synthetic"})).unwrap();}
        call(&mut v,"chat.saveUserMessage",json!({"id":M,"conversationId":A,"content":"Synthetic prompt"})).unwrap();
        let source="assistant-alpha-0001";
        let content="Synthetic <script>plain text</script>\nUrdu: اردو";
        v.append_chat_message(ChatMessageInput{id:source,conversation_id:A,parent_id:Some(M),
            role:ChatRole::Assistant,content,status:ChatStatus::Complete}).unwrap();
        let q=json!({"conversationId":A,"sourceId":source});
        assert!(authorize_request("remote",&request("chat.artifact.createText",q.clone())).is_err());
        assert!(authorize_request("remote",&request("chat.artifact.previewText",q.clone())).is_err());
        for cmd in ["chat.artifact.createText","chat.artifact.previewText"] {
            for bad in [json!({"conversationId":B,"sourceId":source}),
                        json!({"conversationId":A,"sourceId":M}),
                        json!({"conversationId":A,"sourceId":source,"path":"outside"}),
                        json!({"conversationId":A,"sourceId":source,"content":"override"})] {
                assert!(call(&mut v,cmd,bad).is_err());
            }
        }
        assert!(call(&mut v,"chat.artifact.previewText",q.clone()).is_err());
        let created=call(&mut v,"chat.artifact.createText",q.clone()).unwrap();
        assert_eq!(created["replayed"],false);
        assert_eq!(created["attachment"]["bytes"],content.len());
        assert_eq!(created["attachment"]["name"],"assistant-response.txt");
        assert_eq!(created["sourceId"],source);
        assert_eq!(call(&mut v,"chat.artifact.previewText",q.clone()).unwrap()["content"],content);
        drop(v);let mut v=NativeVault::open(&f.0).unwrap();
        let mut replay=created.clone();replay["replayed"]=json!(true);
        assert_eq!(call(&mut v,"chat.artifact.createText",q.clone()).unwrap(),replay);
        assert_eq!(call(&mut v,"chat.artifact.previewText",q).unwrap()["content"],content);
        let h=call(&mut v,"chat.history",json!({"conversationId":A,"after":0,"limit":4})).unwrap();
        assert_eq!(h["items"].as_array().unwrap().len(),3);
        assert_eq!(h["items"][2]["parentId"],source);
        assert_eq!(h["items"][2]["attachments"][0],created["attachment"]);
    }
    #[test]
    fn chat_ipc_large_history_is_byte_bounded_and_continues() {
        let f=Fixture::new();let mut v=NativeVault::open(&f.0).unwrap();
        call(&mut v,"chat.create",json!({"id":A,"title":"Synthetic"})).unwrap();
        let content="x\u{0001}".repeat(131072);
        for i in 1..=3 {
            call(&mut v,"chat.saveUserMessage",json!({"id":format!("message-large-{i:04}"),"conversationId":A,"content":content})).unwrap();
        }
        let page=call(&mut v,"chat.history",json!({"conversationId":A,"after":0,"limit":4})).unwrap();
        assert!(serde_json::to_vec(&page).unwrap().len()<=MAX_RESPONSE_BYTES);
        let cursor=page["next"].as_i64().unwrap();
        assert!(cursor>=1&&cursor<3);
        let rest=call(&mut v,"chat.history",json!({"conversationId":A,"after":cursor,"limit":1})).unwrap();
        assert_eq!(rest["items"][0]["ordinal"],cursor+1);
    }
}
