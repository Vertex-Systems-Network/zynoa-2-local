from pathlib import Path
import json, unittest
ROOT=Path(__file__).resolve().parents[1]
TAURI=ROOT/"apps/desktop/src-tauri"
class ModelGatewayContractTests(unittest.TestCase):
    def setUp(self):
        self.gateway=(TAURI/"src/model_gateway.rs").read_text(encoding="utf-8")
        self.vault=(TAURI/"src/vault.rs").read_text(encoding="utf-8")
        self.ui=(ROOT/"apps/desktop/src/ui/ChatView.tsx").read_text(encoding="utf-8")
        self.transport=(ROOT/"apps/desktop/src/model-transport.ts").read_text(encoding="utf-8")
    def test_fixed_loopback_native_gateway_has_no_renderer_url_authority(self):
        self.assertIn('const OLLAMA_BASE: &str = "http://127.0.0.1:11434"',self.gateway)
        self.assertIn(".no_proxy()",self.gateway)
        self.assertIn("Policy::none()",self.gateway)
        self.assertNotIn("base_url",self.gateway)
        self.assertNotIn("url:String",self.gateway)
        self.assertNotIn("fetch(",self.transport)
    def test_single_explicit_capability_and_command_surface(self):
        capability=json.loads((TAURI/"capabilities/main-chat.json").read_text(encoding="utf-8"))
        self.assertEqual(capability["permissions"],["allow-chat-request","allow-model-request"])
        build=(TAURI/"build.rs").read_text(encoding="utf-8")
        self.assertIn('"workspace_handshake", "chat_request", "model_request"',build)
        self.assertIn("allow_local_model(label)",self.gateway)
        for op in ("inference.health","inference.settings.get","inference.settings.set","inference.context.inspect","inference.turn.generate","inference.turn.cancel"):
            self.assertIn(op,self.gateway)
    def test_turn_does_not_hold_vault_lock_during_http_stream(self):
        context=self.gateway.index("let (settings, context) =")
        post=self.gateway.index("let reply = self",context)
        persist=self.gateway.index("let receipt =",post)
        self.assertIn("(settings, context)",self.gateway[context:post])
        self.assertNotIn("storage.lock()",self.gateway[post:persist])
        self.assertIn("storage.lock()",self.gateway[persist:])
    def test_settings_context_stream_and_retry_are_real_controls(self):
        for text in ("Local model and context settings","Inspect context","Send","Stop","Retry turn"):
            self.assertIn(text,self.ui)
        self.assertIn('new Channel<unknown>()',self.transport)
        self.assertIn("decodeModelEvent",self.transport)
        self.assertIn("set_inference_settings",self.vault)
        self.assertIn("model_context",self.vault)
        self.assertIn("status='complete'",self.vault)
    def test_context_is_bounded_and_cross_thread_scoped(self):
        for text in ("MAX_CONTEXT_MESSAGES","context_limit-reserve","conversation_id=?1 AND status='complete'","selected.reverse()"):
            self.assertIn(text,self.vault)
        self.assertIn("MAX_OUTPUT_BYTES",self.gateway)
        self.assertIn("MAX_EVENT_BYTES",self.gateway)
        self.assertIn("MAX_EVENTS",self.gateway)
if __name__=="__main__":unittest.main()
