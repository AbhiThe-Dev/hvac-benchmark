"""Tests for Addendum 33: the language-model technician's terminal, the shared answer table, the sample, the scoring and the analysis. Simulation only."""
import importlib.util
import json
from pathlib import Path

import numpy as np
import pytest

from docmismatch.troubleshoot.v2 import study_llm as L
from docmismatch.troubleshoot.v2 import world2 as W

SCRIPT = Path(__file__).resolve().parents[1] / "scripts" / "77_llm_technician.py"


@pytest.fixture(scope="module")
def world():
    return L.world()


def _event(events, kind, lo=1, hi=8):
    return next(e for e in events if e.kind == kind and lo <= e.n <= hi)


def _script_module():
    spec = importlib.util.spec_from_file_location("s77", SCRIPT)
    m = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(m)
    return m


# ---------------------------------------------------------------------------------------------- the answer table
def test_table_oracle_is_deterministic_and_order_free(world):
    cases, wp, events = world
    ev = _event(events, "multi")
    cs = [cases[("T3", r)] for r in ev.rooms]
    qs = [(i, ck) for i, c in enumerate(cs) for ck in c.checks if ck.subject != "ahu"]
    a = [L.TableOracle(ev, wp.rel_a).ask_room(i, ck, cs[i].doc) for i, ck in qs]
    o = L.TableOracle(ev, wp.rel_a)
    b = [o.ask_room(i, ck, cs[i].doc) for i, ck in reversed(qs)][::-1]
    assert a == b
    o2 = L.TableOracle(ev, wp.rel_a)
    assert [o2.ask_room(i, ck, cs[i].doc) for i, ck in qs] == a                       # a second oracle, the same answers


def test_table_oracle_different_events_and_keys_differ(world):
    cases, wp, events = world
    ck = cases[("T3", 0)].checks[8]
    draws = {L.TableOracle(e, wp.rel_a)._u(f"room|0|{ck.name}|x") for e in events[:40]}
    assert len(draws) == 40
    o = L.TableOracle(events[0], wp.rel_a)
    assert o._u("a") != o._u("b")


def test_table_oracle_answers_follow_the_probabilities(world):
    cases, wp, events = world
    ev = events[0]
    o = L.TableOracle(ev, wp.rel_a)
    ck = next(c for c in cases[("T3", ev.rooms[0])].checks if c.name == "bas_airflow")
    p = o.p_room(0, ck.name, cases[("T3", ev.rooms[0])].doc)
    us = np.array([o._u(f"room|{k}|bas_airflow|t") for k in range(4000)])
    assert abs((us < p).mean() - p) < 0.03


# ---------------------------------------------------------------------------------------------- the sample
def test_sample_is_stratified_eligible_and_reproducible(world):
    _, _, events = world
    v1, v2 = L.sample_visits(events), L.sample_visits(events)
    assert v1 == v2 and len(v1) == 3 * L.N_PER_KIND
    for k in L.KINDS:
        sel = [v for v in v1 if v["kind"] == k]
        assert len(sel) == L.N_PER_KIND and len({v["event"] for v in sel}) == L.N_PER_KIND
        assert all(events[v["event"]].kind == k and events[v["event"]].n <= L.MAX_COMPLAINTS for v in sel)
    assert len({v["id"] for v in v1}) == len(v1)
    assert sorted(v["id"] for v in v1) == [f"v{k:02d}" for k in range(1, len(v1) + 1)]
    assert L.sample_visits(events, 4) != v1


def test_kind_shares_sum_to_one_and_use_eligible_events(world):
    _, _, events = world
    s = L.kind_shares(events)
    assert abs(sum(s.values()) - 1) < 1e-12 and set(s) == set(L.KINDS)
    el = [e for e in events if e.n <= L.MAX_COMPLAINTS]
    assert abs(s["shared"] - sum(e.kind == "shared" for e in el) / len(el)) < 1e-12


# ---------------------------------------------------------------------------------------------- the terminal
def test_do_charges_the_accountant_and_tracks_location(world):
    cases, wp, events = world
    ev = _event(events, "single")
    v = L.Visit(ev, "T3", cases, wp)
    r = v.do("bas_static", 1)
    assert r["minutes"] == 2.0 and v.minutes == 2.0 and v.at == "bas" and r["first"]
    r2 = v.do("bas_controller", 1)
    assert r2["minutes"] == 2.0 and not r2["first"]                                    # already in the control system: no walking
    r3 = v.do("power_24vac", 1)
    assert r3["minutes"] == 10.0 and v.at == v.cases[0].doc                            # 6 to get there + 4
    assert v.minutes == 14.0 and v.charged == 3


