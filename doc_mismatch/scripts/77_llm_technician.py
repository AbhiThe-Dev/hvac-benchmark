"""A language model as the experienced technician (PREREGISTRATION_DR.md Addendum 33). Simulation only; a PILOT; nothing here is evidence about real technicians.
  .venv/bin/python doc_mismatch/scripts/77_llm_technician.py --dir RUNDIR prepare [--per-kind N]   # sample the visits, run the partners, write the registry and the launcher `tech`
  .venv/bin/python doc_mismatch/scripts/77_llm_technician.py --dir RUNDIR terminal SID COMMAND...  # what the technician runs (through RUNDIR/tech)
  .venv/bin/python doc_mismatch/scripts/77_llm_technician.py --dir RUNDIR analyze [--audit FILE] [--out DIR]
The technician's sessions are worked by a language model that has this terminal and nothing else; RUNDIR holds their state (one file per session).
"""
import argparse
import csv
import json
import os
import stat
import sys
import time
from collections import Counter
from pathlib import Path

import numpy as np

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "src"))
from docmismatch.troubleshoot.v2 import study_llm as L  # noqa: E402

REPO = ROOT.parent
OUT = REPO / "results/docmismatch/troubleshoot_llm"
PY = REPO / ".venv/bin/python"
SUB_TEXT = {"all": "all visits (natural mix)", "shared": "shared-cause visits", "multi": "several complaints, no shared cause", "single": "one complaint"}
COMP_TEXT = {"P": "LLM - routine (`tool_ticket_memo2`)  [PRIMARY]", "Q": "LLM - joint tool (`tool_joint2`)", "R": "LLM - fast_parent (my rule)", "S": "routine - fast_parent (Addendum 31's comparison on this sample)"}
SHOW = ("llm",) + L.PARTNERS


def pct(x):
    return "n/a" if x is None or not np.isfinite(x) else f"{100 * x:.0f}%"


def sumrow(s):
    return "n/a" if not s.get("n") else f"{s['minutes']:.0f} min / {pct(s['accuracy'])} / {pct(s['wrong_confident'])} / {s['checks']:.1f}"


# ---------------------------------------------------------------------------------------------- prepare
def prepare(d: Path, per_kind: int) -> None:
    d.mkdir(parents=True, exist_ok=True)
    (d / "state").mkdir(exist_ok=True)
    cases, wp, events = L.world()
    visits = L.sample_visits(events, per_kind)
    rng = np.random.default_rng([L.SEED, 2])
    combos = [(v["id"], t) for v in visits for t in L.TIERS]
    order = rng.permutation(len(combos))
    reg = {f"S{k + 1:02d}": dict(visit=combos[o][0], tier=combos[o][1], event=next(v["event"] for v in visits if v["id"] == combos[o][0])) for k, o in enumerate(order)}
    partners = {}
    for v in visits:
        for t in L.TIERS:
            for pol, rec in L.run_partners(events[v["event"]], t, cases, wp).items():
                partners[f"{v['id']}|{t}|{pol}"] = rec
    (d / "visits.json").write_text(L.dumps(dict(visits=visits, shares=L.kind_shares(events), per_kind=per_kind, seed=L.SEED)))
    (d / "registry.json").write_text(L.dumps(reg))
    (d / "partners.json").write_text(L.dumps(partners))
    launcher = d / "tech"
    launcher.write_text(f'#!/bin/sh\nexec "{PY}" "{Path(__file__).resolve()}" --dir "{d}" terminal "$@"\n')
    launcher.chmod(launcher.stat().st_mode | stat.S_IXUSR)
    print(f"prepared {len(visits)} visits, {len(reg)} sessions in {d}; launcher {launcher}")


# ---------------------------------------------------------------------------------------------- the terminal
USAGE = "usage: brief | status | checks N | do CHECK N [TARGET_BOX] | conclude N CAUSE confident|unsure | finish"


