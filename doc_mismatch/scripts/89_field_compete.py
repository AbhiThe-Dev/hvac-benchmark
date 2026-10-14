"""Addendum 39 (PREREGISTRATION_DR.md): the live v2 tool against the real technician, on the two calls of Addendum 38.

Both work the same case. The technician's recorded steps are the benchmark (field_cases/compete_*.json). The tool works the same complaint with the same symptoms the technician had,
and its checks are answered from a world: the video's answer where the video shows that quantity (the frozen tables of Addendum 38), and otherwise
  model   a draw from the catalogue's own response model under the case's true cause (1000 worlds; home-field for the tool)
  normal  'normal' (deterministic)
  unsure  'unsure' (deterministic; Addendum 38's rule)
Primary metric: steps to a diagnosis, in catalogue-check units, and whether it is right. Minutes are reported, not scored (catalogue minutes include walking and waiting that the videos edit out).

  .venv/bin/python doc_mismatch/scripts/89_field_compete.py --selftest
  .venv/bin/python doc_mismatch/scripts/89_field_compete.py            # refuses to run if a frozen file changed

Outputs: results/docmismatch/field_compete/ (summary.json, report.md, per-draw rows in draws_<case>_k<k>.csv).
"""

from __future__ import annotations

import argparse
import collections
import csv
import hashlib
import importlib.util
import json
import sys
import tempfile
import zlib
from pathlib import Path

import numpy as np

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "src"))

from docmismatch.troubleshoot import model as M  # noqa: E402
from docmismatch.troubleshoot.v1 import catalogue as K  # noqa: E402
from docmismatch.troubleshoot.v1 import data as D  # noqa: E402
from docmismatch.troubleshoot.v1.engine import make_case_v1  # noqa: E402
from docmismatch.troubleshoot.v2 import cli as V2  # noqa: E402
from docmismatch.troubleshoot.v2.joint import JointSession, JointSettings  # noqa: E402

_s = importlib.util.spec_from_file_location("fc88", ROOT / "scripts" / "88_field_cases.py")
FC = importlib.util.module_from_spec(_s)
_s.loader.exec_module(FC)

CASES_DIR = FC.CASES_DIR
FROZEN2 = CASES_DIR / "FROZEN_COMPETE.sha256"
COMPETE_FILES = ("compete_cold_morning.json", "compete_ep160.json")
OUT = ROOT.parent / "results" / "docmismatch" / "field_compete"
N_DRAWS = 1000
PRIMARY_K = 6
LEVELS = (2, 6, 12)
FEWER_RATIO, MORE_RATIO, MIN_P_CORRECT = 1.25, 0.8, 0.9


def check_frozen2() -> None:
    FC.check_frozen()
    if not FROZEN2.exists():
        raise SystemExit(f"{FROZEN2} does not exist: the competition files have not been frozen")
    want = dict(line.split()[::-1] for line in FROZEN2.read_text().splitlines() if line.strip())
    for name in COMPETE_FILES:
        if want.get(name) != FC.sha256(CASES_DIR / name):
            raise SystemExit(f"{name} has changed since it was frozen ({FROZEN2.name}); a change after the freeze is a logged deviation, not a silent edit")


def u01(draw: int, key: str) -> float:
    """Order-independent uniform draw: a function of (world, complaint, check, target) only."""
    return float(np.random.default_rng([draw, zlib.crc32(key.encode())]).random())


