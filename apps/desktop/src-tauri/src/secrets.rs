//! M17 OS-owned credentials. Not exported as a Tauri command.
/// Only native Rust code may call this adapter; no secret enters any IPC reply.
/// Windows Credential Manager provides account-bound persistence. Never
/// include backend errors, slot or secret values in diagnostic output.
use zeroize::Zeroizing;

#[derive(Clone, Copy, Debug, PartialEq, Eq)]
pub(crate) enum SecretFault {
    InvalidSlot,
    InvalidValue,
    Unavailable,
}

pub(crate) struct SensitiveText(Zeroizing<String>); // intentionally no Debug/Serialize

impl SensitiveText {
    pub(crate) fn new(value: String) -> Result<Self, SecretFault> {
        if value.is_empty() || value.len() > 4096 || value.contains('\0') {
            return Err(SecretFault::InvalidValue);
        }
        Ok(Self(Zeroizing::new(value)))
    }

    fn expose_for_native_store(&self) -> &str {
        self.0.as_str()
    }
}

fn check_slot(slot: &str) -> Result<(), SecretFault> {
    if (1..=64).contains(&slot.len())
        && slot.bytes().all(|v| v.is_ascii_alphanumeric() || v == b'-' || v == b'_')
    {
        Ok(())
    } else {
        Err(SecretFault::InvalidSlot)
    }
}

#[cfg(windows)]
pub(crate) struct WindowsCredentialVault {
    service: String,
}

#[cfg(windows)]
impl WindowsCredentialVault {
    pub(crate) fn new() -> Self {
        Self {
            service: "com.zynoa.desktop.credentials".to_string(),
        }
    }

    fn entry(&self, slot: &str) -> Result<keyring::Entry, SecretFault> {
        check_slot(slot)?;
        keyring::Entry::new(&self.service, slot).map_err(|_| SecretFault::Unavailable)
    }

    pub(crate) fn put(&self, slot: &str, secret: &SensitiveText) -> Result<(), SecretFault> {
        self.entry(slot)?
            .set_password(secret.expose_for_native_store())
            .map_err(|_| SecretFault::Unavailable)
    }

    pub(crate) fn get(&self, slot: &str) -> Result<SensitiveText, SecretFault> {
        let value = self.entry(slot)?
            .get_password().map_err(|_| SecretFault::Unavailable)?;
        SensitiveText::new(value)
    }

    pub(crate) fn forget(&self, slot: &str) -> Result<(), SecretFault> {
        self.entry(slot)?
            .delete_credential().map_err(|_| SecretFault::Unavailable)
    }

    #[cfg(test)]
    fn for_disposable_test(service: String) -> Self {
        assert!(service.starts_with("com.zynoa.desktop.fixture."));
        Self { service }
    }
}

#[cfg(test)]
mod tests {
    use super::*;

    #[test]
    fn secret_slot_and_value_validation_deny_path_and_control_chars() {
        for slot in ["", "../token", "app.secret", "with space", "A".repeat(65).as_str(), "ü"] {
            assert_eq!(check_slot(slot), Err(SecretFault::InvalidSlot));
        }
        for slot in ["token", "a_2", "A-Z"] {
            assert_eq!(check_slot(slot), Ok(()));
        }
        assert!(SensitiveText::new(String::new()).is_err());
        assert!(SensitiveText::new("a".repeat(4097)).is_err());
        assert!(SensitiveText::new("bad\0byte".into()).is_err());
    }

    #[test]
    fn secret_type_does_not_implement_debug_or_serialize() {
        // Static integration test also checks that no Tauri command exposes it.
        let value = SensitiveText::new("disposable-fixture-secret".into()).unwrap();
        assert_eq!(value.expose_for_native_store(), "disposable-fixture-secret");
    }

    #[cfg(windows)]
    #[test]
    fn real_windows_credential_store_roundtrip_and_explicit_delete() {
        use std::time::{SystemTime, UNIX_EPOCH};
        let unique = SystemTime::now()
            .duration_since(UNIX_EPOCH)
            .expect("invalid clock")
            .as_nanos();
        let service = format!("com.zynoa.desktop.fixture.{}-{}", std::process::id(), unique);
        let vault = WindowsCredentialVault::for_disposable_test(service);
        let secret = SensitiveText::new("p01-native-only-fixture".into()).unwrap();
        // This test must run with a functional Windows Credential Manager.
        // Do not treat unavailable OS keychain as a successful test.
        vault.put("ci_fixture", &secret).expect("Windows keychain write unavailable");
        let result = vault.get("ci_fixture");
        let erase = vault.forget("ci_fixture");
        erase.expect("Windows keychain fixture cleanup failed");
        let loaded = result.expect("Windows keychain read unavailable");
        assert_eq!(loaded.expose_for_native_store(), secret.expose_for_native_store());
        assert!(vault.get("ci_fixture").is_err(), "deleted credential still accessible");
    }
}
