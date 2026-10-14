"""POST HOC (added after the graded-readings result was seen; not in READINGS_NOTES.md predictions): what is more reliable reading worth? Single complaints on the bldg11 point map, same visit
draw as study_readings.py. The world's check rates move toward 0.5 (a > 0, worse than the tool assumes) or away from it (a < 0, sharper than the tool assumes); the tool's own rates never change.

  .venv/bin/python doc_mismatch/live_demo_bldg11/sweep_reliability.py [n_visits]
"""
import dataclasses
import sys
from pathlib import Path

import numpy as np

HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE))
import simulate as S  # noqa: E402
import study_readings as R  # noqa: E402
import visit as V  # noqa: E402
from docmismatch.troubleshoot.v1 import catalogue as K  # noqa: E402


def shift(check, a):
    """Every rate moves the fraction `a` of the way toward 0.5 (a < 0: away from it), clipped into the rate floor; a == 0 is the check itself."""
    if a == 0.0:
        return check
    f = lambda p: float(np.clip(0.5 + (p - 0.5) * (1.0 - a), S.M.RATE_FLOOR, 1.0 - S.M.RATE_FLOOR))  # noqa: E731
    if check.is_reading:
        return dataclasses.replace(check, detects={k: f(v) for k, v in check.detects.items()}, bg=f(check.bg))
    return dataclasses.replace(check, v0=dataclasses.replace(check.v0, tpr=f(check.v0.tpr), fpr=f(check.v0.fpr)), overrides={k: f(v) for k, v in check.overrides.items()})


class ShiftedOracle(S.NoisyOracle):
    def __init__(self, visit, cases, world, a):
        super().__init__(visit, cases, world, 0.0)
        self.tc = {c.name: c for c in (shift(c, a) for c in V.CHECKS)}


def main():
    n = int(sys.argv[1]) if len(sys.argv) > 1 else 1500
    S._init()
    rooms = sorted(S._CASES)
    cs, ctx = R.cases(False, rooms)
    from docmismatch.troubleshoot.v2.policies import PriorSession
    print(f"single complaints, n={n}; the tool assumes its own rates in every row")
    print("| world's checks vs the tool's assumption | accuracy | minutes | confidently wrong |\n|---|---|---|---|")
    for a, label in ((0.25, "25% worse"), (0.15, "15% worse"), (0.10, "10% worse"), (0.0, "as assumed"), (-0.10, "10% sharper"), (-0.25, "25% sharper"), (-0.5, "50% sharper"), (-1.0, "twice as sharp")):
        ok = mins = cw = 0.0
        for v in range(n):
            r, c, vis = R.draw(v, cs, rooms); case = cs[r]
            orc = ShiftedOracle(vis, [case], 2, a)
            s = PriorSession(case); s.ctx = ctx; k = 0
            while k < 12:
                st = s.next_step()
                if st is None: break
                ck = st.check
                s.report(orc.ask_ahu(case.ahu, ck) if ck.subject == "ahu" else orc.ask_room(0, ck, st.target)); k += 1
            top, p = s.status()["ranked"][0]
            right = tuple(top) == c
            ok += right; mins += s.elapsed; cw += (not right) and p >= case.settings.tau
        print(f"| {label} (a = {a:+.2f}) | {100*ok/n:.1f}% | {mins/n:.0f} | {100*cw/n:.1f}% |", flush=True)


main()
