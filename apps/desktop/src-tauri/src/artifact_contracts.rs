//! P03 source-only contracts for attachments, artifacts, exports and tools.
//! These validators are deliberately pure: no renderer path, URL or command is trusted.
use sha2::{Digest, Sha256};

const MAX_NAME: usize = 160;
const MAX_ATTACHMENT: u64 = 25 * 1024 * 1024;
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

#[cfg(test)]
mod tests {
    use super::*;
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
