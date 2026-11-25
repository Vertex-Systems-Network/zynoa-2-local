"""P03 T03 native IPC scoped privilege and replay contract; native CI exercises actual DB."""
import json
import unittest
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1]/"apps/desktop/src-tauri"
class ChatIpcContract(unittest.TestCase):
    def test_exact_local_command_grants(self):
        config=json.loads((ROOT/"tauri.conf.json").read_text(encoding="utf-8"))
        self.assertEqual(config["app"]["security"]["capabilities"],["main-readonly","main-chat"])
        cap=json.loads((ROOT/"capabilities/main-chat.json").read_text(encoding="utf-8"))
        self.assertEqual(set(cap),{"identifier","description","local","windows","permissions"})
        self.assertEqual(cap["windows"],["main"])
        self.assertEqual(cap["permissions"],["allow-chat-request"])
        self.assertIs(cap["local"],True)
        self.assertIn('commands(&["workspace_handshake", "chat_request"])',(ROOT/"build.rs").read_text(encoding="utf-8"))
        self.assertIn("generate_handler![ipc::workspace_handshake, chat_ipc::chat_request]",(ROOT/"src/lib.rs").read_text(encoding="utf-8"))
    def test_no_generic_authority_and_native_negative_tests(self):
        src=(ROOT/"src/chat_ipc.rs").read_text(encoding="utf-8")
        for marker in ('deny_unknown_fields','MAX_REQUEST_BYTES','MAX_RESPONSE_BYTES','allow_local_chat(label)','ChatRole::User','ChatStatus::Complete','chat_ipc_denies_wrong_window','chat_ipc_replay_conflict_and_reopen','chat_ipc_scopes_history','chat_ipc_large_history'):
            self.assertIn(marker,src)
        for forbidden in ("reqwest","std::process::Command","println!","eprintln!","tauri::plugin"):
            self.assertNotIn(forbidden,src)
if __name__=="__main__":unittest.main()
