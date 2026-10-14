"""Addendum 40 (PREREGISTRATION_DR.md): the live v2 tool against the real technician in working time at the technician's own observed pace.

Reuses Addendum 39's world, sampling and tool setup (scripts/89_field_compete.py), so that gate G3 can hold: under Addendum 39's sampling truth (S2) this runner must reproduce Addendum 39's
stored per-world check sequences exactly. Adds the pricing of `field_cases/pace_table.json`: a check costs (family ratio) x (its catalogue do_min); BAS family = place 'bas', everything else
physical; travel (access) and waiting are excluded (S3 adds waiting back, unscaled). Nothing here changes the tool, the catalogue or any frozen file.

  .venv/bin/python doc_mismatch/scripts/90_field_pace.py --selftest
  .venv/bin/python doc_mismatch/scripts/90_field_pace.py          # refuses to run if a frozen file changed; checks G3

Outputs: results/docmismatch/field_pace/ (summary.json, report.md, draws_<case>_k6.csv).
"""

from __future__ import annotations

import argparse
import copy
import csv
import importlib.util
import json
import sys
import tempfile
from pathlib import Path

import numpy as np

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "src"))

_s = importlib.util.spec_from_file_location("fcc89", ROOT / "scripts" / "89_field_compete.py")
FCC = importlib.util.module_from_spec(_s)
_s.loader.exec_module(FCC)
FC, K, V2 = FCC.FC, FCC.K, FCC.V2
JointSession, JointSettings = FCC.JointSession, FCC.JointSettings

CASES_DIR = FCC.CASES_DIR
PACE_FILE = CASES_DIR / "pace_table.json"
FROZEN_PACE = CASES_DIR / "FROZEN_PACE.sha256"
A39_DIR = ROOT.parent / "results" / "docmismatch" / "field_compete"
OUT = ROOT.parent / "results" / "docmismatch" / "field_pace"
CK = {c.name: c for c in K.CATALOGUE}
SCEN = ("FAST", "CENTRAL", "SLOW")
S1_ADD_MIN = 3.25          # the technician's physical confirmation in EP160 (2.75 + 0.5), registered


def check_frozen3() -> None:
    FCC.check_frozen2()
    want = dict(line.split()[::-1] for line in FROZEN_PACE.read_text().splitlines() if line.strip())
    if want.get(PACE_FILE.name) != FC.sha256(PACE_FILE):
        raise SystemExit(f"{PACE_FILE.name} has changed since it was frozen; a change after the freeze is a logged deviation, not a silent edit")


# ---------------------------------------------------------------------------------------------- pricing
def family(name: str) -> str:
    return "bas" if CK[name].place == "bas" else "physical"


def price(checks: list[str], scen: dict, wait: bool = False) -> float:
    """Working time of a session: sum over its checks of (family ratio) x (catalogue do_min); with wait=True the catalogue's wait_min is added unscaled (S3)."""
    t = 0.0
    for n in checks:
        ck = CK[n]
        t += (scen["ratio_bas"] if family(n) == "bas" else scen["ratio_physical"]) * float(ck.do_min)
        if wait:
            t += float(ck.wait_min)
    return t


# ---------------------------------------------------------------------------------------------- worlds
class World2(FCC.World):
    """Addendum 39's world, also recording each asked check's data-fallback surcharge."""

    def __init__(self, *a, **k):
        super().__init__(*a, **k)
        self.extras: list[float] = []

    def __call__(self, prompt: str) -> str:
        self.extras.append(float(self.sess._pending.avail.extra_min))
        return super().__call__(prompt)


