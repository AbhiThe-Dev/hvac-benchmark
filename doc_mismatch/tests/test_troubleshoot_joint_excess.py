"""Tests of the exploratory analysis of the joint tool's extra time (scripts/78, troubleshoot/v2/excess.py). Simulation only."""
import importlib.util
import sys
from pathlib import Path

import numpy as np
import pytest

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "src"))
from docmismatch.troubleshoot.v2 import excess as E  # noqa: E402
from docmismatch.troubleshoot.v2 import joint as JT  # noqa: E402
from docmismatch.troubleshoot.v2 import policies as P  # noqa: E402
from docmismatch.troubleshoot.v2 import world2 as W  # noqa: E402

IDX, WP = E.primary()
CASES = E.cases_for(None)
EVENTS = [W.draw_event(IDX, i, WP, CASES) for i in range(60)]


def script():
    spec = importlib.util.spec_from_file_location("s78", ROOT / "scripts" / "78_troubleshoot_joint_excess.py")
    m = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(m)
    return m


def test_primary_cell_and_tau():
    assert IDX == 6 and WP.f == 0.03
    assert CASES[("T2", 0)].settings.tau == 0.95 and E.cases_for(0.9)[("T2", 0)].settings.tau == 0.9


def test_coupled_oracle_answers_do_not_depend_on_who_asks_or_in_what_order():
    ev = EVENTS[4]
    cs = [CASES[("T2", r)] for r in ev.rooms]
    cks = [ck for ck in cs[0].checks if ck.subject != "ahu"][:6]
    a, b = E.Coupled(ev, WP.rel_a, 5), E.Coupled(ev, WP.rel_a, 5)
    fwd = [a.ask_room(0, ck, cs[0].doc) for ck in cks]
    rev = [b.ask_room(0, ck, cs[0].doc) for ck in reversed(cks)][::-1]
    assert fwd == rev
    ahu = next(ck for ck in cs[0].checks if ck.subject == "ahu")
    assert a.ask_ahu(cs[0].ahu, ahu) == b.ask_ahu(cs[0].ahu, ahu) == a.ask_ahu(cs[0].ahu, ahu)
    many = [E.Coupled(ev, WP.rel_a, s) for s in range(40)]
    answers = {tuple(o.ask_room(0, ck, cs[0].doc) for ck in cks) for o in many}
    assert len(answers) > 1                                       # different seeds give different answers


def test_coupled_oracle_follows_the_true_rates():
    ev = next(e for e in (W.draw_event(IDX, i, WP, CASES) for i in range(400)) if "ahu_fan_off" in e.u.values())
    a = next(k for k, v in ev.u.items() if v == "ahu_fan_off")
    ck = next(c for c in CASES[("T2", ev.rooms[0])].checks if c.name == "ahu_visit")
    p = E.Coupled(ev, WP.rel_a, 0).p_ahu(a, "ahu_visit")
    hits = np.mean([E.Coupled(ev, WP.rel_a, s).ask_ahu(a, ck) == ck.words[0] for s in range(400)])
    assert abs(hits - p) < 0.06


@pytest.mark.parametrize("tier", ["T2", "T3"])
def test_instrumented_copies_make_the_libraries_decisions(tier):
    """Same oracle stream, same minutes, checks and guesses as policies.run_policy (no stored file needed)."""
    for i, ev in enumerate(EVENTS[:16]):
        cs = [CASES[(tier, r)] for r in ev.rooms]
        ctxs = [W.context_dict(tier, r) for r in ev.rooms]
        for pol in ("tool_ticket_memo2", "tool_joint2"):
            mk = lambda: W.Oracle(ev, WP.rel_a, np.random.default_rng([31, IDX, 100, i]))
            lib = P.run_policy(pol, cs, mk(), ctxs)
            mine = E.ticket_steps(cs, mk()) if pol == "tool_ticket_memo2" else E.joint_steps(cs, mk())
            assert mine["minutes"] == lib["minutes"] and len(mine["steps"]) == lib["n_checks"] and mine["guess"] == lib["guess"] and mine["concluded"] == lib["concluded"]


def test_step_records_add_up():
    ev = next(e for e in EVENTS if e.n >= 2)
    cs = [CASES[("T2", r)] for r in ev.rooms]
    for r in (E.ticket_steps(cs, E.Coupled(ev, WP.rel_a, 1)), E.joint_steps(cs, E.Coupled(ev, WP.rel_a, 1))):
        assert abs(sum(s["minutes"] for s in r["steps"]) - r["minutes"]) < 1e-9
        assert all(abs(s["minutes"] - (s["access"] + s["do"])) < 1e-9 for s in r["steps"])          # no fallback minutes in this world: every input is declared
        assert all(s["moved"] == (s["access"] > 0) for s in r["steps"] if s["access"] > 0 or s["moved"])


def test_beyond_cap_counts_minutes_after_the_twelfth_check_on_a_complaint():
    steps = [dict(subject="box", who=0, minutes=1.0)] * 14 + [dict(subject="ahu", who="A", minutes=50.0)] + [dict(subject="zone", who=1, minutes=3.0)] * 13
    assert E.beyond_cap(steps) == 2.0 + 3.0                          # two on complaint 0, one on complaint 1; the air handler is not counted
    assert E.beyond_cap(steps, cap=13) == 1.0 + 0.0


