"""Graded numeric readings, first look (EXPLORATORY; predictions in READINGS_NOTES.md were written and hashed before the first run).

Single complaints on the bldg11 point map. A numeric world gives every two-sided reading check a NUMBER (in tolerance units) instead of a yes/no: the matched world draws it from the
Gaussian shape the graded model assumes (so the graded arm has home-field advantage); the mismatched world varies fault severity from visit to visit and uses heavier tails (Student t, 4 df,
equal variance). Arms differ only in `graded`: the binary arm classifies each number against its tolerance (today's engine path), the graded arm uses the number.

  .venv/bin/python doc_mismatch/live_demo_bldg11/study_readings.py [n_visits]
"""
import dataclasses
import sys
from pathlib import Path

import numpy as np

HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE))
import simulate as S  # noqa: E402
import visit as V  # noqa: E402
from docmismatch.troubleshoot.v1 import catalogue as K, data as D, graded as G  # noqa: E402
from docmismatch.troubleshoot.v1.engine import make_case_v1  # noqa: E402
from docmismatch.troubleshoot.v2.policies import PriorSession  # noqa: E402

OUT = HERE.parent.parent / "results" / "docmismatch" / "readings_study"
ENTRY_MIN = 0.5            # sensitivity: minutes to type a number (and the expected value) instead of tapping a word
SEV_SIGMA = 0.5            # mismatched world: lognormal spread of fault severity between visits
T_DF = 4                   # mismatched world: heavy-tailed noise, scaled to equal variance


def two_sided(ck) -> bool:
    return ck.reading is not None and (ck.reading.tol is not None or ck.reading.rel_tol is not None)


class NumOracle(S.NoisyOracle):
    """Words for the yes/no checks (as before); a signed deviation in tolerance units for the two-sided reading checks."""

    def __init__(self, visit, cases, world, a, mismatched):
        super().__init__(visit, cases, world, a)
        self.mis = mismatched
        sev_rng = np.random.default_rng([S.SEED, visit["v"], world, S._crc("severity")])
        self.severity = float(np.exp(SEV_SIGMA * sev_rng.standard_normal() - SEV_SIGMA ** 2 / 2)) if mismatched else 1.0

    def _x(self, p: float, bg: float, tag: str, k1: str, k2: str) -> float:
        p = float(np.clip(p, S.M.RATE_FLOOR, 1.0 - S.M.RATE_FLOOR))
        bg = float(np.clip(bg, S.M.RATE_FLOOR, 1.0 - S.M.RATE_FLOOR))
        m, s = G.row_shape(p, bg)
        rng = np.random.default_rng([S.SEED, self.visit["v"], self.world, S._crc(tag), S._crc(k1), S._crc(k2), 77])
        sign = 1.0 if rng.random() < 0.5 else -1.0
        noise = rng.standard_t(T_DF) / np.sqrt(T_DF / (T_DF - 2.0)) if self.mis else rng.standard_normal()
        return sign * m * self.severity + s * noise

    def num_room(self, i: int, ck, target: str) -> float:
        c = self.tc[ck.name]
        return self._x(K.p_pos(c, self.visit["causes"][i], target, self.cases[i].doc), c.bg, "room", self.cases[i].member, f"{ck.name}|{target}")

    def num_ahu(self, a: str, ck) -> float:
        c = self.tc[ck.name]
        st = self.visit["ahu_state"][a]
        return self._x(c.bg if st == "ok" else c.detects.get(st, c.bg), c.bg, "ahu", a, ck.name)


def cases(graded: bool, rooms, settings=V.SETTINGS, min_rate=V.MIN_RATE):
    ctx = D.Context(**S.CTX)
    return {r: make_case_v1(V.load_building(), r, V.ITEMS, settings, context=ctx, checks=V.CHECKS, min_rate=min_rate, graded=graded) for r in rooms}, ctx


def draw(v, cs, rooms):
    rng = np.random.default_rng([S.SEED, 9000 + v]); r = rooms[int(rng.integers(len(rooms)))]
    if rng.random() < S.P_DOC_WRONG:
        alts = cs[r].candidates[1:]; c = ("unlisted",) if rng.random() < S.P_UNLISTED else ("wrong", alts[int(rng.integers(len(alts)))])
    else:
        c = (S.LOCAL_CAUSES[int(rng.integers(len(S.LOCAL_CAUSES)))],)
    return r, c, dict(v=9000 + v, kind="local", k=0, rooms=[r], causes=[c], ahu_state={"AHU06": "ok", "AHU05": "ok"})


def run(cs, ctx, rooms, world, a, n, numeric: bool, mismatched=False):
    """numeric=False is today's yes/no oracle (the sanity baseline); True gives numbers for the two-sided reading checks."""
    ok = np.zeros(n); mins = np.zeros(n); cw = np.zeros(n); nnum = np.zeros(n)
    for v in range(n):
        r, c, vis = draw(v, cs, rooms); case = cs[r]
        orc = NumOracle(vis, [case], world, a, mismatched)
        s = PriorSession(case); s.ctx = ctx; k = 0
        while k < 12:
            st = s.next_step()
            if st is None: break
            ck = st.check
            if numeric and two_sided(ck):
                x = orc.num_ahu(case.ahu, ck) if ck.subject == "ahu" else orc.num_room(0, ck, st.target)
                e = ck.reading.expected if ck.reading.expected is not None else 100.0
                lo, hi = ck.reading.band({}, e)
                s.report(reading=0.5 * (lo + hi) + 0.5 * (hi - lo) * x, expected=e); nnum[v] += 1
            else:
                s.report(orc.ask_ahu(case.ahu, ck) if ck.subject == "ahu" else orc.ask_room(0, ck, st.target))
            k += 1
        top, p = s.status()["ranked"][0]
        right = tuple(top) == c
        ok[v], mins[v], cw[v] = right, s.elapsed, (not right) and p >= case.settings.tau
    return dict(ok=ok, mins=mins, cw=cw, nnum=nnum)