def run_world(cases: list, base: dict, comp: dict, draw: int) -> dict:
    sess = JointSession(cases, JointSettings(f=JointSettings().f), 1)
    w = World2(sess, base, comp, "model", draw)
    st = V2.run(sess, w, lambda s: None)
    per = []
    for i, c in enumerate(base["complaints"]):
        top = st["complaints"][i]["ranked"][0]
        per.append(dict(correct=top[0][0] in c["truth_accept"], concluded=bool(st["complaints"][i]["concluded"])))
    return dict(draw=draw, checks=[x[2] for x in sess.log], steps=int(st["n_checks"]), cat_min=float(st["elapsed"]), n_fallback=sum(e > 0 for e in w.extras),
                all_correct=all(p["correct"] for p in per))


def with_truth(comp: dict, truth: dict) -> dict:
    c = copy.deepcopy(comp)
    c["sampling_truth"] = dict(truth)
    return c


# ---------------------------------------------------------------------------------------------- summaries
def q(xs, p):
    return float(np.quantile(np.array(xs, float), p))


def label(ratio: float, p_correct: float) -> str:
    if ratio >= 1.25:
        return "TECHNICIAN FASTER"
    if ratio <= 0.8 and p_correct >= 0.9:
        return "TOOL FASTER"
    return "TIE"


def summarise(rows: list[dict], pace: dict, tech: float, is_ep160: bool) -> dict:
    n = len(rows)
    p_correct = sum(r["all_correct"] for r in rows) / n
    out = dict(n=n, steps_median=q([r["steps"] for r in rows], 0.5), p_all_correct=p_correct, catalogue_minutes_median=q([r["cat_min"] for r in rows], 0.5),
               n_checks_with_fallback_surcharge=int(sum(r["n_fallback"] for r in rows)),
               median_bas_reads=q([sum(family(c) == "bas" for c in r["checks"]) for r in rows], 0.5), median_physical_checks=q([sum(family(c) == "physical" for c in r["checks"]) for r in rows], 0.5),
               share_worlds_with_reheat_coil=sum("reheat_coil" in r["checks"] for r in rows) / n, scenarios={})
    for name in SCEN:
        sc = pace["scenarios"][name]
        variants = {"primary": [price(r["checks"], sc) for r in rows], "S3_wait_added": [price(r["checks"], sc, wait=True) for r in rows]}
        if is_ep160:
            variants["S1_like_for_like"] = [price(r["checks"], sc) + (0.0 if "reheat_coil" in r["checks"] else S1_ADD_MIN) for r in rows]
        res = {}
        for vn, ts in variants.items():
            med = q(ts, 0.5)
            res[vn] = dict(median=round(med, 6), q25=round(q(ts, 0.25), 6), q75=round(q(ts, 0.75), 6), ratio=round(med / tech, 6), p_tool_faster=sum(t < tech for t in ts) / n,
                           label=label(med / tech, p_correct))
        out["scenarios"][name] = res
    out["robustness"] = "ROBUST" if len({out["scenarios"][s]["primary"]["label"] for s in SCEN}) == 1 else "SENSITIVE TO PACE"
    return out


def run_case(base: dict, comp: dict, pace: dict, tmp: Path, n_draws: int) -> dict:
    cid = base["id"]
    tech = float(pace["technician_minutes_to_diagnosis"][cid])
    is_ep = cid == "ep160"
    res = dict(case=cid, title=base["title"], technician_minutes=tech, runs={}, worlds={})
    primary_truth = pace["worlds"]["sampling_truth_primary"][cid]
    s2_truth = pace["worlds"]["S2_addendum39_truth"][cid]
    for k in pace["worlds"]["padding_levels"]:
        cases = FCC.make_cases(base, comp, k, tmp)
        c = with_truth(comp, primary_truth)
        rows = [run_world(cases, base, c, d) for d in range(n_draws)]
        res["runs"][f"primary_k{k}"] = summarise(rows, pace, tech, is_ep)
        if k == pace["worlds"]["padding_primary_k"]:
            res["worlds"]["primary_k6"] = rows
    cases = FCC.make_cases(base, comp, pace["worlds"]["padding_primary_k"], tmp)
    c2 = with_truth(comp, s2_truth)
    rows2 = [run_world(cases, base, c2, d) for d in range(n_draws)]
    res["runs"]["S2_k6"] = summarise(rows2, pace, tech, is_ep)
    res["worlds"]["S2_k6"] = rows2
    return res


