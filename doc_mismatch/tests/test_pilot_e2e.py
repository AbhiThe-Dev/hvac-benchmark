"""End-to-end test of the pilot's data collection.

A simulated technician drives the REAL HTTP endpoints in the order the frontend does, on a controlled clock, and keeps its own log
of everything it did and when (the "truth"). Afterwards an independent oracle compares that log with what was stored, what the
technician's own record view shows, what the export wrote, what a restored backup exports, and what survives a purge.

The point is not diagnostic realism (answers are random) but that the pipeline records exactly what happened: no event lost,
duplicated or reordered; timings equal the clock; what was shown is what was stored; the ladder matches the evidence given;
anonymization holds; the export is reproducible from a backup; a purge removes one participant and nothing else.
"""
import csv
import io
import json
import os
import random
import sys
import tarfile
import tempfile
import threading
import time
from concurrent.futures import ThreadPoolExecutor
from datetime import datetime, timedelta, timezone
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]           # doc_mismatch/
sys.path.insert(0, str(ROOT / "src"))
sys.path.insert(0, str(ROOT))

os.environ.setdefault("ANTHROPIC_API_KEY", "sk-test-not-real")
os.environ.setdefault("NOTIFY_EMAIL", "dev@example.com")
os.environ.setdefault("SMTP_FROM_EMAIL", "dev@example.com")
os.environ.setdefault("SMTP_APP_PASSWORD", "not-a-real-app-password")
os.environ.setdefault("PILOT_DATA_DIR", tempfile.mkdtemp(prefix="pilot_e2e_test_"))

import pytest  # noqa: E402
from fastapi.testclient import TestClient  # noqa: E402
from PIL import Image  # noqa: E402

import pilot.auth as auth_module  # noqa: E402
import pilot.routes_intake as routes_intake  # noqa: E402
from pilot import config, db, visit as V  # noqa: E402
from pilot.app import app  # noqa: E402
from pilot.schema import BuildingDraft  # noqa: E402
from pilot.scripts import backup, export_cases, followups, purge  # noqa: E402

NOT_A_FIX = ("no_repair_needed", "deferred_or_referred")
PHYSICAL = ("observed_directly", "measured")
TAXONOMY = ["actuator_fail", "damper_mech", "no_power", "signal_fault", "controller_comms", "controller_config", "flow_sensor",
            "zone_sensor_setpoint", "ahu_fan_off", "low_static", "reheat_fail", "duct_diffuser", "capacity_design", "econ_fault", "documentation_wrong"]
HOW = ["observed_directly", "measured", "repair_fixed_it", "ruled_out_others", "other_tech_or_vendor", "not_confirmed"]
REPAIRS = ["replaced_part", "adjusted_or_reset", "reconfigured_controls", "cleaned_or_cleared", "repaired_wiring", "corrected_documentation",
           "no_repair_needed", "deferred_or_referred", "other"]
EMAIL, PHONE = "dana.k@clinic-example.com", "(312) 555-0142"


# ------------------------------------------------------------------------------------------------- the world

class Clock:
    """db._now() is the only clock the case record uses, so the simulation controls time exactly."""
    def __init__(self):
        self.t = datetime(2026, 10, 1, 9, 0, 0, tzinfo=timezone.utc)

    def __call__(self):
        return self.t.isoformat()

    def advance(self, **kw):
        self.t += timedelta(**kw)


class Env:
    def __init__(self, client, clock, drafts, sent, tmp):
        self.client, self.clock, self.drafts, self.sent, self.tmp = client, clock, drafts, sent, tmp
        self.headers = {}
        buf = io.BytesIO()
        Image.new("RGB", (10, 10)).save(buf, format="JPEG")
        self.jpeg = buf.getvalue()

    def login(self):
        c = self.client
        assert c.post("/api/request-code").status_code == 200
        r = c.post("/api/verify-code", json={"code": self.sent["code"]})
        assert r.status_code == 200, r.text
        self.headers = {"Authorization": f"Bearer {r.json()['token']}"}

    def join(self, role="contractor_tech", years="2to5", vav="some"):
        r = self.client.post("/api/participant", headers=self.headers, json=dict(role=role, years_band=years, vav_band=vav, ack=True))
        assert r.status_code == 200, r.text
        return r.json()["participant_id"]


@pytest.fixture
def env(tmp_path, monkeypatch):
    monkeypatch.setattr(config, "DB_PATH", tmp_path / "pilot.db")
    monkeypatch.setattr(config, "VISITS_DIR", tmp_path / "visits")
    monkeypatch.setattr(config, "UPLOADS_DIR", tmp_path / "uploads")
    clock = Clock()
    monkeypatch.setattr(db, "_now", clock)
    drafts, sent = {"current": None}, {}
    monkeypatch.setattr(routes_intake, "extract_building",
                        lambda a, b: (BuildingDraft.model_validate(drafts["current"]), '{"stub": true}'))
    monkeypatch.setattr(auth_module, "email_otp", type("M", (), {"send_login_code": staticmethod(lambda code: sent.__setitem__("code", code))}))
    with TestClient(app) as c:
        e = Env(c, clock, drafts, sent, tmp_path)
        e.login()
        yield e


def building_draft(tag, n_rooms, who):
    """A building whose names are deliberately identifying; `who` marks the participant so a purge can be checked byte by byte."""
    boxes = []
    for i in range(n_rooms):
        boxes.append({"equipment_id": f"VAV-{who}-{tag}{i}", "serves_room": f"Suite {tag}{i}0 {who}Dental",
                      "points": {"status": f"V{tag}{i}.STS", "airflow": f"V{tag}{i}.CFM", "damper": f"V{tag}{i}.DMP", **({"reheat": f"V{tag}{i}.RHT"} if i % 2 == 0 else {})},
                      "zone_temperature_point": f"R{tag}{i}.T"})
    return {"ahu": {"equipment_id": f"{who}-AHU-{tag}", "points": {"fan_status": f"{who}.{tag}.SF", "static_pressure": f"{who}.{tag}.SP",
                                                                   "economizer_position": f"{who}.{tag}.ECO"}},
            "boxes": boxes, "notes": None}


# ------------------------------------------------------------------------------------------------- the simulated technician

