"""Stdlib Mabel API client. This process never contacts the model provider."""

from __future__ import annotations

import json
import os
import stat
import threading
import urllib.error
import urllib.parse
import urllib.request
from pathlib import Path

from .protocol import BridgeError, sse_events, visible_content


class NoRedirect(urllib.request.HTTPRedirectHandler):
    def redirect_request(self, req, fp, code, msg, headers, newurl):
        raise BridgeError("Mabel attempted an HTTP redirect; refusing to forward credentials")


def token_from_disk():
    """Read a private token file; environment fallback is for developer testing."""
    config_home = Path(os.environ.get("XDG_CONFIG_HOME") or Path.home() / ".config")
    filename = Path(os.environ.get("MABEL_TOKEN_FILE") or config_home / "mabel-quickshell" / "token")
    if filename.is_symlink():
        raise BridgeError("Token file must not be a symlink")
    if filename.exists():
        mode = filename.stat().st_mode
        if not stat.S_ISREG(mode) or mode & 0o077:
            raise BridgeError("Token file must be a regular file with chmod 600")
        return filename.read_text(encoding="utf-8").strip()
    return os.environ.get("MABEL_API_TOKEN", "").strip()


class MabelClient:
    def __init__(self, emit, *, base_url=None, token=None, opener=None):
        self.emit = emit
        self.base = (base_url or os.environ.get("MABEL_URL") or "http://127.0.0.1:7000").rstrip("/")
        parts = urllib.parse.urlsplit(self.base)
        if parts.scheme not in ("http", "https") or not parts.hostname or parts.username or parts.password or parts.query or parts.fragment or parts.path not in ("", "/"):
            raise BridgeError("MABEL_URL must be the Mabel HTTP(S) origin, not a Strata endpoint or API path")
        self.token = token if token is not None else token_from_disk()
        if not self.token and parts.hostname not in ("localhost", "127.0.0.1", "::1"):
            raise BridgeError("Remote Mabel requires a chat-scoped API token")
        self.opener = opener or urllib.request.build_opener(NoRedirect())
        self._lock = threading.Lock()
        self._active_session = None
        self._run_id = None
        self._stop_requested = False
        self._response = None

    def _request(self, method, path, fields=None, extra_headers=None, timeout=20):
        if not path.startswith("/api/"):
            raise BridgeError("Refusing a non-Mabel API path")
        data = urllib.parse.urlencode(fields).encode("utf-8") if fields is not None else None
        headers = {"Accept": "application/json, text/event-stream"}
        if data is not None:
            headers["Content-Type"] = "application/x-www-form-urlencoded"
        if self.token:
            headers["Authorization"] = "Bearer " + self.token
        if extra_headers:
            headers.update(extra_headers)
        request = urllib.request.Request(self.base + path, data=data, headers=headers, method=method)
        try:
            return self.opener.open(request, timeout=timeout)
        except urllib.error.HTTPError as exc:
            detail = exc.read(1000).decode("utf-8", "replace")
            try:
                parsed = json.loads(detail)
                detail = str(parsed.get("detail") or parsed.get("message") or parsed.get("error") or "")
            except ValueError:
                detail = detail.strip()
            raise BridgeError("Mabel HTTP %s: %s" % (exc.code, detail[:300])) from exc
        except urllib.error.URLError as exc:
            raise BridgeError("Cannot reach Mabel at %s: %s" % (self.base, exc.reason)) from exc

    def _json(self, method, path, fields=None, extra_headers=None):
        with self._request(method, path, fields, extra_headers) as response:
            try:
                return json.load(response)
            except (ValueError, UnicodeError) as exc:
                raise BridgeError("Mabel returned invalid JSON") from exc

    def hello(self):
        info = self._json("GET", "/api/companion/ping")
        self.emit({"type": "hello", "name": "Mabel", "backend": info.get("name", "odysseus"), "version": info.get("version", "")})

    def sessions(self):
        rows = self._json("GET", "/api/sessions")
        if not isinstance(rows, list):
            raise BridgeError("Unexpected sessions response")
        self.emit({"type": "sessions", "sessions": [
            {"id": r.get("id"), "name": r.get("name") or "Untitled",
             "model": r.get("model") or "", "endpoint_id": r.get("endpoint_id")}
            for r in rows if isinstance(r, dict) and r.get("id")
        ]})

    def models(self):
        data = self._json("GET", "/api/companion/models")
        options = []
        for endpoint in data.get("endpoints", []):
            if not endpoint.get("endpoint_id"):
                continue
            for model in endpoint.get("models", []):
                if isinstance(model, str) and model:
                    options.append({"endpoint_id": endpoint["endpoint_id"],
                                    "endpoint_url": endpoint.get("endpoint_url", ""),
                                    "model": model,
                                    "label": "%s · %s" % (endpoint.get("name") or "Endpoint", model)})
        self.emit({"type": "models", "models": options})
        return options

    def history(self, session_id):
        sid = urllib.parse.quote(str(session_id), safe="")
        response = self._json("GET", "/api/history/%s?limit=80" % sid)
        rows = response.get("history", [])
        self.emit({"type": "history", "session": session_id, "messages": [
            {"role": m["role"], "content": visible_content(m.get("content"))}
            for m in rows if isinstance(m, dict) and m.get("role") in ("user", "assistant")
        ]})

    def new_session(self, *, endpoint_id=None, endpoint_url=None, model=None):
        if not endpoint_id or not model:
            options = self.models()
            if not options:
                raise BridgeError("No Mabel model endpoints configured; set one up in Odysseus")
            selected = options[0]
            endpoint_id, endpoint_url, model = selected["endpoint_id"], selected["endpoint_url"], selected["model"]
        else:
            # Never trust endpoint URLs from the widget. Resolve only through Mabel's
            # own scoped endpoint inventory; it owns all model provider credentials.
            options = self.models()
            selected = next((row for row in options if row["endpoint_id"] == endpoint_id and row["model"] == model), None)
            if selected is None:
                raise BridgeError("Model endpoint is not available in Mabel")
            endpoint_url = selected["endpoint_url"]
        data = self._json("POST", "/api/session", {
            "name": "Mabel · Quickshell", "endpoint_id": endpoint_id,
            "endpoint_url": endpoint_url or "", "model": model,
        })
        sid = data.get("id")
        if not sid:
            raise BridgeError("Mabel did not return a session ID")
        self.emit({"type": "created", "session": sid})
        self.sessions()
        self.history(sid)

    def _run(self, session_id, fields=None, resume=False):
        self.emit({"type": "begin", "session": session_id})
        saw_done = False
        try:
            path = "/api/chat/resume/" + urllib.parse.quote(session_id, safe="") if resume else "/api/chat_stream"
            response = self._request("GET" if resume else "POST", path, fields, timeout=300)
            with response:
                run_id = response.headers.get("X-Odysseus-Run-Id") or None
                with self._lock:
                    self._run_id = run_id
                    self._response = response
                    pending_stop = self._stop_requested
                self.emit({"type": "run", "session": session_id, "run_id": bool(run_id)})
                if pending_stop and run_id:
                    self._stop_backend(session_id, run_id)
                text = ""
                for event in sse_events(response):
                    if event.get("type") == "done":
                        saw_done = True
                        break
                    if event.get("_sse_event") == "error" or event.get("type") == "error" or (isinstance(event.get("status"), int) and event["status"] >= 400):
                        raise BridgeError(str(event.get("message") or event.get("detail") or "Mabel streamed an error"))
                    kind = event.get("type")
                    if kind == "final_response":
                        text = str(event.get("content") or event.get("delta") or "")
                        self.emit({"type": "reply", "session": session_id, "replace": text})
                    elif isinstance(event.get("delta"), str) and not event.get("thinking"):
                        if event.get("render_owner") == "streamed" and event.get("replacement_scope") == "turn":
                            text = ""
                            self.emit({"type": "reply", "session": session_id, "replace": ""})
                        text += event["delta"]
                        self.emit({"type": "reply", "session": session_id, "delta": event["delta"]})
                    elif kind == "tool_start":
                        self.emit({"type": "activity", "session": session_id, "message": "Using " + str(event.get("tool") or "tool")})
                    elif kind == "ask_user":
                        # API tokens cannot approve tool execution in Odysseus. Keep
                        # its interactive approval boundary intact.
                        question = event.get("question") or event.get("message") or "Mabel needs your input"
                        self.emit({"type": "approval_needed" if (event.get("approval_id") or event.get("kind") == "tool_approval") else "activity",
                                   "session": session_id, "message": str(question)[:500]})
                    elif kind in ("chat_terminal", "agent_terminal"):
                        metrics = event.get("data") or {}
                        if metrics.get("failed") or metrics.get("failure"):
                            raise BridgeError(str((metrics.get("failure") or {}).get("message") or "Mabel failed to complete the turn"))
                if not saw_done:
                    raise BridgeError("Mabel's stream ended without [DONE]; the response may be incomplete")
            self.emit({"type": "done", "session": session_id})
        except Exception as exc:
            self.emit({"type": "error", "session": session_id, "message": str(exc)[:500]})
        finally:
            with self._lock:
                self._active_session = None
                self._run_id = None
                self._response = None
                self._stop_requested = False

    def _start(self, sid, fields=None, resume=False):
        with self._lock:
            if self._active_session is not None:
                raise BridgeError("A Mabel turn is already active; stop or finish it first")
            self._active_session = sid
            self._run_id = None
            self._stop_requested = False
        threading.Thread(target=self._run, args=(sid, fields, resume), daemon=True).start()

    def send(self, command):
        sid = str(command.get("session") or "").strip()
        msg = str(command.get("message") or "").strip()
        if not sid or not msg:
            raise BridgeError("Choose a session and enter a message")
        if len(msg) > 50000:
            raise BridgeError("Message exceeds Mabel's 50,000-character limit")
        mode = "agent" if command.get("mode") == "agent" else "chat"
        self._start(sid, {"session": sid, "message": msg, "mode": mode})

    def resume(self, session):
        if not session:
            raise BridgeError("No session selected")
        self._start(str(session), resume=True)

    def _stop_backend(self, sid, run_id):
        self._json("POST", "/api/chat/stop/" + urllib.parse.quote(sid, safe=""),
                   fields={}, extra_headers={"X-Odysseus-Run-Id": run_id})

    def stop(self, session):
        with self._lock:
            if self._active_session != session:
                raise BridgeError("No active run for this session")
            self._stop_requested = True
            run_id = self._run_id
            response = self._response
        if run_id:
            self._stop_backend(session, run_id)
        elif response is not None:
            response.close()
        self.emit({"type": "activity", "session": session, "message": "Stop requested"})
