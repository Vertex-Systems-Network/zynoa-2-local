//! P03 T12–T14 fail-closed backup/recovery contracts.
use sha2::{Digest, Sha256};

#[derive(Debug, Clone, PartialEq, Eq)]
pub struct BackupEnvelope { pub version: u8, pub nonce: String, pub ciphertext_sha256: String, pub key_ref: String }

pub fn envelope(version: u8, nonce: &str, ciphertext: &[u8], key_ref: &str) -> Option<BackupEnvelope> {
    if version != 1 || nonce.len() < 16 || nonce.len() > 64 || key_ref.is_empty() || key_ref.len() > 128
        || !key_ref.bytes().all(|b| b.is_ascii_alphanumeric() || b == b'-' || b == b'_') || ciphertext.is_empty() { return None; }
    let mut h = Sha256::new(); h.update(ciphertext);
    Some(BackupEnvelope { version, nonce: nonce.to_owned(), ciphertext_sha256: format!("{:x}", h.finalize()), key_ref: key_ref.to_owned() })
}
pub fn verify_envelope(meta: &BackupEnvelope, ciphertext: &[u8]) -> bool { envelope(meta.version, &meta.nonce, ciphertext, &meta.key_ref).is_some_and(|x| x == *meta) }
pub fn staged_restore_target(path: &str) -> Option<String> { if path.is_empty() || path.contains(['/', '\\', '\0']) || path == "." || path == ".." { None } else { Some(format!("restore-staging/{path}")) } }
pub fn performance_budget_ms(cold: u64, warm: &[u64]) -> bool { cold <= 15_000 && !warm.is_empty() && warm.iter().all(|x| *x <= 2_000) }

#[cfg(test)]
mod tests { use super::*;
    #[test] fn encrypted_backup_is_integrity_bound_and_staged() { let e=envelope(1,"0123456789abcdef",b"ciphertext","os-key-01").unwrap(); assert!(verify_envelope(&e,b"ciphertext")); assert!(!verify_envelope(&e,b"plain")); assert_eq!(staged_restore_target("snapshot.bin").as_deref(),Some("restore-staging/snapshot.bin")); assert!(staged_restore_target("../db").is_none()); }
    #[test] fn budget_is_bounded() { assert!(performance_budget_ms(1000,&[100,200])); assert!(!performance_budget_ms(16000,&[100])); }
}