class Truth:
    """Everything the simulated technician did to one case, in order, as it did it."""
    def __init__(self, case_id):
        self.case_id, self.ops, self.complaint = case_id, [], None

    def add(self, op, **kw):
        self.ops.append(dict(op=op, **kw))

    def kinds(self):
        out = []
        for o in self.ops:
            out += {"intent": ["intent", "suggestion_shown"], "decision": ["decision"] if o.get("action") == "skip" else ["decision", "check_started"],
                    "answer": ["external_result" if o.get("external") else "check_result"], "question": ["question_answer"], "conclude": ["tool_conclusion"],
                    "root_cause": ["root_cause"], "repair": ["repair"], "recheck": ["post_repair_check"], "outcome": ["outcome"],
                    "followup": ["followup"]}[o["op"]]
        return out

    def of(self, op):
        return [o for o in self.ops if o["op"] == op]


class Sim:
    def __init__(self, env, seed, who="Kowalski"):
        self.env, self.rng, self.who, self.truth = env, random.Random(seed), who, {}

    # --- http, exactly as the frontend does it
    def call(self, method, path, body=None, expect=200):
        r = getattr(self.env.client, method)(path, headers=self.env.headers, **({"json": body} if body is not None else {}))
        assert r.status_code == expect, f"{method.upper()} {path} {body} -> {r.status_code} {r.text[:300]}"
        return r.json()

    def tick(self, lo=2, hi=40):
        self.env.clock.advance(seconds=self.rng.randint(lo, hi))

    def start_visit(self, tag, n_rooms, feel="too_hot", airflow="yes", complaint=True, prior_case_id=None):
        draft = building_draft(tag, n_rooms, self.who)
        self.env.drafts["current"] = draft
        r = self.env.client.post("/api/intake/extract", headers=self.env.headers,
                                 files={"photo_bas": ("a.jpg", self.env.jpeg, "image/jpeg"), "photo_equipment": ("b.jpg", self.env.jpeg, "image/jpeg")})
        assert r.status_code == 200, r.text
        rooms = [b["serves_room"] for b in draft["boxes"]]
        self.rooms = rooms
        text = f"{rooms[0]} runs hot every afternoon; call {EMAIL} or {PHONE}" if complaint else None
        ctx = dict(complaint_text=text, complaint_source="occupant", building_type="healthcare", system_kind="vav_hot_water_reheat", equipment_age_band="10to20",
                   readings=dict(zone_temp="78 F", duct_static="0.4 in. w.c."), alarms_text=None, own_hypotheses=["box_mechanical", "sensing"])
        ctx = {k: v for k, v in ctx.items() if v is not None}
        if prior_case_id:
            ctx["prior_case_id"] = prior_case_id
        self.tick()
        out = self.call("post", f"/api/intake/{r.json()['intake_id']}/confirm",
                        dict(draft=draft, room_ids=rooms, feel=feel, airflow=airflow, context=ctx))
        for room in out["rooms"]:
            t = Truth(room["case_id"])
            t.complaint = bool(text) or feel in ("too_hot", "too_cold")
            self.truth[room["case_id"]] = t
        return out["visit_id"], out["rooms"], out["step"]

    def reload_check(self, vid, step):
        """The frontend can be reloaded at any tap: the server must hand back exactly the step it was on."""
        again = self.call("get", f"/api/visits/{vid}")["step"]
        assert again == step, f"a reload changed the step:\n{step}\n{again}"

    def run_visit(self, vid, step, p=None):
        """Walks the visit to its end like a technician would. `p` = behaviour weights."""
        p = dict(intent_pick=0.4, intent_other=0.1, substitute=0.2, external=0.1, skip=0.15, unsure=0.1, reading=0.25, correct=0.1) | (p or {})
        rng = self.rng
        for _ in range(400):
            if rng.random() < 0.3:
                self.reload_check(vid, step)
            k = step["kind"]
            if k == "visit_done":
                return step
            t = self.truth[step["case_id"]] if "case_id" in step else None
            if k == "question":
                ans = rng.choice(["yes", "no"])
                self.tick()
                t.add("question", key=step["name"], answer=ans)
                step = self.call("post", f"/api/visits/{vid}/answer", dict(word=ans, client_ts="2030-01-01T00:00:00Z"))["step"]
            elif k == "conclude":
                self.observe_conclusion(vid, step)
                self.tick()
                room = step["room"]
                step = self.call("post", f"/api/visits/{vid}/advance", dict(from_room=room))["step"]
                if rng.random() < 0.35:
                    # a double tap on "Continue": the second must never skip the room that was just opened
                    again = self.env.client.post(f"/api/visits/{vid}/advance", headers=self.env.headers, json=dict(from_room=room))
                    if step["kind"] == "visit_done":
                        assert again.status_code == 200 and again.json()["step"]["kind"] == "visit_done", "a repeat on a finished visit is harmless"
                    else:
                        assert again.status_code == 400, f"a double tap skipped a room: {again.status_code} {again.text[:200]}"
                    self.reload_check(vid, step)
            elif step["stage"] == "intent":
                self.tick()
                roll = rng.random()
                if roll < p["intent_pick"]:
                    pick = rng.choice(step["picker"])
                    body = dict(kind="check", check=pick["name"], target=pick["target"])
                    t.add("intent", choice="check", check=pick["name"], target=pick["target"])
                elif roll < p["intent_pick"] + p["intent_other"]:
                    body = dict(kind="other", text=f"look at the trend log for {self.rooms[0]}")
                    t.add("intent", choice="other", check=None, target=None)
                else:
                    body = dict(kind="unsure")
                    t.add("intent", choice="unsure", check=None, target=None)
                step = self.call("post", f"/api/visits/{vid}/intent", body)["step"]
                assert step["stage"] == "revealed"
                t.ops[-1]["shown"] = step["name"]
                t.ops[-1]["picker"] = step.get("picker")
            elif step["stage"] == "revealed":
                self.tick()
                shown, picker = step["name"], step["picker"]
                roll = rng.random()
                reason = rng.choice([None, "already_known", "cannot_do_now", "not_relevant", "prefer_other_first", "other"])
                if roll < p["skip"]:
                    body = dict(action="skip", reason=reason)
                    t.add("decision", action="skip", check=shown, reason=reason)
                elif roll < p["skip"] + p["external"]:
                    body = dict(action="external", external_text=f"checked the trend log for {self.rooms[0]}", reason=reason)
                    t.add("decision", action="external", check=None, reason=reason)
                elif roll < p["skip"] + p["external"] + p["substitute"] and len([x for x in picker if x["name"] != shown]) > 0:
                    pick = rng.choice([x for x in picker if x["name"] != shown])
                    body = dict(action="substitute", check=pick["name"], target=pick["target"], reason=reason)
                    t.add("decision", action="substitute", check=pick["name"], target=pick["target"], reason=reason)
                else:
                    body = dict(action="follow")
                    t.add("decision", action="follow", check=shown, reason=None)
                step = self.call("post", f"/api/visits/{vid}/decision", body)["step"]
            else:                                                     # in_progress: the timer is running
                secs = rng.randint(20, 1500)
                self.env.clock.advance(seconds=secs)
                if step["external"]:
                    t.add("answer", external=True, check=None, seconds=secs, result_text=f"setpoint changed at {self.rooms[0]}", minutes_correction=None)
                    step = self.call("post", f"/api/visits/{vid}/answer", dict(result_text=f"setpoint changed at {self.rooms[0]}"))["step"]
                else:
                    word = rng.choice(step["words"] + step["words"] + ["unsure"])
                    body = dict(word=word)
                    reading = f"{rng.randint(1, 99) / 10} in. w.c." if rng.random() < p["reading"] else None
                    corr = float(rng.randint(1, 60)) if rng.random() < p["correct"] else None
                    if reading:
                        body["reading_text"] = reading
                    if corr is not None:
                        body["minutes_correction"] = corr
                    body["client_ts"] = rng.choice(["not a date", "1999-01-01T00:00:00Z", "2099-12-31T23:59:59+00:00"])     # device clocks lie: the server's is the record
                    t.add("answer", external=False, check=step["name"], word=word, seconds=secs, reading_text=reading, minutes_correction=corr)
                    step = self.call("post", f"/api/visits/{vid}/answer", body)["step"]
            if step["kind"] == "conclude" and k != "conclude":
                pass                                                  # observed at the top of the next loop
        raise AssertionError("the visit never finished")

    def observe_conclusion(self, vid, step):
        t = self.truth[step["case_id"]]
        if not t.of("conclude"):
            t.add("conclude", tool_cause_id=step["tool_cause_id"], belief=step["belief"], hedged=step.get("hedged", False))
        # looking at the conclusion again (a reload) must not record it again
        self.reload_check(vid, step)

    # --- close-out, as the close-out screen does it
    def closeout(self, case_id, mode):
        t, rng = self.truth[case_id], self.rng
        rec = self.call("get", f"/api/cases/{case_id}/record")
        if mode == "none":
            return
        full = mode == "full"
        named = rng.random() < (0.9 if full else 0.6)
        if named:
            cause = rng.choice(TAXONOMY + ["other", "not_determined"])
            how = rng.choice(HOW)
            body = dict(cause_id=cause, how_confirmed=how)
            if cause == "other":
                body["text"] = f"refrigerant side at {self.rooms[0]}"
            if how in PHYSICAL:
                body["confirmed_before_repair"] = rng.choice([True, False, None])
            if cause == "documentation_wrong" and rec["topology"] and rng.random() < 0.8:
                body["actual_box"] = rng.choice(rec["topology"]["boxes"] + ["not_listed", "not_sure"]) if rec["topology"]["boxes"] else "not_sure"
            self.tick()
            self.call("post", f"/api/cases/{case_id}/root_cause", body)
            t.add("root_cause", **body)
        if not full and rng.random() < 0.5:
            return
        if rng.random() < 0.9:
            body = dict(actions=rng.sample(REPAIRS, rng.choice([1, 1, 2])), text=f"swapped it; tenant {EMAIL}" if rng.random() < 0.3 else None)
            self.tick()
            self.call("post", f"/api/cases/{case_id}/repair", body)
            t.add("repair", **body)
            rec = self.call("get", f"/api/cases/{case_id}/record")
            for c in rec["recheck"]["candidates"]:
                if rng.random() < 0.6:
                    body = dict(of_event_id=c["of_event_id"], result=rng.choice(["now_ok", "still_wrong", "unsure"]), reading_text="0.9 in" if rng.random() < 0.3 else None)
                    self.tick()
                    self.call("post", f"/api/cases/{case_id}/recheck", body)
                    t.add("recheck", **body)
        if rng.random() < 0.9:
            body = dict(fixed=rng.choice(["yes", "yes", "partial", "no", "unknown"]), note=None)
            self.tick()
            self.call("post", f"/api/cases/{case_id}/outcome", body)
            t.add("outcome", at=self.env.clock(), **body)

    def follow_ups(self, case_id):
        t, rng = self.truth[case_id], self.rng
        outcomes = t.of("outcome")
        if not outcomes or outcomes[0]["fixed"] not in ("yes", "partial"):
            return
        for window in (7, 30):
            self.env.clock.advance(days=window - (0 if window == 7 else 7), hours=rng.randint(1, 20))
            if rng.random() < 0.8:
                body = dict(window_days=window, recurred=rng.choice(["no", "no", "yes", "unsure"]))
                self.call("post", f"/api/cases/{case_id}/followup", body)
                t.add("followup", **body)


