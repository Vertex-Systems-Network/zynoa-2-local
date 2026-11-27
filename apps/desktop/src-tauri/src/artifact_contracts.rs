//! P03 source-only contracts for attachments, artifacts, exports and tools.
//! These validators are deliberately pure: no renderer path, URL or command is trusted.
use sha2::{Digest, Sha256};

const MAX_NAME: usize = 160;
pub(crate) const MAX_ATTACHMENT: u64 = 25 * 1024 * 1024;
const MAX_EXPORT_ITEMS: usize = 4096;

#[derive(Debug, Clone, PartialEq, Eq)]
pub struct AttachmentReceipt { pub name: String, pub bytes: u64, pub sha256: String }

/// Cross-platform, single-component display name policy. This is not filesystem
/// authorization; actual import/restore must still use controlled roots and safe handles.
pub(crate) fn valid_managed_basename(name: &str) -> bool {
    if name.is_empty() || name.len() > MAX_NAME
        || name.contains(['/', '\\', ':', '*', '?', '"', '<', '>', '|'])
        || name.chars().any(char::is_control)
        || name.ends_with(' ') || name.ends_with('.') {
        return false;
    }
    let stem = name.split('.').next().unwrap_or("").trim_end_matches(' ').to_ascii_uppercase();
    !matches!(stem.as_str(), "" | "CON" | "PRN" | "AUX" | "NUL" | "CONIN$" | "CONOUT$"
        | "COM1" | "COM2" | "COM3" | "COM4" | "COM5" | "COM6" | "COM7" | "COM8" | "COM9"
        | "LPT1" | "LPT2" | "LPT3" | "LPT4" | "LPT5" | "LPT6" | "LPT7" | "LPT8" | "LPT9"
        | "COM¹" | "COM²" | "COM³" | "LPT¹" | "LPT²" | "LPT³")
}

pub fn attachment_receipt(name: &str, bytes: &[u8]) -> Option<AttachmentReceipt> {
    if !valid_managed_basename(name) || bytes.len() as u64 > MAX_ATTACHMENT { return None; }
    let mut h = Sha256::new(); h.update(bytes);
    Some(AttachmentReceipt { name: name.to_owned(), bytes: bytes.len() as u64,
        sha256: format!("{:x}", h.finalize()) })
}

pub fn verify_attachment(receipt: &AttachmentReceipt, bytes: &[u8]) -> bool {
    attachment_receipt(&receipt.name, bytes).is_some_and(|r| r == *receipt)
}

pub fn export_manifest(ids: &[&str]) -> Option<Vec<String>> {
    if ids.is_empty() || ids.len() > MAX_EXPORT_ITEMS { return None; }
    let mut out = Vec::with_capacity(ids.len());
    for id in ids {
        if id.is_empty() || id.len() > 128 || !id.bytes().all(|b| b.is_ascii_alphanumeric() || b == b'_' || b == b'-') { return None; }
        out.push((*id).to_owned());
    }
    Some(out)
}

pub fn tool_is_allowed(name: &str) -> bool {
    matches!(name, "none" | "local.read_attachment" | "local.write_artifact")
}

/// Closed vocabulary for review candidates; the legacy "none" sentinel
/// is not a reviewable operation. This does not grant execution authority.
#[derive(Debug, Clone, Copy, PartialEq, Eq)]
pub(crate) enum ReviewTool { ReadAttachment, WriteArtifact }

impl ReviewTool {
    fn parse(name: &str) -> Option<Self> {
        match name {
            "local.read_attachment" => Some(Self::ReadAttachment),
            "local.write_artifact" => Some(Self::WriteArtifact),
            _ => None,
        }
    }
}

/// Native-owned, validated identity. No paths, arguments or renderer
/// deserialization. Bind the review to the exact target content, not just its ID.
#[derive(Debug, Clone, PartialEq, Eq)]
pub(crate) struct ToolReviewIdentity {
    conversation_id: String,
    turn_id: String,
    request_id: String,
    target_id: String,
    target_sha256: String,
    tool: ReviewTool,
}

impl ToolReviewIdentity {
    pub(crate) fn new(conversation_id: &str, turn_id: &str, request_id: &str,
        target_id: &str, target_sha256: &str, tool: &str) -> Option<Self> {
        fn valid_id(id: &str) -> bool {
            (8..=64).contains(&id.len())
                && id.bytes().all(|b| b.is_ascii_alphanumeric() || b == b'-' || b == b'_')
        }
        if ![conversation_id, turn_id, request_id, target_id].iter().all(|id| valid_id(id))
            || target_sha256.len() != 64
            || !target_sha256.bytes().all(|b| b.is_ascii_digit() || (b'a'..=b'f').contains(&b)) {
            return None;
        }
        Some(Self { conversation_id: conversation_id.to_owned(), turn_id: turn_id.to_owned(),
            request_id: request_id.to_owned(), target_id: target_id.to_owned(),
            target_sha256: target_sha256.to_owned(), tool: ReviewTool::parse(tool)? })
    }
}

#[derive(Debug, Clone, Copy, PartialEq, Eq)]
pub(crate) enum ReviewChoice { Approve, Deny }

