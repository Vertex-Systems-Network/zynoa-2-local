//! M03 fixed local-domain commands. No generic SQL, path, tool or network authority.
use crate::vault::{NativeVault, VaultFault, ChatMessageInput, ChatRole, ChatStatus, ConversationSummary, StoredChatMessage, ChatWriteReceipt};
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
#[serde(rename_all="camelCase",deny_unknown_fields)]
struct CreatePayload { id: String, title: String }
#[derive(Deserialize)]
#[serde(rename_all="camelCase",deny_unknown_fields)]
struct HistoryPayload { conversation_id: String, after: i64, limit: u32 }
#[derive(Deserialize)]
#[serde(rename_all="camelCase",deny_unknown_fields)]
struct SavePayload { id: String, conversation_id: String, parent_id: Option<String>, content: String }

fn summary(row:&ConversationSummary)->Value {
    json!({"id":row.id,"title":row.title,"revision":row.revision,"createdAt":row.created_at,"updatedAt":row.updated_at})
}
fn message(row:&StoredChatMessage)->Value {
    json!({"id":row.id,"parentId":row.parent_id,"ordinal":row.ordinal,"role":row.role,"content":row.content,
        "status":row.status,"revision":row.revision,"createdAt":row.created_at})
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
    if !matches!(request.command_id.as_str(),"chat.list"|"chat.create"|"chat.history"|"chat.saveUserMessage") {
        return Err(error("ZYN-CHAT-DENIED"));
    }
    if serde_json::to_vec(&request.payload).map_err(|_|error("ZYN-CHAT-INPUT"))?.len()>MAX_REQUEST_BYTES {
        return Err(error("ZYN-CHAT-INPUT"));
    }
    Ok(())
}
fn execute(vault:&mut NativeVault, request:ChatRequest) -> Result<ChatReply,ChatError> {
    let data=match request.command_id.as_str() {
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
                let candidate=json!({"conversation":summary(&thread),"items":items.iter().map(message).collect::<Vec<_>>(),"next":next});
                if serde_json::to_vec(&candidate).map_err(|_|error("ZYN-CHAT-STORAGE"))?.len()<=MAX_RESPONSE_BYTES {break candidate;}
                if items.len()<=1 {return Err(error("ZYN-CHAT-STORAGE"));}
                items.pop(); more=true;
            }
        },
        "chat.saveUserMessage" => {
            let q:SavePayload=parse(request.payload)?;
            if !token(&q.id) {return Err(error("ZYN-CHAT-INPUT"));}
            let input=ChatMessageInput {id:&q.id,conversation_id:&q.conversation_id,parent_id:q.parent_id.as_deref(),
                content:&q.content,role:ChatRole::User,status:ChatStatus::Complete};
            match vault.append_chat_message(input) {
                Ok(row)=>json!({"receipt":receipt(&row),"replayed":false}),
                Err(VaultFault::Conflict)=>{
                    let row=vault.get_chat_message(&q.conversation_id,&q.id)?.ok_or_else(||error("ZYN-CHAT-CONFLICT"))?;
                    if row.content!=q.content || row.parent_id!=q.parent_id || row.role!="user" || row.status!="complete" {
                        return Err(error("ZYN-CHAT-CONFLICT"));
                    }
                    let thread=vault.get_conversation(&q.conversation_id)?.ok_or_else(||error("ZYN-CHAT-CONFLICT"))?;
                    json!({"receipt":{"id":row.id,"revision":row.revision,"conversationRevision":thread.revision,"ordinal":row.ordinal},"replayed":true})
                },
                Err(e)=>return Err(e.into()),
            }
        },
        _=>return Err(error("ZYN-CHAT-DENIED")),
    };
    Ok(ChatReply {schema_version:1,command_id:request.command_id,correlation_id:request.correlation_id,data})
}

// Async Tauri dispatch runs off the GUI thread; no await with a vault lock held.
#[tauri::command]
pub async fn chat_request(window:tauri::Window, storage:tauri::State<'_,std::sync::Mutex<NativeVault>>,
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