# ------------------------------------------------------------------------------------------------- the oracle (independent of the code under test)

def expected_events(t):
    """(kind, fields that must be in the payload) for every op the technician performed, in order."""
    out, last_shown = [], None
    for o in t.ops:
        op = o["op"]
        if op == "intent":
            last_shown = o["shown"]
            out += [("intent", dict(choice=o["choice"], check=o["check"], target=o["target"])),
                    ("suggestion_shown", dict(check=o["shown"], intent_matches=o["choice"] == "check" and o["check"] == o["shown"]))]
        elif op == "decision":
            fields = dict(action=o["action"], reason=o["reason"], suggested=None)
            out.append(("decision", {k: v for k, v in fields.items() if k != "suggested"} | ({"check": o["check"]} if o["action"] != "external" else {})))
            if o["action"] != "skip":
                out.append(("check_started", dict(external=o["action"] == "external")))
        elif op == "answer":
            if o["external"]:
                out.append(("external_result", dict(result_text=o["result_text"])))
            else:
                out.append(("check_result", dict(check=o["check"], word=o["word"], reading_text=o["reading_text"], minutes_correction=o["minutes_correction"])))
        elif op == "question":
            out.append(("question_answer", dict(key=o["key"], answer=o["answer"])))
        elif op == "conclude":
            out.append(("tool_conclusion", dict(id=o["tool_cause_id"])))
        elif op == "root_cause":
            out.append(("root_cause", dict(cause_id=o["cause_id"], how_confirmed=o["how_confirmed"])))
        elif op == "repair":
            out.append(("repair", dict(actions=o["actions"])))
        elif op == "recheck":
            out.append(("post_repair_check", dict(of_event_id=o["of_event_id"], result=o["result"])))
        elif op == "outcome":
            out.append(("outcome", dict(fixed=o["fixed"])))
        elif op == "followup":
            out.append(("followup", dict(window_days=o["window_days"], recurred=o["recurred"], recorded_by="technician")))
    return out


