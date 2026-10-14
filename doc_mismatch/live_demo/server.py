"""A tiny local web app wired directly to the REAL v2 engine -- no precomputed tree, no depth cap, no "most likely answer" shortcuts. Every click in the browser is a genuine
live call into the same tool_ticket_memo2 routine the rest of this session's work was about (T3-noattr item set, min_rate = the live shipped default). Stdlib only, no new
dependency: http.server for the tiny JSON API, one in-memory session (this is a single-technician local demo, not a multi-user service).
  .venv/bin/python server.py           # serves http://localhost:8743

The intro screen offers two settings of the joint model, Mixed severity (the default) and Shipped.
"""
import json
import sys
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from pathlib import Path

ROOT = Path("/Users/abhinavakula/BuildingMapping/doc_mismatch")
sys.path.insert(0, str(ROOT / "src"))

from docmismatch.troubleshoot.v1 import data as D  # noqa: E402
from docmismatch.troubleshoot.v1.engine import Obs, Question, make_case_v1  # noqa: E402
from docmismatch.troubleshoot.v2 import cli as V2CLI  # noqa: E402
from docmismatch.troubleshoot.v2.joint import JointModel, JointSettings  # noqa: E402
from docmismatch.troubleshoot.v2.policies import PriorSession  # noqa: E402

BUILDING = ROOT / "examples/troubleshoot_example/building_v2.json"
ROOM_IDS = ["Room-0", "Room-1"]
ITEMS = D.TIERS["T1"] | {"bas_access", "point_map"}     # T1 + (T3 minus T2): the user's actual documentation profile, not plain T3
MIN_RATE = V2CLI.LIVE_MIN_RATE_DEFAULT                  # the live shipped default (0.02), not the old 0.015
PORT = 8743

# Two settings of the joint model (live_demo_bldg11/README.md): "shipped" assumes about half of the rooms on a low-static handler complain; "mixed" (the default) weighs 5%, 15%, 50% and
# 90% and lets the complaints pick. On this building's 8-room handlers the two make the same decisions (live_demo_bldg11/FIRST_DEMO_NOTES.md); on large handlers mixed finds shared faults shipped cannot.
MIX = ((0.05, 0.25), (0.15, 0.25), (0.5, 0.25), (0.9, 0.25))
MODELS = [dict(key="shipped", label="Shipped settings"), dict(key="mixed", label="Mixed severity (general)")]
DEFAULT_MODEL = "mixed"

STATIC_DIR = Path(__file__).with_name("static")


def build_cases():
    b = D.load_building_v1(BUILDING)
    ctx = D.Context(instrument="yes", occupant="no")
    return [make_case_v1(b, r, ITEMS, None, context=ctx, min_rate=MIN_RATE) for r in ROOM_IDS]


