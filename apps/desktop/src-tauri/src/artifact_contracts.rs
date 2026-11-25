//! P03 source-only contracts for attachments, artifacts, exports and tools.
//! These validators are deliberately pure: no renderer path, URL or command is trusted.
use sha2::{Digest, Sha256};

const MAX_NAME: usize = 160;
const MAX_ATTACHMENT: u64 = 25 * 1024 * 1024;
const MAX_EXPORT_ITEMS: usize = 4096;

#[derive(Debug, Clone, PartialEq, Eq)]
pub struct AttachmentReceipt { pub name: String, pub bytes: u64, pub sha256: String }

pub fn attachment_receipt(name: &str, bytes: &[u8]) -> Option<AttachmentReceipt> {
    if name.is_empty() || name.len() > MAX_NAME || name.contains(['/', '\\', '\0'])
        || name == "." || name == ".." || bytes.len() as u64 > MAX_ATTACHMENT { return None; }
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

#[cfg(test)]
mod tests {
    use super::*;
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