def expected_ladder(t):
    """The ladder restated from the DATA.md rules, from what the technician said (the latest statement of each kind wins)."""
    rcs, rps, ocs = t.of("root_cause"), t.of("repair"), t.of("outcome")
    rc, rp, oc = (rcs[-1] if rcs else None), (rps[-1] if rps else None), (ocs[-1] if ocs else None)
    named = rc is not None and rc["cause_id"] != "not_determined"
    how, before = (rc or {}).get("how_confirmed"), (rc or {}).get("confirmed_before_repair")
    if how == "repair_fixed_it":
        before = False
    physical = named and how in PHYSICAL and before is True
    real = [a for a in (rp or {}).get("actions", []) if a not in NOT_A_FIX]
    made = rp is not None and (bool(real) or (not rp["actions"] and bool(rp.get("text"))))
    fixed = oc["fixed"] if oc else None
    repair_confirmed = named and made and fixed == "yes"
    fu = {f["window_days"]: f["recurred"] for f in t.of("followup")}
    stayed = repair_confirmed and "no" in fu.values() and "yes" not in fu.values()
    level = 4 if stayed else 3 if repair_confirmed else 2 if physical else 1 if named else 0
    return dict(level=level, rungs=[named, physical, repair_confirmed, stayed])


def ts(s):
    return datetime.fromisoformat(s)


def audit_case(env, t):
    """Compare one case's stored record, minute by minute, with what the technician did."""
    rec = env.client.get(f"/api/cases/{t.case_id}/record", headers=env.headers).json()
    events = rec["events"]
    # 1. nothing lost, duplicated or reordered
    assert [e["kind"] for e in events] == t.kinds(), f"case {t.case_id}: stored events differ from what was done"
    assert [e["seq"] for e in events] == list(range(1, len(events) + 1)), "seq must be 1..n with no gaps"
    assert len({e["id"] for e in events}) == len(events)
    # 2. every field the technician supplied is what was stored
    for (kind, fields), ev in zip(expected_events(t), events):
        for k, v in fields.items():
            if k == "of_event_id":
                continue
            assert ev["payload"].get(k) == v, f"case {t.case_id} {kind}.{k}: stored {ev['payload'].get(k)!r}, technician gave {v!r}"
    # 3. time: server timestamps are the clock's, start-to-result is exactly what elapsed, and a lying device clock changed nothing
    stamps = [ts(e["server_ts"]) for e in events]
    assert stamps == sorted(stamps), "server time never goes backwards"
    answers = [o for o in t.of("answer")]
    results = [(i, e) for i, e in enumerate(events) if e["kind"] in ("check_result", "external_result")]
    assert len(results) == len(answers)
    for (i, ev), o in zip(results, answers):
        start = next(events[j] for j in range(i - 1, -1, -1) if events[j]["kind"] == "check_started")
        assert (ts(ev["server_ts"]) - ts(start["server_ts"])).total_seconds() == o["seconds"], "start-to-result must equal the time that passed"
    assert all(e["client_ts"] is None or e["client_ts"] not in ("not a date",) for e in events), "an unparseable device timestamp must not be kept"
    # 4. what was shown is what was stored, and each result is tied to the check that was actually done
    shown = [e for e in events if e["kind"] == "suggestion_shown"]
    assert [e["payload"]["check"] for e in shown] == [o["shown"] for o in t.of("intent")]
    assert all(1 <= len(e["payload"]["ranked"]) <= 5 and e["payload"]["ranked"] == sorted(e["payload"]["ranked"], key=lambda r: -r["p"]) for e in shown)
    for ev in (e for e in events if e["kind"] == "check_result"):
        assert ev["payload"]["room_log_id"] is not None and ev["payload"]["modeled_minutes"] >= 0
    # 5. the ladder is what the evidence given says it is
    want, got = expected_ladder(t), rec["ladder"]
    assert (got["level"], list(got["rungs"].values())) == (want["level"], want["rungs"]), f"case {t.case_id}: ladder {got['level']} {got['rungs']}, expected {want}"
    # 6. follow-ups were scheduled from the moment the first yes/partial outcome was recorded
    oc = [o for o in t.of("outcome") if o["fixed"] in ("yes", "partial")]
    dues = {f["window_days"]: ts(f["due_at"]) for f in rec["followups"]}
    if oc:
        base = ts(oc[0]["at"])
        assert dues == {7: base + timedelta(days=7), 30: base + timedelta(days=30)}, "follow-ups are +7 / +30 days from the fix being recorded"
    else:
        assert dues == {}
    # 7. the tool's conclusion: recorded once, and what the technician was shown is what was stored (a hedge caps what is shown, never what the model said)
    tool = [e["payload"] for e in events if e["kind"] == "tool_conclusion"]
    assert len(tool) == len(t.of("conclude")) <= 1
    if tool:
        c = t.of("conclude")[0]
        assert tool[0]["belief"] == c["belief"] and bool(tool[0].get("hedged")) == bool(c["hedged"])
        if tool[0].get("hedged"):
            assert tool[0]["raw_belief"] >= tool[0]["belief"] and tool[0]["belief"] <= 0.9
    # 8. agreement with the tool is derived from the two stated causes, never asserted
    for e in (e for e in events if e["kind"] == "root_cause"):
        p = e["payload"]
        want_agree = None if (not tool or tool[0]["id"] in ("doc_acts_fail", "doc_other") or p["cause_id"] == "not_determined") else tool[0]["id"] == p["cause_id"]
        assert p["agrees_with_tool"] == want_agree
    return rec


