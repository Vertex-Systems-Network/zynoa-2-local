"""T03 UI source contract; actual Windows interaction evidence remains required."""
import unittest
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1]/"apps/desktop"
class ChatUiContract(unittest.TestCase):
    def test_actual_transport_and_save_only_semantics(self):
        view=(ROOT/"src/ui/ChatView.tsx").read_text(encoding="utf-8")
        transport=(ROOT/"src/chat-transport.ts").read_text(encoding="utf-8")
        app=(ROOT/"src/App.tsx").read_text(encoding="utf-8")
        for fragment in ('Retry same request','pendingRef.current','lock.current','chat.saveUserMessage','No model response was requested','Browser preview: saving is unavailable','aria-label="Saved messages"','htmlFor="chat-message"','role="alert"','role="status"','{m.content}'):
            self.assertIn(fragment,view)
        self.assertIn('invoke<unknown>("chat_request",{request})',transport)
        self.assertIn('decodeReply(reply,command,correlationId,payload)',transport)
        self.assertIn('hidden={view !== "chat"}',app)
        for forbidden in ("localStorage","sessionStorage","dangerouslySetInnerHTML","fetch(","console.log"):
            self.assertNotIn(forbidden,view+transport)
if __name__=="__main__":unittest.main()
