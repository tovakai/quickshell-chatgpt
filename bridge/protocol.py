"""Mabel's SSE transport decoder. No OpenAI/Strata request schema lives here."""

import json


class BridgeError(RuntimeError):
    """A backend or transport error suitable for presentation to the user."""


def sse_events(lines):
    """Yield JSON Mabel events and an explicit done marker from an SSE byte stream.

    HTTPResponse iterates over byte lines. SSE may split data over multiple
    lines and include heartbeat comments and named events.
    """
    data = []
    event_type = "message"

    def emit():
        if not data:
            return None
        payload = "\n".join(data)
        if payload == "[DONE]":
            return {"type": "done"}
        try:
            decoded = json.loads(payload)
        except ValueError as exc:
            raise BridgeError("Mabel returned malformed SSE JSON") from exc
        if not isinstance(decoded, dict):
            raise BridgeError("Mabel returned a non-object SSE event")
        decoded["_sse_event"] = event_type
        return decoded

    for raw in lines:
        line = raw.decode("utf-8", "replace") if isinstance(raw, bytes) else raw
        line = line.rstrip("\r\n")
        if not line:
            item = emit()
            if item is not None:
                yield item
            data = []
            event_type = "message"
        elif line.startswith(":"):
            continue
        elif line.startswith("data:"):
            data.append(line[5:].lstrip(" "))
        elif line.startswith("event:"):
            event_type = line[6:].strip()
    item = emit()
    if item is not None:
        yield item


def visible_content(value):
    """Flatten persisted text-block history without exposing hidden tool events."""
    if isinstance(value, str):
        return value
    if isinstance(value, list):
        return "\n".join(
            item["text"] for item in value
            if isinstance(item, dict) and isinstance(item.get("text"), str)
        )
    return ""