def g3_reproduction(res: dict) -> dict:
    """Under S2 this runner's per-world sequences must equal Addendum 39's stored draws, all 1000 worlds."""
    cid = res["case"]
    f = A39_DIR / f"draws_compete_{cid}_k6.csv"
    stored = list(csv.DictReader(open(f)))
    mine = res["worlds"]["S2_k6"]
    bad = [i for i, (a, b) in enumerate(zip(stored, mine)) if a["checks"] != " ".join(b["checks"]) or int(a["steps"]) != b["steps"] or a["minutes"] != f"{b['cat_min']:.1f}"]
    return dict(case=cid, n_stored=len(stored), n_mine=len(mine), n_mismatch=len(bad), first_mismatch=bad[:3], passed=len(stored) == len(mine) and not bad)


# ---------------------------------------------------------------------------------------------- predictions, evaluated mechanically
def predictions(results: dict) -> list[dict]:
    cm, ep = results["cold_morning"]["runs"], results["ep160"]["runs"]
    L = lambda r, s, v="primary": r["scenarios"][s][v]["label"]       # noqa: E731
    out = []
    out.append(("P1", "EP160, CENTRAL: label is TIE", L(ep["primary_k6"], "CENTRAL") == "TIE", f"label {L(ep['primary_k6'], 'CENTRAL')}, ratio {ep['primary_k6']['scenarios']['CENTRAL']['primary']['ratio']:.3f}"))
    out.append(("P2", "cold-morning, CENTRAL, primary truth: TIE or TECHNICIAN FASTER", L(cm["primary_k6"], "CENTRAL") in ("TIE", "TECHNICIAN FASTER"),
                f"label {L(cm['primary_k6'], 'CENTRAL')}, ratio {cm['primary_k6']['scenarios']['CENTRAL']['primary']['ratio']:.3f}"))
    out.append(("P3", "no case is TOOL FASTER at CENTRAL", all(L(r["primary_k6"], "CENTRAL") != "TOOL FASTER" for r in (cm, ep)), "-"))
    p4 = L(ep["primary_k6"], "FAST") != "TECHNICIAN FASTER" and L(ep["primary_k6"], "SLOW") == "TECHNICIAN FASTER" and ep["primary_k6"]["robustness"] == "SENSITIVE TO PACE"
    out.append(("P4", "EP160 SENSITIVE TO PACE (not TECHNICIAN FASTER at FAST, TECHNICIAN FASTER at SLOW)", p4, f"FAST {L(ep['primary_k6'], 'FAST')}, SLOW {L(ep['primary_k6'], 'SLOW')}, {ep['primary_k6']['robustness']}"))
    s1 = ep["primary_k6"]["scenarios"]["CENTRAL"]["S1_like_for_like"]
    out.append(("P5", "S1 (EP160) CENTRAL ratio >= 1.25", s1["ratio"] >= 1.25, f"ratio {s1['ratio']:.3f}, median {s1['median']:.2f} min"))
    pf = [r["primary_k6"]["scenarios"]["CENTRAL"]["primary"]["p_tool_faster"] for r in (cm, ep)]
    out.append(("P6", "share of worlds where the tool is faster is under 50% at CENTRAL, both cases", all(x < 0.5 for x in pf), f"cold-morning {pf[0]:.0%}, EP160 {pf[1]:.0%}"))
    pc = [r["primary_k6"]["p_all_correct"] for r in (cm, ep)]
    out.append(("P7", "tool right on every complaint in >= 90% of worlds, both cases", all(x >= 0.9 for x in pc), f"cold-morning {pc[0]:.0%}, EP160 {pc[1]:.0%}"))
    out.append(("P8", "S2 cold-morning, CENTRAL: TECHNICIAN FASTER", L(cm["S2_k6"], "CENTRAL") == "TECHNICIAN FASTER", f"label {L(cm['S2_k6'], 'CENTRAL')}, ratio {cm['S2_k6']['scenarios']['CENTRAL']['primary']['ratio']:.3f}"))
    return [dict(id=i, claim=c, held=bool(h), detail=d) for i, c, h, d in out]


