"""Exploratory note E2, extended to the language-model comparison (PREREGISTRATION_DR.md): does "T3-noattr" (BAS access + a point map, no documented attributes; `v1/study_tiers_ext.py`)
hold up against the language model on Addendum 33's own 30 visits, the way Addendum 35/36's `min_rate` variants were checked against it (`scripts/80_minrate_vs_llm.py`)? No new language
model call: Addendum 33's stored `llm_records.csv` numbers are reused unchanged; only the routine (`tool_ticket_memo2`) is replayed, at the new item set, on the same visits and the same
world (Addendum 30's primary cell, `world2.py`).

`T3-noattr` is added to `world2.TIER_ITEMS` as a new key at import time: a strictly additive dict mutation (a key nothing existing looks up), verified against the two original keys and
against `TIER_NAMES` (already bound to `("T2", "T3")` at `world2` import time, so nothing that loops over `TIER_NAMES` sees a third tier appear).
"""

from __future__ import annotations

from ..v1 import data as D
from ..v1.engine import make_case_v1
from . import policies as P
from . import study_llm as L
from . import world2 as W

EXT_ARM = "T3-noattr"
EXT_ITEMS: frozenset = D.TIERS["T1"] | {"bas_access", "point_map"}
ROUTINE = "tool_ticket_memo2"

assert W.TIER_ITEMS["T2"] == D.TIERS["T2"] and W.TIER_ITEMS["T3"] == D.TIERS["T3"] and W.TIER_NAMES == ("T2", "T3"), "world2's original tiers must be untouched before the additive line below"
W.TIER_ITEMS[EXT_ARM] = EXT_ITEMS


def make_cases_ext(bld: D.Building1 | None = None) -> dict:
    """`world2.make_cases()`'s own (T2, T3) entries, plus `(EXT_ARM, room)` for every room."""
    bld = bld or W.make_building2()
    cases = W.make_cases(bld)
    s = W.tool_settings()
    for r in range(W.N_BOX):
        cases[(EXT_ARM, r)] = make_case_v1(bld, f"Room-{r}", EXT_ITEMS, settings=s, context=W.tier_context(EXT_ARM, r), member_name=f"Room {r}")
    return cases


def add_ext_routine(recs: dict, visits: list, wp, events: list, cases: dict) -> None:
    """Replays the routine at the T3-noattr item set on Addendum 33's own visits, writing into `recs` in the same shape `study_llm.py`'s own records use."""
    for v in visits:
        ev = events[v["event"]]
        cs = [cases[(EXT_ARM, r)] for r in ev.rooms]
        ctxs = [W.context_dict(EXT_ARM, r) for r in ev.rooms]
        res = P.run_policy(ROUTINE, cs, L.TableOracle(ev, wp.rel_a), ctxs)
        recs[(v["id"], EXT_ARM, ROUTINE)] = L.record(res, ev)
