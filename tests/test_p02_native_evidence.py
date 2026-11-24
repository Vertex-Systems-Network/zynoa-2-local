"""P02 fail-closed Windows native PNG provenance contracts.

Generated test PNGs here are synthetic fixtures ONLY for gate unit tests; never
present them as native screenshots, publish them, or use them for visual review.
"""
import hashlib
import json
from pathlib import Path
import struct
import tempfile
import unittest
import zlib

from tools.verify_p02_native_evidence import (
    InvalidNativeEvidence, SCREEN_IDS, OPTION_REFERENCE_MATRIX, DIRECT_CONTROL_MATRIX, ORIGIN, STATUS, validate_candidate, verify,
)

SOURCE_SHA = "a" * 40


def fixture_png(width: int, height: int, marker: int) -> bytes:
    def chunk(tag: bytes, payload: bytes) -> bytes:
        return (struct.pack(">I", len(payload)) + tag + payload +
                struct.pack(">I", zlib.crc32(tag + payload) & 0xffffffff))
    scanline = b"\x00" + bytes((marker, marker, marker, 255)) * width
    return (b"\x89PNG\r\n\x1a\n" +
            chunk(b"IHDR", struct.pack(">IIBBBBB", width, height, 8, 6, 0, 0, 0)) +
            chunk(b"IDAT", zlib.compress(scanline * height)) +
            chunk(b"IEND", b""))


