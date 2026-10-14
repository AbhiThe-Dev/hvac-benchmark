"""Addendum 38 (PREREGISTRATION_DR.md): replay two real technician videos against the live v2 tool.

The real v2 CLI loop (`docmismatch.troubleshoot.v2.cli.run`) is driven by a scripted technician that answers a check only when the case file's frozen answer table says the video shows
that quantity, and says "unsure" otherwise (the check's minutes are spent, nothing is learned). The tool's settings are the live CLI's own: JointSession, min_rate = LIVE_MIN_RATE_DEFAULT,
drawings "mostly_right", f = 0.03, lookahead 1, group_informing off.

  .venv/bin/python doc_mismatch/scripts/88_field_cases.py --selftest      # harness check on the synthetic example building; never touches the real cases
  .venv/bin/python doc_mismatch/scripts/88_field_cases.py                 # the two real cases at k = 2, 6, 12 padding rooms (6 is primary); refuses to run if a case file changed since the freeze

Outputs (results/docmismatch/field_cases/): trace_<case>_k<k>.json, cli_<case>_k<k>.txt (the tool's own text), report.md.
"""

from __future__ import annotations

import argparse
import copy
import hashlib
import json
import sys
import tempfile
from pathlib import Path

import numpy as np

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "src"))

from docmismatch.troubleshoot import model as M  # noqa: E402
from docmismatch.troubleshoot.v1 import data as D  # noqa: E402
from docmismatch.troubleshoot.v1.engine import make_case_v1  # noqa: E402
from docmismatch.troubleshoot.v2 import cli as V2  # noqa: E402
from docmismatch.troubleshoot.v2.joint import JointSession, JointSettings  # noqa: E402

CASES_DIR = ROOT / "field_cases"
FROZEN = CASES_DIR / "FROZEN.sha256"
OUT = ROOT.parent / "results" / "docmismatch" / "field_cases"
CASE_FILES = ("cold_morning.json", "ep160.json")


def sha256(p: Path) -> str:
    return hashlib.sha256(p.read_bytes()).hexdigest()


def check_frozen() -> None:
    if not FROZEN.exists():
        raise SystemExit(f"{FROZEN} does not exist: the case files have not been frozen")
    want = dict(line.split()[::-1] for line in FROZEN.read_text().splitlines() if line.strip())
    for name in CASE_FILES:
        if want.get(name) != sha256(CASES_DIR / name):
            raise SystemExit(f"{name} has changed since it was frozen ({FROZEN.name}); a change after the freeze is a logged deviation, not a silent edit")


# ---------------------------------------------------------------------------------------------- building
def build_building(spec: dict, k: int | None, tmp: Path) -> D.Building1:
    b = copy.deepcopy(spec["building"])
    pad = spec.get("padding")
    if pad and k:
        for i in range(1, k + 1):
            b["equipment"] += [{"id": f"VAV-P{i}", "kind": "VAV", "area": pad["area"]}, {"id": f"Room-P{i}", "kind": "Zone", "area": pad["area"]}]
            b["claims"]["vav_zone"][f"Room-P{i}"] = f"VAV-P{i}"
            b["claims"]["ahu_vav"][f"VAV-P{i}"] = pad["ahu"]
    p = tmp / f"{spec['id']}_k{k}.json"
    p.write_text(json.dumps(b))
    return D.load_building_v1(p)


# ---------------------------------------------------------------------------------------------- the scripted technician
class Replay:
    """Answers each recommendation from the frozen table: the video's answer if it shows that quantity, 'unsure' otherwise."""

    def __init__(self, sess: JointSession, spec: dict):
        self.sess, self.spec = sess, spec
        self.table = {}
        for a in spec["answers"]:
            key = ("complaint", a["room"], a["check"]) if a["scope"] == "complaint" else ("ahu", a["ahu"], a["check"])
            self.table[key] = a
        self.steps: list[dict] = []

    def _truth_mass(self, marg) -> list[dict]:
        out = []
        for i, m in enumerate(marg):
            causes = self.sess.model.causes[i]
            acc = set(self.spec["complaints"][i]["truth_accept"])
            order = np.argsort(-m, kind="stable")[:3]
            out.append(dict(room=self.sess.model.cases[i].member, truth_mass=float(sum(p for c, p in zip(causes, m) if c[0] in acc)),
                            top=[(list(causes[j]), float(m[j])) for j in order]))
        return out

    def __call__(self, prompt: str) -> str:
        o = self.sess._pending
        m = self.sess.model
        if o.kind == "complaint":
            who = m.cases[o.who].member
            key = ("complaint", who, o.check.name)
        else:
            who = o.who
            key = ("ahu", who, o.check.name)
        hit = self.table.get(key)
        ans = "u" if hit is None else ("a" if hit["outcome"] == o.check.words[0] else "n")
        self.steps.append(dict(n=len(self.steps) + 1, kind=o.kind, who=who, check=o.check.name, target=o.target, minutes=float(o.minutes), p_pos=float(o.pyes), gain=float(o.gain),
                               audience=int(o.audience), evidence="E" if hit else "U", outcome=hit["outcome"] if hit else "unsure", t=hit["t"] if hit else None,
                               state_before=self._truth_mass(self.sess.marginals())))
        return ans