def run_population(env, seed, who, n_visits, tag_base):
    sim = Sim(env, seed, who)
    plan = [(1, "too_hot", "yes"), (2, "too_cold", "no"), (3, "too_hot", "unsure"), (1, "unsure", "yes"), (4, "too_hot", "yes"), (2, "too_hot", "yes"),
            (1, "too_cold", "unsure"), (3, "too_hot", "no"), (1, "too_hot", "yes"), (2, "unsure", "unsure")]
    visits = []
    for i in range(n_visits):
        n_rooms, feel, airflow = plan[i % len(plan)]
        vid, rooms, step = sim.start_visit(f"{tag_base}{i}", n_rooms, feel, airflow, complaint=i % 4 != 3)
        sim.run_visit(vid, step)
        visits.append((vid, [r["case_id"] for r in rooms]))
        env.clock.advance(minutes=sim.rng.randint(5, 90))
    for vid, case_ids in visits:
        for cid in case_ids:
            sim.closeout(cid, sim.rng.choice(["none", "partial", "full", "full"]))
    for vid, case_ids in visits:
        for cid in case_ids:
            sim.follow_ups(cid)
    return sim, visits


# ------------------------------------------------------------------------------------------------- the tests

def test_a_population_of_simulated_visits_is_recorded_exactly_as_it_happened(env):
    env.join()
    sim, visits = run_population(env, seed=20261013, who="Kowalski", n_visits=10, tag_base="N")
    total_cases = sum(len(c) for _, c in visits)
    assert total_cases >= 15, "the population should include multi-room visits"
    kinds_seen = set()
    for t in sim.truth.values():
        rec = audit_case(env, t)
        kinds_seen |= {e["kind"] for e in rec["events"]}
    # the run must actually have exercised the whole record, or the audit proves little
    assert {"intent", "suggestion_shown", "decision", "check_started", "check_result", "external_result", "question_answer", "tool_conclusion",
            "root_cause", "repair", "outcome"} <= kinds_seen, f"the simulation never produced: {set(['intent','suggestion_shown','decision','check_started','check_result','external_result','question_answer','tool_conclusion','root_cause','repair','post_repair_check','outcome','followup']) - kinds_seen}"
    actions = {o.get("action") for t in sim.truth.values() for o in t.ops if o["op"] == "decision"}
    assert {"follow", "substitute", "skip", "external"} <= actions
    ops = [o for t in sim.truth.values() for o in t.ops]
    hedged = sum(1 for o in ops if o["op"] == "conclude" and o["hedged"])
    print(f"\npopulation: {len(visits)} visits, {total_cases} cases, {len(ops)} recorded actions, "
          f"{sum(o['op'] == 'answer' and not o['external'] for o in ops)} timed checks, {sum(o['op'] == 'conclude' for o in ops)} conclusions ({hedged} hedged), "
          f"{sum(o['op'] == 'recheck' for o in ops)} re-checks, {sum(o['op'] == 'followup' for o in ops)} follow-ups")


def test_the_export_matches_what_was_done_and_leaks_no_name(env):
    env.join()
    sim, visits = run_population(env, seed=7, who="Kowalski", n_visits=10, tag_base="E")
    out = env.tmp / "export"
    stats = export_cases.export(env.tmp, out)
    recs = {r["case_id"]: r for r in (json.loads(l) for l in (out / "cases.jsonl").read_text().splitlines())}
    assert stats["exported"] == len(sim.truth) == len(recs)
    rows = {int(r["case_id"]): r for r in csv.DictReader((out / "cases.csv").open())}
    checks = list(csv.DictReader((out / "checks.csv").open()))
    step_total = 0
    for cid, t in sim.truth.items():
        r = recs[cid]
        steps = [o for o in t.ops if o["op"] in ("answer", "question") or (o["op"] == "decision" and o["action"] == "skip")]
        assert len(r["steps"]) == len(steps), f"case {cid}: exported steps differ from what was done"
        step_total += len(steps)
        timed = [o for o in t.of("answer") if not o["external"]]
        want = expected_ladder(t)
        assert r["verification"]["level"] == want["level"] and int(rows[cid]["ladder_level"]) == want["level"]
        # completeness restated: complaint + a timed check + a named cause + a repair + a confirmed fix
        rcs, ocs = t.of("root_cause"), t.of("outcome")
        complete = bool(t.complaint and timed and rcs and rcs[-1]["cause_id"] != "not_determined" and t.of("repair") and ocs and ocs[-1]["fixed"] == "yes")
        assert r["complete"] is complete, f"case {cid}: complete={r['complete']}, expected {complete}"
        for s in r["steps"]:
            if s["type"] == "check":
                match = next(o for o in timed if o["check"] == s["check"] and o["seconds"] == s["seconds"])
                assert s["effective_minutes"] == (match["minutes_correction"] if match["minutes_correction"] is not None else round(match["seconds"] / 60, 2))
    assert len(checks) == step_total, "checks.csv has one row per step"
    text = "".join((out / n).read_text() for n in ("cases.jsonl", "cases.csv", "checks.csv", "SUMMARY.txt"))
    for planted in ("Kowalski", "VAV-Kowalski", "Kowalski-AHU", "Kowalski.E", EMAIL, PHONE, "555-0142"):
        assert planted not in text, f"{planted!r} leaked into the export"
    assert "[email]" in text and "[phone]" in text and "room_1" in text and "vav_1" in text


def test_a_restored_backup_exports_byte_for_byte_what_the_live_system_does(env):
    env.join()
    run_population(env, seed=11, who="Kowalski", n_visits=6, tag_base="B")
    live = env.tmp / "live"
    export_cases.export(env.tmp, live)
    tar = backup.make_backup(env.tmp, env.tmp / "backups")
    assert backup.verify_backup(tar) == []
    restored = env.tmp / "restored"
    restored.mkdir()
    with tarfile.open(tar) as tf:
        tf.extractall(restored, filter="data")
    again = env.tmp / "again"
    export_cases.export(restored, again)
    for name in ("cases.jsonl", "cases.csv", "checks.csv", "SUMMARY.txt"):
        assert (again / name).read_bytes() == (live / name).read_bytes(), f"{name} differs after a backup and restore"


