"""Synthetic verifier tests only, never native screenshot evidence."""
import hashlib
import json
import struct
import tempfile
import unittest
import zlib
from pathlib import Path
from unittest.mock import patch
from scripts.verify_p03_screenshot_inventory import verify, png_receipt

class ScreenshotInventoryTests(unittest.TestCase):
    def test_missing_wrong_head_and_changed_image_fail_closed(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            exe = root / "fixture.exe"
            exe.write_bytes(b"synthetic binary")
            folder = root / "p03-chat-ui-proof"
            folder.mkdir()
            image = folder / "fixture.png"
            # Tiny-compressed synthetic flat image; not a native capture.
            def chunk(kind, payload):
                return struct.pack(">I", len(payload)) + kind + payload + struct.pack(">I", zlib.crc32(kind+payload))
            header = struct.pack(">IIBBBBB", 900, 600, 8, 2, 0, 0, 0)
            pixels = (b"\0" + b"\0" * 900 * 3) * 600
            data = b"\x89PNG\r\n\x1a\n" + chunk(b"IHDR", header) + chunk(b"IDAT", zlib.compress(pixels)) + chunk(b"IEND", b"")
            image.write_bytes(data)
            proof = folder / "p03-chat-ui-proof.json"
            row = {"schema_version": 1, "synthetic_only": True,
                   "source_commit_sha": "a"*40,
                   "executable_sha256": hashlib.sha256(exe.read_bytes()).hexdigest(),
                   "images": {"fixture.png": hashlib.sha256(data).hexdigest()}}
            with patch("scripts.verify_p03_screenshot_inventory.EXPECTED", {("chat","chat"): ("fixture.png",)}):
                with self.assertRaises(ValueError):
                    verify(root, "a"*40, exe)
                proof.write_text(json.dumps(row), encoding="utf-8")
                result = verify(root, "a"*40, exe)
                self.assertEqual(result["image_count"], 1)
                self.assertEqual(result["visual_review"], "pending")
                self.assertFalse(result["hosted_wiki_verified"])
                with self.assertRaises(ValueError):
                    verify(root, "b"*40, exe)
                image.write_bytes(data+b"changed")
                with self.assertRaises(ValueError):
                    verify(root, "a"*40, exe)
                broken = data[:-1]
                image.write_bytes(broken)
                with self.assertRaises(ValueError):
                    png_receipt(image, hashlib.sha256(broken).hexdigest())
                image.unlink()
                with self.assertRaises(ValueError):
                    verify(root, "a"*40, exe)

if __name__ == "__main__":
    unittest.main()
