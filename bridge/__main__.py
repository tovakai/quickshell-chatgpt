"""JSON-lines IPC between Quickshell and the Mabel/Odysseus API."""

import json
import sys
import threading

from .client import MabelClient
from .protocol import BridgeError


def main():
    output_lock = threading.Lock()

    def emit(message):
        with output_lock:
            print(json.dumps(message, ensure_ascii=False), flush=True)

    try:
        client = MabelClient(emit)
    except BridgeError as exc:
        emit({"type": "error", "message": str(exc)})
        return 1

    for line in sys.stdin:
        if len(line) > 150_000:
            emit({"type": "error", "message": "IPC message too large"})
            continue
        try:
            command = json.loads(line)
            if not isinstance(command, dict):
                raise BridgeError("Expected JSON object")
            op = command.get("op")
            if op == "hello":
                client.hello()
            elif op == "sessions":
                client.sessions()
            elif op == "models":
                client.models()
            elif op == "history":
                client.history(str(command.get("session") or ""))
            elif op == "new":
                client.new_session(endpoint_id=command.get("endpoint_id"), model=command.get("model"))
            elif op == "send":
                client.send(command)
            elif op == "resume":
                client.resume(command.get("session"))
            elif op == "stop":
                client.stop(command.get("session"))
            else:
                raise BridgeError("Unknown IPC command")
        except (BridgeError, ValueError, TypeError) as exc:
            emit({"type": "error", "message": str(exc)[:500]})
        except Exception as exc:
            emit({"type": "error", "message": "Mabel bridge error: " + str(exc)[:250]})
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
