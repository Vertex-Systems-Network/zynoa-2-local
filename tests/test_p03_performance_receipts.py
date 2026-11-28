"""Synthetic inputs test receipt validation, not actual performance."""
import hashlib
import json
import tempfile
import unittest
from pathlib import Path
from scripts.verify_p03_performance_receipts import EARLY, INSTALLED, collect

class PerformanceReceiptTests(unittest.TestCase):
    def test_exact_source_scope_duration_and_budget(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            exe = root / "fixture.exe"
            exe.write_bytes(b"synthetic binary")
            binary = hashlib.sha256(exe.read_bytes()).hexdigest()
            rows = {}
            for folder, name, flags, keys in EARLY + (INSTALLED,):
                directory = root / ("p03-" + folder + "-ui-proof")
                directory.mkdir(exist_ok=True)
                path = directory / ("p03-" + name + "-ui-proof.json")
                row = {"schema_version": 1, "source_commit_sha": "a"*40, "executable_sha256": binary,
                       "synthetic_only": True, "actual_model": "qwen2.5:1.5b", "live_prefix_chars": 12,
                       **dict.fromkeys(flags, True), **dict.fromkeys(keys, 123)}
                if name == "reinstall":
                    row.update(startup_budget_ms=15000, startup_within_budget=True)
                path.write_text(json.dumps(row), encoding="utf-8")
                rows[name] = (path, row)
            report = collect(root, "a"*40, exe, True)
            self.assertEqual(report["metrics"]["save_to_acknowledgement_ms"], 123)
            self.assertFalse(report["full_performance_accepted"])
            self.assertFalse(report["visible_prefix_is_exact_ttft"])
            self.assertTrue(report["metrics"]["startup_within_budget"])
            path, original = rows["chat"]
            for bad in ({"source_commit_sha": "b"*40}, {"save_to_acknowledgement_ms": -1},
                        {"save_to_acknowledgement_ms": True}, {"ui_create_save": False}):
                path.write_text(json.dumps({**original, **bad}), encoding="utf-8")
                with self.assertRaises(ValueError):
                    collect(root, "a"*40, exe)
            path.write_text(json.dumps(original), encoding="utf-8")
            path, original = rows["reinstall"]
            path.write_text(json.dumps({**original, "installed_startup_ms": 16000}), encoding="utf-8")
            with self.assertRaises(ValueError):
                collect(root, "a"*40, exe, True)
            path.unlink()
            self.assertEqual(len(collect(root, "a"*40, exe)["receipt_sha256"]), 3)
            with self.assertRaises(ValueError):
                collect(root, "a"*40, exe, True)
if __name__ == "__main__":
    unittest.main()
