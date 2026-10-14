"""EXPLORATORY: accuracy on visits shaped like the demo's script (4 rooms on the faulty handler AHU06 with low static; on the healthy handler AHU05 one failed actuator and one wrong documented box),
with random rooms and noisy answers, against the registered sim's mixed visits (shared plus random local rooms, half the visits with no shared cause). Not registered; no predictions were written.

  .venv/bin/python doc_mismatch/live_demo_bldg11/demo_composition.py [n_visits]
"""
import sys
from pathlib import Path

import numpy as np

HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE))
import simulate as S  # noqa: E402
import visit as V  # noqa: E402
import world as Wd  # noqa: E402
from docmismatch.troubleshoot.v2.joint import JointSettings  # noqa: E402
from docmismatch.troubleshoot.v2.policies import run_policy  # noqa: E402


def demo_visit(v, cases):
    rng = np.random.default_rng([S.SEED, 777, v])
    a06 = sorted(r for r in cases if cases[r].ahu == "AHU06")
    a05 = sorted(r for r in cases if cases[r].ahu == "AHU05")
    sh = [a06[i] for i in rng.choice(len(a06), 4, replace=False)]
    act, wrong = [a05[i] for i in rng.choice(len(a05), 2, replace=False)]
    alts = cases[wrong].candidates[1:]
    items = [(r, ("low_static",), "shared") for r in sh] + [(act, ("actuator_fail",), "local"), (wrong, ("wrong", alts[int(rng.integers(len(alts)))]), "local")]
    items = [items[int(i)] for i in rng.permutation(len(items))]
    return dict(v=v, kind="shared", k=4, rooms=[i[0] for i in items], causes=[i[1] for i in items], seg=[i[2] for i in items], ahu_state={"AHU06": "low_static", "AHU05": "ok"})


def main():
    n = int(sys.argv[1]) if len(sys.argv) > 1 else 200
    S._init()
    cases = S._CASES
    sc = Wd.load_scenario()
    settings = {"shipped": JointSettings(), "mixed": V.joint_settings(sc, "mixed")}
    print(f"visits shaped like the demo's script, {n} per cell; 6 complaints each; accuracy per room (minutes per visit)")
    print("| answers | setting | all 6 | the 4 shared-cause rooms | the 2 local rooms | visits with all 6 right |\n|---|---|---|---|---|---|")
    for wname, wi, a in (("W0 (checks as the tool assumes)", 0, 0.0), ("W1 (checks 25% worse)", 1, 0.25)):
        for sname, js in settings.items():
            ok = np.zeros((n, 6)); seg = np.zeros((n, 6), bool); mins = np.zeros(n)
            for v in range(n):
                vis = demo_visit(v, cases)
                cl = [cases[r] for r in vis["rooms"]]
                orc = S.NoisyOracle(vis, cl, wi, a)
                r = run_policy("tool_ticket_memo2", cl, orc, [S.CTX] * 6, js)
                ok[v] = [tuple(g) == tuple(c) for g, c in zip(r["guess"], vis["causes"])]
                seg[v] = [s == "shared" for s in vis["seg"]]
                mins[v] = r["minutes"]
            print(f"| {wname} | {sname} | {100*ok.mean():.1f}% ({mins.mean():.0f} min) | {100*ok[seg].mean():.1f}% | {100*ok[~seg].mean():.1f}% | {100*ok.all(axis=1).mean():.0f}% |", flush=True)


main()
