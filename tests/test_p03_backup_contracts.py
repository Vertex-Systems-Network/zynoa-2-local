from pathlib import Path
import unittest
class P03BackupContracts(unittest.TestCase):
    def test_backup_contracts_are_integrity_bound_and_staged(self):
        src=(Path(__file__).parents[1]/"apps/desktop/src-tauri/src/backup_contracts.rs").read_text(encoding="utf-8")
        for part in ("BackupEnvelope","ciphertext_sha256","verify_envelope","staged_restore_target","performance_budget_ms"): self.assertIn(part,src)
        self.assertNotIn("fs::write",src)
    def test_real_crypto_and_independent_restore_are_not_hash_only(self):
        root=Path(__file__).parents[1]
        crypto=(root/"apps/desktop/src-tauri/src/backup_contracts.rs").read_text(encoding="utf-8")
        vault=(root/"apps/desktop/src-tauri/src/vault.rs").read_text(encoding="utf-8")
        probe=(root/"scripts/probe_p03_chat_ui.ps1").read_text(encoding="utf-8")
        verifier=(root/"scripts/verify_p03_backup_ui_database.py").read_text(encoding="utf-8")
        for marker in ("Argon2id","AES_256_GCM","seal_in_place_append_tag","open_in_place","SystemRandom","Zeroizing"):
            self.assertIn(marker,crypto)
        for marker in ("Backup::new","serialize(MAIN_DB)","deserialize_read_exact","validate_portable_db","write_portable_new","verified.json","active_profile_changed:false"):
            self.assertIn(marker,vault)
        for marker in ("Type-SyntheticSecret","Read-BackupVault 'wrong'","Read-BackupVault 'restored'","actual_native_separate_restore"):
            self.assertIn(marker,probe)
        self.assertIn("db_state(profile)==rows",verifier)
        self.assertIn("mode=ro",verifier)
if __name__ == "__main__": unittest.main()
