import json
import os
from pathlib import Path
import subprocess
import tempfile
import unittest

REPO = Path(__file__).resolve().parent.parent
QML = REPO / "end4" / "AiChat.qml"
INSTALLER = REPO / "install.sh"


class End4IntegrationTests(unittest.TestCase):
    def test_component_preserves_end4_sidebar(self):
        component = QML.read_text()
        self.assertIn("WebEngineView", component)
        self.assertIn("WebEngineProfile", component)
        self.assertIn("ForcePersistentCookies", component)
        self.assertIn("onFocusChanged", component)
        self.assertNotIn("PanelWindow", component)
        self.assertNotIn("Strata", component)
        self.assertNotIn("Bearer", component)

    def test_installer_backup_restore_and_url(self):
        with tempfile.TemporaryDirectory() as directory:
            config = Path(directory) / "ii"
            chat = config / "modules/ii/sidebarLeft/AiChat.qml"
            chat.parent.mkdir(parents=True)
            original = "Item { property string original: 'untouched' }"
            chat.write_text(original)
            env = dict(os.environ, QS_CONFIG_DIR=str(config),
                       MABEL_SKIP_WEBENGINE_CHECK="1",
                       MABEL_URL="https://private-mabel.example.test/")
            installed = subprocess.run(["bash", str(INSTALLER)], env=env,
                                       capture_output=True, text=True)
            self.assertEqual(installed.returncode, 0, installed.stderr)
            self.assertEqual((chat.parent / "AiChat.qml.before-mabel").read_text(), original)
            self.assertIn(json.dumps(env["MABEL_URL"]), chat.read_text())
            self.assertIn("WebEngineView", chat.read_text())
            restored = subprocess.run(["bash", str(INSTALLER), "restore"],
                                      env=env, capture_output=True, text=True)
            self.assertEqual(restored.returncode, 0, restored.stderr)
            self.assertEqual(chat.read_text(), original)

    def test_installer_refuses_missing_end4(self):
        with tempfile.TemporaryDirectory() as directory:
            env = dict(os.environ, QS_CONFIG_DIR=directory, MABEL_SKIP_WEBENGINE_CHECK="1")
            result = subprocess.run(["bash", str(INSTALLER)],
                                    env=env, capture_output=True, text=True)
            self.assertNotEqual(result.returncode, 0)
            self.assertIn("AiChat.qml not found", result.stderr)

    def test_bash_syntax(self):
        for name in ("install.sh", "scripts/check-webengine.sh"):
            p = subprocess.run(["bash", "-n", str(REPO / name)], capture_output=True, text=True)
            self.assertEqual(p.returncode, 0, p.stderr)


if __name__ == "__main__":
    unittest.main()
