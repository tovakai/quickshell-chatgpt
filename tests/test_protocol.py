import unittest

from bridge.protocol import BridgeError, sse_events


class CompatibilityProtocolTests(unittest.TestCase):
    def test_sse_done(self):
        self.assertEqual(list(sse_events([b"data: [DONE]\n", b"\n"])), [{"type": "done"}])

    def test_reject_bad_sse(self):
        with self.assertRaises(BridgeError):
            list(sse_events(["data: no-json\n", "\n"]))


if __name__ == "__main__":
    unittest.main()
