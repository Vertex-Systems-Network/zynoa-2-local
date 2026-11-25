"""P01-T03 static app contract; native boot must be verified by Windows CI."""
import json
from pathlib import Path
import unittest

ROOT = Path(__file__).resolve().parents[1]
APP = ROOT / "apps" / "desktop"


class DesktopShellContractTests(unittest.TestCase):
    def test_files_exist_and_dependency_versions_pinned(self):
        for path in (
            "src/main.tsx", "src/App.tsx", "src/styles.css", "index.html",
            "vite.config.ts", "tsconfig.json", "src-tauri/Cargo.toml",
            "src-tauri/build.rs", "src-tauri/src/main.rs",
            "src-tauri/src/lib.rs", "src-tauri/tauri.conf.json",
            "src-tauri/capabilities/main-readonly.json", "src-tauri/icons/icon.png",
            "src-tauri/icons/icon.ico",
        ):
            self.assertTrue((APP / path).is_file(), path)
        pkg = json.loads((APP / "package.json").read_text(encoding="utf-8"))
        self.assertEqual("2.12.6", pkg["devDependencies"]["@tauri-apps/cli"])
        for group in ("dependencies", "devDependencies"):
            self.assertTrue(all(x and x[0].isdigit() for x in pkg[group].values()))
        cargo = (APP / "src-tauri/Cargo.toml").read_text(encoding="utf-8")
        self.assertIn('version = "=2.12.7"', cargo)
        self.assertIn('version = "=2.7.6"', cargo)

    def test_default_deny_no_native_command_or_network(self):
        cfg = json.loads((APP / "src-tauri/tauri.conf.json").read_text(encoding="utf-8"))
        cap = json.loads((APP / "src-tauri/capabilities/main-readonly.json").read_text(encoding="utf-8"))
        self.assertEqual(["main-readonly", "main-chat"], cfg["app"]["security"]["capabilities"])
        chat = json.loads((APP / "src-tauri/capabilities/main-chat.json").read_text(encoding="utf-8"))
        self.assertEqual(["main"],chat["windows"])
        self.assertEqual(["allow-chat-request"],chat["permissions"])
        self.assertIs(chat["local"],True)
        self.assertNotIn("remote",chat)
        self.assertEqual(["main"], cap["windows"])
        self.assertEqual(["allow-workspace-handshake"], cap["permissions"])
        self.assertEqual("main", cap["windows"][0])
        self.assertNotIn("remote", cap)
        self.assertIn("connect-src 'self'", cfg["app"]["security"]["csp"])
        native = (APP / "src-tauri/src/lib.rs").read_text(encoding="utf-8")
        self.assertIn("generate_handler![ipc::workspace_handshake, chat_ipc::chat_request]", native)
        self.assertNotIn("fs:", json.dumps(cap))
        self.assertNotIn(".plugin(", native)
        frontend = (APP / "src/App.tsx").read_text(encoding="utf-8")
        for forbidden in ("fetch(", "localStorage", "sessionStorage", "invoke(", "http://", "https://"):
            self.assertNotIn(forbidden, frontend)

    def test_navigation_keyboard_disabled_pending_features(self):
        frontend = (APP / "src/App.tsx").read_text(encoding="utf-8")
        for marker in ("Overview", "Settings", "Recovery", "Diagnostics",
                       "No verified backups", "No workspace data stored", "disabled",
                       "Browser preview", "event.ctrlKey", 'aria-label="Primary navigation"'):
            self.assertIn(marker, frontend)
        self.assertIn('"__TAURI_INTERNALS__" in window', frontend)
        self.assertIn('role="status"', frontend)
        self.assertIn('surface.scrollTop = 0;', frontend)
        self.assertIn('surface.focus({ preventScroll: true });', frontend)
        # P02 remapping replaces fixed numeric index arithmetic with an allowlisted
        # lookup, preserving P01's safety guarantee for non-numeric shortcut keys.
        mapping = (APP / "src/ui/shortcut-map.ts").read_text(encoding="utf-8")
        guard = "const target = viewForShortcut(event.key, shortcuts);"
        self.assertIn(guard, frontend)
        self.assertIn("if (!target) return;", frontend)
        self.assertLess(frontend.index(guard), frontend.index("setView(target);"))
        self.assertIn("return isShortcutKey(key) ? current[key] : null;", mapping)
        self.assertIn('shortcutKeys = ["1", "2", "3", "4", "5", "6"]', mapping)
        self.assertIn("if (!event.ctrlKey || event.altKey || event.metaKey || event.shiftKey) return;", frontend)

    def test_windows_build_gated_read_only_and_no_release(self):
        wf = (ROOT / ".github/workflows/p01-desktop.yml").read_text(encoding="utf-8")
        for expected in (
            "concurrency:", "cancel-in-progress: true", "desktop: ",
            "windows-latest", "npm ci", "npm run build",
            "tauri -- build --no-bundle", "actions/upload-artifact@v6",
            "phase/01-foundation",
        ):
            self.assertIn(expected, wf)
        for forbidden in ("contents: write", "schedule:", "pull_request_target:", "merge_pull_request"):
            self.assertNotIn(forbidden, wf)


if __name__ == "__main__":
    unittest.main()
