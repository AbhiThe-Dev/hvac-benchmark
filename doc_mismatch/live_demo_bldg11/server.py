"""A second, separate local demo (the first, ../live_demo, is untouched): the real v2 engine on a real layout (Mortar bldg11, two air handlers) with a SCRIPTED six-complaint scenario.

  .venv/bin/python doc_mismatch/live_demo_bldg11/server.py        # serves http://localhost:8744   (the original demo uses 8743)

Needs the Mortar Brick file in data_cache/ (not part of the repository: the building file is generated from it on first use and never committed). Stdlib only, one in-memory visit, a
single-presenter local demo, not a service. See README.md for what is real and what is scripted.
"""

import json
import sys
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from pathlib import Path

HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE))

from visit import Visit, autoplay, coverage  # noqa: E402
from world import load_scenario  # noqa: E402

PORT = 8744
STATIC_DIR = HERE / "static"
VISIT: Visit | None = None


def _models(scenario: dict) -> list:
    return [dict(key=k, label=v["label"], r_low=v["r_low"]) for k, v in scenario["model"].items() if not v.get("hidden")]      # "adjusted" stays defined for the registered scripts and tests, not on the page


def api_start(body):
    global VISIT
    model = body.get("model", "shipped")
    VISIT = Visit(model)
    sc = VISIT.scenario
    fault_ahu = next(a for a, s in sc["ahu_truth"].items() if s != "ok")
    return dict(rooms=VISIT.room_info(), step=VISIT.current_step(), model=model, models=_models(sc), prior=VISIT.prior_info(), title=sc["title"], note=sc["note"],
                coverage=coverage(), ahus=sorted({c.ahu for c in VISIT.cases}), fault_ahu=fault_ahu)


def api_answer(body):
    if VISIT is None:
        raise ValueError("call /api/start first")
    return dict(step=VISIT.answer(body["word"]))


def api_advance(body):
    if VISIT is None:
        raise ValueError("call /api/start first")
    return dict(step=VISIT.advance_room())


def api_autoplay(body):
    return autoplay(body.get("model", "shipped"))


ROUTES = {"/api/start": api_start, "/api/answer": api_answer, "/api/advance": api_advance, "/api/autoplay": api_autoplay}


class Handler(BaseHTTPRequestHandler):
    def _send_json(self, obj, status=200):
        payload = json.dumps(obj).encode()
        self.send_response(status)
        self.send_header("Content-Type", "application/json")
        self.send_header("Content-Length", str(len(payload)))
        self.end_headers()
        self.wfile.write(payload)

    def _send_file(self, path, content_type):
        data = path.read_bytes()
        self.send_response(200)
        self.send_header("Content-Type", content_type)
        self.send_header("Content-Length", str(len(data)))
        self.end_headers()
        self.wfile.write(data)

    def do_GET(self):
        if self.path == "/" or self.path == "/index.html":
            return self._send_file(STATIC_DIR / "index.html", "text/html; charset=utf-8")
        self.send_response(404)
        self.end_headers()

    def do_HEAD(self):
        self.send_response(200 if self.path in ("/", "/index.html") else 404)
        self.end_headers()

    def do_POST(self):
        if self.path not in ROUTES:
            return self._send_json({"error": f"no such route {self.path!r}"}, 404)
        length = int(self.headers.get("Content-Length", 0))
        body = json.loads(self.rfile.read(length) or b"{}")
        try:
            return self._send_json(ROUTES[self.path](body))
        except Exception as e:  # noqa: BLE001 -- a local single-user demo; surface the error to the browser console instead of a bare 500
            return self._send_json({"error": str(e)}, 400)

    def log_message(self, fmt, *args):
        sys.stderr.write(f"{self.address_string()} - {fmt % args}\n")


if __name__ == "__main__":
    load_scenario()
    print(f"Service Call Assistant (bldg11 scenario) on http://localhost:{PORT}")
    ThreadingHTTPServer(("127.0.0.1", PORT), Handler).serve_forever()