def pct(x: float) -> str:
    return f"{100 * x:.0f}%"


def report(results: dict, preds: list[dict], g3: list[dict], g2: str) -> str:
    L = ["# The live v2 tool against the real technician, in working time at his own pace (Addendum 40)", "",
         "Two real calls, n = 2. Working time only (travel and waiting excluded for both, unless stated). The tool's checks are priced at the technician's observed pace from "
         "`field_cases/pace_table.json`; his time is his video minutes to diagnosis. He is correct by construction; the tool's unshown checks are answered by the catalogue's own model "
         "(home-field). The physical pace rests on two observations of one check family from one video.", ""]
    L += [f"**Gates.** G1 frozen files match: yes (the run refuses otherwise). G2: {g2}. G3 reproduction of Addendum 39's stored worlds under S2: " +
          "; ".join(f"{g['case']}: {'PASS' if g['passed'] else 'FAIL'} ({g['n_mismatch']} of {g['n_stored']} differ)" for g in g3) + ". G4 (byte-identical under two hash seeds) is checked outside this script. "
          f"G5: no error; asked checks carrying a data-fallback surcharge (excluded from the price): " +
          ", ".join(f"{r['case']} {sum(v['n_checks_with_fallback_surcharge'] for v in r['runs'].values())}" for r in results.values()) + ".", ""]
    for r in results.values():
        P = r["runs"]["primary_k6"]
        L += [f"## {r['title']}", "", f"Technician: {r['technician_minutes']} minutes to diagnosis. Tool at k = 6: median {P['steps_median']:.0f} steps ({P['median_bas_reads']:.0f} BAS reads and "
              f"{P['median_physical_checks']:.0f} physical or in-room checks), right on every complaint in {pct(P['p_all_correct'])} of worlds. Catalogue minutes (not comparable): {P['catalogue_minutes_median']:.0f}.", "",
              "**Primary (k = 6, primary truth).**", "", "| pace | tool working time, median (IQR) | tool / technician | worlds where the tool is faster | label |", "|---|---|---|---|---|"]
        for s in SCEN:
            x = P["scenarios"][s]["primary"]
            L.append(f"| {s} | {x['median']:.2f} ({x['q25']:.2f}-{x['q75']:.2f}) | {x['ratio']:.2f} | {pct(x['p_tool_faster'])} | {x['label']} |")
        L += ["", f"Robustness: **{P['robustness']}**.", "", "**Sensitivities at CENTRAL.**", "", "| variant | tool median (IQR) | ratio | worlds where the tool is faster | label |", "|---|---|---|---|---|"]
        rows = [("S2: Addendum 39's sampling truth, k = 6", r["runs"]["S2_k6"]["scenarios"]["CENTRAL"]["primary"]),
                ("S3: waiting added, k = 6", P["scenarios"]["CENTRAL"]["S3_wait_added"]),
                ("padding k = 2", r["runs"]["primary_k2"]["scenarios"]["CENTRAL"]["primary"]), ("padding k = 12", r["runs"]["primary_k12"]["scenarios"]["CENTRAL"]["primary"])]
        if "S1_like_for_like" in P["scenarios"]["CENTRAL"]:
            rows.insert(0, ("S1: plus his physical confirmation (3.25 min) when the tool asks for none", P["scenarios"]["CENTRAL"]["S1_like_for_like"]))
        for name, x in rows:
            L.append(f"| {name} | {x['median']:.2f} ({x['q25']:.2f}-{x['q75']:.2f}) | {x['ratio']:.2f} | {pct(x['p_tool_faster'])} | {x['label']} |")
        L.append("")
    L += ["## Registered predictions (evaluated by the runner)", "", "| | claim | held | detail |", "|---|---|---|---|"]
    for p in preds:
        L.append(f"| {p['id']} | {p['claim']} | {'yes' if p['held'] else 'NO'} | {p['detail']} |")
    return "\n".join(L)