def per_complaint(steps):
    n = {}
    for s in steps:
        if s["subject"] != "ahu":
            n[s["who"]] = n.get(s["who"], 0) + 1
    return n


def test_cap_session_never_exceeds_the_cap_and_the_uncapped_session_does():
    over_plain = over_cap = 0
    for ev in [e for e in EVENTS if e.kind == "multi"][:12]:
        cs = [CASES[("T3", r)] for r in ev.rooms]
        plain = E.joint_steps(cs, E.Coupled(ev, WP.rel_a, 3))
        capped = E.joint_steps(cs, E.Coupled(ev, WP.rel_a, 3), session_cls=E.CapSession)
        over_plain += max(per_complaint(plain["steps"]).values(), default=0) > E.CAP
        over_cap += max(per_complaint(capped["steps"]).values(), default=0) > E.CAP
    assert over_plain >= 1 and over_cap == 0


def test_focus_session_works_complaints_in_arrival_order():
    checked = 0
    for ev in [e for e in EVENTS if e.n >= 2][:12]:
        cs = [CASES[("T2", r)] for r in ev.rooms]
        r = E.joint_steps(cs, E.Coupled(ev, WP.rel_a, 2), session_cls=E.FocusSession)
        who = [s["who"] for s in r["steps"] if s["subject"] != "ahu"]
        assert who == sorted(who)
        checked += len(who) > 1
    assert checked >= 1


def test_run_event_fields_and_single_complaint_visits_are_identical_for_every_policy():
    assert len(E.FIELDS) == 9
    ev = next(e for e in EVENTS if e.kind == "single")
    got = {p: E.run_event(p, "T2", ev, E.Coupled(ev, WP.rel_a, 9), CASES) for p in E.POLICIES}
    assert all(len(v) == 9 for v in got.values())
    ref = got["tool_ticket_memo2"]
    assert all(v[:5] == ref[:5] and v[5] == "single" for v in got.values())     # one complaint: nothing to pool, share or reorder


def test_grid_is_deterministic_whatever_the_workers():
    a = E.run_grid((0.95,), (1, 2), 0, 6, ("tool_ticket_memo2", "tool_joint2"), workers=1)
    b = E.run_grid((0.95,), (1, 2), 0, 6, ("tool_ticket_memo2", "tool_joint2"), workers=2)
    assert a == b and set(a) == {(0.95, s, t, p) for s in (1, 2) for t in ("T2", "T3") for p in ("tool_ticket_memo2", "tool_joint2")}


def synthetic():
    def rows(ms, cor):
        return [(m, 5, c, 0, 2, k, 1, 3.0, 0.0) for m, c, k in zip(ms, cor, ("shared", "shared", "multi", "single"))]
    return {(0.95, 1, "T2", "tool_ticket_memo2"): rows([10, 20, 30, 40], [2, 2, 2, 2]), (0.95, 1, "T2", "tool_joint2"): rows([15, 20, 40, 40], [2, 2, 1, 2]),
            (0.95, 2, "T2", "tool_ticket_memo2"): rows([10, 20, 30, 40], [2, 2, 2, 2]), (0.95, 2, "T2", "tool_joint2"): rows([25, 20, 40, 40], [2, 2, 1, 2])}


def test_summary_and_paired_on_known_numbers():
    res = synthetic()
    s = E.summary(res, 0.95, "T2", "tool_joint2", "shared")
    assert s["events"] == 2 and s["minutes"] == pytest.approx(20.0) and s["correct"] == 100.0 and s["checks"] == 5
    assert E.summary(res, 0.95, "T2", "tool_joint2", "all")["events"] == 4
    p = E.paired(res, 0.95, "T2", "tool_joint2", "tool_ticket_memo2", "shared")
    assert p["minutes"] == pytest.approx(5.0) and p["correct"] == 0.0            # per event mean over the two seeds: (+5, +15) -> 10 and (0, 0) -> 0; their mean is 5
    assert p["minutes_ci"][0] <= p["minutes"] <= p["minutes_ci"][1]
    m = E.paired(res, 0.95, "T2", "tool_joint2", "tool_ticket_memo2", "multi")
    assert m["minutes"] == pytest.approx(10.0) and m["correct"] == pytest.approx(-50.0)      # 1 of 2 complaints right against 2 of 2


def test_gate_on_a_few_events_reproduces_the_stored_study():
    s = script()
    if not s.RAW31.exists():
        pytest.skip("Addendum 31's raw results are not present")
    g = s.gate(8)
    assert g["pass"] is True and "replays" in g["detail"]


def test_report_renders_from_a_small_grid():
    s = script()
    res = E.run_grid((0.95,), (1,), 0, 30, E.POLICIES[:2], workers=1)
    text = s.report({"diagnose": res}, {"pass": True, "detail": "x"}, True)
    assert "SMOKE RUN" in text and "tool_joint2" in text and "Paired differences" in text and "PASS" in text