#[derive(Debug, Clone, Copy, PartialEq, Eq)]
pub(crate) enum ReviewState { Pending, Denied, ScopeMismatch, ApprovedCandidate }

/// Classify only. A matching approval is NOT a grant; a future native broker
/// must verify provenance and expiry and atomically consume a durable review.
pub(crate) fn classify_tool_review(expected: &ToolReviewIdentity,
    review: Option<(&ToolReviewIdentity, ReviewChoice)>) -> ReviewState {
    match review {
        None => ReviewState::Pending,
        Some((actual, _)) if actual != expected => ReviewState::ScopeMismatch,
        Some((_, ReviewChoice::Deny)) => ReviewState::Denied,
        Some((_, ReviewChoice::Approve)) => ReviewState::ApprovedCandidate,
    }
}

#[cfg(test)]
mod tests {
    use super::*;
    #[test]
    fn tool_review_is_bound_to_every_identity_field() {
        let digest = "a".repeat(64);
        let identity = ToolReviewIdentity::new("thread_001", "turn_001", "request_001",
            "target_001", &digest, "local.read_attachment").unwrap();
        assert_eq!(classify_tool_review(&identity, None), ReviewState::Pending);
        assert_eq!(classify_tool_review(&identity, Some((&identity, ReviewChoice::Deny))), ReviewState::Denied);
        assert_eq!(classify_tool_review(&identity, Some((&identity, ReviewChoice::Approve))), ReviewState::ApprovedCandidate);
        let mut mismatches = Vec::new();
        let mut other = identity.clone(); other.conversation_id = "thread_002".into(); mismatches.push(other);
        let mut other = identity.clone(); other.turn_id = "turn_002".into(); mismatches.push(other);
        let mut other = identity.clone(); other.request_id = "request_002".into(); mismatches.push(other);
        let mut other = identity.clone(); other.target_id = "target_002".into(); mismatches.push(other);
        let mut other = identity.clone(); other.target_sha256 = "b".repeat(64); mismatches.push(other);
        let mut other = identity.clone(); other.tool = ReviewTool::WriteArtifact; mismatches.push(other);
        for other in mismatches {
            for choice in [ReviewChoice::Approve, ReviewChoice::Deny] {
                assert_eq!(classify_tool_review(&identity, Some((&other, choice))), ReviewState::ScopeMismatch);
            }
        }
    }

    #[test]
    fn tool_review_rejects_malformed_scope_and_nonlocal_tools() {
        let digest = "a".repeat(64);
        for bad in ["", "short", "../target", "target/01", "target:01", "target 01", "target_é", "target_01\n", &"x".repeat(65)] {
            for index in 0..4 {
                let mut ids = ["thread_001", "turn_001", "request_001", "target_001"];
                ids[index] = bad;
                assert!(ToolReviewIdentity::new(ids[0], ids[1], ids[2], ids[3], &digest, "local.read_attachment").is_none());
            }
        }
        for bad in ["", "none", "shell.exec", "local.read_attachment ", "Local.read_attachment", "https://example.invalid"] {
            assert!(ToolReviewIdentity::new("thread_001", "turn_001", "request_001", "target_001", &digest, bad).is_none());
        }
        for bad in ["", &"a".repeat(63), &"a".repeat(65), &"A".repeat(64), &"g".repeat(64)] {
            assert!(ToolReviewIdentity::new("thread_001", "turn_001", "request_001", "target_001", bad, "local.write_artifact").is_none());
        }
        assert!(ToolReviewIdentity::new(&"x".repeat(64), "turn_001", "request_001", "target_001", &digest, "local.write_artifact").is_some());
    }
    #[test]
    fn managed_basename_rejects_unsafe_platform_names() {
        for name in ["", ".", "..", "dir/file", "dir\\file", "file:stream", "a\0b",
            "a\nb", "name.", "name ", "CON", "nul.txt", "CoM1 .txt", "LPT².log",
            "CONIN$", "bad?.txt", "bad*.txt", "bad|.txt", "bad<.txt", "bad>.txt", "bad\".txt"] {
            assert!(!valid_managed_basename(name), "{name:?}");
            assert!(attachment_receipt(name, b"x").is_none(), "{name:?}");
        }
        for name in ["note.txt", "résumé.pdf", "聊天.txt", "a b.txt", "COM10.txt"] {
            assert!(attachment_receipt(name, b"x").is_some(), "{name:?}");
        }
        assert!(attachment_receipt(&"a".repeat(MAX_NAME), b"x").is_some());
        assert!(attachment_receipt(&"a".repeat(MAX_NAME + 1), b"x").is_none());
    }
    #[test] fn attachment_hash_is_immutable_and_bounded() {
        let r = attachment_receipt("note.txt", b"hello").unwrap();
        assert!(verify_attachment(&r, b"hello")); assert!(!verify_attachment(&r, b"bye"));
        assert!(attachment_receipt("../secret", b"x").is_none());
    }
    #[test] fn export_and_tool_boundaries_fail_closed() {
        assert_eq!(export_manifest(&["thread_1", "message-2"]).unwrap().len(), 2);
        assert!(export_manifest(&["thread/escape"]).is_none());
        assert!(tool_is_allowed("local.read_attachment"));
        assert!(!tool_is_allowed("shell.exec"));
    }
}
