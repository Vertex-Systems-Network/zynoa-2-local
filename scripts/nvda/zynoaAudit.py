"""CI-only NVDA speech observer. Never synthesizes speech or reads user content."""
import json
import os
import time
import globalPluginHandler
from synthDriverHandler import pre_synthSpeak

DEST = os.environ.get("ZYNOA_NVDA_SPEECH_PROOF", "")
STAGE_FILE = os.environ.get("ZYNOA_NVDA_STAGE_FILE", "")
TERMS = ("preferences", "command palette", "search available commands",
         "wiki mapping and link checker", "interface appearance", "navigation density")

def append(kind, value=""):
    if not DEST:
        return
    # Only allowlisted UI labels from a disposable no-user-data CI Windows runner.
    if kind == "speech" and not any(term in value.lower() for term in TERMS):
        return
    try:
        with open(STAGE_FILE, "r", encoding="utf-8") as stream:
            stage = stream.read(40).strip()
    except OSError:
        stage = "unattributed"
    with open(DEST, "a", encoding="utf-8") as f:
        f.write(json.dumps({"kind": kind, "stage": stage, "label": value[:280], "unix_ms": int(time.time()*1000)}) + "\n")

class GlobalPlugin(globalPluginHandler.GlobalPlugin):
    def __init__(self):
        super().__init__()
        pre_synthSpeak.register(self._capture)
        append("plugin_loaded", "official_NVDA_pre_synthSpeak")
    def _capture(self, speechSequence, **kwargs):
        spoken = " ".join(s for s in speechSequence if isinstance(s, str)).strip()
        if spoken:
            # NVDA can synthesize an entire landmark in one long utterance.
            # Extract only tightly bounded context around allowlisted UI words;
            # first-280-char truncation previously erased the actual evidence.
            lower = spoken.lower()
            for term in TERMS:
                at = lower.find(term)
                if at >= 0:
                    append("speech", spoken[max(0, at-42):at+len(term)+48])
    def terminate(self):
        pre_synthSpeak.unregister(self._capture)
        super().terminate()