def test_an_air_handler_reading_is_charged_once_for_the_visit(world):
    cases, wp, events = world
    ev = next(e for e in events if e.kind == "shared" and 3 <= e.n <= 6)
    v = L.Visit(ev, "T3", cases, wp)
    same = [i for i, c in enumerate(v.cases) if c.ahu == v.cases[0].ahu]
    assert len(same) >= 2
    a = v.do("bas_ahu_fan", 1)
    b = v.do("bas_ahu_fan", same[1] + 1)
    assert b["repeat"] and b["minutes"] == 0.0 and b["answer"] == a["answer"] and v.charged == 1 and v.minutes == a["minutes"]
    assert L.checks_text(v, same[1] + 1).count("[already done]") >= 1


def test_refusals_charge_nothing(world):
    cases, wp, events = world
    ev = _event(events, "single")
    v = L.Visit(ev, "T2", cases, wp)
    for bad in (lambda: v.do("bas_static", 1), lambda: v.do("nope", 1), lambda: v.do("power_24vac", 2), lambda: v.do("power_24vac", 1, "VAV-99"),
                lambda: v.do("static_at_box", 1, "VAV-99"), lambda: v.conclude(1, "banana", "confident"), lambda: v.conclude(1, "ok", "confident"),
                lambda: v.conclude(1, "actuator_fail", "sure"), lambda: v.finish()):
        with pytest.raises(L.VisitError):
            bad()
    assert v.minutes == 0.0 and v.charged == 0 and not v.log and v.commands == []
    v.do("power_24vac", 1)
    with pytest.raises(L.VisitError, match="already done"):
        v.do("power_24vac", 1)


def test_box_checks_take_a_target_and_others_do_not(world):
    cases, wp, events = world
    ev = _event(events, "single")
    v = L.Visit(ev, "T3", cases, wp)
    alt = next(c for c in v.cases[0].candidates if c != v.cases[0].doc)
    assert v.do("override_diffuser", 1, alt)["minutes"] > 0
    assert v.do("override_diffuser", 1)["minutes"] > 0                                 # the documented box is another target
    with pytest.raises(L.VisitError):
        v.do("confirm_acts", 1, alt)                                                   # doc_only


def test_conclude_parsing_and_finish(world):
    cases, wp, events = world
    ev = _event(events, "single")
    v = L.Visit(ev, "T3", cases, wp)
    alt = next(c for c in v.cases[0].candidates if c != v.cases[0].doc)
    for text, want in (("actuator_fail", ("actuator_fail",)), ("unlisted", ("unlisted",)), (f"wrong:{alt}", ("wrong", alt)), ("ahu_fan_off", ("ahu_fan_off",))):
        v.conclude(1, text, "unsure")
        assert v.concl[0][0] == want and v.concl[0][1] is False
    with pytest.raises(L.VisitError):
        v.conclude(1, f"wrong:{v.cases[0].doc}", "confident")                          # the documented box is not an alternative
    v.conclude(1, "low_static", "confident")
    v.finish()
    assert v.finished and v.result()["finished"] and v.result()["concluded"] == [True] and v.result()["guess"] == [("low_static",)]
    with pytest.raises(L.VisitError):
        v.do("power_24vac", 1)


def test_the_check_cap_stops_a_visit(world):
    cases, wp, events = world
    ev = _event(events, "single")
    v = L.Visit(ev, "T3", cases, wp)
    names = [c.name for c in v.cases[0].checks if c.is_reading and v.minutes_now(0, c) is not None]          # every reading this box allows (13+ of them at T3)
    assert len(names) > 12
    n = 0
    with pytest.raises(L.VisitError, match="limit"):
        for name in names:
            v.do(name, 1)
            n += 1
    assert v.charged == v.cap == 12 and n == 12


def test_unfinished_visit_scores_unconcluded_complaints_wrong(world):
    cases, wp, events = world
    ev = _event(events, "multi", 2, 4)
    v = L.Visit(ev, "T3", cases, wp)
    v.conclude(1, ev.causes[0][0] if ev.causes[0][0] != "wrong" else "unlisted", "confident")
    rec = L.record(v.result(), ev)
    assert rec["abandoned"] and rec["concluded"] == 1 and rec["correct"] <= 1 and rec["n"] == ev.n


def test_replay_reproduces_a_visit_exactly(world):
    cases, wp, events = world
    ev = _event(events, "shared", 3, 6)
    v = L.Visit(ev, "T3", cases, wp)
    v.do("bas_ahu_fan", 1)
    v.do("bas_static", 1)
    v.do("power_24vac", 2)
    v.conclude(1, "low_static", "confident")
    w = L.Visit(ev, "T3", cases, wp).replay(v.commands)
    assert w.minutes == v.minutes and w.log == v.log and w.concl == v.concl and w.at == v.at