class Visit:
    """All server-side state for the one visit this demo runs at a time."""

    def __init__(self, model: str = DEFAULT_MODEL):
        if model not in {m["key"] for m in MODELS}:
            raise ValueError(f"model must be one of {[m['key'] for m in MODELS]}, not {model!r}")
        self.model_name = model
        self.cases = build_cases()
        self.model = JointModel(self.cases, JointSettings(low_mix=MIX) if model == "mixed" else JointSettings())
        self.room = 0
        self.memo = {}
        self.low_static_seen = set()
        self.at = None
        self.visit_minutes = 0.0
        self.visit_checks = 0
        self.conclusions = []
        self.sess = None
        self.pending = None   # {"kind": "check", "name":..., "target":...} or {"kind": "question", "key":...}
        self._start_room()

    def _start_room(self):
        i = self.room
        sess = PriorSession(self.cases[i], (self.model.causes[i], self.model.marg0[i]))
        sess.at = self.at
        for (a, name), word in self.memo.items():
            if a == self.cases[i].ahu:
                sess.log.append(Obs(name, self.cases[i].doc, word, 0.0))
        if self.cases[i].ahu in self.low_static_seen:
            sess.log.append(Obs("static_at_box", self.cases[i].doc, "abnormal", 0.0))
        self.sess = sess

    def room_info(self):
        return [dict(id=c.member, name=c.member_name, ahu=c.ahu, documented_box=c.doc) for c in self.cases]

    def current_step(self):
        """What the frontend should show right now: the next check/question, or a conclude/visit_done payload. Also records `self.pending` so `answer()` knows what to apply."""
        step = self.sess.next_step()
        if step is None:
            st = self.sess.status()
            top = st["ranked"][0]
            leaf = dict(kind="conclude", room=self.room, conclusion=self.sess.describe(top[0]), belief=round(float(top[1]), 3),
                        minutes_so_far=round(self.sess.elapsed, 1), checks_so_far=st["n_checks"], forced=not st["concluded"])
            self.visit_minutes += leaf["minutes_so_far"]
            self.visit_checks += leaf["checks_so_far"]
            self.conclusions.append(leaf)
            has_next = self.room + 1 < len(self.cases)
            leaf["has_next"] = has_next
            if has_next:
                nxt = self.cases[self.room + 1]
                carried = [f"{name.replace('_', ' ')}: {word}" for (a, name), word in self.memo.items() if a == nxt.ahu]
                if nxt.ahu in self.low_static_seen:
                    carried.append("low duct static already found on this air handler")
                leaf["carried_into_next"] = carried
                leaf["next_room_name"] = nxt.member_name
            leaf["visit_minutes"] = round(self.visit_minutes, 1)
            leaf["visit_checks"] = self.visit_checks
            self.pending = None
            return leaf
        if isinstance(step, Question):
            self.pending = dict(kind="question", key=step.key)
            return dict(kind="question", room=self.room, name=step.key, text=step.text, words=list(step.options))
        ck = step.check
        already_memoed = (self.sess.case.ahu, ck.name) in self.memo
        self.pending = dict(kind="check", name=ck.name, target=step.target)
        return dict(kind="check", room=self.room, name=ck.name, text=step.text, minutes=round(step.minutes, 1), words=list(ck.words), p_pos=round(step.p_pos, 2),
                    memo_note=("Already read for an earlier room on this air handler -- free here." if already_memoed else
                                "A reading on the air handler itself: later rooms on the same air handler get this one for free." if ck.subject == "ahu" else None))

    def advance_room(self):
        """Called by the frontend after showing a conclude payload, to move on to the next room (or finish the visit)."""
        if self.room + 1 >= len(self.cases):
            return dict(kind="visit_done", conclusions=self.conclusions, visit_minutes=round(self.visit_minutes, 1), visit_checks=self.visit_checks,
                        rooms=[dict(name=c.member_name) for c in self.cases])
        self.room += 1
        self.at = self.sess.at
        self._start_room()
        return self.current_step()

    def answer(self, word):
        if self.pending is None:
            raise ValueError("nothing is pending")
        if self.pending["kind"] == "question":
            self.sess.declare(self.pending["key"], word)
        else:
            name, target = self.pending["name"], self.pending["target"]
            ck = next(c for c in self.sess.case.checks if c.name == name)
            self.sess.report(word, check=name, target=target)
            if ck.subject == "ahu":
                self.memo[(self.sess.case.ahu, name)] = word
            elif name == "static_at_box" and word == "abnormal":
                self.low_static_seen.add(self.sess.case.ahu)
        return self.current_step()


VISIT: Visit | None = None


def api_start(body=None):
    global VISIT
    VISIT = Visit((body or {}).get("model", DEFAULT_MODEL))
    post0 = VISIT.model.ahu_posterior_by_cause(VISIT.model.initial())        # what the joint model believes about each air handler before any check
    return dict(rooms=VISIT.room_info(), step=VISIT.current_step(), model=VISIT.model_name, models=MODELS,
                prior={a: {k: round(float(x), 4) for k, x in d.items()} for a, d in post0.items()})


def api_answer(body):
    if VISIT is None:
        raise ValueError("call /api/start first")
    return dict(step=VISIT.answer(body["word"]))


def api_advance():
    if VISIT is None:
        raise ValueError("call /api/start first")
    return dict(step=VISIT.advance_room())


ROUTES = {"/api/start": api_start, "/api/answer": api_answer, "/api/advance": lambda body: api_advance()}


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
        if self.path.startswith("/static/"):
            p = STATIC_DIR / self.path[len("/static/"):]
            if p.exists():
                ctype = "text/css" if p.suffix == ".css" else "application/javascript" if p.suffix == ".js" else "application/octet-stream"
                return self._send_file(p, ctype)
        self.send_response(404)
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
    print(f"Service Call Assistant (live) on http://localhost:{PORT}")
    ThreadingHTTPServer(("127.0.0.1", PORT), Handler).serve_forever()
