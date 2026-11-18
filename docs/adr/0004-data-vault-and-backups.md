# ADR 0004 — User Data Vault & Backups

**Proposed, not implemented.** Persist all user-owned records independently of binaries. SQLite online backup + content-addressed managed files, optional encrypted backups with real restore testing. Alternative rejected: naive live `.sqlite` file copy under WAL. See [details](../operations/DATA_VAULT_BACKUP_RECOVERY.md).