class World:
    """Answers the tool's recommendations: the video's answer where shown, else by `policy`."""

    def __init__(self, sess: JointSession, base: dict, comp: dict, policy: str, draw: int):
        self.sess, self.comp, self.policy, self.draw = sess, comp, policy, draw
        self.table = {}
        for a in base["answers"]:
            self.table[("complaint", a["room"], a["check"]) if a["scope"] == "complaint" else ("ahu", a["ahu"], a["check"])] = a
        self.sources: list[str] = []

    def __call__(self, prompt: str) -> str:
        o, m = self.sess._pending, self.sess.model
        if o.kind == "complaint":
            who = m.cases[o.who].member
            key = ("complaint", who, o.check.name)
        else:
            who = o.who
            key = ("ahu", who, o.check.name)
        hit = self.table.get(key)
        if hit is not None:
            self.sources.append("E")
            return "a" if hit["outcome"] == o.check.words[0] else "n"
        if self.policy == "unsure":
            self.sources.append("U")
            return "u"
        if self.policy == "normal":
            self.sources.append("N")
            return "n"
        if o.kind == "complaint":
            p = float(np.clip(K.p_pos(o.check, (self.comp["sampling_truth"][who],), o.target, m.cases[o.who].doc), M.RATE_FLOOR, 1.0 - M.RATE_FLOOR))
        else:
            p = float(np.clip(o.check.bg, M.RATE_FLOOR, 1.0 - M.RATE_FLOOR))
        self.sources.append("M")
        return "a" if u01(self.draw, f"{key}|{o.target}") < p else "n"


def make_cases(base: dict, comp: dict, k: int, tmp: Path) -> list:
    b = FC.build_building(base, k, tmp)
    tier = frozenset(base["tier_items"])
    settings = M.Settings().with_drawings("mostly_right")
    sym = comp["symptoms"]
    out = []
    for c in base["complaints"]:
        ctx = D.Context()
        for key, v in {**base["context"], "reheat": c["reheat"]}.items():
            ctx = ctx.declare(key, v)
        out.append(make_case_v1(b, c["room"], tier, settings, airflow=sym.get("airflow"), feel=sym.get("feel"), context=ctx, min_rate=V2.LIVE_MIN_RATE_DEFAULT))
    return out


def one_world(cases: list, base: dict, comp: dict, policy: str, draw: int) -> dict:
    sess = JointSession(cases, JointSettings(f=JointSettings().f), 1)
    w = World(sess, base, comp, policy, draw)
    st = V2.run(sess, w, lambda s: None)
    per = []
    for i, c in enumerate(base["complaints"]):
        p = st["complaints"][i]
        top = p["ranked"][0]
        per.append(dict(room=c["room"], top=top[0][0], top_p=float(top[1]), correct=top[0][0] in c["truth_accept"], concluded=bool(p["concluded"]),
                        wrong_and_confident=bool(p["concluded"] and top[0][0] not in c["truth_accept"])))
    return dict(draw=draw, steps=int(st["n_checks"]), minutes=float(st["elapsed"]), first=sess.log[0][2] if sess.log else None, checks=[x[2] for x in sess.log],
                n_E=w.sources.count("E"), n_M=w.sources.count("M"), complaints=per, all_correct=all(p["correct"] for p in per), any_wc=any(p["wrong_and_confident"] for p in per),
                all_concluded=all(p["concluded"] for p in per))


def quant(xs, q):
    return float(np.quantile(np.array(xs, float), q))


def summarise(rows: list[dict], tech_steps: int) -> dict:
    steps = [r["steps"] for r in rows]
    n = len(rows)
    med = quant(steps, 0.5)
    ratio = med / tech_steps
    p_corr = sum(r["all_correct"] for r in rows) / n
    return dict(n=n, steps_median=med, steps_q25=quant(steps, 0.25), steps_q75=quant(steps, 0.75), steps_mean=float(np.mean(steps)), ratio_median_to_technician=ratio,
                p_steps_le_technician=sum(s <= tech_steps for s in steps) / n, p_steps_lt_technician=sum(s < tech_steps for s in steps) / n, p_all_correct=p_corr,
                per_complaint_correct=[sum(r["complaints"][i]["correct"] for r in rows) / n for i in range(len(rows[0]["complaints"]))],
                p_wrong_and_confident=sum(r["any_wc"] for r in rows) / n, p_all_concluded=sum(r["all_concluded"] for r in rows) / n, minutes_median=quant([r["minutes"] for r in rows], 0.5),
                first_check=dict(sorted(collections.Counter(r["first"] for r in rows).items(), key=lambda kv: (-kv[1], str(kv[0])))[:4]),
                checks_most_asked=dict(sorted(collections.Counter(c for r in rows for c in sorted(set(r["checks"]))).items(), key=lambda kv: (-kv[1], kv[0]))[:8]),
                mean_checks_answered_by_video=float(np.mean([r["n_E"] for r in rows])), mean_checks_answered_by_world=float(np.mean([r["n_M"] for r in rows])))


