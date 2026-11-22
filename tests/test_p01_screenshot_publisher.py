"""P01-T10 screenshot publisher must never trust arbitrary artifacts or paths."""
import hashlib
import struct
import unittest

from scripts.publish_p01_native_evidence import (
    REVIEWED_IDS, validate_approval, validate_png_and_capture,
    trusted_redirect_target,
)


class ScreenshotEvidencePublisherTests(unittest.TestCase):
    def manifest(self):
        return {
            "schema_version": 1, "phase": "P01",
            "decision": "ACCEPTED_NATIVE_FOUNDATION_ONLY",
            "reviewer": "ChatGPT independent visual inspection",
            "review_notes": "Reviewed actual native screenshots for visible frame, dark scrollbar, text readability and privacy; no release or future feature claims.",
            "run_id": 12345, "artifact_id": 67890,
            "source_commit_sha": "a" * 40,
            "sha256_by_screenshot": {key: "b" * 64 for key in REVIEWED_IDS},
        }

    def test_only_five_approved_native_views_allowed(self):
        validate_approval(self.manifest())
        for bad in ("../../danger", "M17-S01"):
            m = self.manifest()
            m["sha256_by_screenshot"][bad] = "b" * 64
            with self.assertRaises(ValueError):
                validate_approval(m)

    def test_unreviewed_and_invalid_hashes_fail_closed(self):
        m = self.manifest()
        m["decision"] = "CANDIDATE"
        with self.assertRaises(ValueError):
            validate_approval(m)
        m = self.manifest()
        m["sha256_by_screenshot"]["M01-S01"] = "not-a-sha"
        with self.assertRaises(ValueError):
            validate_approval(m)

    def test_redirect_target_never_leaks_github_token_to_untrusted_host(self):
        trusted_redirect_target("https://example.blob.core.windows.net/ci/asset?sig=abc")
        trusted_redirect_target("https://results.actions.githubusercontent.com/asset")
        for url in ("http://example.blob.core.windows.net/asset",
                    "https://evil.example.com/asset",
                    "https://blob.core.windows.net.evil.example/asset"):
            with self.assertRaises(ValueError):
                trusted_redirect_target(url)

    def test_provenance_mismatch_or_fake_image_rejected(self):
        payload = b"\x89PNG\r\n\x1a\n" + b"\x00\x00\x00\x0DIHDR" + struct.pack(">II", 998, 701) + b"x" * 1020
        digest = hashlib.sha256(payload).hexdigest()
        meta = {
            "screenshot_id": "M01-S01", "sha256": digest,
            "source_commit_sha": "a" * 40, "built_commit_sha": "a" * 40,
            "source": "GitHub Windows Actions actual Tauri process",
            "capture_verified": False, "capture_status": "candidate_pending_visual_review",
            "window_fully_visible": True, "frame_bounds_source": "DwmGetWindowAttribute 9",
            "window_width": 998, "window_height": 701,
            "alt_text": "Authentic native First Boot screenshot showing read-only startup",
            "privacy": "Disposable CI fixture with no user content or secrets",
        }
        validate_png_and_capture(payload, meta, "M01-S01", digest, "a" * 40)
        with self.assertRaises(ValueError):
            validate_png_and_capture(payload, meta, "M01-S01", "f" * 64, "a" * 40)
        with self.assertRaises(ValueError):
            validate_png_and_capture(b"browser-preview" * 200, meta, "M01-S01", digest, "a" * 40)
        meta["capture_verified"] = True
        with self.assertRaises(ValueError):
            validate_png_and_capture(payload, meta, "M01-S01", digest, "a" * 40)


if __name__ == "__main__":
    unittest.main()
