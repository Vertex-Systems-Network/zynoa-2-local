//! M03 fixed-loopback Ollama gateway. Renderer-controlled URLs, proxies,
//! credentials, redirects and remote hosts are intentionally impossible.
use crate::vault::{ChatMessageInput, ChatRole, ChatStatus, NativeVault};
use serde::{Deserialize, Serialize};
use serde_json::{json, Value};
use std::collections::HashMap;
use std::io::BufRead;
use std::sync::{
    atomic::{AtomicBool, Ordering},
    Arc, Mutex,
};
use std::time::Duration;
use tauri::ipc::Channel;

const OLLAMA_BASE: &str = "http://127.0.0.1:11434";
const MAX_MODELS: usize = 128;
const MAX_EVENT_BYTES: usize = 65_536;
const MAX_EVENTS: usize = 4096;
const MAX_OUTPUT_BYTES: usize = 262_144;
const CONTEXT_RESERVE: u32 = 128;

#[derive(Deserialize)]
#[serde(rename_all = "camelCase", deny_unknown_fields)]
pub struct ModelRequest {
    schema_version: u8,
    command_id: String,
    correlation_id: String,
    workspace_scope: String,
    payload: Value,
}

#[derive(Serialize)]
#[serde(rename_all = "camelCase")]
pub struct ModelReply {
    schema_version: u8,
    command_id: String,
    correlation_id: String,
    data: Value,
}

#[derive(Serialize, Clone)]
#[serde(rename_all = "camelCase")]
pub struct ModelEvent {
    schema_version: u8,
    turn_id: String,
    sequence: u32,
    kind: &'static str,
    content: String,
}

#[derive(Serialize, Debug)]
#[serde(rename_all = "camelCase")]
pub struct ModelError {
    code: &'static str,
    recovery_action: &'static str,
}
fn fault(code: &'static str) -> ModelError {
    ModelError {
        code,
        recovery_action:
            "Check the local Ollama runtime, preserve the draft, then retry explicitly.",
    }
}

#[derive(Clone)]
pub struct LocalModelGateway {
    client: reqwest::blocking::Client,
    base: String,
    active: Arc<Mutex<HashMap<String, (String, Arc<AtomicBool>)>>>,
}

#[derive(Deserialize)]
#[serde(rename_all = "camelCase", deny_unknown_fields)]
struct ConversationPayload {
    conversation_id: String,
}
#[derive(Deserialize)]
#[serde(rename_all = "camelCase", deny_unknown_fields)]
struct ContextPayload {
    conversation_id: String,
    draft: String,
}
#[derive(Deserialize)]
#[serde(rename_all = "camelCase", deny_unknown_fields)]
struct SettingsPayload {
    conversation_id: String,
    model: String,
    context_limit: u32,
}
#[derive(Deserialize)]
#[serde(rename_all = "camelCase", deny_unknown_fields)]
struct GeneratePayload {
    turn_id: String,
    conversation_id: String,
    assistant_message_id: String,
    parent_id: String,
}
#[derive(Deserialize)]
#[serde(rename_all = "camelCase", deny_unknown_fields)]
struct CancelPayload {
    turn_id: String,
    conversation_id: String,
}

fn token(value: &str) -> bool {
    (8..=64).contains(&value.len())
        && value
            .bytes()
            .all(|b| b.is_ascii_alphanumeric() || b == b'-' || b == b'_')
}
fn model_name(value: &str) -> bool {
    !value.is_empty()
        && value.len() <= 128
        && value
            .bytes()
            .all(|b| b.is_ascii_alphanumeric() || matches!(b, b'.' | b'_' | b':' | b'/' | b'-'))
}
fn parse<T: serde::de::DeserializeOwned>(value: Value) -> Result<T, ModelError> {
    serde_json::from_value(value).map_err(|_| fault("ZYN-MODEL-INPUT"))
}