def verdict(s: dict) -> str:
    if s["ratio_median_to_technician"] >= FEWER_RATIO:
        return "TECHNICIAN FEWER STEPS"
    if s["ratio_median_to_technician"] <= MORE_RATIO and s["p_all_correct"] >= MIN_P_CORRECT:
        return "TOOL FEWER STEPS"
    return "TIE"


def run_case(base: dict, comp: dict, tmp: Path, n_draws: int, levels=LEVELS) -> dict:
    tech = comp["technician"]
    res = dict(case=comp["id"], title=base["title"], technician=dict(steps=tech["steps_primary"], steps_per_complaint=tech["steps_per_complaint_count"],
                                                                      video_minutes=tech["video_minutes_to_diagnosis"], correct=tech["diagnosis_correct"], verified=tech["verified"]), runs={})
    for k in levels:
        cases = make_cases(base, comp, k, tmp)
        rows = [one_world(cases, base, comp, "model", d) for d in range(n_draws)]
        s = summarise(rows, tech["steps_primary"])
        s["verdict"] = verdict(s)
        s["ratio_per_complaint_count"] = s["steps_median"] / tech["steps_per_complaint_count"]
        res["runs"][f"model_k{k}"] = s
        if k == PRIMARY_K:
            OUT.mkdir(parents=True, exist_ok=True)
            with open(OUT / f"draws_{comp['id']}_k{k}.csv", "w", newline="") as fh:
                wr = csv.writer(fh)
                wr.writerow(["draw", "steps", "minutes", "first_check", "all_correct", "any_wrong_and_confident", "all_concluded", "checks"])
                for r in rows:
                    wr.writerow([r["draw"], r["steps"], f"{r['minutes']:.1f}", r["first"], int(r["all_correct"]), int(r["any_wc"]), int(r["all_concluded"]), " ".join(r["checks"])])
    for pol in ("normal", "unsure"):
        cases = make_cases(base, comp, PRIMARY_K, tmp)
        r = one_world(cases, base, comp, pol, 0)
        res["runs"][f"{pol}_k{PRIMARY_K}"] = dict(steps=r["steps"], minutes=r["minutes"], first=r["first"], checks=r["checks"], all_correct=r["all_correct"], any_wc=r["any_wc"],
                                                   complaints=r["complaints"], n_E=r["n_E"])
    return res


def pct(x: float) -> str:
    return f"{100 * x:.0f}%"


def report(results: list[dict]) -> str:
    L = ["# The live v2 tool against the real technician (Addendum 39)", "",
         "Two real calls, n = 2. Steps are catalogue-check units. The technician's accepted causes are his own findings, so he cannot lose on accuracy by construction. "
         "Tool answers for checks the video does not show are drawn from the catalogue's own response model (home-field). Minutes are reported, not scored.", ""]
    for r in results:
        t = r["technician"]
        L += [f"## {r['title']}", "", f"**Technician:** {t['steps']} steps ({t['steps_per_complaint']} if each complaint's check is counted separately), {t['video_minutes']} video minutes to diagnosis, "
                                      f"correct by construction. Verified in the video: {t['verified']}", "",
              "| tool, answers from the world | steps median (IQR) | tool / technician | P(tool steps <= technician's) | P(right on every complaint) | P(wrong and confident) | P(concluded) | catalogue min (median) | verdict |",
              "|---|---|---|---|---|---|---|---|---|"]
        for key, s in r["runs"].items():
            if key.startswith("model"):
                L.append(f"| model draws, k = {key.split('k')[1]}{' (primary)' if key.endswith(f'k{PRIMARY_K}') else ''} | {s['steps_median']:.0f} ({s['steps_q25']:.0f}-{s['steps_q75']:.0f}) | "
                         f"{s['ratio_median_to_technician']:.2f} | {pct(s['p_steps_le_technician'])} | {pct(s['p_all_correct'])} | {pct(s['p_wrong_and_confident'])} | {pct(s['p_all_concluded'])} | "
                         f"{s['minutes_median']:.0f} | {s['verdict']} |")
        for key in (f"normal_k{PRIMARY_K}", f"unsure_k{PRIMARY_K}"):
            s = r["runs"][key]
            L.append(f"| {key.split('_')[0]} (one run, k = {PRIMARY_K}) | {s['steps']} | {s['steps'] / t['steps']:.2f} | - | {'yes' if s['all_correct'] else 'no'} | {'yes' if s['any_wc'] else 'no'} | - | {s['minutes']:.0f} | - |")
        p = r["runs"][f"model_k{PRIMARY_K}"]
        L += ["", f"First check the tool picks (primary): {p['first_check']}. Checks it asks most often: {p['checks_most_asked']}. On average {p['mean_checks_answered_by_video']:.1f} of its checks are answered "
                  f"by the video and {p['mean_checks_answered_by_world']:.1f} by the drawn world. Right per complaint: {[pct(x) for x in p['per_complaint_correct']]}.", ""]
    return "\n".join(L)