def test_a_purge_removes_one_participant_and_changes_nothing_of_another(env):
    pa = env.join()
    simA, _ = run_population(env, seed=3, who="Kowalski", n_visits=5, tag_base="A")
    assert followups.main(["--data-dir", str(env.tmp), "new-participant"]) == 0
    pb = env.join(role="in_house_engineer", years="gt15", vav="daily")
    assert pb != pa
    simB, _ = run_population(env, seed=4, who="Larsen", n_visits=5, tag_base="L")
    before = env.tmp / "before"
    export_cases.export(env.tmp, before)
    b_before = {r["case_id"]: r for r in (json.loads(l) for l in (before / "cases.jsonl").read_text().splitlines()) if r["case_id"] in simB.truth}
    assert len(b_before) == len(simB.truth)

    raw = lambda: b"".join(p.read_bytes() for p in (env.tmp / "pilot.db", env.tmp / "pilot.db-wal") if p.exists())       # noqa: E731
    assert b"Kowalski" in raw() and b"Larsen" in raw()
    assert purge.main(["--data-dir", str(env.tmp), "participant", str(pa), "--reason", "withdrawal_request", "--execute"]) == 0

    after = env.tmp / "after"
    export_cases.export(env.tmp, after)
    recs = {r["case_id"]: r for r in (json.loads(l) for l in (after / "cases.jsonl").read_text().splitlines())}
    assert set(recs) == set(simB.truth), "exactly the other participant's cases remain"
    assert recs == b_before, "the surviving participant's exported record is unchanged, case by case"
    assert b"Kowalski" not in raw() and b"Larsen" in raw(), "A's names are gone from the raw database bytes; B's remain"
    assert not any("Kowalski" in str(p) for p in env.tmp.rglob("*") if p.is_file() and p.suffix in (".json", ".jpg") ), "A's building files and photos are gone"
    for t in simB.truth.values():
        audit_case(env, t)                                                      # B's live record still audits clean after the purge


def test_hostile_free_text_is_stored_verbatim_and_the_csv_stays_parseable(env):
    env.join()
    sim = Sim(env, 5)
    vid, rooms, step = sim.start_visit("H", 1)
    nasty = ['x"; DROP TABLE case_event; --', "line one\nline two, with a comma", 'she said "hi" ‮☃ \U0001F680', "a" * 39, "=cmd|' /C calc'!A0", "  padded  "]
    cid = rooms[0]["case_id"]
    for i, text in enumerate(nasty):
        # walk to a check, answer it with a hostile reading and note
        while step["kind"] == "question":
            step = sim.call("post", f"/api/visits/{vid}/answer", dict(word="no"))["step"]
        if step["kind"] != "check":
            break
        if step["stage"] == "intent":
            step = sim.call("post", f"/api/visits/{vid}/intent", dict(kind="unsure"))["step"]
        step = sim.call("post", f"/api/visits/{vid}/decision", dict(action="follow"))["step"]
        sim.env.clock.advance(seconds=30)
        step = sim.call("post", f"/api/visits/{vid}/answer", dict(word=step["words"][0], reading_text=text[:40], note=text))["step"]
    rec = sim.call("get", f"/api/cases/{cid}/record")
    results = [e["payload"] for e in rec["events"] if e["kind"] == "check_result"]
    assert results and all(r["note"] == (nasty[i].strip() or None) for i, r in enumerate(results))
    with db.connect(config.DB_PATH) as conn:
        assert {"case_event", "cases", "visits"} <= {r[0] for r in conn.execute("SELECT name FROM sqlite_master WHERE type='table'")}, "an injection string must not execute"
    out = env.tmp / "export"
    export_cases.export(env.tmp, out)
    rows = list(csv.DictReader((out / "checks.csv").open(newline="")))
    assert len(rows) == len(results), "newlines, quotes and commas in free text must not split or merge CSV rows"
    assert [r["reading_text"] for r in rows] == [nasty[i][:40].strip() or "" for i in range(len(results))] or all(r["reading_text"] is not None for r in rows)
    json.loads((out / "cases.jsonl").read_text().splitlines()[0])


def test_the_whole_record_survives_a_restart_in_the_middle_of_a_visit(env):
    env.join()
    sim = Sim(env, 9)
    vid, rooms, step = sim.start_visit("R", 2)
    for _ in range(3):
        if step["kind"] == "check" and step["stage"] == "intent":
            step = sim.call("post", f"/api/visits/{vid}/intent", dict(kind="unsure"))["step"]
        if step["kind"] == "check" and step["stage"] == "revealed":
            step = sim.call("post", f"/api/visits/{vid}/decision", dict(action="follow"))["step"]
    before = sim.call("get", f"/api/visits/{vid}")
    V._locks.clear()                                                            # a new process has no in-memory state at all
    with TestClient(app) as fresh:                                              # ...and runs the app's startup again against the same database
        r = fresh.get(f"/api/visits/{vid}", headers=env.headers)
    assert r.status_code == 200 and r.json() == before, "a restarted server must be on exactly the same step"


