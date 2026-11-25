//! M17 native-only capability checks. These are not WebView-provided grants.
use std::collections::HashSet;

#[derive(Clone, Copy, Debug, PartialEq, Eq, Hash)]
pub(crate) enum Capability {
    WorkspaceStatus,
    ChatLocal,
    ReadUserFile,
    WriteUserFile,
    OutboundNetwork,
    ReadCredential,
    WriteCredential,
}

#[derive(Clone, Copy, Debug, PartialEq, Eq)]
pub(crate) enum SecurityFault {
    Denied,
}

/// Empty by default. The only P01 opt-in is the already-scoped status query.
/// Grants for secrets, user files and outbound connections are not available.
#[derive(Default)]
pub(crate) struct NativeAccessBroker {
    approved: HashSet<Capability>,
}

impl NativeAccessBroker {
    pub(crate) fn for_local_read_only_shell() -> Self {
        let mut broker = Self::default();
        broker.approved.insert(Capability::WorkspaceStatus);
        broker
    }

    pub(crate) fn authorize(
        &self, native_window_label: &str, capability: Capability,
    ) -> Result<(), SecurityFault> {
        if native_window_label != "main" || !self.approved.contains(&capability) {
            return Err(SecurityFault::Denied);
        }
        Ok(())
    }

    pub(crate) fn revoke(&mut self, capability: Capability) {
        self.approved.remove(&capability);
    }
}

pub(crate) fn allow_local_chat(label: &str) -> Result<(), SecurityFault> {
    let mut broker = NativeAccessBroker::default();
    broker.approved.insert(Capability::ChatLocal);
    broker.authorize(label, Capability::ChatLocal)
}

pub(crate) fn allow_local_workspace_handshake(label: &str) -> Result<(), SecurityFault> {
    NativeAccessBroker::for_local_read_only_shell()
        .authorize(label, Capability::WorkspaceStatus)
}

#[cfg(test)]
mod tests {
    use super::*;

    #[test]
    fn default_policy_denies_all_native_capabilities() {
        let empty = NativeAccessBroker::default();
        for capability in [
            Capability::WorkspaceStatus, Capability::ChatLocal,
            Capability::ReadUserFile, Capability::WriteUserFile,
            Capability::OutboundNetwork, Capability::ReadCredential,
            Capability::WriteCredential,
        ] {
            assert_eq!(empty.authorize("main", capability), Err(SecurityFault::Denied));
        }
    }

    #[test]
    fn only_native_main_window_gets_nonmutating_status() {
        let broker = NativeAccessBroker::for_local_read_only_shell();
        assert_eq!(broker.authorize("main", Capability::WorkspaceStatus), Ok(()));
        assert_eq!(broker.authorize("main", Capability::ChatLocal), Err(SecurityFault::Denied));
        assert_eq!(allow_local_chat("main"), Ok(()));
        assert_eq!(allow_local_chat("remote"), Err(SecurityFault::Denied));
        for other in ["", "settings", "remote", "main/", "main\0"] {
            assert_eq!(
                broker.authorize(other, Capability::WorkspaceStatus),
                Err(SecurityFault::Denied),
            );
        }
        for capability in [
            Capability::ReadUserFile, Capability::WriteUserFile,
            Capability::OutboundNetwork, Capability::ReadCredential,
            Capability::WriteCredential,
        ] {
            assert_eq!(broker.authorize("main", capability), Err(SecurityFault::Denied));
        }
    }

    #[test]
    fn revocation_is_immediate_and_cannot_be_recovered_by_request_replay() {
        let mut broker = NativeAccessBroker::for_local_read_only_shell();
        assert_eq!(broker.authorize("main", Capability::WorkspaceStatus), Ok(()));
        broker.revoke(Capability::WorkspaceStatus);
        for _ in 0..3 {
            assert_eq!(
                broker.authorize("main", Capability::WorkspaceStatus),
                Err(SecurityFault::Denied),
            );
        }
    }
}