def selftest() -> None:
    base = dict(id="selftest", title="selftest", tier_label="T3", tier_items=sorted(D.TIERS["T3"]), context=dict(bas_access="yes", instrument="no", occupant="no"),
                building=json.loads((ROOT / "examples" / "troubleshoot_example" / "building_v2.json").read_text()), padding=None,
                complaints=[dict(room="Room-0", reheat="yes", truth_accept=["zone_sensor_setpoint"]), dict(room="Room-1", reheat="yes", truth_accept=["zone_sensor_setpoint"])],
                answers=[dict(scope="complaint", room="Room-0", check="bas_zone", outcome="abnormal", t="toy")], technician_sequence=[], technician_first_check="bas_zone")
    comp = dict(id="selftest", symptoms=dict(feel="too_cold", airflow=None), sampling_truth={"Room-0": "zone_sensor_setpoint", "Room-1": "zone_sensor_setpoint"}, ahu_state_for_sampling="ok",
                technician=dict(steps_primary=4, steps_per_complaint_count=4, video_minutes_to_diagnosis=1.0, diagnosis_correct=True, verified="toy"))
    with tempfile.TemporaryDirectory() as td:
        cases = make_cases(base, comp, 0, Path(td))
        a = [one_world(cases, base, comp, "model", d) for d in range(30)]
        b = [one_world(cases, base, comp, "model", d) for d in range(30)]
    assert [r["checks"] for r in a] == [r["checks"] for r in b], "draws are not reproducible"
    assert len({tuple(r["checks"]) for r in a}) > 1, "draws do not vary"
    assert all(0 < r["steps"] <= 24 for r in a)
    s = summarise(a, 4)
    print(f"selftest ok: 30 worlds reproduce exactly and vary; steps median {s['steps_median']:.0f}, P(correct) {s['p_all_correct']:.2f}; verdict machinery -> {verdict(s)}")


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("--selftest", action="store_true")
    ap.add_argument("--draws", type=int, default=N_DRAWS)
    a = ap.parse_args()
    if a.selftest:
        selftest()
        return
    check_frozen2()
    OUT.mkdir(parents=True, exist_ok=True)
    results = []
    with tempfile.TemporaryDirectory() as td:
        for name in COMPETE_FILES:
            comp = json.loads((CASES_DIR / name).read_text())
            base = json.loads((CASES_DIR / comp["base_case"]).read_text())
            results.append(run_case(base, comp, Path(td), a.draws))
    (OUT / "summary.json").write_text(json.dumps(results, indent=1))
    (OUT / "report.md").write_text(report(results) + "\n")
    print((OUT / "report.md").read_text())
    print("hashes:", {n: FC.sha256(CASES_DIR / n)[:12] for n in COMPETE_FILES}, "| runner:", FC.sha256(Path(__file__))[:12])


if __name__ == "__main__":
    main()