class P02NativeEvidenceGateTests(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        self.addCleanup(self.tmp.cleanup)
        self.root = Path(self.tmp.name)
        self.receipts = {}
        for index, screen_id in enumerate(SCREEN_IDS):
            folder = self.root / ("M19" if screen_id.startswith("M19-") or screen_id.startswith("P02-T10-CTRL-M19-") else "M02")
            folder.mkdir(parents=True, exist_ok=True)
            narrow = (screen_id.startswith("P02-T02-07") or screen_id.startswith("P02-T02-12")
                      or screen_id in ("M02-OPT-04", "P02-T02-OPT-04-swapped")
                      or screen_id.startswith("P02-T03-RAIL-"))
            width, height = (898, 653) if narrow else (998, 701)
            png = fixture_png(width, height, index + 1)
            (folder / f"{screen_id}.png").write_bytes(png)
            meta = {
                "screenshot_id": screen_id,
                "source_commit_sha": SOURCE_SHA,
                "built_commit_sha": SOURCE_SHA,
                "source": ORIGIN,
                "capture_status": STATUS,
                "capture_verified": False,
                "window_width": width,
                "window_height": height,
                "window_fully_visible": True,
                "frame_bounds_source": "DwmGetWindowAttribute DWMWA_EXTENDED_FRAME_BOUNDS (9)",
                "sha256": hashlib.sha256(png).hexdigest(),
                "alt_text": "Synthetic unit-test geometry for independent verifier gates only",
                "privacy": "Disposable CI fixture with no user content or secrets",
            }
            if screen_id in DIRECT_CONTROL_MATRIX:
                meta["candidate_final_asset_id"] = screen_id.removeprefix("P02-T10-CTRL-")
                meta["interaction"] = "actual-native-screen-or-control:keyboard"
                meta["evidence_limit"] = "NOT a final manifest screenshot or independent visual approval"
            if screen_id in OPTION_REFERENCE_MATRIX:
                meta["option_id"] = screen_id.replace("-T10-REF-OPT-", "-OPT-")
                meta["interaction"] = "palette:exact-id:enter:option-detail"
            self.receipts[screen_id] = folder / f"{screen_id}.capture.json"
            self._write(screen_id, meta)

    def _write(self, screen_id, meta):
        self.receipts[screen_id].write_text(json.dumps(meta), encoding="utf-8")

    def _mutate(self, screen_id, key, value):
        meta = json.loads(self.receipts[screen_id].read_text(encoding="utf-8"))
        meta[key] = value
        self._write(screen_id, meta)

    def test_all_machine_candidates_validate_but_do_not_self_approve(self):
        result = verify(self.root, SOURCE_SHA)
        self.assertEqual("MACHINE_METADATA_HASH_VALIDATED_ONLY", result["status"])
        self.assertEqual(69, len(result["screens"]))
        self.assertEqual(15, result["actual_screen_control_candidates"]["count"])
        self.assertEqual("MACHINE_CONTROL_CAPTURE_ONLY",
                         result["actual_screen_control_candidates"]["status"])
        self.assertEqual(16, result["option_reference_matrix"]["count"])
        self.assertEqual("MACHINE_REFERENCE_CAPTURE_ONLY",
                         result["option_reference_matrix"]["status"])
        self.assertFalse(result["option_reference_matrix"]["final_29_manifest_assets_verified"])
        self.assertFalse(result["independent_visual_review"])
        self.assertFalse(result["manifest_completed"])

    def test_workbench_native_control_navigation_respects_roving_tabindex(self):
        script = (Path(__file__).resolve().parents[1] / "scripts/capture_p01_desktop.ps1").read_text(encoding="utf-8")
        self.assertIn("-ScreenshotId 'P02-T10-CTRL-M02-OPT-06' -Shortcut '+{TAB}{RIGHT}{RIGHT}{PGUP}'", script)
        self.assertLess(script.index("-ScreenshotId 'M02-OPT-03'"),
                        script.index("-ScreenshotId 'P02-T10-CTRL-M02-OPT-06'"))
        self.assertLess(script.index("-ScreenshotId 'P02-T10-CTRL-M02-OPT-06'"),
                        script.index("-ScreenshotId 'M02-S05'"))
        self.assertNotIn("Focus-P02NativeControl -AccessibleName 'Left pane width'", script)
        self.assertNotIn("Focus-P02NativeControl -AccessibleName 'Runtime status'", script)
        self.assertNotIn("Focus-P02NativeControl -AccessibleName 'Layout controls'", script)

    def test_f1_recovers_shortcut_navigation_after_native_range_input(self):
        src = (Path(__file__).resolve().parents[1] / "scripts/capture_p01_desktop.ps1").read_text(encoding="utf-8")
        control = src.index("-ScreenshotId 'P02-T10-CTRL-M02-OPT-06'")
        gallery = src.index("-ScreenshotId 'M02-S05'")
        self.assertLess(control, gallery)
        self.assertIn("[System.Windows.Forms.SendKeys]::SendWait('{F1}')",
                      src[control:gallery])

    def test_faq_capture_reselects_native_tab_after_glossary_scroll(self):
        root = Path(__file__).resolve().parents[1]
        src = (root / "scripts/capture_p01_desktop.ps1").read_text(encoding="utf-8")
        before = src.index("-ScreenshotId 'P02-T10-CTRL-M19-OPT-04'")
        after = src.index("-ScreenshotId 'P02-T10-CTRL-M19-OPT-05'")
        segment = src[before:after]
        for marker in ("FAQ & glossary", "InvokePattern", "ScrollItemPattern",
                       "ZYN-SCREEN-044", "Focus-P02NativeControl -AccessibleName 'Does a native connection mean my work is saved?'"):
            self.assertIn(marker, segment)

    def test_help_input_and_faq_capture_focus_real_native_disclosure(self):
        root = Path(__file__).resolve().parents[1]
        src = (root / "scripts/capture_p01_desktop.ps1").read_text(encoding="utf-8")
        faq = (root / "apps/desktop/src/ui/help-workflows.ts").read_text(encoding="utf-8")
        self.assertIn("-ScreenshotId 'P02-T10-CTRL-M19-OPT-02' -Shortcut '{TAB}{TAB}^{2}{F1}{PGDN}'", src)
        question = "Does a native connection mean my work is saved?"
        self.assertIn(question, faq)
        marker = "Focus-P02NativeControl -AccessibleName '" + question + "'"
        before = src.index("-ScreenshotId 'P02-T10-CTRL-M19-OPT-04'")
        after = src.index("-ScreenshotId 'P02-T10-CTRL-M19-OPT-05'")
        self.assertIn(marker, src[before:after])
        self.assertIn("-ScreenshotId 'P02-T10-CTRL-M19-OPT-05' -Shortcut '{ENTER}'", src)
        self.assertNotIn("-ScreenshotId 'P02-T10-CTRL-M19-OPT-05' -Shortcut '{TAB}{TAB}", src)
        self.assertNotIn("-ScreenshotId 'P02-T10-CTRL-M19-OPT-05' -Shortcut '{ENTER}{PGDN}'", src)

    def test_m19_search_screenshot_keeps_actual_input_visible(self):
        src = (Path(__file__).resolve().parents[1] / "scripts/capture_p01_desktop.ps1").read_text(encoding="utf-8")
        focus = "Focus-P02NativeControl -AccessibleName 'Search offline help'"
        direct = "-ScreenshotId 'P02-T10-CTRL-M19-OPT-01' -Shortcut 'theme'"
        self.assertIn(focus, src)
        self.assertIn(direct, src)
        self.assertLess(src.index(focus), src.index(direct))
        self.assertNotIn("-ScreenshotId 'P02-T10-CTRL-M19-OPT-01' -Shortcut 'theme{PGDN}'", src)

    def test_reduced_motion_uses_real_distinct_keyboard_control(self):
        script = (Path(__file__).resolve().parents[1] / "scripts/capture_p01_desktop.ps1").read_text(encoding="utf-8")
        self.assertIn("Focus-P02NativeControl -AccessibleName 'Reduced motion (M02-OPT-08)'", script)
        self.assertIn("-ScreenshotId 'P02-T10-CTRL-M02-OPT-08' -Shortcut '{TAB}+{TAB}'", script)
        self.assertNotIn("-ScreenshotId 'P02-T10-CTRL-M02-OPT-08' -Shortcut '^{2}{PGDN}'", script)
        self.assertIn("T10 native actual-control candidates include duplicate frames",
                      (Path(__file__).resolve().parents[1] / "tools/verify_p02_native_evidence.py").read_text(encoding="utf-8"))

    def test_real_control_candidate_identity_is_required(self):
        self.assertEqual(15, len(DIRECT_CONTROL_MATRIX))
        self._mutate("P02-T10-CTRL-M19-OPT-07", "candidate_final_asset_id", "M19-OPT-08")
        with self.assertRaisesRegex(InvalidNativeEvidence, "target identity mismatch"):
            verify(self.root, SOURCE_SHA)

    def test_control_candidates_are_not_help_references_or_final_acceptance(self):
        self._mutate("P02-T10-CTRL-M02-OPT-01", "interaction",
                     "palette:exact-id:enter:option-detail")
        with self.assertRaisesRegex(InvalidNativeEvidence, "native control evidence"):
            verify(self.root, SOURCE_SHA)
        self._mutate("P02-T10-CTRL-M02-OPT-01", "interaction",
                     "actual-native-screen-or-control:keyboard")
        self._mutate("P02-T10-CTRL-M02-OPT-01", "capture_verified", True)
        with self.assertRaisesRegex(InvalidNativeEvidence, "cannot self-approve"):
            verify(self.root, SOURCE_SHA)

    def test_missing_real_direct_control_frame_rejected(self):
        (self.root / "M19" / "P02-T10-CTRL-M19-OPT-04.png").unlink()
        with self.assertRaisesRegex(InvalidNativeEvidence, "missing PNG/capture pair"):
            verify(self.root, SOURCE_SHA)

    def test_malformed_sha_rejected(self):
        with self.assertRaisesRegex(InvalidNativeEvidence, "invalid PR source SHA"):
            verify(self.root, "not-a-source-sha")

    def test_mismatched_build_sha_rejected(self):
        self._mutate("M02-S03", "built_commit_sha", "b" * 40)
        with self.assertRaisesRegex(InvalidNativeEvidence, "wrong build SHA"):
            verify(self.root, SOURCE_SHA)

    def test_mismatched_source_sha_rejected(self):
        self._mutate("M02-S05", "source_commit_sha", "b" * 40)
        with self.assertRaisesRegex(InvalidNativeEvidence, "wrong source SHA"):
            verify(self.root, SOURCE_SHA)

    def test_png_hash_change_rejected(self):
        png = self.root / "M02" / "M02-S05.png"
        png.write_bytes(png.read_bytes() + b"untrusted trailing bytes")
        with self.assertRaisesRegex(InvalidNativeEvidence, "PNG hash mismatch"):
            verify(self.root, SOURCE_SHA)

    def test_png_metadata_geometry_mismatch_rejected(self):
        self._mutate("P02-T02-07", "window_width", 998)
        with self.assertRaisesRegex(InvalidNativeEvidence, "geometry does not match"):
            verify(self.root, SOURCE_SHA)

    def test_never_accept_machine_claim_of_visual_approval(self):
        self._mutate("M02-OPT-07", "capture_verified", True)
        with self.assertRaisesRegex(InvalidNativeEvidence, "cannot self-approve"):
            verify(self.root, SOURCE_SHA)

    def test_missing_screenshot_or_receipt_rejected(self):
        (self.root / "M02" / "M02-S06.png").unlink()
        with self.assertRaisesRegex(InvalidNativeEvidence, "missing PNG/capture pair"):
            verify(self.root, SOURCE_SHA)

    def test_falsely_narrow_native_frame_rejected(self):
        name = "P02-T02-07"
        png = fixture_png(998, 653, 8)
        (self.root / "M02" / f"{name}.png").write_bytes(png)
        self._mutate(name, "window_width", 998)
        self._mutate(name, "sha256", hashlib.sha256(png).hexdigest())
        with self.assertRaisesRegex(InvalidNativeEvidence, "did not become narrower"):
            verify(self.root, SOURCE_SHA)

    def test_same_narrow_screenshot_rejected_as_fake_scroll(self):
        first = self.root / "M02" / "P02-T02-07.png"
        second_name = "P02-T02-07-continued"
        last = self.root / "M02" / f"{second_name}.png"
        last.write_bytes(first.read_bytes())
        self._mutate(second_name, "sha256", hashlib.sha256(first.read_bytes()).hexdigest())
        with self.assertRaisesRegex(InvalidNativeEvidence, "did not change view pixels"):
            verify(self.root, SOURCE_SHA)

    def test_identical_light_dark_images_are_rejected(self):
        name = "P02-T02-12-DARK"
        light = (self.root / "M02" / "P02-T02-12-LIGHT.png").read_bytes()
        (self.root / "M02" / f"{name}.png").write_bytes(light)
        self._mutate(name, "sha256", hashlib.sha256(light).hexdigest())
        with self.assertRaisesRegex(InvalidNativeEvidence, "identical pixels"):
            verify(self.root, SOURCE_SHA)

    def test_shortcut_swap_candidate_must_really_change_pixels(self):
        src = (self.root / "M02" / "M02-OPT-04.png").read_bytes()
        swap_id = "P02-T02-OPT-04-swapped"
        target = self.root / "M02" / f"{swap_id}.png"
        target.write_bytes(src)
        self._mutate(swap_id, "sha256", hashlib.sha256(src).hexdigest())
        with self.assertRaisesRegex(InvalidNativeEvidence, "did not visibly change"):
            verify(self.root, SOURCE_SHA)

    def test_command_palette_escape_has_distinct_native_frame(self):
        name = "P02-T04-ESCAPE"
        source = (self.root / "M02" / "P02-T04-NO-MATCH.png").read_bytes()
        (self.root / "M02" / f"{name}.png").write_bytes(source)
        self._mutate(name, "sha256", hashlib.sha256(source).hexdigest())
        with self.assertRaisesRegex(InvalidNativeEvidence, "Escape failed"):
            verify(self.root, SOURCE_SHA)

    def test_enter_navigation_must_leave_help_view(self):
        name = "P02-T04-ENTER-NAV"
        source = (self.root / "M19" / "M19-S01.png").read_bytes()
        (self.root / "M02" / f"{name}.png").write_bytes(source)
        self._mutate(name, "sha256", hashlib.sha256(source).hexdigest())
        with self.assertRaisesRegex(InvalidNativeEvidence, "did not visibly navigate"):
            verify(self.root, SOURCE_SHA)

    def test_unified_palette_results_must_open_distinct_real_native_destinations(self):
        result = "M19-UNIFIED-OPTION-RESULTS"
        destination = "M19-UNIFIED-OPTION-DEST"
        png = (self.root / "M19" / f"{result}.png").read_bytes()
        (self.root / "M19" / f"{destination}.png").write_bytes(png)
        self._mutate(destination, "sha256", hashlib.sha256(png).hexdigest())
        with self.assertRaisesRegex(InvalidNativeEvidence, "Unified search Enter failed"):
            verify(self.root, SOURCE_SHA)

    def test_unified_palette_article_option_targets_must_be_distinct(self):
        src = (self.root / "M19" / "M19-UNIFIED-OPTION-DEST.png").read_bytes()
        target = "M19-UNIFIED-ARTICLE-DEST"
        (self.root / "M19" / f"{target}.png").write_bytes(src)
        self._mutate(target, "sha256", hashlib.sha256(src).hexdigest())
        with self.assertRaisesRegex(InvalidNativeEvidence, "visually distinct Help destinations"):
            verify(self.root, SOURCE_SHA)

    def test_rail_collapse_and_expand_must_really_change_native_pixels(self):
        first = "P02-T03-RAIL-COLLAPSED"
        target = "P02-T03-RAIL-EXPANDED"
        original = (self.root / "M02" / f"{first}.png").read_bytes()
        (self.root / "M02" / f"{target}.png").write_bytes(original)
        self._mutate(target, "sha256", hashlib.sha256(original).hexdigest())
        with self.assertRaisesRegex(InvalidNativeEvidence, "rail toggle must visibly change"):
            verify(self.root, SOURCE_SHA)

    def test_false_native_rail_width_is_rejected(self):
        target = "P02-T03-RAIL-COLLAPSED"
        png = fixture_png(998, 653, 22)
        (self.root / "M02" / f"{target}.png").write_bytes(png)
        self._mutate(target, "window_width", 998)
        self._mutate(target, "sha256", hashlib.sha256(png).hexdigest())
        with self.assertRaisesRegex(InvalidNativeEvidence, "native narrow window"):
            verify(self.root, SOURCE_SHA)

    def test_all_sixteen_options_require_exact_identity_proof(self):
        self.assertEqual(16, len(OPTION_REFERENCE_MATRIX))
        self._mutate("M19-T10-REF-OPT-06", "option_id", "M19-OPT-07")
        with self.assertRaisesRegex(InvalidNativeEvidence, "option identity"):
            verify(self.root, SOURCE_SHA)

    def test_typed_option_keyboard_journey_receipt_required(self):
        self._mutate("M02-T10-REF-OPT-04", "interaction", "untrusted")
        with self.assertRaisesRegex(InvalidNativeEvidence, "keyboard journey receipt"):
            verify(self.root, SOURCE_SHA)

    def test_no_duplicate_native_option_reference_images(self):
        first = (self.root / "M02" / "M02-T10-REF-OPT-01.png").read_bytes()
        duplicate_id = "M02-T10-REF-OPT-02"
        (self.root / "M02" / f"{duplicate_id}.png").write_bytes(first)
        self._mutate(duplicate_id, "sha256", hashlib.sha256(first).hexdigest())
        with self.assertRaisesRegex(InvalidNativeEvidence, "duplicate captured pixels"):
            verify(self.root, SOURCE_SHA)

    def test_wrong_origin_or_missing_alt_text_rejected(self):
        self._mutate("M19-S01", "source", "mock browser screenshot")
        with self.assertRaisesRegex(InvalidNativeEvidence, "wrong native capture origin"):
            verify(self.root, SOURCE_SHA)
        self._mutate("M19-S01", "source", ORIGIN)
        self._mutate("M19-S01", "alt_text", "none")
        with self.assertRaisesRegex(InvalidNativeEvidence, "meaningful alt text missing"):
            verify(self.root, SOURCE_SHA)

    def test_invisible_native_window_rejected(self):
        self._mutate("M02-S04", "window_fully_visible", False)
        with self.assertRaisesRegex(InvalidNativeEvidence, "not fully in desktop"):
            validate_candidate(self.root, "M02-S04", SOURCE_SHA)


if __name__ == "__main__":
    unittest.main()