impl LocalModelGateway {
    pub fn new() -> Result<Self, std::io::Error> {
        Self::with_base(OLLAMA_BASE)
    }
    fn with_base(base: &str) -> Result<Self, std::io::Error> {
        let parsed =
            reqwest::Url::parse(base).map_err(|_| std::io::Error::other("ZYN-MODEL-BASE"))?;
        if parsed.scheme() != "http"
            || parsed.host_str() != Some("127.0.0.1")
            || parsed.port().is_none()
            || parsed.path() != "/"
            || parsed.query().is_some()
            || parsed.fragment().is_some()
            || !parsed.username().is_empty()
            || parsed.password().is_some()
        {
            return Err(std::io::Error::other("ZYN-MODEL-BASE"));
        }
        let client = reqwest::blocking::Client::builder()
            .no_proxy()
            .redirect(reqwest::redirect::Policy::none())
            .connect_timeout(Duration::from_secs(2))
            .timeout(Duration::from_secs(150))
            .user_agent("Zynoa-local-model/0.1")
            .build()
            .map_err(|_| std::io::Error::other("ZYN-MODEL-CLIENT"))?;
        Ok(Self {
            client,
            base: base.to_owned(),
            active: Arc::new(Mutex::new(HashMap::new())),
        })
    }
    #[cfg(test)]
    fn fixture(base: &str) -> Self {
        Self::with_base(base).unwrap()
    }

    fn get_json(&self, path: &str) -> Result<Value, ModelError> {
        let reply = self
            .client
            .get(format!("{}{}", self.base, path))
            .send()
            .map_err(|_| fault("ZYN-MODEL-OFFLINE"))?;
        if !reply.status().is_success() {
            return Err(fault("ZYN-MODEL-OFFLINE"));
        }
        let bytes = reply.bytes().map_err(|_| fault("ZYN-MODEL-RESPONSE"))?;
        if bytes.len() > 1_000_000 {
            return Err(fault("ZYN-MODEL-RESPONSE"));
        }
        serde_json::from_slice(&bytes).map_err(|_| fault("ZYN-MODEL-RESPONSE"))
    }
    fn inventory(&self) -> Result<(String, Vec<Value>), ModelError> {
        let version = self
            .get_json("/api/version")?
            .get("version")
            .and_then(Value::as_str)
            .filter(|x| !x.is_empty() && x.len() <= 64 && x.bytes().all(|b| b.is_ascii_graphic()))
            .ok_or_else(|| fault("ZYN-MODEL-RESPONSE"))?
            .to_owned();
        let raw = self.get_json("/api/tags")?;
        let rows = raw
            .get("models")
            .and_then(Value::as_array)
            .ok_or_else(|| fault("ZYN-MODEL-RESPONSE"))?;
        if rows.len() > MAX_MODELS {
            return Err(fault("ZYN-MODEL-RESPONSE"));
        }
        let mut models = Vec::new();
        for row in rows {
            let name = row
                .get("name")
                .and_then(Value::as_str)
                .filter(|x| model_name(x))
                .ok_or_else(|| fault("ZYN-MODEL-RESPONSE"))?;
            let digest = row.get("digest").and_then(Value::as_str).unwrap_or("");
            if digest.len() > 128 {
                return Err(fault("ZYN-MODEL-RESPONSE"));
            }
            let size = row.get("size").and_then(Value::as_u64).unwrap_or(0);
            models.push(json!({"name":name,"digest":digest,"size":size}));
        }
        Ok((version, models))
    }
    fn has_model(models: &[Value], name: &str) -> bool {
        models
            .iter()
            .any(|m| m.get("name").and_then(Value::as_str) == Some(name))
    }