def test_replay_of_policies_matches_their_own_minutes(world):
    cases, wp, events = world
    n = 0
    for tier in L.TIERS:
        for pol in ("fast_parent", L.ROUTINE, "tool_joint2"):
            for e in [x for x in events[:25] if x.n <= L.MAX_COMPLAINTS]:
                m, c, pm, pc = L.replay_policy(e, tier, cases, wp, pol)
                assert abs(m - pm) < 1e-9 and c == pc, (tier, pol, e.i)
                n += 1
    assert n > 100


def test_brief_shows_what_the_tier_allows_and_no_hidden_numbers(world):
    cases, wp, events = world
    ev = _event(events, "single")
    t2, t3 = L.Visit(ev, "T2", cases, wp), L.Visit(ev, "T3", cases, wp)
    b2, b3 = L.brief_text(t2, "S01", cases), L.brief_text(t3, "S02", cases)
    assert "bas_static" not in b2 and "NO access to the building control system" in b2
    assert "bas_static" in b3 and "point map exists" in b3
    assert "design data on file" in b2 and "design data on file" in b3
    for hidden in ("0.95", "prior", "false alarm", "false-alarm", "detects", "P(abnormal)", "probabilit"):
        assert hidden not in b2 and hidden not in b3, hidden
    assert "actuator_fail" in b3 and "unlisted" in b3 and "wrong:<box>" in b3
    assert f"{t3.cap} checks" in b3
    assert "shared-cause" not in b3 and "multi" not in b3 and "kind" not in b3         # the kind of visit is never named


# ---------------------------------------------------------------------------------------------- the launcher script
def test_terminal_persists_state_and_reports_errors(tmp_path, world, capsys):
    s = _script_module()
    s.prepare(tmp_path, 1)
    reg = json.loads((tmp_path / "registry.json").read_text())
    sid = next(k for k, r in reg.items() if r["tier"] == "T3")
    s.terminal(tmp_path, sid, ["brief"])
    assert "SESSION" in capsys.readouterr().out
    s.terminal(tmp_path, sid, ["do", "power_24vac", "1"])
    assert "ANSWER" in capsys.readouterr().out
    s.terminal(tmp_path, sid, ["do", "power_24vac", "1"])
    assert "ERROR" in capsys.readouterr().out
    s.terminal(tmp_path, sid, ["do", "power_24vac", "x"])
    assert "ERROR" in capsys.readouterr().out
    s.terminal(tmp_path, "S99", ["brief"])
    assert "unknown session" in capsys.readouterr().out
    st = json.loads((tmp_path / "state" / f"{sid}.json").read_text())
    assert len(st) == 1 and st[0][0] == "do"
    s.terminal(tmp_path, sid, ["status"])
    assert "Minutes so far" in capsys.readouterr().out
    assert len((tmp_path / "state" / f"{sid}.log").read_text().splitlines()) == 5
    assert (tmp_path / "tech").exists() and (tmp_path / "tech").stat().st_mode & 0o100


def test_prepare_registry_hides_kind_and_is_complete(tmp_path):
    s = _script_module()
    s.prepare(tmp_path, 2)
    reg = json.loads((tmp_path / "registry.json").read_text())
    assert len(reg) == 12 and sorted(reg) == [f"S{k:02d}" for k in range(1, 13)]
    assert {(r["visit"], r["tier"]) for r in reg.values()} == {(f"v{k:02d}", t) for k in range(1, 7) for t in L.TIERS}
    part = json.loads((tmp_path / "partners.json").read_text())
    assert len(part) == 6 * 2 * len(L.PARTNERS)
    assert all(set(r) >= {"minutes", "checks", "correct", "n", "wc", "acc"} for r in part.values())


# ---------------------------------------------------------------------------------------------- analysis
def _synthetic(visits, llm_min, rout_min, llm_acc=0.6, rout_acc=0.8):
    recs = {}
    for v in visits:
        for t in L.TIERS:
            for pol, m, a in (("llm", llm_min, llm_acc), (L.ROUTINE, rout_min, rout_acc), ("tool_joint2", rout_min, rout_acc), ("fast_parent", 100.0, 0.5)):
                n = 2
                recs[(v["id"], t, pol)] = dict(minutes=m + (hash(v["id"]) % 7), checks=8.0, correct=round(a * n), wc=0, concluded=n, n=n, acc=a, wcr=0.0, conc=1.0, first_ahu=(pol == "llm"), abandoned=False)
    return recs


