from __future__ import annotations

import json
import threading
from http.server import SimpleHTTPRequestHandler, ThreadingHTTPServer
from pathlib import Path
from urllib.parse import urlparse

from tigress.engine import TigressEngine
from tigress.models import Event, EventType

ROOT = Path(__file__).resolve().parent
WEB_ROOT = ROOT / "visual_lab"
HOST = "127.0.0.1"
PORT = 8765

engine = TigressEngine()
lock = threading.RLock()
sequence = 0
latest = {
    "connected": True,
    "sequence": 0,
    "action": "IDLE",
    "dialogue": "Main yahin hoon. Batao, kya chal raha hai?",
    "explanation": "Runtime ready. Waiting for an interaction.",
    "expression": "friendly",
    "state": engine.state.to_dict(),
}


def expression_for(action: str, state: dict) -> str:
    if action == "ASK_FOR_CONTEXT":
        return "curious"
    if action in {"LISTEN_AND_EVALUATE", "CONSIDER_AND_DECIDE",
                  "DISCUSS_AND_EVALUATE"}:
        return "thinking"
    if action in {"CHALLENGE_AND_SET_BOUNDARY",
                  "NAME_THE_BEHAVIOUR_AND_SET_BOUNDARY",
                  "PROTECT_BOUNDARIES_AND_REASSESS_TRUST"}:
        return "hurt" if state.get("hurt", 0) >= 0.35 else "confident"
    if action in {"RECOGNISE_CHANGE_AND_REBUILD_GRADUALLY",
                  "ACKNOWLEDGE_RESPECT"}:
        return "friendly"
    return "friendly"


def process_event(payload: dict) -> dict:
    global sequence

    raw_type = str(payload.get("event_type", "UNCLEAR")).upper()
    try:
        event_type = EventType(raw_type)
    except ValueError as exc:
        raise ValueError(f"Unsupported event_type: {raw_type}") from exc

    description = str(payload.get("description", ""))[:1000]
    evidence = float(payload.get("evidence_strength", 0.7))
    evidence = max(0.0, min(1.0, evidence))
    context_known = bool(payload.get("context_known", True))

    with lock:
        decision = engine.respond(Event(
            event_type=event_type,
            description=description,
            evidence_strength=evidence,
            context_known=context_known,
        ))
        sequence += 1
        state = decision.state_after

        latest.update({
            "connected": True,
            "sequence": sequence,
            "action": decision.action,
            "dialogue": decision.dialogue,
            "explanation": decision.explanation,
            "expression": expression_for(decision.action, state),
            "state": state,
            "event_type": event_type.value,
            "description": description,
        })
        return dict(latest)


class RuntimeHandler(SimpleHTTPRequestHandler):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, directory=str(WEB_ROOT), **kwargs)

    def log_message(self, fmt, *args):
        print("[runtime] " + (fmt % args))

    def send_json(self, data: dict, status: int = 200):
        body = json.dumps(data, ensure_ascii=False).encode("utf-8")
        self.send_response(status)
        self.send_header("Content-Type", "application/json; charset=utf-8")
        self.send_header("Content-Length", str(len(body)))
        self.send_header("Cache-Control", "no-store")
        self.send_header("Access-Control-Allow-Origin", "http://127.0.0.1:8765")
        self.end_headers()
        self.wfile.write(body)

    def do_GET(self):
        path = urlparse(self.path).path

        if path == "/api/state":
            with lock:
                self.send_json(dict(latest))
            return

        if path == "/api/health":
            self.send_json({
                "ok": True,
                "service": "statecraft-runtime",
                "sequence": sequence,
            })
            return

        if path == "/":
            self.path = "/index.html"

        super().do_GET()

    def do_POST(self):
        path = urlparse(self.path).path
        if path != "/api/event":
            self.send_json({"error": "Not found"}, 404)
            return

        try:
            length = int(self.headers.get("Content-Length", "0"))
            if length < 2 or length > 10000:
                self.send_json({"error": "Request body must be 2-10000 bytes"}, 400)
                return

            payload = json.loads(self.rfile.read(length).decode("utf-8"))
            if not isinstance(payload, dict):
                self.send_json({"error": "JSON body must be an object"}, 400)
                return

            self.send_json(process_event(payload))
        except (ValueError, TypeError, json.JSONDecodeError) as exc:
            self.send_json({"error": str(exc)}, 400)
        except Exception as exc:
            self.send_json({"error": f"Runtime error: {exc}"}, 500)


def main():
    if not (WEB_ROOT / "index.html").exists():
        raise SystemExit(f"Missing browser UI: {WEB_ROOT / 'index.html'}")

    server = ThreadingHTTPServer((HOST, PORT), RuntimeHandler)
    print(f"Character runtime: http://{HOST}:{PORT}")
    print("API health:        http://{HOST}:{PORT}/api/health")
    print("Press Ctrl+C to stop.")
    try:
        server.serve_forever()
    except KeyboardInterrupt:
        print("\nStopping runtime...")
    finally:
        server.server_close()


if __name__ == "__main__":
    main()