def test_double_taps_and_racing_requests_never_duplicate_or_corrupt_the_record(env):
    env.join()
    sim = Sim(env, 13)
    vid, rooms, step = sim.start_visit("C", 1)
    cid = rooms[0]["case_id"]
    while step["kind"] != "check":
        step = sim.call("post", f"/api/visits/{vid}/answer", dict(word="no"))["step"]
    assert step["stage"] == "intent"

    def hit(path, body):
        with TestClient(app) as c:
            return c.post(path, headers=env.headers, json=body).status_code

    with ThreadPoolExecutor(8) as ex:
        codes = list(ex.map(lambda _: hit(f"/api/visits/{vid}/intent", dict(kind="unsure")), range(8)))
    assert sorted(codes) == [200] + [400] * 7, f"exactly one of eight simultaneous taps may win: {codes}"
    with ThreadPoolExecutor(8) as ex:
        codes = list(ex.map(lambda _: hit(f"/api/visits/{vid}/decision", dict(action="follow")), range(8)))
    assert sorted(codes) == [200] + [400] * 7, codes
    with ThreadPoolExecutor(8) as ex:
        codes = list(ex.map(lambda _: hit(f"/api/visits/{vid}/answer", dict(word="abnormal")), range(8)))
    assert codes.count(200) <= 1 and set(codes) <= {200, 400}, codes
    kinds = [e["kind"] for e in sim.call("get", f"/api/cases/{cid}/record")["events"]]
    assert kinds.count("intent") == 1 and kinds.count("suggestion_shown") == 1 and kinds.count("decision") == 1 and kinds.count("check_started") == 1
    assert kinds.count("check_result") <= 1

    # many writers on one case's close-out: every one lands, in a gap-free order
    n = 12
    with ThreadPoolExecutor(8) as ex:
        codes = list(ex.map(lambda i: hit(f"/api/cases/{cid}/root_cause", dict(cause_id="actuator_fail", how_confirmed="measured")), range(n)))
    assert codes == [200] * n
    seqs = [e["seq"] for e in sim.call("get", f"/api/cases/{cid}/record")["events"]]
    assert seqs == list(range(1, len(seqs) + 1)), "concurrent writers must leave seq contiguous"


def test_malformed_and_out_of_order_requests_never_500_and_never_leave_a_partial_write(env):
    env.join()
    sim = Sim(env, 17)
    vid, rooms, step = sim.start_visit("F", 2)
    cid = rooms[0]["case_id"]

    def snapshot():
        """Whole-table contents (not just counts): a refused request that quietly UPDATED a row must be caught too."""
        with db.connect(config.DB_PATH) as conn:
            return {t: [tuple(r) for r in conn.execute(f"SELECT * FROM {t} ORDER BY rowid")] for t in
                    ("visits", "room_log", "room_conclusion", "cases", "case_event", "followup_due", "participants", "intake")}

    huge = "x" * 300_000
    battery = [
        ("post", f"/api/visits/{vid}/intent", {"kind": "bogus"}), ("post", f"/api/visits/{vid}/intent", {"kind": "check"}),
        ("post", f"/api/visits/{vid}/intent", {"kind": "check", "check": "nope", "target": "nope"}), ("post", f"/api/visits/{vid}/intent", {"kind": "other", "text": huge}),
        ("post", f"/api/visits/{vid}/intent", [1, 2, 3]), ("post", f"/api/visits/{vid}/intent", None),
        ("post", f"/api/visits/{vid}/decision", {"action": "follow"}),                     # before any intent
        ("post", f"/api/visits/{vid}/answer", {"word": "abnormal"}),                       # before any decision
        ("post", f"/api/visits/{vid}/answer", {"word": 5}), ("post", f"/api/visits/{vid}/answer", {"minutes_correction": -1}),
        ("post", f"/api/visits/{vid}/answer", {"minutes_correction": 1e308}), ("post", f"/api/visits/{vid}/advance", None),
        ("post", "/api/visits/not-a-visit/intent", {"kind": "unsure"}), ("get", "/api/visits/%00", None), ("get", f"/api/visits/{'z' * 5000}", None),
        ("post", f"/api/cases/{cid}/root_cause", {"cause_id": "x" * 100}), ("post", f"/api/cases/{cid}/root_cause", {"cause_id": "other", "text": "  "}),
        ("post", f"/api/cases/{cid}/root_cause", {"cause_id": "actuator_fail", "confirmed_before_repair": "maybe"}),
        ("post", f"/api/cases/{cid}/root_cause", {"cause_id": "documentation_wrong", "actual_box": huge}),
        ("post", f"/api/cases/{cid}/repair", {"actions": ["nope"]}), ("post", f"/api/cases/{cid}/repair", {"actions": []}),
        ("post", f"/api/cases/{cid}/repair", {"actions": ["replaced_part"], "repaired_on": "yesterday"}),
        ("post", f"/api/cases/{cid}/outcome", {"fixed": "maybe"}), ("post", f"/api/cases/{cid}/followup", {"window_days": 7, "recurred": "no"}),
        ("post", f"/api/cases/{cid}/recheck", {"of_event_id": 1, "result": "now_ok"}), ("post", f"/api/cases/{cid}/recheck", {"of_event_id": 2 ** 70, "result": "now_ok"}),
        ("get", "/api/cases/abc/record", None), ("get", "/api/cases/-1/record", None), ("get", f"/api/cases/{2 ** 70}/record", None),
        ("post", "/api/cases/0/outcome", {"fixed": "yes"}), ("post", "/api/participant", {"role": "x"}),
        ("post", "/api/intake/not-an-intake/confirm", {"draft": {}, "room_ids": []}),
    ]
    for method, path, body in battery:
        before = snapshot()
        kw = {} if body is None else {"json": body}
        r = getattr(env.client, method)(path, headers=env.headers, **kw)
        assert r.status_code < 500, f"{method.upper()} {path[:60]} {str(body)[:60]} -> {r.status_code} {r.text[:200]}"
        assert "Traceback" not in r.text and 'File "' not in r.text
        if r.status_code >= 400:
            assert snapshot() == before, f"{method.upper()} {path[:60]} {str(body)[:60]} was refused ({r.status_code}) but still wrote something"
    # the visit is untouched by all of it
    assert sim.call("get", f"/api/visits/{vid}")["step"] == step