    fn generate(
        &self,
        storage: &Arc<Mutex<NativeVault>>,
        q: GeneratePayload,
        on_event: &Channel<ModelEvent>,
    ) -> Result<Value, ModelError> {
        if !token(&q.turn_id)
            || !token(&q.conversation_id)
            || !token(&q.assistant_message_id)
            || !token(&q.parent_id)
        {
            return Err(fault("ZYN-MODEL-INPUT"));
        }
        let (settings, context) = {
            let vault = storage.lock().map_err(|_| fault("ZYN-MODEL-STORAGE"))?;
            let parent = vault
                .get_chat_message(&q.conversation_id, &q.parent_id)
                .map_err(|_| fault("ZYN-MODEL-STORAGE"))?
                .ok_or_else(|| fault("ZYN-MODEL-INPUT"))?;
            if parent.role != "user" || parent.status != "complete" {
                return Err(fault("ZYN-MODEL-INPUT"));
            }
            let settings = vault
                .get_inference_settings(&q.conversation_id)
                .map_err(|_| fault("ZYN-MODEL-STORAGE"))?
                .ok_or_else(|| fault("ZYN-MODEL-SETTINGS"))?;
            let context = vault
                .model_context(&q.conversation_id, settings.context_limit, CONTEXT_RESERVE)
                .map_err(|_| fault("ZYN-MODEL-CONTEXT"))?;
            if context.messages.last().map(|m| m.id.as_str()) != Some(q.parent_id.as_str()) {
                return Err(fault("ZYN-MODEL-INPUT"));
            }
            (settings, context)
        };
        let (_, models) = self.inventory()?;
        if !Self::has_model(&models, &settings.model) {
            return Err(fault("ZYN-MODEL-MISSING"));
        }
        let flag = Arc::new(AtomicBool::new(false));
        {
            let mut active = self.active.lock().map_err(|_| fault("ZYN-MODEL-BUSY"))?;
            if active.contains_key(&q.conversation_id) {
                return Err(fault("ZYN-MODEL-BUSY"));
            }
            active.insert(q.conversation_id.clone(), (q.turn_id.clone(), flag.clone()));
        }
        struct Guard<'a> {
            map: &'a Mutex<HashMap<String, (String, Arc<AtomicBool>)>>,
            conversation: String,
        }
        impl Drop for Guard<'_> {
            fn drop(&mut self) {
                if let Ok(mut m) = self.map.lock() {
                    m.remove(&self.conversation);
                }
            }
        }
        let _guard = Guard {
            map: &self.active,
            conversation: q.conversation_id.clone(),
        };
        let mut messages = vec![
            json!({"role":"system","content":"You are a local assistant. Answer directly and do not claim unavailable tools."}),
        ];
        messages.extend(
            context
                .messages
                .iter()
                .map(|m| json!({"role":&m.role,"content":&m.content})),
        );
        let body = json!({"model":settings.model,"messages":messages,"stream":true,
            "options":{"num_ctx":settings.context_limit,"num_predict":std::cmp::min(2048,std::cmp::max(64,settings.context_limit/4))}});
        let reply = self
            .client
            .post(format!("{}/api/chat", self.base))
            .json(&body)
            .send()
            .map_err(|_| fault("ZYN-MODEL-OFFLINE"))?;
        if !reply.status().is_success() {
            return Err(fault("ZYN-MODEL-RUNTIME"));
        }
        let content_type = reply
            .headers()
            .get(reqwest::header::CONTENT_TYPE)
            .and_then(|x| x.to_str().ok())
            .unwrap_or("");
        if !content_type.starts_with("application/x-ndjson") {
            return Err(fault("ZYN-MODEL-RESPONSE"));
        }
        let mut reader = std::io::BufReader::new(reply);
        let mut output = String::new();
        let mut sequence = 0u32;
        let mut complete = false;
        let mut stream_failed = false;
        let mut eval_count = 0u64;
        for _ in 0..MAX_EVENTS {
            if flag.load(Ordering::Acquire) {
                break;
            }
            let mut line = Vec::new();
            let size = match reader.read_until(b'\n', &mut line) {
                Ok(n) => n,
                Err(_) => {
                    stream_failed = true;
                    break;
                }
            };
            if size == 0 {
                stream_failed = true;
                break;
            }
            if size > MAX_EVENT_BYTES {
                stream_failed = true;
                break;
            }
            let event: Value = match serde_json::from_slice(&line) {
                Ok(v) => v,
                Err(_) => {
                    stream_failed = true;
                    break;
                }
            };
            if event.get("error").is_some() {
                stream_failed = true;
                break;
            }
            let delta = event
                .get("message")
                .and_then(|m| m.get("content"))
                .and_then(Value::as_str)
                .unwrap_or("");
            if !delta.is_empty() {
                if output.len().saturating_add(delta.len()) > MAX_OUTPUT_BYTES {
                    stream_failed = true;
                    break;
                }
                output.push_str(delta);
                sequence += 1;
                if on_event
                    .send(ModelEvent {
                        schema_version: 1,
                        turn_id: q.turn_id.clone(),
                        sequence,
                        kind: "delta",
                        content: delta.to_owned(),
                    })
                    .is_err()
                {
                    stream_failed = true;
                    break;
                }
            }
            if event.get("done") == Some(&Value::Bool(true)) {
                complete = true;
                eval_count = event.get("eval_count").and_then(Value::as_u64).unwrap_or(0);
                break;
            }
        }
        let cancelled = flag.load(Ordering::Acquire);
        let status = if cancelled {
            "cancelled"
        } else if complete && !stream_failed && !output.trim().is_empty() {
            "complete"
        } else {
            "failed"
        };
        let receipt = if output.trim().is_empty() {
            None
        } else {
            let mut vault = storage.lock().map_err(|_| fault("ZYN-MODEL-STORAGE"))?;
            let saved = vault
                .append_chat_message(ChatMessageInput {
                    id: &q.assistant_message_id,
                    conversation_id: &q.conversation_id,
                    parent_id: Some(&q.parent_id),
                    role: ChatRole::Assistant,
                    content: &output,
                    status: if cancelled {
                        ChatStatus::Cancelled
                    } else if complete {
                        ChatStatus::Complete
                    } else {
                        ChatStatus::Failed
                    },
                })
                .map_err(|_| fault("ZYN-MODEL-STORAGE"))?;
            Some(
                json!({"id":saved.id,"revision":saved.revision,"conversationRevision":saved.conversation_revision,"ordinal":saved.ordinal}),
            )
        };
        on_event
            .send(ModelEvent {
                schema_version: 1,
                turn_id: q.turn_id.clone(),
                sequence: sequence + 1,
                kind: "terminal",
                content: String::new(),
            })
            .map_err(|_| fault("ZYN-MODEL-CHANNEL"))?;
        Ok(
            json!({"turnId":q.turn_id,"status":status,"receipt":receipt,"evalCount":eval_count,
            "context":{"estimatedTokens":context.estimated_tokens,"limit":context.limit,"omittedMessages":context.omitted_messages}}),
        )
    }
}

