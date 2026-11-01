"""Offline contract tests, no Strata, OAuth, or live Mabel required."""

import io
import os
import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch

from bridge.client import MabelClient, token_from_disk
from bridge.protocol import BridgeError, sse_events, visible_content


class ProtocolTests(unittest.TestCase):
    def test_multiline_sse(self):
        wire = [b": ping\n", b"event: update\n", b'data: {"type": "reply",\n',
                b'data: "delta": "hello"}\n', b"\n", b"data: [DONE]\n", b"\n"]
        self.assertEqual(list(sse_events(wire)),
                         [{"type": "reply", "delta": "hello", "_sse_event": "update"}, {"type": "done"}])

    def test_unterminated_final_event(self):
        self.assertEqual(list(sse_events([b'data: {"delta":"ok"}'])),
                         [{"delta": "ok", "_sse_event": "message"}])

    def test_invalid_json_rejected(self):
        with self.assertRaises(BridgeError):
            list(sse_events(["data: ?\n", "\n"]))

    def test_history_blocks(self):
        self.assertEqual(visible_content([{"type": "text", "text": "hi"}, {"type": "image_url"}]), "hi")

    def test_refuse_remote_without_token(self):
        with self.assertRaises(BridgeError):
            MabelClient(lambda _: None, base_url="https://some-host.invalid", token="")

    def test_refuse_non_origin_url(self):
        with self.assertRaises(BridgeError):
            MabelClient(lambda _: None, base_url="http://localhost:7000/v1", token="")

    def test_token_permissions(self):
        with tempfile.TemporaryDirectory() as tmp:
            path = Path(tmp) / "token"
            path.write_text("sample")
            path.chmod(0o644)
            with patch.dict(os.environ, {"MABEL_TOKEN_FILE": str(path)}):
                with self.assertRaises(BridgeError):
                    token_from_disk()
            path.chmod(0o600)
            with patch.dict(os.environ, {"MABEL_TOKEN_FILE": str(path)}):
                self.assertEqual(token_from_disk(), "sample")


if __name__ == "__main__":
    unittest.main()