def test_analysis_labels_a_clear_gap_and_a_null(world):
    _, _, events = world
    visits = L.sample_visits(events)
    shares = L.kind_shares(events)
    an = L.analyze(_synthetic(visits, 150.0, 100.0), visits, shares)
    e = an["cmp"][("T2", "P", "all")]
    assert e["time"] == "SLOWER" and e["acc"] == "LESS" and e["label"] == "WORSE" and 45 < e["d_min"] < 55
    assert L.decision(an).count("THE ROUTINE IS FASTER") == 2
    an0 = L.analyze(_synthetic(visits, 100.0, 100.0, 0.8, 0.8), visits, shares)
    assert an0["cmp"][("T3", "P", "all")]["time"] == "SAME" and "NO CLEAR SPEED DIFFERENCE" in L.decision(an0)
    an1 = L.analyze(_synthetic(visits, 60.0, 100.0, 0.8, 0.8), visits, shares)
    assert "THE LLM TECHNICIAN IS FASTER" in L.decision(an1)


def test_weighted_estimate_uses_the_kind_shares(world):
    _, _, events = world
    visits = L.sample_visits(events)
    shares = dict(single=0.5, multi=0.3, shared=0.2)
    recs = {}
    per = dict(single=10.0, multi=20.0, shared=50.0)
    for v in visits:
        for t in L.TIERS:
            for pol in ("llm",) + L.PARTNERS:
                recs[(v["id"], t, pol)] = dict(minutes=per[v["kind"]], checks=1.0, correct=1, wc=0, concluded=1, n=1, acc=1.0, wcr=0.0, conc=1.0, first_ahu=False, abandoned=False)
    an = L.analyze(recs, visits, shares)
    assert abs(an["sum"][("T2", "llm", "all")]["minutes"] - (0.5 * 10 + 0.3 * 20 + 0.2 * 50)) < 1e-9
    assert an["sum"][("T2", "llm", "shared")]["minutes"] == 50.0 and an["sum"][("T2", "llm", "shared")]["n"] == L.N_PER_KIND
    assert an["cmp"][("T2", "P", "all")]["d_min"] == 0.0 and an["cmp"][("T2", "P", "all")]["label"] == "NEITHER"


def test_predictions_are_strict_on_their_thresholds(world):
    _, _, events = world
    visits = L.sample_visits(events)
    an = L.analyze(_synthetic(visits, 150.0, 100.0), visits, L.kind_shares(events))
    p = L.predictions(an)
    assert set(p) == {f"P{k}" for k in range(1, 9)}
    assert p["P1"][0] and not p["P2"][0] and p["P3"][0] and p["P5"][0] and p["P8"][0]


# ---------------------------------------------------------------------------------------------- the audit
def test_audit_flags_anything_but_the_launcher():
    ok = [dict(name="Bash", input=dict(command="/x/tech S01 do bas_static 1")), dict(name="Bash", input=dict(command="/x/tech S01 brief"))]
    assert L.audit_tool_calls(ok, "/x/tech") == []
    assert L.audit_tool_calls(ok + [dict(name="SubagentHandback", input=dict(message="DONE"))], "/x/tech") == []
    bad = [dict(name="Read", input=dict(file_path="/x")), dict(name="Bash", input=dict(command="cat /x/state/S01.json")), dict(name="Bash", input=dict(command="/x/tech S01 brief; ls")),
           dict(name="Bash", input=dict(command="/x/tech S01 brief | head")), dict(name="Bash", input=dict(command="ls /x/tech"))]
    assert len(L.audit_tool_calls(bad, "/x/tech")) == 5


def test_first_check_detection():
    assert L.first_check_is_ahu([(0, "bas_static", "VAV-1", "normal")]) and not L.first_check_is_ahu([(0, "power_24vac", "VAV-1", "normal")])
    assert L.first_check_is_ahu([("ahu", "AHU-1", "bas_ahu_fan", "AHU-1", "normal")]) and L.first_check_is_ahu([("group", "AHU-0", "ahu_gauge", "VAV-1", "normal")])
    assert not L.first_check_is_ahu([])


def test_tool_calls_are_found_wherever_they_are_nested(tmp_path):
    p = tmp_path / "t.jsonl"
    lines = [json.dumps({"type": "assistant", "message": {"content": [{"type": "text", "text": "hi"}, {"type": "tool_use", "name": "Bash", "input": {"command": "/x/tech S01 brief"}}]}}),
             "", json.dumps({"type": "user", "message": {"content": [{"type": "tool_result", "content": "..."}]}}),
             json.dumps({"deep": {"a": [{"type": "tool_use", "name": "Read", "input": {"file_path": "/etc/hosts"}}]}}), "not json"]
    p.write_text("\n".join(lines))
    calls = L.tool_calls_in_transcript(p)
    assert [c["name"] for c in calls] == ["Bash", "Read", "UNREADABLE-LINE"]
    assert len(L.audit_tool_calls(calls, "/x/tech S01 ")) == 2
    assert L.audit_tool_calls(calls[:1], "/x/tech S01 ") == []
    assert len(L.audit_tool_calls(calls[:1], "/x/tech S02 ")) == 1                          # another session's id is a breach