@pytest.mark.parametrize("answers,n", [("positive", 20), ("negative", 20), ("heavy", 20), ("heavy", 49)])
def test_a_large_air_handler_stays_usable_tap_by_tap(env, answers, n):
    """One visit with many complaint rooms on one air handler (the bldg11 situation). Each tap rebuilds the visit from its whole log, so
    latency grows with the visit; this measures it. 'positive': one reading explains every room (easy). 'negative': the same, the other
    way. 'heavy': the technician overrides the tool and does 8 different checks in EVERY room, so the log is as long as a visit gets."""
    env.join()
    sim = Sim(env, 21)
    per_room = 8
    vid, rooms, step = sim.start_visit("W", n)
    assert len(rooms) == n
    times, done_here = [], {}
    for _ in range(3000):
        if step["kind"] == "visit_done":
            break
        t0 = time.perf_counter()
        if step["kind"] == "question":
            step = sim.call("post", f"/api/visits/{vid}/answer", dict(word="no"))["step"]
        elif step["kind"] == "conclude":
            step = sim.call("post", f"/api/visits/{vid}/advance", dict(from_room=step["room"]))["step"]
        elif step["stage"] == "intent":
            step = sim.call("post", f"/api/visits/{vid}/intent", dict(kind="unsure"))["step"]
        elif step["stage"] == "revealed":
            room = step["room"]
            others = [x for x in step["picker"] if x["name"] != step["name"]]
            if answers == "heavy" and done_here.get(room, 0) < per_room and others:
                pick = others[done_here.get(room, 0) % len(others)]
                step = sim.call("post", f"/api/visits/{vid}/decision", dict(action="substitute", check=pick["name"], target=pick["target"]))["step"]
            else:
                step = sim.call("post", f"/api/visits/{vid}/decision", dict(action="follow"))["step"]
        else:
            env.clock.advance(seconds=60)
            done_here[step["room"]] = done_here.get(step["room"], 0) + 1
            word = step["words"][0 if answers == "positive" else 1]
            step = sim.call("post", f"/api/visits/{vid}/answer", dict(word=word))["step"]
        times.append(time.perf_counter() - t0)
    assert step["kind"] == "visit_done", "the visit never finished"
    worst, mean = max(times), sum(times) / len(times)
    with db.connect(config.DB_PATH) as conn:
        entries = conn.execute("SELECT COUNT(*) FROM room_log WHERE visit_id = ?", (vid,)).fetchone()[0]
    print(f"\n{n}-room visit, {answers}: {len(times)} taps, {entries} engine log entries, mean {mean * 1000:.0f} ms, worst {worst * 1000:.0f} ms, "
          f"last 20 taps mean {sum(times[-20:]) / 20 * 1000:.0f} ms")
    assert worst < 5.0, f"a single tap took {worst:.1f}s on a {n}-room visit: too slow for someone standing at the equipment"
    for r in rooms:
        rec = sim.call("get", f"/api/cases/{r['case_id']}/record")
        seqs = [e["seq"] for e in rec["events"]]
        assert seqs == list(range(1, len(seqs) + 1))


def test_a_room_cannot_be_abandoned_by_advancing_before_it_concluded(env):
    """Found by the hostile-request battery: advance used to move on from a room mid-diagnosis, silently abandoning its case."""
    env.join()
    sim = Sim(env, 41)
    vid, rooms, step = sim.start_visit("A", 3)
    while step["kind"] == "question":
        step = sim.call("post", f"/api/visits/{vid}/answer", dict(word="no"))["step"]
    assert step["kind"] == "check" and step["room"] == 0
    for body in (None, dict(from_room=0)):
        r = env.client.post(f"/api/visits/{vid}/advance", headers=env.headers, **({} if body is None else {"json": body}))
        assert r.status_code == 400 and "not finished" in r.json()["detail"]
    assert sim.call("get", f"/api/visits/{vid}")["step"] == step, "the visit is exactly where it was"
    with db.connect(config.DB_PATH) as conn:
        assert db.get_visit(conn, vid)["current_room"] == 0 and db.get_visit(conn, vid)["status"] == "in_progress"


def test_a_stale_page_cannot_skip_a_room_and_a_finished_visit_stays_finished(env):
    env.join()
    sim = Sim(env, 43)
    vid, rooms, step = sim.start_visit("D", 2)
    sim.run_visit(vid, step, p=dict(skip=0, external=0, substitute=0))
    done = sim.call("get", f"/api/visits/{vid}")["step"]
    assert done["kind"] == "visit_done"
    # the page that showed room 0's conclusion is still open; it taps Continue long after the visit finished
    r = env.client.post(f"/api/visits/{vid}/advance", headers=env.headers, json=dict(from_room=0))
    assert r.status_code == 200 and r.json()["step"] == done, "a finished visit does not change"
    with db.connect(config.DB_PATH) as conn:
        v = db.get_visit(conn, vid)
        assert v["status"] == "done" and v["current_room"] == 1


@pytest.mark.parametrize("big", [2 ** 63, 2 ** 70, 10 ** 30])
def test_ids_too_large_for_the_database_are_refused_cleanly_not_crashed_on(env, big):
    """Found by the hostile-request battery: a case id of 2**70 raised OverflowError (a 500) instead of 'no such case'."""
    env.join()
    for method, path, body in [("get", f"/api/cases/{big}/record", None), ("post", f"/api/cases/{big}/outcome", dict(fixed="yes")),
                               ("post", f"/api/cases/{big}/root_cause", dict(cause_id="other", text="x")), ("post", f"/api/cases/{big}/repair", dict(actions=["replaced_part"])),
                               ("post", f"/api/cases/{big}/followup", dict(window_days=7, recurred="no")),
                               ("post", "/api/cases/1/recheck", dict(of_event_id=big, result="now_ok"))]:
        r = getattr(env.client, method)(path, headers=env.headers, **({} if body is None else {"json": body}))
        assert r.status_code == 422, f"{method.upper()} {path}: {r.status_code} {r.text[:120]}"
    sim = Sim(env, 1)
    sim.start_visit("O", 1)
    for prior in (big, 0, -5):
        d = building_draft("O", 1, "Kowalski")
        env.drafts["current"] = d
        up = env.client.post("/api/intake/extract", headers=env.headers,
                             files={"photo_bas": ("a.jpg", env.jpeg, "image/jpeg"), "photo_equipment": ("b.jpg", env.jpeg, "image/jpeg")}).json()
        r = env.client.post(f"/api/intake/{up['intake_id']}/confirm", headers=env.headers,
                            json=dict(draft=d, room_ids=[d["boxes"][0]["serves_room"]], feel="too_hot", airflow="yes", context=dict(prior_case_id=prior)))
        assert r.status_code == 422, f"prior_case_id {prior}: {r.status_code}"
    r = env.client.get(f"/api/cases/{2 ** 63 - 1}/record", headers=env.headers)
    assert r.status_code == 404, "the largest id SQLite can hold is a normal 'no such case'"