def boot(d, B=2000, seed=5):
    rng = np.random.default_rng(seed); n = len(d)
    return np.percentile([d[rng.integers(n, size=n)].mean() for _ in range(B)], [2.5, 97.5])


def main():
    n = int(sys.argv[1]) if len(sys.argv) > 1 else 1500
    S._init()
    rooms = sorted(S._CASES)
    cb, ctx = cases(False, rooms); cg, _ = cases(True, rooms)
    lines = [f"# Graded readings, first look (exploratory; predictions in READINGS_NOTES.md)\n", f"Single complaints on the bldg11 point map, n = {n} per cell, accuracy % (minutes per complaint) [confidently wrong %].\n"]
    res = {}
    for wname, (world, a) in {"W0": (0, 0.0), "W1": (1, 0.25)}.items():
        res[wname, "baseline"] = run(cb, ctx, rooms, world, a, n, numeric=False)
        for mname, mis in (("matched", False), ("mismatched", True)):
            res[wname, mname, "binary"] = run(cb, ctx, rooms, world, a, n, True, mis)
            res[wname, mname, "graded"] = run(cg, ctx, rooms, world, a, n, True, mis)
    def cell(r):
        return f"{100*r['ok'].mean():.1f}% ({r['mins'].mean():.0f}) [{100*r['cw'].mean():.1f}]"
    lines += ["| world | numbers from | yes/no baseline | binary arm | graded arm | graded minus binary, accuracy points (95% CI) | minutes | numeric readings per visit | minutes with +0.5 min per reading |", "|---|---|---|---|---|---|---|---|---|"]
    for w in ("W0", "W1"):
        for m in ("matched", "mismatched"):
            b, g = res[w, m, "binary"], res[w, m, "graded"]
            d = 100 * (g["ok"] - b["ok"]); ci = boot(d)
            dm = (g["mins"] - b["mins"]).mean()
            cw = 100 * (g["cw"] - b["cw"]).mean()
            lines.append(f"| {w} | {m} | {cell(res[w, 'baseline'])} | {cell(b)} | {cell(g)} | {d.mean():+.1f} ({ci[0]:+.1f}, {ci[1]:+.1f}); confidently wrong {cw:+.1f} | {dm:+.1f} | {g['nnum'].mean():.2f} | {(b['mins'] + ENTRY_MIN * b['nnum']).mean():.0f} vs {(g['mins'] + ENTRY_MIN * g['nnum']).mean():.0f} |")
    lines.append("")
    # predictions
    base0, b0, g0 = res["W0", "baseline"], res["W0", "matched", "binary"], res["W0", "matched", "graded"]
    p0 = abs(100 * (b0["ok"].mean() - base0["ok"].mean())) <= 2 and abs(b0["mins"].mean() - base0["mins"].mean()) <= 3
    gain = {k: 100 * (res[k[0], k[1], "graded"]["ok"] - res[k[0], k[1], "binary"]["ok"]).mean() for k in [(w, m) for w in ("W0", "W1") for m in ("matched", "mismatched")]}
    cwd1 = 100 * (res["W1", "matched", "graded"]["cw"] - res["W1", "matched", "binary"]["cw"]).mean()
    mins_rel = (g0["mins"].mean() - b0["mins"].mean()) / b0["mins"].mean()
    entry = [((r["mins"] + ENTRY_MIN * r["nnum"]).mean() - r["mins"].mean()) for r in (res["W0", "matched", "graded"],)]
    lines += ["## Predictions (written before the run)", "",
              f"- P0 sanity (binary arm vs yes/no baseline, W0 matched: accuracy within 2 points and minutes within 3): {'HELD' if p0 else 'FAILED - NO RESULT'} (accuracy {100*b0['ok'].mean():.1f}% vs {100*base0['ok'].mean():.1f}%, minutes {b0['mins'].mean():.1f} vs {base0['mins'].mean():.1f})",
              f"- P1 (matched, W0: graded +1 to +6 points, minutes within 8%): {'HELD' if 1 <= gain['W0','matched'] <= 6 and abs(mins_rel) <= 0.08 else 'FAILED'} (gain {gain['W0','matched']:+.1f}, minutes {100*mins_rel:+.1f}%)",
              f"- P2 (matched, W1: graded still gains and confidently-wrong rises by at least 1 point): {'HELD' if gain['W1','matched'] > 0 and cwd1 >= 1 else 'FAILED'} (gain {gain['W1','matched']:+.1f}, confidently wrong {cwd1:+.1f})",
              f"- P3 (mismatched W0 gain at most half of matched W0 gain): {'HELD' if gain['W0','mismatched'] <= 0.5 * gain['W0','matched'] else 'FAILED'} (mismatched {gain['W0','mismatched']:+.1f} vs matched {gain['W0','matched']:+.1f})",
              f"- P4 (no W0 cell reaches 80%): {'HELD' if all(100*res[('W0',)+k]['ok'].mean() < 80 for k in [('matched','binary'),('matched','graded'),('mismatched','binary'),('mismatched','graded')]) else 'FAILED'}",
              f"- P5 (entry cost changes minutes by less than 3): {'HELD' if entry[0] < 3 else 'FAILED'} ({entry[0]:.1f} min)", ""]
    OUT.mkdir(parents=True, exist_ok=True)
    (OUT / "report.md").write_text("\n".join(lines))
    print("\n".join(lines))


if __name__ == "__main__":
    main()