def terminal(d: Path, sid: str, argv: list[str]) -> None:
    reg = json.loads((d / "registry.json").read_text())
    if sid not in reg:
        print(f"ERROR: unknown session {sid!r}")
        return
    r = reg[sid]
    cases, wp, ev = L.event_at(r["event"])
    v = L.Visit(ev, r["tier"], cases, wp)
    sp = d / "state" / f"{sid}.json"
    saved = json.loads(sp.read_text()) if sp.exists() else []
    v.replay(saved)
    try:
        if not argv:
            raise L.VisitError(USAGE)
        cmd, a = argv[0], argv[1:]
        if cmd == "brief":
            out = L.brief_text(v, sid, cases)
        elif cmd == "status":
            out = L.status_text(v)
        elif cmd == "checks" and len(a) == 1:
            out = L.checks_text(v, int(a[0]))
        elif cmd == "do" and len(a) in (2, 3):
            out = L.do_text(v.do(a[0], int(a[1]), a[2] if len(a) == 3 else None))
        elif cmd == "conclude" and len(a) == 3:
            v.conclude(int(a[0]), a[1], a[2])
            out = f"Recorded: complaint {a[0]} = {a[1]} ({a[2]}). Concluded so far: {sorted(i + 1 for i in v.concl)} of {v.n}."
        elif cmd == "finish" and not a:
            v.finish()
            out = f"Visit finished. Total {v.minutes:g} minutes. Reply with the single word DONE."
        else:
            raise L.VisitError(USAGE)
        status = "ok"
    except (L.VisitError, ValueError) as e:
        out, status = f"ERROR: {e}", "error"
    if v.commands != saved:
        sp.write_text(json.dumps(v.commands))
    with open(d / "state" / f"{sid}.log", "a") as f:
        f.write(json.dumps([time.time(), status, argv]) + "\n")
    print(out)


# ---------------------------------------------------------------------------------------------- analyze
def load_llm(d: Path):
    reg = json.loads((d / "registry.json").read_text())
    cases, wp, events = L.world()
    recs, visits_obj, behaviour = {}, {}, {}
    for sid, r in reg.items():
        ev = events[r["event"]]
        v = L.Visit(ev, r["tier"], cases, wp)
        sp = d / "state" / f"{sid}.json"
        v.replay(json.loads(sp.read_text()) if sp.exists() else [])
        recs[(r["visit"], r["tier"], "llm")] = L.record(v.result(), ev)
        visits_obj[sid] = v
        lg = d / "state" / f"{sid}.log"
        behaviour[sid] = [json.loads(x) for x in lg.read_text().splitlines()] if lg.exists() else []
    return reg, recs, visits_obj, behaviour, (cases, wp, events)


def gates(d, reg, recs, world, audit, visits_obj, behaviour, per_kind):
    cases, wp, events = world
    vis = json.loads((d / "visits.json").read_text())
    g = {}
    # G1: determinism and order independence of the answer table
    ok = True
    for r in list(reg.values())[:12]:
        ev = events[r["event"]]
        cs = [cases[(r["tier"], x)] for x in ev.rooms]
        o1, o2 = L.TableOracle(ev, wp.rel_a), L.TableOracle(ev, wp.rel_a)
        qs = [(i, ck, ck.name) for i, c in enumerate(cs) for ck in c.checks if not ck.subject == "ahu"][:60]
        a = [o1.ask_room(i, ck, cs[i].doc) for i, ck, _ in qs]
        b = [o2.ask_room(i, ck, cs[i].doc) for i, ck, _ in reversed(qs)][::-1]
        ok &= a == b
    g["G1 answers"] = (ok, "the answer table is deterministic and independent of question order on 12 sessions' questions")
    # G2: the terminal's accounting against the policies' own
    bad, n = 0, 0
    for v in vis["visits"]:
        for t in L.TIERS:
            for pol in ("fast_parent", L.ROUTINE):
                m, c, pm, pc = L.replay_policy(events[v["event"]], t, cases, wp, pol)
                n += 1
                bad += int(abs(m - pm) > 1e-9 or c != pc)
    g["G2 accounting"] = (bad == 0, f"{n} replays of fast_parent and the routine through the terminal: {bad} differ in minutes or checks")
    # G3: audit
    if audit is None:
        g["G3 audit"] = (True, "NOT AUDITED: the transcripts were not inspected")
    else:
        viol = {k: x for k, x in audit.items() if x}
        g["G3 audit"] = (not viol, f"{len(audit)} sessions audited; {len(viol)} with a breach: {viol}" if viol else f"{len(audit)} sessions audited; no breach")
    # G4: completeness
    unfinished = [s for s, v in visits_obj.items() if not v.finished]
    empty = [s for s, v in visits_obj.items() if not v.log and not v.concl]
    g["G4 completeness"] = (not empty and len(visits_obj) == 2 * per_kind * 3, f"{len(visits_obj)} sessions; {len(unfinished)} ended without `finish` (scored as abandoned: {sorted(unfinished)}); {len(empty)} took no action")
    # G5: partners reproduce
    stored = json.loads((d / "partners.json").read_text())
    bad5 = 0
    for v in vis["visits"][:10]:
        for t in L.TIERS:
            for pol, rec in L.run_partners(events[v["event"]], t, cases, wp).items():
                bad5 += int(abs(rec["minutes"] - stored[f"{v['id']}|{t}|{pol}"]["minutes"]) > 1e-9 or rec["correct"] != stored[f"{v['id']}|{t}|{pol}"]["correct"])
    g["G5 partners"] = (bad5 == 0, f"{bad5} of 60 re-run partner results differ from the stored ones")
    # G6: sample and seed
    again = L.sample_visits(events, per_kind, L.SEED)
    g["G6 sample"] = (again == vis["visits"] and vis["seed"] == L.SEED and per_kind == vis["per_kind"], f"seed {vis['seed']}, {vis['per_kind']} per kind, sample reproduced")
    return g


