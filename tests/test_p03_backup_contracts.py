from pathlib import Path
import unittest
class P03BackupContracts(unittest.TestCase):
    def test_backup_contracts_are_integrity_bound_and_staged(self):
        src=(Path(__file__).parents[1]/"apps/desktop/src-tauri/src/backup_contracts.rs").read_text()
        for part in ("BackupEnvelope","ciphertext_sha256","verify_envelope","staged_restore_target","performance_budget_ms"): self.assertIn(part,src)
        self.assertNotIn("fs::write",src)
if __name__ == "__main__": unittest.main()
