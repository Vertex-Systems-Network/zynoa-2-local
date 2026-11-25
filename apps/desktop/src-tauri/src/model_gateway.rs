//! M03 fixed-loopback Ollama gateway. Renderer-controlled URLs, proxies,
//! credentials, redirects and remote hosts are intentionally impossible.
use crate::vault::{ChatMessageInput, ChatRole, ChatStatus, NativeVault};
use serde::{Deserialize, Serialize};
use serde_json::{json, Value};
use std::collections::HashMap;
use std::sync::{Arc, Mutex};
use std::time::Duration;
use tauri::ipc::Channel;

const OLLAMA_BASE: &str = "http://127.0.0.1:11434";
const MAX_MODELS: usize = 128;
const MAX_EVENT_BYTES: usize = 65_536;
const MAX_EVENTS: usize = 4096;
const MAX_OUTPUT_BYTES: usize = 262_144;
const SYSTEM_PROMPT: &str = "You are a local assistant. Answer directly and do not claim unavailable tools.";

fn output_budget(context_limit: u32) -> u32 {
    std::cmp::min(2048, std::cmp::max(64, context_limit / 4))
}

fn context_reserve(context_limit: u32) -> u32 {
    output_budget(context_limit)
        .saturating_add(NativeVault::estimate_message_tokens(SYSTEM_PROMPT))
        .saturating_add(32)
}

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

#[derive(Default)]
struct TurnCancellation {
    state: Mutex<TurnCancellationState>,
}
#[derive(Default)]
struct TurnCancellationState {
    cancelled: bool,
    sealed: bool,
    waker: Option<std::task::Waker>,
}
impl TurnCancellation {
    fn request(&self) -> bool {
        let wake = {
            let mut state = self.state.lock().unwrap_or_else(|e| e.into_inner());
            if state.sealed { return false; }
            state.cancelled = true;
            state.waker.take()
        };
        if let Some(waker) = wake { waker.wake(); }
        true
    }
    // Serialize publication with Stop acknowledgement: no delta is emitted after Stop is accepted.
    fn publish<T>(&self, action: impl FnOnce() -> T) -> Option<T> {
        let state = self.state.lock().unwrap_or_else(|e| e.into_inner());
        if state.cancelled || state.sealed { return None; }
        Some(action())
    }
    fn is_cancelled(&self) -> bool {
        self.state.lock().unwrap_or_else(|e| e.into_inner()).cancelled
    }
    // Terminal classification and Stop acceptance share a single linearization point.
    fn seal(&self) -> bool {
        let mut state = self.state.lock().unwrap_or_else(|e| e.into_inner());
        state.sealed = true;
        state.waker = None;
        state.cancelled
    }
    async fn interrupt<T>(&self, future: impl std::future::Future<Output = T>) -> Option<T> {
        use std::task::Poll;
        let mut future = std::pin::pin!(future);
        std::future::poll_fn(|cx| {
            {
                let mut state = self.state.lock().unwrap_or_else(|e| e.into_inner());
                if state.cancelled || state.sealed { return Poll::Ready(None); }
                state.waker = Some(cx.waker().clone());
            }
            match std::future::Future::poll(future.as_mut(), cx) {
                Poll::Pending => Poll::Pending,
                Poll::Ready(value) => {
                    let mut state = self.state.lock().unwrap_or_else(|e| e.into_inner());
                    state.waker = None;
                    if state.cancelled || state.sealed { Poll::Ready(None) }
                    else { Poll::Ready(Some(value)) }
                }
            }
        }).await
    }
}

#[derive(Clone)]
pub struct LocalModelGateway {
    client: reqwest::Client,
    base: String,
    active: Arc<Mutex<HashMap<String, (String, Arc<TurnCancellation>)>>>,
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
    crate::vault::valid_model(value)
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
        let client = reqwest::Client::builder()
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

    fn append_json_bytes(bytes: &mut Vec<u8>, chunk: &[u8]) -> Result<(), ModelError> {
        const MAX_JSON_BYTES: usize = 1_000_000;
        if chunk.len() > MAX_JSON_BYTES.saturating_sub(bytes.len()) {
            return Err(fault("ZYN-MODEL-RESPONSE"));
        }
        bytes.extend_from_slice(chunk);
        Ok(())
    }
    async fn get_json(&self, path: &str) -> Result<Value, ModelError> {
        let mut reply = self.client.get(format!("{}{}", self.base, path))
            .timeout(Duration::from_secs(5)).send().await
            .map_err(|_| fault("ZYN-MODEL-OFFLINE"))?;
        if !reply.status().is_success() {
            return Err(fault("ZYN-MODEL-OFFLINE"));
        }
        let mut bytes = Vec::new();
        while let Some(chunk) = reply.chunk().await.map_err(|_| fault("ZYN-MODEL-RESPONSE"))? {
            Self::append_json_bytes(&mut bytes, &chunk)?;
        }
        serde_json::from_slice(&bytes).map_err(|_| fault("ZYN-MODEL-RESPONSE"))
    }