fn authorize(label: &str, request: &ModelRequest) -> Result<(), ModelError> {
    crate::security::allow_local_model(label).map_err(|_| fault("ZYN-MODEL-DENIED"))?;
    if request.schema_version != 1
        || request.workspace_scope != "local"
        || !token(&request.correlation_id)
        || !matches!(
            request.command_id.as_str(),
            "inference.health"
                | "inference.settings.get"
                | "inference.settings.set"
                | "inference.context.inspect"
                | "inference.turn.generate"
                | "inference.turn.cancel"
        )
    {
        return Err(fault("ZYN-MODEL-INPUT"));
    }
    Ok(())
}

fn execute(
    gateway: &LocalModelGateway,
    storage: &Arc<Mutex<NativeVault>>,
    request: ModelRequest,
    on_event: &Channel<ModelEvent>,
) -> Result<ModelReply, ModelError> {
    let data = match request.command_id.as_str() {
        "inference.health" => {
            let (version, models) = gateway.inventory()?;
            json!({"version":version,"models":models})
        }
        "inference.settings.get" => {
            let q: ConversationPayload = parse(request.payload)?;
            let value = storage
                .lock()
                .map_err(|_| fault("ZYN-MODEL-STORAGE"))?
                .get_inference_settings(&q.conversation_id)
                .map_err(|_| fault("ZYN-MODEL-STORAGE"))?;
            json!({"settings":value})
        }
        "inference.settings.set" => {
            let q: SettingsPayload = parse(request.payload)?;
            let (_, models) = gateway.inventory()?;
            if !LocalModelGateway::has_model(&models, &q.model) {
                return Err(fault("ZYN-MODEL-MISSING"));
            }
            let value = storage
                .lock()
                .map_err(|_| fault("ZYN-MODEL-STORAGE"))?
                .set_inference_settings(&q.conversation_id, &q.model, q.context_limit)
                .map_err(|_| fault("ZYN-MODEL-STORAGE"))?;
            json!({"settings":value})
        }
        "inference.context.inspect" => {
            let q: ContextPayload = parse(request.payload)?;
            if q.draft.len() > 262_144 || q.draft.contains('\0') {
                return Err(fault("ZYN-MODEL-INPUT"));
            }
            let vault = storage.lock().map_err(|_| fault("ZYN-MODEL-STORAGE"))?;
            let settings = vault
                .get_inference_settings(&q.conversation_id)
                .map_err(|_| fault("ZYN-MODEL-STORAGE"))?
                .ok_or_else(|| fault("ZYN-MODEL-SETTINGS"))?;
            let context = vault
                .model_context(&q.conversation_id, settings.context_limit, CONTEXT_RESERVE)
                .map_err(|_| fault("ZYN-MODEL-CONTEXT"))?;
            let draft_tokens = ((q.draft.as_bytes().len() as u32).saturating_add(3) / 4)
                .saturating_add(if q.draft.is_empty() { 0 } else { 8 });
            let estimated = context.estimated_tokens.saturating_add(draft_tokens);
            if estimated > context.limit {
                return Err(fault("ZYN-MODEL-CONTEXT"));
            }
            json!({"estimatedTokens":estimated,"limit":context.limit,"includedMessages":context.messages.len()+(if q.draft.is_empty(){0}else{1}),"omittedMessages":context.omitted_messages})
        }
        "inference.turn.generate" => {
            gateway.generate(storage, parse(request.payload)?, on_event)?
        }
        "inference.turn.cancel" => {
            let q: CancelPayload = parse(request.payload)?;
            let active = gateway.active.lock().map_err(|_| fault("ZYN-MODEL-BUSY"))?;
            let stopped = active.get(&q.conversation_id).is_some_and(|(id, flag)| {
                if id == &q.turn_id {
                    flag.store(true, Ordering::Release);
                    true
                } else {
                    false
                }
            });
            json!({"turnId":q.turn_id,"stopped":stopped})
        }
        _ => return Err(fault("ZYN-MODEL-DENIED")),
    };
    Ok(ModelReply {
        schema_version: 1,
        command_id: request.command_id,
        correlation_id: request.correlation_id,
        data,
    })
}

