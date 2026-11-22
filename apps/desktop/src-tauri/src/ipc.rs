//! P01 M01/M16 versioned read-only transport; not a workspace database.
//! Caller input cannot grant filesystem, secret, process or outbound authority.
use serde::{Deserialize, Serialize};

const SCHEMA_VERSION: u8 = 1;
const MAX_ENVELOPE_BYTES: usize = 1024;

#[derive(Clone, Debug, Deserialize, Serialize)]
#[serde(rename_all = "camelCase", deny_unknown_fields)]
pub struct WorkspaceStatusRequest {
    schema_version: u8,
    command_id: String,
    correlation_id: String,
    workspace_scope: String,
    payload: EmptyPayload,
}

#[derive(Clone, Debug, Deserialize, Serialize)]
#[serde(deny_unknown_fields)]
struct EmptyPayload {}

#[derive(Debug, PartialEq, Eq, Serialize)]
#[serde(rename_all = "camelCase")]
pub struct IpcError {
    code: &'static str,
    recovery_action: &'static str,
}

fn denied(code: &'static str) -> IpcError {
    IpcError {
        code,
        recovery_action: "Review the request or restart the local application.",
    }
}

#[derive(Debug, PartialEq, Eq, Serialize)]
#[serde(rename_all = "camelCase")]
pub struct WorkspaceStatusReply {
    schema_version: u8,
    command_id: &'static str,
    correlation_id: String,
    status: &'static str,
    workspace_state: &'static str,
    writable: bool,
}

fn validate(request: WorkspaceStatusRequest) -> Result<WorkspaceStatusReply, IpcError> {
    let encoded_len = serde_json::to_vec(&request)
        .map_err(|_| denied("ZYN-IPC-004"))?
        .len();
    if encoded_len > MAX_ENVELOPE_BYTES {
        return Err(denied("ZYN-IPC-004"));
    }
    if request.schema_version != SCHEMA_VERSION {
        return Err(denied("ZYN-IPC-001"));
    }
    if request.command_id != "workspace.status" {
        return Err(denied("ZYN-IPC-002"));
    }
    if request.workspace_scope != "local" {
        return Err(denied("ZYN-IPC-003"));
    }
    let id = &request.correlation_id;
    if !(16..=64).contains(&id.len())
        || !id.bytes().all(|ch| ch.is_ascii_alphanumeric() || ch == b'-')
    {
        return Err(denied("ZYN-IPC-005"));
    }
    Ok(WorkspaceStatusReply {
        schema_version: SCHEMA_VERSION,
        command_id: "workspace.status",
        correlation_id: request.correlation_id,
        status: "ok",
        workspace_state: "not_configured",
        writable: false,
    })
}

/// The Tauri capability allows this command only from main's local origin.
/// An independent runtime window-label check rejects accidental extra grants.
#[tauri::command]
pub fn workspace_handshake(
    window: tauri::Window,
    request: WorkspaceStatusRequest,
) -> Result<WorkspaceStatusReply, IpcError> {
    if window.label() != "main" {
        return Err(denied("ZYN-IPC-006"));
    }
    crate::security::allow_local_workspace_handshake(window.label())
        .map_err(|_| denied("ZYN-IPC-006"))?;
    validate(request)
}

#[cfg(test)]
mod tests {
    use super::*;

    fn valid() -> WorkspaceStatusRequest {
        WorkspaceStatusRequest {
            schema_version: 1,
            command_id: "workspace.status".into(),
            correlation_id: "d4ae7a09-142f-4db9-85c3".into(),
            workspace_scope: "local".into(),
            payload: EmptyPayload {},
        }
    }

    #[test]
    fn valid_handshake_is_read_only_not_a_workspace_claim() {
        let reply = validate(valid()).unwrap();
        assert_eq!(reply.status, "ok");
        assert_eq!(reply.workspace_state, "not_configured");
        assert_eq!(reply.command_id, "workspace.status");
        assert!(!reply.writable);
    }

    #[test]
    fn wrong_version_command_scope_and_id_are_denied() {
        let mut old = valid();
        old.schema_version = 0;
        assert_eq!(validate(old).unwrap_err().code, "ZYN-IPC-001");
        let mut unknown = valid();
        unknown.command_id = "workspace.delete".into();
        assert_eq!(validate(unknown).unwrap_err().code, "ZYN-IPC-002");
        let mut other_scope = valid();
        other_scope.workspace_scope = "../external".into();
        assert_eq!(validate(other_scope).unwrap_err().code, "ZYN-IPC-003");
        let mut malformed_id = valid();
        malformed_id.correlation_id = "../../secrets".into();
        assert_eq!(validate(malformed_id).unwrap_err().code, "ZYN-IPC-005");
    }

    #[test]
    fn oversized_envelope_is_bounded_without_user_payload_logging() {
        let mut oversized = valid();
        oversized.command_id = "x".repeat(MAX_ENVELOPE_BYTES);
        assert_eq!(validate(oversized).unwrap_err().code, "ZYN-IPC-004");
    }

    #[test]
    fn strict_json_rejects_extra_fields_and_path_payloads() {
        let mut raw = serde_json::to_value(valid()).unwrap();
        raw["payload"]["path"] = serde_json::json!("C:/Users/private");
        assert!(serde_json::from_value::<WorkspaceStatusRequest>(raw).is_err());
        let mut unknown = serde_json::to_value(valid()).unwrap();
        unknown["newPrivilege"] = serde_json::json!(true);
        assert!(serde_json::from_value::<WorkspaceStatusRequest>(unknown).is_err());
    }

    #[test]
    fn repeated_read_is_idempotent_and_never_writable() {
        let a = validate(valid()).unwrap();
        let b = validate(valid()).unwrap();
        assert_eq!(a, b);
        assert!(!b.writable);
    }
}
