"""Where does the joint tool's extra time go? (PREREGISTRATION_DR.md, exploratory note E1: NOT a pre-registered test; the variants were designed after looking at the diagnosis.) Simulation only; nothing here is
evidence about real technicians, and every number is the model's own family with placeholder rates.
  .venv/bin/python doc_mismatch/scripts/78_troubleshoot_joint_excess.py gate      # the instrumented replays reproduce Addendum 31's stored minutes, checks and correct counts exactly
  .venv/bin/python doc_mismatch/scripts/78_troubleshoot_joint_excess.py run       # the four runs (a few minutes on 8 workers); the gate runs first; raw results are pickled
  .venv/bin/python doc_mismatch/scripts/78_troubleshoot_joint_excess.py report    # tables from the stored raw results
  add --smoke to `run` for a plumbing check on 40 events (numbers meaningless)
Every policy gets the same answer to the same question (excess.Coupled), so a paired difference is the policies alone.
"""
import argparse
import json
import pickle
import sys
import time
from pathlib import Path

import numpy as np

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "src"))
from docmismatch.troubleshoot.v2 import excess as E  # noqa: E402
from docmismatch.troubleshoot.v2 import policies as P  # noqa: E402
from docmismatch.troubleshoot.v2 import world2 as W  # noqa: E402

REPO = ROOT.parent
OUT = REPO / "results/docmismatch/troubleshoot_joint_excess"
RAW31 = REPO / "results/docmismatch/troubleshoot_joint2/joint2_raw.pkl"
MEMO, JOINT, CAP, FOCUS = E.POLICIES
# events 0..999 are the study's own events; 1000..1999 and 2000..2999 are further draws of the same world (never used before this note)
RUNS = {"diagnose": dict(taus=(0.95,), seeds=tuple(range(201, 209)), n0=0, n=1000, policies=(MEMO, JOINT)),
        "sweep": dict(taus=(0.90, 0.92, 0.94, 0.95, 0.96, 0.97, 0.98, 0.99), seeds=tuple(range(201, 205)), n0=0, n=1000, policies=(MEMO, JOINT)),
        "focus": dict(taus=(0.90, 0.92, 0.95), seeds=tuple(range(301, 305)), n0=1000, n=1000, policies=(MEMO, JOINT, FOCUS)),
        "cap": dict(taus=(0.90, 0.92, 0.94, 0.95), seeds=tuple(range(401, 405)), n0=2000, n=1000, policies=(MEMO, JOINT, CAP))}
SUBS = ("shared", "multi", "single", "all")
STORED_SEED = 31          # Addendum 31's answer seed; its events use the world's seed 30


def gate(n_events: int = 200) -> dict:
    """Replay the first `n_events` of the primary cell with Addendum 31's own answer streams and compare with its stored arrays."""
    if not RAW31.exists():
        return {"pass": None, "detail": f"stored results not found: {RAW31}"}
    idx, wp = E.primary()
    stored = next(r for r in pickle.loads(RAW31.read_bytes()) if r["idx"] == idx)
    cases = E.cases_for(None)
    events = [W.draw_event(idx, i, wp, cases) for i in range(n_events)]
    bad, checked = [], 0
    for ti, tier in enumerate(W.TIER_NAMES):
        for pol in (MEMO, JOINT):
            st = stored["pol"][(tier, pol)]
            for i, ev in enumerate(events):
                cs = [cases[(tier, r)] for r in ev.rooms]
                oracle = W.Oracle(ev, wp.rel_a, np.random.default_rng([STORED_SEED, idx, 100 + 10 * ti + P.POLICY_INDEX[pol], i]))
                r = E.ticket_steps(cs, oracle) if pol == MEMO else E.joint_steps(cs, oracle)
                got = (r["minutes"], len(r["steps"]), sum(g == t for g, t in zip(r["guess"], ev.causes)))
                if not (abs(got[0] - st["minutes"][i]) < 1e-9 and got[1] == st["checks"][i] and got[2] == st["correct"][i]):
                    bad.append((tier, pol, i))
                checked += 1
    return {"pass": not bad, "detail": f"{checked} replays, {len(bad)} differ" + (f" (first: {bad[:3]})" if bad else "")}


def f1(x):
    return f"{x:.1f}"


def summary_table(res, tau, tier, pols, sub):
    L = ["| policy | minutes | checks | moves | travel min | min beyond 12th check | % correct | % wrong-and-confident |", "|---|---|---|---|---|---|---|---|"]
    for p in pols:
        s = E.summary(res, tau, tier, p, sub)
        L.append(f"| {p} | {f1(s['minutes'])} | {s['checks']:.2f} | {s['moves']:.2f} | {f1(s['travel'])} | {f1(s['beyond'])} | {f1(s['correct'])} | {s['wc']:.1f} |")
    return L


def paired_line(res, tau, tier, a, b, sub):
    p = E.paired(res, tau, tier, a, b, sub)
    return f"{p['minutes']:+.1f} [{p['minutes_ci'][0]:+.1f}, {p['minutes_ci'][1]:+.1f}] min, {p['correct']:+.1f} pts"