def report(an, gs, preds, dec, beh, n_ab, per_kind, enforced=True):
    L_ = ["# A language model as the experienced technician (Addendum 33): a pilot", "",
          f"{per_kind} visits of each kind ({3 * per_kind} visits) from Addendum 30's primary cell, each worked at T2 and T3 by the routine, the joint tool, my rule-based stand-in and a language model (Claude `sonnet`, one fresh session per "
          "visit and tier) working through a terminal. Identical answers to identical questions; the tool's own accountant charges the minutes. Simulation only, from the tool's own model family with placeholder numbers; a language model is "
          "not an experienced technician and nothing here is evidence about real technicians. About 10 visits per kind: wide intervals.", "", "## Gates", "", "| gate | result | detail |", "|---|---|---|"]
    for k, (ok, det) in gs.items():
        L_.append(f"| {k} | {'PASS' if ok else 'FAIL'} | {det} |")
    if enforced and not all(ok for ok, _ in gs.values()):
        return "\n".join(L_ + ["", "## NO RESULT (a gate failed)"])
    for t in L.TIERS:
        L_ += ["", f"## Tier {t}: minutes per visit / share of complaints diagnosed exactly right / wrong-and-confident / checks per visit (kind shares re-weighted to the cell's)", "",
               "| policy | " + " | ".join(SUB_TEXT[k] for k in L.SUBS) + " |", "|---|" + "---|" * len(L.SUBS)]
        for p in SHOW:
            L_.append(f"| {p} | " + " | ".join(sumrow(an["sum"][(t, p, s)]) for s in L.SUBS) + " |")
    L_ += ["", "## Comparisons on the same visits (paired, bootstrap 95% intervals, Addendum 21 labels)", "",
           "| comparison | tier | subset | d minutes | d accuracy | d wrong-and-confident | time / accuracy | label | break-even cost of a wrong diagnosis |", "|---|---|---|---|---|---|---|---|---|"]
    for name in L.COMPS:
        for s in L.SUBS:
            for t in L.TIERS:
                e = an["cmp"][(t, name, s)]
                be = {"DOMINATES": "first ahead on both", "DOMINATED": "second ahead on both"}.get(e["break_even"]) or (f"{e['wrong_cost']:.0f} min (first wins above)" if e["break_even"] == "SLOWER-MORE" else f"{e['wrong_cost']:.0f} min (first wins below)")
                L_.append(f"| {name}: {COMP_TEXT[name]} | {t} | {SUB_TEXT[s]} | {e['d_min']:+.1f} ({100 * e['r_min']:+.0f}%) [{e['ci_min'][0]:+.0f}, {e['ci_min'][1]:+.0f}] | {e['d_acc']:+.3f} [{e['ci_acc'][0]:+.2f}, {e['ci_acc'][1]:+.2f}] | "
                          f"{e['d_wc']:+.3f} | {e['time']} / {e['acc']} | {e['label']} | {be} |")
    L_ += ["", "## What the language model did", "", f"Sessions abandoned (stopped without `finish`): {n_ab}.", "", "| tier | checks per visit | first check at the air handler (all / shared) | 'confident' share of conclusions | most used checks |", "|---|---|---|---|---|"]
    for t in L.TIERS:
        b = beh[t]
        L_.append(f"| {t} | {b['checks']:.1f} | {pct(b['first_all'])} / {pct(b['first_shared'])} | {pct(b['confident'])} | {', '.join(f'{k} {v}' for k, v in b['top'])} |")
    L_ += ["", "## Predictions (written before the run; each strict)", "", "| prediction | holds | values |", "|---|---|---|"]
    for k, (ok, det) in preds.items():
        L_.append(f"| {k} | {'holds' if ok else 'does not hold'} | {det} |")
    L_ += ["", f"## Frozen decision: {dec}"]
    return "\n".join(L_)


