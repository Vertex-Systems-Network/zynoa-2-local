"""T03 UI source contract; actual Windows interaction evidence remains required."""
import unittest
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1]/"apps/desktop"
class ChatUiContract(unittest.TestCase):
    def test_actual_storage_and_local_inference_semantics(self):
        view=(ROOT/"src/ui/ChatView.tsx").read_text(encoding="utf-8")
        transport=(ROOT/"src/chat-transport.ts").read_text(encoding="utf-8")
        app=(ROOT/"src/App.tsx").read_text(encoding="utf-8")
        for fragment in ('Retry same request','pendingRef.current','lock.current','chat.saveUserMessage','Local model and context settings','Browser preview: local inference is unavailable','aria-label="Saved messages"','htmlFor="chat-message"','role="alert"','role="status"','{m.content}','>Send<','>Stop<','>Retry turn<'):
            self.assertIn(fragment,view)
        self.assertIn('invoke<unknown>("chat_request",{request})',transport)
        self.assertIn('decodeReply(reply,command,correlationId,payload)',transport)
        self.assertIn('hidden={view !== "chat"}',app)
        for forbidden in ("localStorage","sessionStorage","dangerouslySetInnerHTML","fetch(","console.log"):
            self.assertNotIn(forbidden,view+transport)
    def test_review_panel_requires_selected_conversation(self):
        view=(ROOT/"src/ui/ChatView.tsx").read_text(encoding="utf-8")
        self.assertIn('{selected&&<section className="chat-recovery" aria-label="Tool trace and permission review">',view)
        self.assertIn('</section>}\n    {selected&&<section className="chat-recovery" aria-label="Conversation export">',view)

    def test_review_focus_defaults_to_deny_once_per_request(self):
        view=(ROOT/"src/ui/ChatView.tsx").read_text(encoding="utf-8")
        for fragment in ('reviewDenyRef=useRef<HTMLButtonElement>(null)',
                         'focusedReviewRequest.current===review.requestId',
                         'focusedReviewRequest.current=review.requestId',
                         'if(!button||button.disabled)return',
                         'button.focus()',
                         'ref={reviewDenyRef} data-testid="chat-review-deny"'):
            self.assertIn(fragment,view)

    def test_chat_receipt_fields_wrap_without_losing_exact_readback(self):
        view=(ROOT/"src/ui/ChatView.tsx").read_text(encoding="utf-8")
        css=(ROOT/"src/styles.css").read_text(encoding="utf-8")
        self.assertIn("grid-template-columns:minmax(180px, 26%) minmax(0, 1fr)",css)
        self.assertIn("@container(max-width:580px)",css)
        self.assertIn("position:sticky; top:12px",css)
        self.assertIn('className="chat-review-fields"',view)
        for label in ("Relative export path","Export SHA-256"):
            self.assertIn(f'<textarea className="chat-receipt-value" readOnly aria-label="{label}"',view)
        self.assertIn("overflow-wrap:anywhere; white-space:pre-wrap",css)

    def test_model_ui_state_is_scoped_and_fail_closed(self):
        view=(ROOT/"src/ui/ChatView.tsx").read_text(encoding="utf-8")
        transport=(ROOT/"src/model-transport.ts").read_text(encoding="utf-8")
        for fragment in ('modelAvailable(settings,models,runtimeVersion)',
                         'retryAvailable(retryTarget,selected?.id??null,installed)',
                         'currentContext(contextSnapshot,selected?.id??null,selected?.revision??null,settings,draft)',
                         'invalidateInventory();const health=await',
                         'disabled={!canEdit||!installed||files.length>0||!validText(draft,262144)}>Send',
                         'setDraft(e.target.value);setContext(null)',
                         'activeTurnRef.current===turnId',
                         'modelSelectValue(settings,models,runtimeVersion)',
                         'Previously selected model unavailable'):
            self.assertIn(fragment,view)
        self.assertIn('closed=true',transport)
        self.assertIn('terminalSeen',transport)
if __name__=="__main__":unittest.main()