def report(allres: dict, gate_res: dict, smoke: bool) -> str:
    L = ["# Where does the joint tool's extra time go? (exploratory note E1)", "",
         "Simulation only, the model's own family, placeholder numbers; not a pre-registered test; the variants (`joint2_focus`, `joint2_cap12`) were designed after looking at the diagnosis. Every policy gets the SAME answer to "
         "the same question (a coupled oracle), so differences between policies are the policies alone. The routine is `tool_ticket_memo2`, the joint tool `tool_joint2`; both are Addendum 31's, at the conclusion threshold "
         "tau shown (the tool's own is 0.95). `joint2_cap12`: the joint session with the routine's cap of 12 room or box checks per complaint. `joint2_focus`: the joint session working the complaints in arrival order.", "",
         f"Gate (the instrumented replays reproduce Addendum 31's stored minutes, checks and correct counts): **{'PASS' if gate_res['pass'] else 'FAIL' if gate_res['pass'] is False else 'NOT RUN'}**, {gate_res['detail']}.", ""]
    if smoke:
        L += ["**SMOKE RUN: the numbers below are meaningless.**", ""]
    sub_text = {"shared": "shared-cause visits", "multi": "several complaints, no shared cause", "single": "one complaint", "all": "all visits"}
    for name, spec in RUNS.items():
        if name not in allres:
            continue
        res = allres[name]
        L += [f"## Run `{name}`: events {spec['n0']}-{spec['n0'] + spec['n'] - 1} of the primary cell, answer seeds {spec['seeds'][0]}-{spec['seeds'][-1]}, policies {', '.join(spec['policies'])}", ""]
        for sub in ("shared", "multi", "all") if name != "sweep" else ("shared", "multi", "all"):
            for tier in W.TIER_NAMES:
                for tau in spec["taus"]:
                    if name == "sweep" and tau not in (0.90, 0.92, 0.94, 0.95, 0.97, 0.99):
                        continue
                    L += [f"**{sub_text[sub]}, {tier}, tau {tau:.2f}** ({E.summary(res, tau, tier, spec['policies'][0], sub)['events']} events)", ""] + summary_table(res, tau, tier, spec["policies"], sub) + [""]
        L += [f"### Paired differences in run `{name}` (first minus second, per event over the answer seeds; 95% bootstrap interval over events)", "",
              "| subset | tier | tau | " + " | ".join(f"{a} - {b}" for a, b in _pairs(spec["policies"])) + " |", "|---|---|---|" + "---|" * len(_pairs(spec["policies"]))]
        for sub in ("shared", "multi", "all"):
            for tier in W.TIER_NAMES:
                for tau in spec["taus"]:
                    L.append(f"| {sub_text[sub]} | {tier} | {tau:.2f} | " + " | ".join(paired_line(res, tau, tier, a, b, sub) for a, b in _pairs(spec["policies"])) + " |")
        L.append("")
    return "\n".join(L)


def _pairs(pols):
    pairs = [(JOINT, MEMO)]
    pairs += [(p, MEMO) for p in pols if p not in (MEMO, JOINT)] + [(p, JOINT) for p in pols if p not in (MEMO, JOINT)]
    return pairs


def main(argv=None):
    ap = argparse.ArgumentParser()
    ap.add_argument("cmd", choices=("gate", "run", "report"))
    ap.add_argument("--smoke", action="store_true")
    ap.add_argument("--out", type=Path, default=OUT)
    ap.add_argument("--workers", type=int)
    a = ap.parse_args(argv)
    a.out.mkdir(parents=True, exist_ok=True)
    if a.cmd == "gate":
        g = gate()
        print(json.dumps(g))
        sys.exit(0 if g["pass"] else 1)
    if a.cmd == "run":
        g = gate(20 if a.smoke else 200)
        (a.out / "gate.json").write_text(json.dumps(g) + "\n")
        print("gate:", g)
        if g["pass"] is False:
            sys.exit("the replays do not reproduce Addendum 31: stop")
        allres, t0 = {}, time.time()
        for name, spec in RUNS.items():
            n = 40 if a.smoke else spec["n"]
            seeds = spec["seeds"][:2] if a.smoke else spec["seeds"]
            allres[name] = E.run_grid(spec["taus"], seeds, spec["n0"], n, spec["policies"], a.workers)
            print(f"{name}: {time.time() - t0:.0f}s", flush=True)
            (a.out / ("raw_smoke.pkl" if a.smoke else "raw.pkl")).write_bytes(pickle.dumps(allres))
    raw = a.out / ("raw_smoke.pkl" if a.smoke else "raw.pkl")
    allres = pickle.loads(raw.read_bytes())
    g = json.loads((a.out / "gate.json").read_text()) if (a.out / "gate.json").exists() else {"pass": None, "detail": "gate.json missing"}
    text = report(allres, g, a.smoke)
    (a.out / ("report_smoke.md" if a.smoke else "report.md")).write_text(text + "\n")
    print(f"wrote {a.out / ('report_smoke.md' if a.smoke else 'report.md')}")


if __name__ == "__main__":
    main()