def run_one(spec: dict, k: int | None, tmp: Path) -> dict:
    b = build_building(spec, k, tmp)
    tier = frozenset(spec["tier_items"])
    settings = M.Settings().with_drawings("mostly_right")
    cases = []
    for c in spec["complaints"]:
        ctx = D.Context()
        for key, v in {**spec["context"], "reheat": c["reheat"]}.items():
            ctx = ctx.declare(key, v)
        cases.append(make_case_v1(b, c["room"], tier, settings, context=ctx, min_rate=V2.LIVE_MIN_RATE_DEFAULT))
    sess = JointSession(cases, JointSettings(f=JointSettings().f), 1)
    rp = Replay(sess, spec)
    prior = rp._truth_mass(sess.marginals())
    lines: list[str] = []
    st = V2.run(sess, rp, lines.append)
    final = rp._truth_mass(sess.marginals())
    per = []
    for i, c in enumerate(spec["complaints"]):
        p = st["complaints"][i]
        top = p["ranked"][0]
        per.append(dict(room=c["room"], accept=c["truth_accept"], prior_truth_mass=prior[i]["truth_mass"], final_truth_mass=final[i]["truth_mass"], top_cause=list(top[0]), top_p=float(top[1]),
                        top_in_accept=top[0][0] in c["truth_accept"], concluded=bool(p["concluded"]), wrong_and_confident=bool(p["concluded"] and top[0][0] not in c["truth_accept"]),
                        prior_top=prior[i]["top"], final_top=final[i]["top"]))
    steps = rp.steps
    nE = sum(s["evidence"] == "E" for s in steps)
    tool_names = [s["check"] for s in steps]
    tech_names = [t["maps_to"] for t in spec["technician_sequence"] if t.get("maps_to")]
    stop = ("every complaint concluded" if st["concluded"] else "stalled (nothing left worth its time)" if st["stalled"] else "check limit")
    if not steps:
        stop += " [zero checks offered]"
    return dict(case=spec["id"], k=k, n_recommended=len(steps), n_answered_from_video=nE, coverage=(nE / len(steps)) if steps else None, elapsed_min=float(st["elapsed"]),
                minutes_on_E=float(sum(s["minutes"] for s in steps if s["evidence"] == "E")), minutes_on_U=float(sum(s["minutes"] for s in steps if s["evidence"] == "U")),
                stop=stop, first_check=(steps[0]["check"] if steps else None), first_check_minutes=(steps[0]["minutes"] if steps else None),
                technician_first_check=spec["technician_first_check"], first_check_matches=bool(steps and steps[0]["check"] == spec["technician_first_check"]),
                tech_checks_never_recommended=sorted(set(tech_names) - set(tool_names)), tool_checks_not_done_by_technician=sorted(set(tool_names) - set(tech_names)),
                complaints=per, ahu_posterior={a: [float(x) for x in w] for a, w in sess.model.ahu_posterior(sess.state).items()}, steps=steps, cli_text="\n".join(lines))


def fmt_pct(x: float) -> str:
    return f"{100 * x:.0f}%"