#[tauri::command]
pub async fn model_request(
    window: tauri::Window,
    gateway: tauri::State<'_, LocalModelGateway>,
    storage: tauri::State<'_, Arc<Mutex<NativeVault>>>,
    request: ModelRequest,
    on_event: Channel<ModelEvent>,
) -> Result<ModelReply, ModelError> {
    if let Err(error) = authorize(window.label(), &request) {
        return Err(error);
    }
    let gateway = gateway.inner().clone();
    let storage = storage.inner().clone();
    tauri::async_runtime::spawn_blocking(move || execute(&gateway, &storage, request, &on_event))
        .await
        .map_err(|_| fault("ZYN-MODEL-RUNTIME"))?
}

#[cfg(test)]
mod tests {
    use super::*;
    use std::io::{Read, Write};
    use std::net::TcpListener;
    fn fixture(responses: Vec<&'static str>) -> (String, std::thread::JoinHandle<()>) {
        let listener = TcpListener::bind("127.0.0.1:0").unwrap();
        let address = listener.local_addr().unwrap();
        let handle = std::thread::spawn(move || {
            for body in responses {
                let (mut stream, _) = listener.accept().unwrap();
                let mut request = [0u8; 2048];
                let _ = stream.read(&mut request).unwrap();
                write!(stream,"HTTP/1.1 200 OK\r\nContent-Type: application/json\r\nContent-Length: {}\r\nConnection: close\r\n\r\n{}",body.len(),body).unwrap();
            }
        });
        (format!("http://{}", address), handle)
    }
    #[test]
    fn inventory_accepts_only_bounded_loopback_runtime_data() {
        let (base, server) = fixture(vec![
            r#"{"version":"0.40.18"}"#,
            r#"{"models":[{"name":"qwen2.5:0.5b","digest":"abc","size":42}]}"#,
        ]);
        let gateway = LocalModelGateway::fixture(&base);
        let (version, models) = gateway.inventory().unwrap();
        server.join().unwrap();
        assert_eq!(version, "0.40.18");
        assert_eq!(models.len(), 1);
        assert_eq!(models[0]["name"], "qwen2.5:0.5b");
    }
    #[test]
    fn client_constructor_rejects_remote_credentials_and_paths() {
        for base in [
            "https://127.0.0.1:11434",
            "http://localhost:11434",
            "http://127.0.0.1:11434/path",
            "http://user@127.0.0.1:11434",
        ] {
            assert!(
                LocalModelGateway::with_base(base).is_err(),
                "accepted {base}"
            );
        }
    }
    #[test]
    fn authorization_is_exact_main_local_and_known_operations() {
        let request = ModelRequest {
            schema_version: 1,
            command_id: "inference.health".into(),
            correlation_id: "correlation-00001".into(),
            workspace_scope: "local".into(),
            payload: json!({}),
        };
        assert!(authorize("main", &request).is_ok());
        assert!(authorize("remote", &request).is_err());
        let bad = ModelRequest {
            command_id: "inference.fetchUrl".into(),
            ..request
        };
        assert!(authorize("main", &bad).is_err());
    }
}
