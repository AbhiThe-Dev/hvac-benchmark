"""POST HOC (not registered; run after seeing the registered result of study_softcopy.py; SOFTCOPY_NOTES.md's last paragraph named the limit this checks).

Two questions about the folded-room gain of the soft copy on the registered composition B (bldg11, bldg15, bldg9; 100 visits each; W0 and W1):
  (a) how much of it comes from folded rooms taking a box-level static reading of their own (which the simulation answers from the room's own cause, so an own-fault room reads NORMAL);
  (b) does it survive a harsher, more realistic convention: a faulty handler starves EVERY box it feeds, so static at any box on it reads like low static (or fan off) whatever the room's own fault is,
      while the tool still believes the catalogue's rate for local causes (the tool is wrong about this check, as it may well be in a real building).

  .venv/bin/python doc_mismatch/live_demo_bldg11/posthoc_softcopy.py        -> results/docmismatch/softcopy_study/posthoc.md
"""
import sys
from concurrent.futures import ProcessPoolExecutor
from pathlib import Path

import numpy as np

HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE))
import study_fanmix as FM  # noqa: E402
import study_mix as MX  # noqa: E402
import study_softcopy as SC  # noqa: E402
from docmismatch.troubleshoot import model as M  # noqa: E402
from docmismatch.troubleshoot.v1 import catalogue as K  # noqa: E402

OUT = HERE.parent.parent / "results" / "docmismatch" / "softcopy_study"
CONV = {"original": False, "harsh box static": True}


class HarshOracle(MX.FamOracle):
    """static at a box on a faulty handler reads as the handler's state, whatever the room's own fault is; every other answer is the parent's."""

    def ask_room(self, i, ck, target):
        st = self.visit["ahu_state"][self.cases[i].ahu]
        if ck.name != "static_at_box" or st == "ok":
            return super().ask_room(i, ck, target)
        c = self.tc[ck.name]
        p = float(np.clip(K.p_pos(c, (st,), target, self.cases[i].doc), M.RATE_FLOOR, 1.0 - M.RATE_FLOOR))
        word = ck.words[0] if self._u("room", self.cases[i].member, f"{ck.name}|{target}") < p else ck.words[1]
        assert word in ck.words
        return word


def run_chunk(args):
    fam, bld, wi, harsh, lo, hi = args
    visits, cases, checks = SC.fam_visits(fam, bld, range(lo, hi))
    a = list(SC.WORLDS.values())[wi][1]
    out = []
    for visit in visits:
        cl = [cases[r] for r in visit["rooms"]]
        visit = dict(visit, faulty=[visit["ahu_state"][c.ahu] != "ok" for c in cl])
        orc = (HarshOracle if harsh else MX.FamOracle)(visit, cl, wi, a, checks)
        rec = {}
        for arm in SC.ARMS:
            r = SC.run_arm(arm, cl, orc)
            rec[arm] = dict(guess=[tuple(g) for g in r["guess"]], conc=[bool(c) for c in r["concluded"]], own=[bool(x) for x in r["own_static"]], minutes=float(r["minutes"]))
        out.append((visit, rec))
    return (fam, bld, (wi, harsh), lo, hi), out


def main():
    tasks = [("B", b, wi, h, lo, lo + 20) for b in SC.REAL for wi in (0, 1) for h in (False, True) for lo in range(0, 100, 20)]
    with ProcessPoolExecutor(max_workers=9) as ex:
        results = list(ex.map(run_chunk, tasks))
    res = SC.collect(results)
    L = ["# Post hoc: where does the soft copy's folded-room gain come from? (NOT registered; run after the registered result was seen)", "",
         "Registered composition B, 100 visits per building, simulated answers. `original` = the convention of every earlier study (a room check is answered from the room's own cause, so an own-fault room reads NORMAL static at its own box). "
         "`harsh box static` = static at any box on a faulty handler reads as the handler's state whatever the room's own fault is, while the tool still believes the catalogue's rate for local causes.", "",
         "| building | answers | convention | arm | accuracy | folded rooms (n) | folded rooms that took their own static reading | folded rooms right: with / without their own reading | folded called low static | minutes / visit | wrong and confident | with the hedge |", "|---|---|---|---|---|---|---|---|---|---|---|---|"]
    for b in SC.REAL:
        for wi, w in ((0, "W0"), (1, "W1")):
            for h, cname in ((False, "original"), (True, "harsh box static")):
                d = res["B", b, (wi, h)]
                m = SC.masks(d)["folded"]
                for arm in SC.ARMS:
                    s = SC.stats(d, arm)
                    x = d[arm]
                    own = x["own"] & m
                    nown = m & ~x["own"]
                    r_with = f"{100 * x['ok'][own].mean():.0f}% ({int(own.sum())})" if own.any() else "-"
                    r_wo = f"{100 * x['ok'][nown].mean():.0f}% ({int(nown.sum())})" if nown.any() else "-"
                    L.append(f"| {b} | {w} | {cname} | {arm} | {s['acc']:.1f}% | {s['folded']:.1f}% ({s['n_folded']}) | {100 * own.sum() / max(m.sum(), 1):.0f}% | {r_with} / {r_wo} | {s['folded_ls']:.0f}% | {s['minutes']:.0f} | {s['wc']:.1f}% | {s['wc_h']:.1f}% |")
    L += ["", "## Paired differences against HARD, same convention (accuracy over all rooms and over folded rooms; minutes)", "", "| building | answers | convention | arm | all rooms (95% CI) | folded rooms (95% CI) | minutes (95% CI) |", "|---|---|---|---|---|---|---|"]
    for b in SC.REAL:
        for wi, w in ((0, "W0"), (1, "W1")):
            for h, cname in ((False, "original"), (True, "harsh box static")):
                d = res["B", b, (wi, h)]
                for arm in ("SOFT", "JOINT"):
                    g, gci = SC.diff_ci([d], arm, "HARD", "all")
                    f_, fci = SC.diff_ci([d], arm, "HARD", "folded")
                    dm, dmci = SC.minutes_diff(d, arm)
                    L.append(f"| {b} | {w} | {cname} | {arm} | {g:+.1f} ({gci[0]:+.1f}, {gci[1]:+.1f}) | {f_:+.1f} ({fci[0]:+.1f}, {fci[1]:+.1f}) | {dm:+.0f} ({dmci[0]:+.0f}, {dmci[1]:+.0f}) |")
    OUT.mkdir(parents=True, exist_ok=True)
    (OUT / "posthoc.md").write_text("\n".join(L))
    print("\n".join(L))


if __name__ == "__main__":
    main()