def selftest() -> str:
    pace = json.loads(PACE_FILE.read_text())
    c = pace["scenarios"]["CENTRAL"]
    t = price(["bas_zone", "bas_zone", "thermostat"], c)
    assert abs(t - (0.375 * 2 * 2 + 0.1625 * 6)) < 1e-12, t                              # 1.5 + 0.975
    assert abs(price(["override_room"], c, wait=True) - (0.1625 * 2 + 30)) < 1e-12
    assert abs(price(["reheat_coil"], c) - 1.625) < 1e-12 and abs(price(["bas_reheat"], c) - 0.75) < 1e-12
    for n, ck in CK.items():
        assert isinstance(float(ck.do_min), float) and float(ck.do_min) >= 0 and float(ck.wait_min) >= 0, n
        assert family(n) in ("bas", "physical"), n
    assert sum(family(n) == "bas" for n in CK) == 8 and sum(family(n) == "physical" for n in CK) == 22 and len(CK) == 30
    for name, sc in pace["scenarios"].items():
        assert abs(sc["ratio_bas"] * 2.0 - sc["bas_minutes_per_read"]) < 1e-12 and abs(sc["ratio_physical"] * 10.0 - sc["physical_minutes_per_reheat_coil"]) < 1e-12, name
    return "pricing hand-checked (BAS 0.75 per read, reheat_coil 1.625 at CENTRAL, waiting added unscaled); all 30 checks classified (8 BAS, 22 physical) with a do_min"


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("--selftest", action="store_true")
    ap.add_argument("--draws", type=int, default=1000)
    a = ap.parse_args()
    g2 = selftest()
    if a.selftest:
        print("selftest ok:", g2)
        return
    check_frozen3()
    pace = json.loads(PACE_FILE.read_text())
    OUT.mkdir(parents=True, exist_ok=True)
    results, g3 = {}, []
    with tempfile.TemporaryDirectory() as td:
        for name in FCC.COMPETE_FILES:
            comp = json.loads((CASES_DIR / name).read_text())
            base = json.loads((CASES_DIR / comp["base_case"]).read_text())
            r = run_case(base, comp, pace, Path(td), a.draws)
            results[base["id"]] = r
            if a.draws == 1000:
                g3.append(g3_reproduction(r))
    if g3 and not all(g["passed"] for g in g3):
        raise SystemExit(f"G3 FAILED (NO RESULT): {g3}")
    for r in results.values():
        rows = r["worlds"]["primary_k6"]
        with open(OUT / f"draws_{r['case']}_k6.csv", "w", newline="") as fh:
            wr = csv.writer(fh)
            wr.writerow(["draw", "steps", "t_fast", "t_central", "t_slow", "all_correct", "checks"])
            for w in rows:
                wr.writerow([w["draw"], w["steps"]] + [f"{price(w['checks'], pace['scenarios'][s]):.4f}" for s in SCEN] + [int(w["all_correct"]), " ".join(w["checks"])])
    summary = {cid: {k: v for k, v in r.items() if k != "worlds"} for cid, r in results.items()}
    preds = predictions(summary)
    (OUT / "summary.json").write_text(json.dumps(dict(results=summary, predictions=preds, g3=g3, g2=g2), indent=1, sort_keys=True))
    (OUT / "report.md").write_text(report(summary, preds, g3, g2) + "\n")
    print((OUT / "report.md").read_text())
    print("hashes: pace", FC.sha256(PACE_FILE)[:12], "| runner", FC.sha256(Path(__file__))[:12])


if __name__ == "__main__":
    main()