def report(results: list[dict], specs: dict, primary_k: int = 6) -> str:
    L = ["# Field-case replay of the live v2 tool (Addendum 38)", "",
         "Simulation-grade placeholders throughout; two real videos; n = 2. The scripted technician answers only from what the video shows ('E') and says 'unsure' otherwise ('U'). "
         "Padding rooms (k) are invented. Nothing here validates or calibrates the tool.", ""]
    for cid in specs:
        spec = specs[cid]
        rs = [r for r in results if r["case"] == cid]
        L += [f"## {spec['title']}", "", f"Technician's first check: `{spec['technician_first_check']}`. Tier: {spec['tier_label']}.", "",
              "| k (non-complaining rooms) | checks recommended | answered from video | coverage | tool minutes (U minutes) | first check | = technician's? | stop |", "|---|---|---|---|---|---|---|---|"]
        for r in rs:
            L.append(f"| {r['k']}{' (primary)' if r['k'] == primary_k else ''} | {r['n_recommended']} | {r['n_answered_from_video']} | "
                     f"{'-' if r['coverage'] is None else fmt_pct(r['coverage'])} | {r['elapsed_min']:.0f} ({r['minutes_on_U']:.0f}) | `{r['first_check']}` | {'yes' if r['first_check_matches'] else 'no'} | {r['stop']} |")
        L.append("")
        for r in rs:
            L += [f"### k = {r['k']}: complaints (probability mass on the accepted causes, before -> after)", "", "| complaint | accepted | before | after | tool's leading cause | concluded | wrong and confident |", "|---|---|---|---|---|---|---|"]
            for p in r["complaints"]:
                L.append(f"| {p['room']} | {', '.join(p['accept'])} | {fmt_pct(p['prior_truth_mass'])} | {fmt_pct(p['final_truth_mass'])} | {p['top_cause'][0]} {fmt_pct(p['top_p'])} | "
                         f"{'yes' if p['concluded'] else 'no'} | {'YES' if p['wrong_and_confident'] else 'no'} |")
            L += ["", "| # | check | for | min | answer | basis |", "|---|---|---|---|---|---|"]
            for s in r["steps"]:
                L.append(f"| {s['n']} | `{s['check']}` | {s['who']} | {s['minutes']:.0f} | {s['outcome']} ({s['evidence']}) | {s['t'] or ''} |")
            L += ["", f"Technician's mapped checks the tool never recommended: {', '.join(r['tech_checks_never_recommended']) or 'none'}. "
                      f"Checks the tool recommended that the technician did not do: {', '.join(r['tool_checks_not_done_by_technician']) or 'none'}.", "",
                  "Air handler belief at the end (ok / fan off / low static): " + "; ".join(f"{a}: " + " / ".join(fmt_pct(x) for x in w) for a, w in r["ahu_posterior"].items()), ""]
    return "\n".join(L)


def selftest() -> None:
    """Harness check on the synthetic example building: toy answers, no padding, never the real cases."""
    spec = dict(id="selftest", title="selftest", tier_label="T3", tier_items=sorted(D.TIERS["T3"]), context=dict(bas_access="yes", instrument="no", occupant="no"),
                building=json.loads((ROOT / "examples" / "troubleshoot_example" / "building_v2.json").read_text()), padding=None,
                complaints=[dict(room="Room-0", reheat="yes", truth_accept=["zone_sensor_setpoint"]), dict(room="Room-1", reheat="yes", truth_accept=["zone_sensor_setpoint"])],
                answers=[dict(scope="complaint", room="Room-0", check="bas_zone", outcome="abnormal", t="toy"), dict(scope="ahu", ahu="AHU-0", check="bas_ahu_fan", outcome="normal", t="toy")],
                technician_sequence=[dict(t="toy", did="toy", maps_to="bas_zone")], technician_first_check="bas_zone")
    with tempfile.TemporaryDirectory() as td:
        r = run_one(spec, None, Path(td))
    assert r["n_recommended"] >= 1 and r["steps"][0]["state_before"], r
    print(f"selftest ok: {r['n_recommended']} checks recommended, {r['n_answered_from_video']} answered from the toy table, stop = {r['stop']}")
    print(r["cli_text"][:1800])


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("--selftest", action="store_true")
    a = ap.parse_args()
    if a.selftest:
        selftest()
        return
    check_frozen()
    OUT.mkdir(parents=True, exist_ok=True)
    specs = {}
    results = []
    with tempfile.TemporaryDirectory() as td:
        for name in CASE_FILES:
            spec = json.loads((CASES_DIR / name).read_text())
            specs[spec["id"]] = spec
            for k in spec["padding"]["levels"]:
                r = run_one(spec, k, Path(td))
                results.append(r)
                (OUT / f"trace_{spec['id']}_k{k}.json").write_text(json.dumps({x: y for x, y in r.items() if x != "cli_text"}, indent=1))
                (OUT / f"cli_{spec['id']}_k{k}.txt").write_text(r["cli_text"] + "\n")
    (OUT / "report.md").write_text(report(results, specs) + "\n")
    print((OUT / "report.md").read_text())
    print("case-file hashes:", {n: sha256(CASES_DIR / n)[:12] for n in CASE_FILES}, "| runner:", sha256(Path(__file__))[:12])


if __name__ == "__main__":
    main()
