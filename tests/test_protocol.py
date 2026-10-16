import json
import unittest

from bridge.protocol import ProtocolError, build_request, stream_text


class ProtocolTests(unittest.TestCase):
    def test_request_contract(self):
        request = build_request("account-model", [{"role": "user", "content": "hello"}])
        self.assertIs(request["store"], False)
        self.assertIs(request["stream"], True)
        self.assertNotIn("temperature", request)
        self.assertNotIn("previous_response_id", request)

    def test_reject_system_message(self):
        with self.assertRaises(ProtocolError):
            build_request("model", [{"role": "system", "content": "secret"}])

    def test_sse_stream(self):
        event = lambda obj: ["data: " + json.dumps(obj) + "\n", "\n"]
        lines = [
            *event({"type": "response.output_text.delta", "delta": "Hel"}),
            *event({"type": "response.output_text.delta", "delta": "lo"}),
            *event({"type": "response.completed"}),
        ]
        self.assertEqual("".join(stream_text(lines)), "Hello")

    def test_failed_stream(self):
        with self.assertRaises(ProtocolError):
            list(stream_text(["data: {\"type\":\"response.failed\"}\n", "\n"]))

    def test_unfinished_stream(self):
        with self.assertRaises(ProtocolError):
            list(stream_text(["data: {\"type\":\"response.output_text.delta\",\"delta\":\"hi\"}\n", "\n"]))


if __name__ == "__main__":
    unittest.main()
