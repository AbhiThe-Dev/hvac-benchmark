"""Does the already-confirmed `min_rate` lever (Addenda 34-36) also cut minutes for the T3-noattr documentation profile (Exploratory note E2), and does it close the gap against the
language model on the ordinary (non-shared) complaints where E2's extension found it losing? (PREREGISTRATION_DR.md; exploratory, asked directly by the user: "how can we make it faster
to beat the LLM technician... fine if we sacrifice a TINY bit of accuracy for a huge speed gain".)

Motivation for trying this lever specifically: E2's extension found T3-noattr pays two costs relative to full T3 -- fallback-penalised checks (`k_factor`, `max_airflow`, `static_at_box`
each cost extra minutes without documented attributes) and one check (`design_load`) becoming entirely unavailable, forcing costlier substitutes. Raising `min_rate` (the bits-per-minute
bar a check must clear to be offered) makes the tool more reluctant to pay for a check that is only marginally informative -- exactly the class of check this profile now has more of.

No new engine code: this reuses `study_minrate.run_variant_events`/`cases_with` unchanged, just pointed at the `T3-noattr` item set (already registered in `world2.TIER_ITEMS` by
importing `study_llm_ext`). Zero risk of perturbing any existing result: a parameter sweep on an item set nothing else uses.
"""

from __future__ import annotations

import numpy as np

from ..v1.engine import make_case_v1
from . import policies as P
from . import study_joint as J
from . import study_llm as L
from . import study_llm_ext as E  # noqa: F401  (import side effect: registers "T3-noattr" in world2.TIER_ITEMS)
from . import study_minrate as MR
from . import world2 as W

GRID_FINE = (0.003, 0.01, 0.015, 0.017, 0.018, 0.02, 0.022, 0.025, 0.03, 0.05)
SPOT_CELLS = (0, 5, 9, 13, 17)                 # a spread of shared-frequency / map / reliability levels, not just the primary cell
CANDIDATE = 0.02                                # this note's recommendation


def primary_sweep(grid: tuple = GRID_FINE, n: int = J.N_EPISODES) -> list[dict]:
    cell = next(c for c in J.all_cells() if c.is_primary)
    wp = cell.params()
    bld = W.make_building2()
    cases_all = W.make_cases(bld)
    events = [W.draw_event(0, i, wp, cases_all) for i in range(n)]
    kinds = np.array([e.kind for e in events])
    out = []
    for mr in grid:
        r = MR.run_variant_events(E.EXT_ARM, mr, events, wp, bld)
        row = dict(min_rate=mr, minutes=float(r["minutes"].mean()), acc=float(r["acc"].mean()), wc=float(r["wc"].mean()), checks=float(r["checks"].mean()))
        for k in ("single", "multi", "shared"):
            m = kinds == k
            row[f"{k}_minutes"] = float(r["minutes"][m].mean())
            row[f"{k}_acc"] = float(r["acc"][m].mean())
        out.append(row)
    return out


def cell_spot_check(cells: tuple = SPOT_CELLS, grid: tuple = (0.003, CANDIDATE), n: int = J.N_EPISODES) -> list[dict]:
    all_cells = J.all_cells()
    bld = W.make_building2()
    cases_all = W.make_cases(bld)
    out = []
    for idx in cells:
        c = all_cells[idx]
        wp = c.params()
        events = [W.draw_event(idx, i, wp, cases_all) for i in range(n)]
        row = dict(idx=idx, cell=c)
        for mr in grid:
            r = MR.run_variant_events(E.EXT_ARM, mr, events, wp, bld)
            row[mr] = dict(minutes=float(r["minutes"].mean()), acc=float(r["acc"].mean()), wc=float(r["wc"].mean()))
        out.append(row)
    return out


def _cases_ext_mr(mr: float) -> dict:
    bld = W.make_building2()
    cases = W.make_cases(bld)
    s = W.tool_settings()
    for r in range(W.N_BOX):
        cases[(E.EXT_ARM, r)] = make_case_v1(bld, f"Room-{r}", E.EXT_ITEMS, settings=s, context=W.tier_context(E.EXT_ARM, r), member_name=f"Room {r}", min_rate=mr)
    return cases


def llm_comparison(visits: list, shares: dict, events: list, wp, recs: dict, grid: tuple = (0.003, 0.01, 0.015, CANDIDATE)) -> dict:
    """Replays the routine at T3-noattr, at each `min_rate` in `grid`, on Addendum 33's own visits; writes into `recs` and returns {min_rate: {kind: compare-vs-LLM@T3}}."""
    out = {}
    for mr in grid:
        cases = _cases_ext_mr(mr)
        label = f"{E.EXT_ARM}_mr{mr:g}"
        for v in visits:
            ev = events[v["event"]]
            cs = [cases[(E.EXT_ARM, r)] for r in ev.rooms]
            ctxs = [W.context_dict(E.EXT_ARM, r) for r in ev.rooms]
            res = P.run_policy(E.ROUTINE, cs, L.TableOracle(ev, wp.rel_a), ctxs)
            recs[(v["id"], label, E.ROUTINE)] = L.record(res, ev)
        arrX = L.strat_arrays(recs, visits, label, E.ROUTINE)
        out[mr] = dict(label=label, arr=arrX,
                        summary={sub: dict(minutes=L.wmean(arrX, shares, "minutes", kinds), acc=L.wmean(arrX, shares, "acc", kinds), wcr=L.wmean(arrX, shares, "wcr", kinds))
                                 for sub, kinds in L.SUBS.items()},
                        vs_t3={sub: L.compare(arrX, L.strat_arrays(recs, visits, "T3", "llm"), shares, kinds, (500 + i,)) for i, (sub, kinds) in enumerate(L.SUBS.items())},
                        vs_t2={sub: L.compare(arrX, L.strat_arrays(recs, visits, "T2", "llm"), shares, kinds, (600 + i,)) for i, (sub, kinds) in enumerate(L.SUBS.items())})
    return out