def behaviour(visits_obj, reg, vis):
    kind = {v["id"]: v["kind"] for v in vis["visits"]}
    out = {}
    for t in L.TIERS:
        ss = [s for s, r in reg.items() if r["tier"] == t]
        ck, first_all, first_sh, conf, cnt = [], [], [], [], Counter()
        for s in ss:
            v = visits_obj[s]
            ck.append(v.charged)
            f = bool(v.log and v.log[0]["subject"] == "ahu")
            first_all.append(f)
            if kind[reg[s]["visit"]] == "shared":
                first_sh.append(f)
            conf += [c[1] for c in v.concl.values()]
            cnt.update(x["check"] for x in v.log)
        out[t] = dict(checks=float(np.mean(ck)), first_all=float(np.mean(first_all)), first_shared=float(np.mean(first_sh)) if first_sh else float("nan"), confident=float(np.mean(conf)) if conf else float("nan"),
                      top=cnt.most_common(6))
    return out


def analyze(d: Path, audit_path: Path | None, out: Path, enforced: bool = True) -> None:
    out.mkdir(parents=True, exist_ok=True)
    vis = json.loads((d / "visits.json").read_text())
    reg, recs, visits_obj, _, world = load_llm(d)
    for k, rec in json.loads((d / "partners.json").read_text()).items():
        i, t, p = k.split("|")
        recs[(i, t, p)] = rec
    audit = json.loads(audit_path.read_text()) if audit_path else None
    gs = gates(d, reg, recs, world, audit, visits_obj, {}, vis["per_kind"])
    an = L.analyze(recs, vis["visits"], vis["shares"])
    n_ab = sum(1 for v in visits_obj.values() if not v.finished)
    text = report(an, gs, L.predictions(an), L.decision(an), behaviour(visits_obj, reg, vis), n_ab, vis["per_kind"], enforced)
    (out / "llm_report.md").write_text(text + "\n")
    with open(out / "llm_records.csv", "w", newline="") as f:
        w = csv.writer(f)
        w.writerow(["visit", "kind", "tier", "policy", "minutes", "checks", "correct", "complaints", "wrong_confident", "concluded", "first_check_ahu", "abandoned"])
        kind = {v["id"]: v["kind"] for v in vis["visits"]}
        for (i, t, p), r in sorted(recs.items()):
            w.writerow([i, kind[i], t, p, f"{r['minutes']:.1f}", f"{r['checks']:.0f}", r["correct"], r["n"], r["wc"], r["concluded"], int(r["first_ahu"]), int(r["abandoned"])])
    (out / "llm_sessions.json").write_text(json.dumps({s: dict(reg[s], commands=v.commands) for s, v in visits_obj.items()}))
    print(f"wrote {out / 'llm_report.md'}; gates: " + ", ".join(f"{k.split()[0]} {'PASS' if ok else 'FAIL'}" for k, (ok, _) in gs.items()))


def audit(d: Path, mapping: Path, out: Path) -> None:
    """mapping = {session id: path of that session's transcript}; writes {session id: [breaches]} (a breach = any tool call other than the terminal command for that session)."""
    res = {}
    for sid, path in json.loads(mapping.read_text()).items():
        calls = L.tool_calls_in_transcript(path)
        res[sid] = L.audit_tool_calls(calls, f"{d / 'tech'} {sid} ") if calls else ["no tool calls found in the transcript"]
    out.write_text(json.dumps(res, indent=1))
    print(f"audited {len(res)} sessions; breaches in {sum(bool(v) for v in res.values())}: " + json.dumps({k: v for k, v in res.items() if v})[:600])


def main(argv=None):
    ap = argparse.ArgumentParser()
    ap.add_argument("--dir", type=Path, required=True)
    sub = ap.add_subparsers(dest="cmd", required=True)
    p1 = sub.add_parser("prepare")
    p1.add_argument("--per-kind", type=int, default=L.N_PER_KIND)
    p2 = sub.add_parser("terminal")
    p2.add_argument("sid")
    p2.add_argument("rest", nargs=argparse.REMAINDER)
    p3 = sub.add_parser("analyze")
    p3.add_argument("--audit", type=Path)
    p3.add_argument("--out", type=Path, default=OUT)
    p3.add_argument("--smoke", action="store_true")
    p4 = sub.add_parser("audit")
    p4.add_argument("mapping", type=Path)
    p4.add_argument("out", type=Path)
    a = ap.parse_args(argv)
    if a.cmd == "prepare":
        prepare(a.dir, a.per_kind)
    elif a.cmd == "terminal":
        terminal(a.dir, a.sid, a.rest)
    elif a.cmd == "audit":
        audit(a.dir, a.mapping, a.out)
    else:
        analyze(a.dir, a.audit, a.out, not a.smoke)


if __name__ == "__main__":
    main()
