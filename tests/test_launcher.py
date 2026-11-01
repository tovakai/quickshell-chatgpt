import os
from pathlib import Path
import runpy
import unittest
from unittest.mock import patch

FILE = Path(__file__).resolve().parent.parent / "scripts" / "mabel-webui"
wrapper = runpy.run_path(str(FILE))


class LauncherTests(unittest.TestCase):
    def test_mabel_url(self):
        with patch.dict(os.environ, {"MABEL_URL": "http://127.0.0.1:7001/"}):
            self.assertEqual(wrapper["mabel_url"](), "http://127.0.0.1:7001")

    def test_non_web_url_rejected(self):
        for address in ("file:///tmp/a", "javascript:alert(1)", "https://bad@host"):
            with self.subTest(address=address), patch.dict(os.environ, {"MABEL_URL": address}):
                with self.assertRaises(ValueError):
                    wrapper["mabel_url"]()

    def test_browser_loads_original_webui(self):
        argv = wrapper["command"]("/usr/bin/chromium", "http://127.0.0.1:7001",
                                  Path("/tmp/mabel-profile-test"))
        self.assertIn("--app=http://127.0.0.1:7001", argv)
        self.assertIn("--window-size=480,900", argv)
        self.assertIn("--user-data-dir=/tmp/mabel-profile-test", argv)
        self.assertFalse(any("8080" in a or "/api/" in a for a in argv))

    def test_mobile_geometry(self):
        x, y, width, height = wrapper["geometry"](
            {"x": 100, "y": 50, "width": 1920, "height": 1080, "scale": 1})
        self.assertEqual((x, y, width, height), (1524, 88, 480, 1026))

    def test_window_matching_avoids_regular_firefox(self):
        prof = Path("/tmp/mabel-profile-unique")
        self.assertFalse(wrapper["matches"](
            {"address": "0x123", "class": "firefox", "title": "Odysseus Chat"},
            prof, "http://127.0.0.1:7000"))
        self.assertTrue(wrapper["matches"](
            {"address": "0x124", "class": "chrome-127.0.0.1__-Default",
             "title": "Odysseus Chat"}, prof, "http://127.0.0.1:7000"))
        self.assertTrue(wrapper["matches"](
            {"address": "0x125", "class": "MabelWebUI"},
            prof, "http://127.0.0.1:7000"))

    def test_no_chat_client(self):
        code = FILE.read_text()
        self.assertNotIn("/api/chat_stream", code)
        self.assertNotIn("Authorization", code)


if __name__ == "__main__":
    unittest.main()
