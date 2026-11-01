"""Contract test: bridge calls only Odysseus endpoints, never the model provider."""

import io
import json
import threading
import unittest
import urllib.parse

from bridge.client import MabelClient


class Reply(io.BytesIO):
    def __init__(self, data, headers=None):
        super().__init__(data.encode("utf-8"))
        self.headers = headers or {}


class FakeOpener:
    def __init__(self):
        self.requests = []

    def open(self, req, timeout=20):
        self.requests.append(req)
        path = urllib.parse.urlsplit(req.full_url).path
        if path == "/api/companion/ping":
            return Reply('{"ok":true,"name":"odysseus","version":"test"}')
        if path == "/api/companion/models":
            return Reply(json.dumps({"endpoints": [
                {"endpoint_id": "mabel-1", "name": "Mabel", "endpoint_url": "http://inference-internal:8080/v1/chat/completions", "models": ["model-a"]}
            ]}))
        if path == "/api/sessions":
            return Reply('[]')
        if path == "/api/session":
            return Reply('{"id":"session-a"}')
        if path == "/api/history/session-a":
            return Reply('{"history":[{"role":"user","content":"hi"},{"role":"assistant","content":"Hello"}]}')
        if path == "/api/chat_stream":
            return Reply('data: {"delta":"Hel"}\n\ndata: {"type":"final_response","content":"Hello"}\n\ndata: [DONE]\n\n',
                         headers={"X-Odysseus-Run-Id": "run-a"})
        raise AssertionError("Unexpected path: " + path)


class APIContractTests(unittest.TestCase):
    def test_end_to_end_without_provider_call(self):
        events = []
        complete = threading.Event()

        def emit(event):
            events.append(event)
            if event.get("type") in ("done", "error"):
                complete.set()

        fake = FakeOpener()
        client = MabelClient(emit, base_url="http://127.0.0.1:7000", token="sample", opener=fake)
        client.hello()
        client.new_session(endpoint_id="mabel-1", model="model-a")
        client.send({"session":"session-a","message":"hi","mode":"agent"})
        self.assertTrue(complete.wait(3), events)
        self.assertFalse(any(e["type"] == "error" for e in events), events)
        self.assertTrue(any(e["type"] == "reply" and e.get("replace") == "Hello" for e in events))
        self.assertTrue(any(e["type"] == "done" for e in events))
        paths = [urllib.parse.urlsplit(req.full_url).path for req in fake.requests]
        self.assertIn("/api/chat_stream", paths)
        self.assertFalse(any("/v1/" in path for path in paths))
        sent = next(req for req in fake.requests if req.full_url.endswith("/api/chat_stream"))
        params = urllib.parse.parse_qs(sent.data.decode("utf-8"))
        self.assertEqual(params["mode"], ["agent"])
        self.assertEqual(params["session"], ["session-a"])
        self.assertEqual(sent.get_header("Authorization"), "Bearer sample")

    def test_truncated_stream_not_success(self):
        class Broken(FakeOpener):
            def open(self, req, timeout=20):
                if req.full_url.endswith("/api/chat_stream"):
                    return Reply('data: {"delta":"unfinished"}\n\n')
                return super().open(req, timeout)

        events = []
        done = threading.Event()
        def emit(e):
            events.append(e)
            if e.get("type") in ("done", "error"):
                done.set()
        client = MabelClient(emit, base_url="http://localhost:7000", token="", opener=Broken())
        client.send({"session": "session-a", "message": "hi", "mode": "agent"})
        self.assertTrue(done.wait(3))
        self.assertEqual(events[-1]["type"], "error")
        self.assertIn("[DONE]", events[-1]["message"])


if __name__ == "__main__":
    unittest.main()
