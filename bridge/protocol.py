"""Pure request validation and SSE parsing; never stores or fetches credentials."""

from __future__ import annotations

import json
from collections.abc import Iterable, Iterator


class ProtocolError(ValueError):
    """Invalid inference request or interrupted response."""


def build_request(model: str, messages: list[dict[str, str]], instructions: str | None = None) -> dict:
    """Build an SIWC-compatible Responses request (not an API-key request)."""
    if not isinstance(model, str) or not model.strip():
        raise ProtocolError("model must be a non-empty string")
    if not isinstance(messages, list) or not messages:
        raise ProtocolError("messages must be a non-empty list")
    allowed = {"user", "assistant", "developer"}
    items = []
    for msg in messages:
        if not isinstance(msg, dict) or msg.get("role") not in allowed:
            raise ProtocolError("unsupported message role")
        content = msg.get("content")
        if not isinstance(content, str) or not content.strip():
            raise ProtocolError("message content must be non-empty text")
        items.append({"role": msg["role"], "content": content})
    payload = {"model": model, "input": items, "store": False, "stream": True}
    if instructions:
        payload["instructions"] = instructions
    return payload


def parse_sse_lines(lines: Iterable[str]) -> Iterator[dict]:
    """Read data events from a text/event-stream response. Caller handles terminal events.

    Handles multi-line SSE data, blank-line event boundaries, comments and [DONE].
    This is a transport parser, not a ChatGPT sign-in or inference client.
    """
    data_lines: list[str] = []
    for raw in lines:
        line = raw.rstrip("\r\n")
        if not line:
            if data_lines:
                payload = "\n".join(data_lines)
                data_lines.clear()
                if payload == "[DONE]":
                    return
                try:
                    obj = json.loads(payload)
                except json.JSONDecodeError as exc:
                    raise ProtocolError("invalid JSON in SSE data event") from exc
                if not isinstance(obj, dict):
                    raise ProtocolError("SSE data event must be a JSON object")
                yield obj
            continue
        if line.startswith(":"):
            continue
        if line.startswith("data:"):
            data_lines.append(line[5:].lstrip(" "))
    if data_lines:
        raise ProtocolError("stream ended with an unterminated SSE event")


def stream_text(lines: Iterable[str]) -> Iterator[str]:
    """Yield output text deltas, requiring successful response.completed."""
    completed = False
    for event in parse_sse_lines(lines):
        kind = event.get("type")
        if kind == "response.output_text.delta":
            delta = event.get("delta")
            if isinstance(delta, str):
                yield delta
        elif kind in ("response.failed", "response.incomplete", "error"):
            raise ProtocolError(f"inference failed: {kind}")
        elif kind == "response.completed":
            completed = True
    if not completed:
        raise ProtocolError("stream ended without response.completed")