    // Consume at most one newline-terminated event from a network chunk.
    // The caller advances by the returned count and retains no unbounded copy.
    fn push_event_bytes(
        pending: &mut Vec<u8>,
        chunk: &[u8],
    ) -> Result<(usize, Option<Vec<u8>>), ModelError> {
        let end = chunk.iter().position(|&b| b == b'\n');
        let used = end.map_or(chunk.len(), |i| i + 1);
        if used > MAX_EVENT_BYTES.saturating_sub(pending.len()) {
            return Err(fault("ZYN-MODEL-RESPONSE"));
        }
        pending.extend_from_slice(&chunk[..used]);
        Ok((used, end.map(|_| std::mem::take(pending))))
    }
    async fn inventory(&self) -> Result<(String, Vec<Value>), ModelError> {
        let version = self
            .get_json("/api/version").await?
            .get("version")
            .and_then(Value::as_str)
            .filter(|x| !x.is_empty() && x.len() <= 64 && x.bytes().all(|b| b.is_ascii_graphic()))
            .ok_or_else(|| fault("ZYN-MODEL-RESPONSE"))?
            .to_owned();
        let raw = self.get_json("/api/tags").await?;
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

    fn cancel_turn(&self, conversation_id: &str, turn_id: &str) -> Result<bool, ModelError> {
        if !token(conversation_id) || !token(turn_id) { return Err(fault("ZYN-MODEL-INPUT")); }
        let active = self.active.lock().map_err(|_| fault("ZYN-MODEL-BUSY"))?;
        Ok(active.get(conversation_id).is_some_and(|(id, flag)| id == turn_id && flag.request()))
    }

    async fn generate(
        &self,
        storage: &Arc<Mutex<NativeVault>>,
        q: GeneratePayload,
        on_event: &(impl Fn(ModelEvent) -> Result<(), ModelError> + Sync),
    ) -> Result<Value, ModelError> {
        self.generate_measured(storage, q, on_event).await.map(|(reply, _)| reply)
    }

    // Runtime-reported prompt usage stays native-only; the public reply schema
    // does not change. Integration tests can compare it with the estimate.
    async fn generate_measured(
        &self,
        storage: &Arc<Mutex<NativeVault>>,
        q: GeneratePayload,
        on_event: &(impl Fn(ModelEvent) -> Result<(), ModelError> + Sync),
    ) -> Result<(Value, Option<u64>), ModelError> {
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
                .model_context(&q.conversation_id, settings.context_limit, context_reserve(settings.context_limit))
                .map_err(|_| fault("ZYN-MODEL-CONTEXT"))?;
            if context.messages.last().map(|m| m.id.as_str()) != Some(q.parent_id.as_str()) {
                return Err(fault("ZYN-MODEL-INPUT"));
            }
            (settings, context)
        };
        let flag = Arc::new(TurnCancellation::default());
        {
            let mut active = self.active.lock().map_err(|_| fault("ZYN-MODEL-BUSY"))?;
            if active.contains_key(&q.conversation_id) {
                return Err(fault("ZYN-MODEL-BUSY"));
            }
            active.insert(q.conversation_id.clone(), (q.turn_id.clone(), flag.clone()));
        }
        struct Guard<'a> {
            map: &'a Mutex<HashMap<String, (String, Arc<TurnCancellation>)>>,
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
            json!({"role":"system","content":SYSTEM_PROMPT}),
        ];
        messages.extend(
            context
                .messages
                .iter()
                .map(|m| json!({"role":&m.role,"content":&m.content})),
        );
        let body = json!({"model":settings.model,"messages":messages,"stream":true,
            "options":{"num_ctx":settings.context_limit,"num_predict":output_budget(settings.context_limit)}});
        let mut output = String::new();
        let mut sequence = 0u32;
        let result: Result<(u64, Option<u64>), ModelError> = async {
            let (_, models) = flag.interrupt(self.inventory()).await
                .ok_or_else(|| fault("ZYN-MODEL-CANCELLED"))??;
            if !Self::has_model(&models, &settings.model) {
                return Err(fault("ZYN-MODEL-MISSING"));
            }
            let reply = self.client.post(format!("{}/api/chat", self.base)).json(&body).send();
            let mut reply = flag.interrupt(reply).await
                .ok_or_else(|| fault("ZYN-MODEL-CANCELLED"))?
                .map_err(|_| fault("ZYN-MODEL-OFFLINE"))?;
            if !reply.status().is_success() {
                return Err(fault("ZYN-MODEL-RUNTIME"));
            }
            let content_type = reply.headers().get(reqwest::header::CONTENT_TYPE)
                .and_then(|x| x.to_str().ok()).unwrap_or("");
            if !content_type.split(';').next().is_some_and(|s| s.trim().eq_ignore_ascii_case("application/x-ndjson")) {
                return Err(fault("ZYN-MODEL-RESPONSE"));
            }
            let mut pending = Vec::new();
            let mut events = 0usize;
            loop {
                let chunk = flag.interrupt(reply.chunk()).await
                    .ok_or_else(|| fault("ZYN-MODEL-CANCELLED"))?
                    .map_err(|_| fault("ZYN-MODEL-RESPONSE"))?
                    .ok_or_else(|| fault("ZYN-MODEL-RESPONSE"))?;
                let mut rest = chunk.as_ref();
                while !rest.is_empty() {
                    if flag.is_cancelled() {
                        return Err(fault("ZYN-MODEL-CANCELLED"));
                    }
                    let (used, line) = Self::push_event_bytes(&mut pending, rest)?;
                    rest = &rest[used..];
                    if let Some(line) = line {
                        events += 1;
                        if events > MAX_EVENTS { return Err(fault("ZYN-MODEL-RESPONSE")); }
                        let event: Value = serde_json::from_slice(&line)
                            .map_err(|_| fault("ZYN-MODEL-RESPONSE"))?;
                        if !event.is_object() || event.get("error").is_some() {
                            return Err(fault("ZYN-MODEL-RESPONSE"));
                        }
                        let delta = event.get("message").and_then(|m| m.get("content"))
                            .and_then(Value::as_str).unwrap_or("");
                        if !delta.is_empty() {
                            if output.len().saturating_add(delta.len()) > MAX_OUTPUT_BYTES {
                                return Err(fault("ZYN-MODEL-RESPONSE"));
                            }
                            flag.publish(|| {
                                output.push_str(delta);
                                sequence += 1;
                                on_event(ModelEvent {
                                    schema_version: 1, turn_id: q.turn_id.clone(),
                                    sequence, kind: "delta", content: delta.to_owned(),
                                })
                            }).ok_or_else(|| fault("ZYN-MODEL-CANCELLED"))??;
                        }
                        if event.get("done") == Some(&Value::Bool(true)) {
                            return Ok((
                                event.get("eval_count").and_then(Value::as_u64).unwrap_or(0),
                                event.get("prompt_eval_count").and_then(Value::as_u64),
                            ));
                        }
                    }
                }
            }
        }.await;
        // The response future has been dropped; Stop cannot change the sealed outcome.
        let cancelled = flag.seal();
        let (eval_count, prompt_eval_count) = result.as_ref().copied().unwrap_or((0, None));
        let status = if cancelled {
            "cancelled"
        } else if result.is_ok() && !output.trim().is_empty() {
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
                    } else if status == "complete" {
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
        on_event(ModelEvent {
            schema_version: 1, turn_id: q.turn_id.clone(), sequence: sequence + 1,
            kind: "terminal", content: String::new(),
        })?;
        if !cancelled && receipt.is_none() {
            if let Err(error) = result { return Err(error); }
        }
        Ok((
            json!({"turnId":q.turn_id,"status":status,"receipt":receipt,"evalCount":eval_count,
            "context":{"estimatedTokens":context.estimated_tokens,"limit":context.limit,"omittedMessages":context.omitted_messages}}),
            prompt_eval_count,
        ))
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

async fn execute(
    gateway: &LocalModelGateway,
    storage: &Arc<Mutex<NativeVault>>,
    request: ModelRequest,
    on_event: &Channel<ModelEvent>,
) -> Result<ModelReply, ModelError> {
    let data = match request.command_id.as_str() {
        "inference.health" => {
            let (version, models) = gateway.inventory().await?;
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
            let (_, models) = gateway.inventory().await?;
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
                .model_context_with_draft(&q.conversation_id, settings.context_limit, context_reserve(settings.context_limit), &q.draft)
                .map_err(|_| fault("ZYN-MODEL-CONTEXT"))?;
            json!({"estimatedTokens":context.estimated_tokens,"limit":context.limit,"includedMessages":context.messages.len()+(if q.draft.is_empty(){0}else{1}),"omittedMessages":context.omitted_messages})
        }
        "inference.turn.generate" => {
            gateway.generate(storage, parse(request.payload)?, &|event| on_event.send(event).map_err(|_| fault("ZYN-MODEL-CHANNEL"))).await?
        }
        "inference.turn.cancel" => {
            let q: CancelPayload = parse(request.payload)?;
            let stopped = gateway.cancel_turn(&q.conversation_id, &q.turn_id)?;
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
    execute(&gateway, &storage, request, &on_event).await
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
        let (version, models) = tauri::async_runtime::block_on(gateway.inventory()).unwrap();
        server.join().unwrap();
        assert_eq!(version, "0.40.18");
        assert_eq!(models.len(), 1);
        assert_eq!(models[0]["name"], "qwen2.5:0.5b");
    }
    #[test]
    fn bounded_json_chunks_reject_oversize_without_growing_buffer() {
        let mut bytes = Vec::new();
        let exact = format!("\"{}\"", "x".repeat(999_998));
        LocalModelGateway::append_json_bytes(&mut bytes, exact.as_bytes()).unwrap();
        assert!(serde_json::from_slice::<Value>(&bytes).is_ok());
        assert!(LocalModelGateway::append_json_bytes(&mut bytes, b"x").is_err());
        assert_eq!(bytes.len(), 1_000_000);
    }
    #[test]
    fn async_event_framing_preserves_chunk_boundaries() {
        let mut pending = Vec::new();
        let (used, line) = LocalModelGateway::push_event_bytes(&mut pending, b"{").unwrap();
        assert_eq!(used, 1);
        assert!(line.is_none());
        let (used, line) = LocalModelGateway::push_event_bytes(&mut pending, b"}\n{}\n").unwrap();
        assert_eq!(used, 2);
        assert_eq!(line.unwrap(), b"{}\n");
        let (used, line) = LocalModelGateway::push_event_bytes(&mut pending, b"{}\n").unwrap();
        assert_eq!(used, 3);
        assert_eq!(line.unwrap(), b"{}\n");
        assert!(pending.is_empty());
        let exact = vec![b'x'; MAX_EVENT_BYTES - 1];
        assert!(LocalModelGateway::push_event_bytes(&mut pending, &exact).unwrap().1.is_none());
        assert!(LocalModelGateway::push_event_bytes(&mut pending, b"\n").unwrap().1.is_some());
        assert!(LocalModelGateway::push_event_bytes(&mut pending, &exact).unwrap().1.is_none());
        assert!(LocalModelGateway::push_event_bytes(&mut pending, b"x\n").is_err());
        assert_eq!(pending.len(), MAX_EVENT_BYTES - 1);
    }
    #[test]
    fn cancellation_latches_and_seals_terminal_outcome() {
        let flag = TurnCancellation::default();
        assert!(flag.request());
        assert!(flag.request());
        assert_eq!(tauri::async_runtime::block_on(flag.interrupt(std::future::ready(42))), None);
        assert_eq!(flag.publish(|| 1), None);
        assert!(flag.seal());
        assert!(!flag.request());
        let completed = TurnCancellation::default();
        assert_eq!(tauri::async_runtime::block_on(completed.interrupt(std::future::ready(42))), Some(42));
        assert!(!completed.seal());
        assert!(!completed.request());
    }

    #[test]
    fn stalled_turn_stops_and_persists_partial_response() {
        use std::sync::mpsc;
        use std::time::{Instant, SystemTime, UNIX_EPOCH};
        let path = std::env::temp_dir().join(format!("zynoa-cancel-{}-{}", std::process::id(),
            SystemTime::now().duration_since(UNIX_EPOCH).unwrap().as_nanos())).join("com.zynoa.desktop");
        std::fs::create_dir_all(&path).unwrap();
        struct Cleanup(std::path::PathBuf);
        impl Drop for Cleanup { fn drop(&mut self) { let _ = std::fs::remove_dir_all(&self.0); } }
        let _cleanup = Cleanup(path.parent().unwrap().to_owned());
        let mut vault = NativeVault::open(&path).unwrap();
        vault.create_conversation("thread_alpha", "Alpha").unwrap();
        vault.append_chat_message(ChatMessageInput { id: "message_user_001", conversation_id: "thread_alpha",
            parent_id: None, role: ChatRole::User, content: "Hello", status: ChatStatus::Complete }).unwrap();
        vault.set_inference_settings("thread_alpha", "qwen2.5:0.5b", 2048).unwrap();
        let storage = Arc::new(Mutex::new(vault));
        let listener = TcpListener::bind("127.0.0.1:0").unwrap();
        let gateway = LocalModelGateway::fixture(&format!("http://{}", listener.local_addr().unwrap()));
        let (release_tx, release_rx) = mpsc::channel::<()>();
        let server = std::thread::spawn(move || {
            for body in [r#"{"version":"0.40.18"}"#, r#"{"models":[{"name":"qwen2.5:0.5b","digest":"abc","size":42}]}"#] {
                let (mut stream, _) = listener.accept().unwrap();
                stream.set_read_timeout(Some(Duration::from_secs(3))).unwrap();
                let mut request = [0u8; 4096]; let _ = stream.read(&mut request).unwrap();
                write!(stream, "HTTP/1.1 200 OK\r\nContent-Type: application/json\r\nContent-Length: {}\r\nConnection: close\r\n\r\n{}", body.len(), body).unwrap();
            }
            let (mut stream, _) = listener.accept().unwrap();
            stream.set_read_timeout(Some(Duration::from_secs(3))).unwrap();
            // Read the request headers AND body before writing a response, so socket
            // shutdown cannot reset a response with unread request data.
            let mut reader = std::io::BufReader::new(&mut stream);
            let mut length = 0usize;
            loop {
                let mut line = String::new();
                if std::io::BufRead::read_line(&mut reader, &mut line).unwrap() == 0 { panic!("request ended"); }
                if line == "\r\n" { break; }
                if let Some((key, value)) = line.split_once(':') {
                    if key.eq_ignore_ascii_case("content-length") { length = value.trim().parse().unwrap(); }
                }
            }
            let mut body = vec![0; length]; reader.read_exact(&mut body).unwrap();
            drop(reader);
            let frame = "{\"message\":{\"content\":\"partial\"},\"done\":false}\n";
            write!(stream, "HTTP/1.1 200 OK\r\nContent-Type: application/x-ndjson\r\nTransfer-Encoding: chunked\r\n\r\n{:X}\r\n{}\r\n", frame.len(), frame).unwrap();
            stream.flush().unwrap();
            let _ = release_rx.recv_timeout(Duration::from_secs(5));
        });
        let (delta_tx, delta_rx) = mpsc::channel::<()>();
        let stop_gateway = gateway.clone();
        let stopper = std::thread::spawn(move || {
            delta_rx.recv_timeout(Duration::from_secs(4)).unwrap();
            assert!(!stop_gateway.cancel_turn("thread_alpha", "wrong_turn_01").unwrap());
            let start = Instant::now();
            assert!(stop_gateway.cancel_turn("thread_alpha", "turn_alpha_001").unwrap());
            start
        });
        let events = Mutex::new(Vec::<ModelEvent>::new());
        let result = tauri::async_runtime::block_on(gateway.generate(&storage, GeneratePayload {
            conversation_id: "thread_alpha".into(), turn_id: "turn_alpha_001".into(),
            parent_id: "message_user_001".into(), assistant_message_id: "message_asst_001".into(),
        }, &|event| {
            if event.kind == "delta" { let _ = delta_tx.send(()); }
            events.lock().unwrap().push(event);
            Ok(())
        }));
        let stopped_at = stopper.join().unwrap();
        let elapsed = stopped_at.elapsed();
        let _ = release_tx.send(()); server.join().unwrap();
        let result = result.unwrap();
        assert!(elapsed < Duration::from_secs(2), "Stop stalled for {elapsed:?}");
        assert_eq!(result["status"], "cancelled");
        assert_eq!(result["receipt"]["id"], "message_asst_001");
        assert!(gateway.active.lock().unwrap().is_empty());
        assert!(!gateway.cancel_turn("thread_alpha", "turn_alpha_001").unwrap());
        let events = events.into_inner().unwrap();
        assert_eq!(events.len(), 2);
        assert_eq!(events[0].kind, "delta"); assert_eq!(events[0].sequence, 1);
        assert_eq!(events[1].kind, "terminal"); assert_eq!(events[1].sequence, 2);
        drop(storage);
        let reopened = NativeVault::open(&path).unwrap();
        let saved = reopened.get_chat_message("thread_alpha", "message_asst_001").unwrap().unwrap();
        assert_eq!(saved.status, "cancelled"); assert_eq!(saved.content, "partial");
    }

    // A loopback fixture that deliberately stalls one HTTP stage without
    // relying on an installed model. Then accept an explicit retry.
    #[test]
    fn cancel_inventory_headers_and_incomplete_frame_then_retry() {
        use std::sync::mpsc;
        use std::time::{Instant, SystemTime, UNIX_EPOCH};
        fn accept(listener: &TcpListener) -> std::net::TcpStream {
            let start = Instant::now();
            loop {
                match listener.accept() {
                    Ok((stream, _)) => {
                        stream.set_nonblocking(false).unwrap();
                        stream.set_read_timeout(Some(Duration::from_secs(3))).unwrap();
                        stream.set_write_timeout(Some(Duration::from_secs(3))).unwrap();
                        return stream;
                    }
                    Err(e) if e.kind() == std::io::ErrorKind::WouldBlock => {
                        assert!(start.elapsed() < Duration::from_secs(8), "fixture accept timed out");
                        std::thread::sleep(Duration::from_millis(5));
                    }
                    Err(e) => panic!("fixture accept: {e}"),
                }
            }
        }
        fn read_request(stream: &mut std::net::TcpStream) -> String {
            use std::io::BufRead;
            let mut reader = std::io::BufReader::new(stream);
            let mut first = String::new();
            assert!(reader.read_line(&mut first).unwrap() > 0);
            let mut length = 0usize;
            loop {
                let mut line = String::new();
                assert!(reader.read_line(&mut line).unwrap() > 0);
                if line == "\r\n" { break; }
                if let Some((key, value)) = line.split_once(':') {
                    if key.eq_ignore_ascii_case("content-length") { length = value.trim().parse().unwrap(); }
                }
            }
            let mut bytes = vec![0; length]; reader.read_exact(&mut bytes).unwrap();
            first
        }
        fn json_response(stream: &mut std::net::TcpStream, body: &str) {
            write!(stream, "HTTP/1.1 200 OK\r\nContent-Type: application/json\r\nContent-Length: {}\r\nConnection: close\r\n\r\n{}", body.len(), body).unwrap();
        }
        const VERSION: &str = r#"{"version":"0.40.18"}"#;
        const MODELS: &str = r#"{"models":[{"name":"qwen2.5:0.5b","digest":"abc","size":42}]}"#;
        for stage in ["inventory", "headers", "frame"] {
            let root = std::env::temp_dir().join(format!("zynoa-cancel-stage-{}-{}-{stage}", std::process::id(),
                SystemTime::now().duration_since(UNIX_EPOCH).unwrap().as_nanos()));
            let path = root.join("com.zynoa.desktop");
            std::fs::create_dir_all(&path).unwrap();
            struct Cleanup(std::path::PathBuf);
            impl Drop for Cleanup { fn drop(&mut self) { let _ = std::fs::remove_dir_all(&self.0); } }
            let _cleanup = Cleanup(root);
            let mut vault = NativeVault::open(&path).unwrap();
            vault.create_conversation("thread_alpha", "Alpha").unwrap();
            vault.append_chat_message(ChatMessageInput { id: "message_user_001", conversation_id: "thread_alpha",
                parent_id: None, role: ChatRole::User, content: "Hello", status: ChatStatus::Complete }).unwrap();
            vault.set_inference_settings("thread_alpha", "qwen2.5:0.5b", 2048).unwrap();
            let storage = Arc::new(Mutex::new(vault));
            let listener = TcpListener::bind("127.0.0.1:0").unwrap();
            listener.set_nonblocking(true).unwrap();
            let gateway = LocalModelGateway::fixture(&format!("http://{}", listener.local_addr().unwrap()));
            let (stalled_tx, stalled_rx) = mpsc::channel::<()>();
            let (release_tx, release_rx) = mpsc::channel::<()>();
            let server = std::thread::spawn(move || {
                let mut version = accept(&listener);
                assert!(read_request(&mut version).starts_with("GET /api/version "));
                if stage == "inventory" {
                    stalled_tx.send(()).unwrap();
                    let _ = release_rx.recv_timeout(Duration::from_secs(5));
                    drop(version);
                } else {
                    json_response(&mut version, VERSION); drop(version);
                    let mut models = accept(&listener);
                    assert!(read_request(&mut models).starts_with("GET /api/tags "));
                    json_response(&mut models, MODELS); drop(models);
                    let mut chat = accept(&listener);
                    assert!(read_request(&mut chat).starts_with("POST /api/chat "));
                    if stage == "frame" {
                        let incomplete = "{\"message\":{\"content\":\"uncommitted";
                        write!(chat, "HTTP/1.1 200 OK\r\nContent-Type: application/x-ndjson\r\nTransfer-Encoding: chunked\r\n\r\n{:X}\r\n{}\r\n", incomplete.len(), incomplete).unwrap();
                        chat.flush().unwrap();
                    }
                    stalled_tx.send(()).unwrap();
                    let _ = release_rx.recv_timeout(Duration::from_secs(5));
                    drop(chat);
                }
                let mut version = accept(&listener);
                assert!(read_request(&mut version).starts_with("GET /api/version "));
                json_response(&mut version, VERSION); drop(version);
                let mut models = accept(&listener);
                assert!(read_request(&mut models).starts_with("GET /api/tags "));
                json_response(&mut models, MODELS); drop(models);
                let mut chat = accept(&listener);
                assert!(read_request(&mut chat).starts_with("POST /api/chat "));
                let body = "{\"message\":{\"content\":\"retry complete\"},\"done\":true,\"eval_count\":2}\n";
                write!(chat, "HTTP/1.1 200 OK\r\nContent-Type: application/x-ndjson\r\nContent-Length: {}\r\nConnection: close\r\n\r\n{}", body.len(), body).unwrap();
            });
            let stopper_gateway = gateway.clone();
            let stopper = std::thread::spawn(move || {
                stalled_rx.recv_timeout(Duration::from_secs(5)).unwrap();
                // Give the client a chance to enter its pending read.
                std::thread::sleep(Duration::from_millis(50));
                assert!(!stopper_gateway.cancel_turn("thread_alpha", "wrong_turn_01").unwrap());
                let start = Instant::now();
                assert!(stopper_gateway.cancel_turn("thread_alpha", "turn_alpha_001").unwrap());
                start
            });
            let events = Mutex::new(Vec::<ModelEvent>::new());
            let first = tauri::async_runtime::block_on(gateway.generate(&storage, GeneratePayload {
                conversation_id: "thread_alpha".into(), turn_id: "turn_alpha_001".into(),
                parent_id: "message_user_001".into(), assistant_message_id: "message_asst_001".into(),
            }, &|event| { events.lock().unwrap().push(event); Ok(()) }));
            let elapsed = stopper.join().unwrap().elapsed();
            let _ = release_tx.send(());
            let first = first.unwrap();
            assert!(elapsed < Duration::from_secs(2), "Stop stalled at {stage}: {elapsed:?}");
            assert_eq!(first["status"], "cancelled", "{stage}");
            assert!(first["receipt"].is_null());
            assert!(gateway.active.lock().unwrap().is_empty());
            assert!(!gateway.cancel_turn("thread_alpha", "turn_alpha_001").unwrap());
            {
                let mut recorded = events.lock().unwrap();
                assert_eq!(recorded.len(), 1);
                assert_eq!(recorded[0].kind, "terminal");
                assert_eq!(recorded[0].sequence, 1);
                recorded.clear();
            }
            let retry = tauri::async_runtime::block_on(gateway.generate(&storage, GeneratePayload {
                conversation_id: "thread_alpha".into(), turn_id: "turn_alpha_002".into(),
                parent_id: "message_user_001".into(), assistant_message_id: "message_asst_002".into(),
            }, &|event| { events.lock().unwrap().push(event); Ok(()) })).unwrap();
            server.join().unwrap();
            assert_eq!(retry["status"], "complete", "{stage}");
            assert_eq!(retry["receipt"]["id"], "message_asst_002");
            assert_eq!(retry["evalCount"], 2);
            assert!(gateway.active.lock().unwrap().is_empty());
            let recorded = events.into_inner().unwrap();
            assert_eq!(recorded.len(), 2);
            assert_eq!(recorded[0].turn_id, "turn_alpha_002");
            assert_eq!(recorded[0].kind, "delta");
            assert_eq!(recorded[1].kind, "terminal");
            drop(storage);
            let reopened = NativeVault::open(&path).unwrap();
            assert!(reopened.get_chat_message("thread_alpha", "message_asst_001").unwrap().is_none());
            let saved = reopened.get_chat_message("thread_alpha", "message_asst_002").unwrap().unwrap();
            assert_eq!(saved.status, "complete");
            assert_eq!(saved.content, "retry complete");
        }
    }

    #[test]
    fn accepted_stop_and_terminal_seal_agree_under_race() {
        for _ in 0..32 {
            let state = Arc::new(TurnCancellation::default());
            let barrier = Arc::new(std::sync::Barrier::new(2));
            let other = state.clone();
            let start = barrier.clone();
            let worker = std::thread::spawn(move || {
                start.wait();
                other.request()
            });
            barrier.wait();
            let cancelled = state.seal();
            assert_eq!(worker.join().unwrap(), cancelled);
            assert!(!state.request());
        }
    }

    // Explicit CI-only integration: the shipped gateway, not a fixture HTTP
    // implementation, sends a synthetic turn to the pinned local CPU runtime.
    #[test]
    #[ignore = "requires the pinned local Ollama runtime and installed model"]
    fn real_ollama_product_gateway_and_restart() {
        use std::time::{Instant, SystemTime, UNIX_EPOCH};
        use std::io::Write;
        assert_eq!(std::env::var("GITHUB_ACTIONS").as_deref(), Ok("true"));
        let source = std::env::var("ZYNOA_P03_SOURCE_SHA").unwrap();
        assert_eq!(source.len(), 40);
        assert!(source.bytes().all(|b| b.is_ascii_hexdigit()));
        let proof_path = std::path::PathBuf::from(std::env::var_os("ZYNOA_P03_REAL_MODEL_PROOF").unwrap());
        let root = std::env::temp_dir().join(format!("zynoa-real-model-{}-{}", std::process::id(),
            SystemTime::now().duration_since(UNIX_EPOCH).unwrap().as_nanos()));
        let path = root.join("com.zynoa.desktop");
        std::fs::create_dir_all(&path).unwrap();
        struct Cleanup(std::path::PathBuf);
        impl Drop for Cleanup { fn drop(&mut self) { let _ = std::fs::remove_dir_all(&self.0); } }
        let _cleanup = Cleanup(root);
        let gateway = LocalModelGateway::new().unwrap();
        let (version, models) = tauri::async_runtime::block_on(gateway.inventory()).unwrap();
        assert_eq!(version, "0.40.18");
        let model = "qwen2.5:0.5b";
        let matches: Vec<_> = models.iter().filter(|m| m["name"].as_str() == Some(model)).collect();
        assert_eq!(matches.len(), 1);
        let digest = matches[0]["digest"].as_str().unwrap();
        assert_eq!(digest.len(), 64);
        assert_eq!(digest, "a8b0c51577010a279d933d14c2a8ab4b268079d44c5c8830c0a93900f1827c67");
        assert!(LocalModelGateway::has_model(&models, model));
        let mut vault = NativeVault::open(&path).unwrap();
        vault.create_conversation("thread_alpha", "Synthetic model acceptance").unwrap();
        vault.create_conversation("thread_bravo", "Isolated synthetic conversation").unwrap();
        vault.set_inference_settings("thread_alpha", model, 1024).unwrap();
        vault.set_inference_settings("thread_bravo", model, 2048).unwrap();
        let prompt = "Reply with a short greeting.";
        let preview = vault.model_context_with_draft("thread_alpha", 1024, context_reserve(1024), prompt).unwrap();
        vault.append_chat_message(ChatMessageInput {
            id: "message_user_001", conversation_id: "thread_alpha", parent_id: None,
            role: ChatRole::User, content: prompt, status: ChatStatus::Complete,
        }).unwrap();
        let multilingual = "Reply with a short greeting. اردو 中文 Türkçe العربية 🙂";
        let multilingual_preview = vault.model_context_with_draft("thread_bravo", 2048, context_reserve(2048), multilingual).unwrap();
        vault.append_chat_message(ChatMessageInput {
            id: "message_other_01", conversation_id: "thread_bravo", parent_id: None,
            role: ChatRole::User, content: multilingual, status: ChatStatus::Complete,
        }).unwrap();
        let storage = Arc::new(Mutex::new(vault));
        let events = Mutex::new(Vec::<ModelEvent>::new());
        let first_delta = Mutex::new(None::<u64>);
        let started = Instant::now();
        let (result, prompt_eval_count) = tauri::async_runtime::block_on(gateway.generate_measured(&storage, GeneratePayload {
            conversation_id: "thread_alpha".into(), turn_id: "turn_alpha_001".into(),
            parent_id: "message_user_001".into(), assistant_message_id: "message_asst_001".into(),
        }, &|event| {
            if event.kind == "delta" {
                let mut first = first_delta.lock().unwrap();
                if first.is_none() { *first = Some(started.elapsed().as_millis() as u64); }
            }
            events.lock().unwrap().push(event);
            Ok(())
        })).unwrap();
        let total_ms = started.elapsed().as_millis() as u64;
        let ttft_ms = first_delta.into_inner().unwrap().expect("actual streamed text required");
        assert_eq!(result["status"], "complete");
        assert_eq!(result["receipt"]["id"], "message_asst_001");
        assert!(result["evalCount"].as_u64().unwrap() > 0);
        assert_eq!(result["context"]["estimatedTokens"].as_u64(), Some(preview.estimated_tokens as u64));
        assert_eq!(result["context"]["omittedMessages"].as_u64(), Some(preview.omitted_messages as u64));
        assert_eq!(result["context"]["limit"], 1024);
        let reported_prompt = prompt_eval_count.expect("real runtime prompt_eval_count required");
        assert!(reported_prompt > 0);
        assert!(reported_prompt + u64::from(output_budget(1024)) <= u64::from(preview.estimated_tokens));
        assert!(result["evalCount"].as_u64().unwrap() <= u64::from(output_budget(1024)));
        assert!(gateway.active.lock().unwrap().is_empty());
        let events = events.into_inner().unwrap();
        assert!(events.len() >= 2);
        assert_eq!(events.last().unwrap().kind, "terminal");
        assert!(events.iter().enumerate().all(|(i, event)|
            event.sequence == i as u32 + 1 && event.turn_id == "turn_alpha_001"));
        assert_eq!(events.iter().filter(|event| event.kind == "terminal").count(), 1);
        let streamed: String = events.iter().filter(|event| event.kind == "delta")
            .map(|event| event.content.as_str()).collect();
        assert!(!streamed.trim().is_empty());
        let (multilingual_result, multilingual_count) = tauri::async_runtime::block_on(gateway.generate_measured(&storage, GeneratePayload {
            conversation_id: "thread_bravo".into(), turn_id: "turn_bravo_001".into(),
            parent_id: "message_other_01".into(), assistant_message_id: "message_asst_002".into(),
        }, &|_| Ok(()))).unwrap();
        assert_eq!(multilingual_result["status"], "complete");
        assert_eq!(multilingual_result["context"]["estimatedTokens"].as_u64(), Some(multilingual_preview.estimated_tokens as u64));
        assert_eq!(multilingual_result["context"]["limit"], 2048);
        let multilingual_count = multilingual_count.expect("real multilingual prompt_eval_count required");
        assert!(multilingual_count > 0);
        assert!(multilingual_count + u64::from(output_budget(2048)) <= u64::from(multilingual_preview.estimated_tokens));
        assert!(multilingual_result["evalCount"].as_u64().unwrap() <= u64::from(output_budget(2048)));
        drop(storage);
        let reopened = NativeVault::open(&path).unwrap();
        let saved = reopened.get_chat_message("thread_alpha", "message_asst_001").unwrap().unwrap();
        assert_eq!(saved.content, streamed);
        assert_eq!(saved.status, "complete");
        assert!(reopened.get_chat_message("thread_bravo", "message_asst_001").unwrap().is_none());
        let second_saved = reopened.get_chat_message("thread_bravo", "message_asst_002").unwrap().unwrap();
        assert_eq!(second_saved.status, "complete");
        assert!(!second_saved.content.trim().is_empty());
        let alpha = reopened.get_inference_settings("thread_alpha").unwrap().unwrap();
        let bravo = reopened.get_inference_settings("thread_bravo").unwrap().unwrap();
        assert_eq!(alpha.model, model); assert_eq!(alpha.context_limit, 1024);
        assert_eq!(bravo.model, model); assert_eq!(bravo.context_limit, 2048);
        let proof = json!({
            "schema_version":1, "source_commit_sha":source, "runtime_version":version,
            "model":model, "model_digest":digest, "local_only":true, "synthetic_prompt":true,
            "product_adapter":true, "native_ui":false, "ttft_ms":ttft_ms, "total_ms":total_ms,
            "content_chunks":events.len()-1, "output_bytes":streamed.len(),
            "eval_count":result["evalCount"], "context_preview_matches":true,
            "context_limit":1024, "estimated_tokens":preview.estimated_tokens,
            "terminal_count":1, "durable_receipt_and_restart":true, "thread_settings_isolated":true,
            "token_calibration": [
                {"case":"short_english","context_limit":1024,"estimated_total":preview.estimated_tokens,
                 "runtime_reported_prompt":reported_prompt,"reserved_output":output_budget(1024),
                 "generated_tokens":result["evalCount"]},
                {"case":"mixed_utf8","context_limit":2048,"estimated_total":multilingual_preview.estimated_tokens,
                 "runtime_reported_prompt":multilingual_count,"reserved_output":output_budget(2048),
                 "generated_tokens":multilingual_result["evalCount"]}
            ],
            "token_counts_scope":"runtime-reported counts; cache and template dependent, not a universal tokenizer bound",
            "done":true
        });
        let mut file = std::fs::OpenOptions::new().write(true).create_new(true).open(proof_path).unwrap();
        writeln!(file, "{}", serde_json::to_string_pretty(&proof).unwrap()).unwrap();
        println!("{}", proof);
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
