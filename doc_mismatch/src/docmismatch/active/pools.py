"""Reading pools: every reading an auditor could take, precomputed, for one topology / dataset.

A *reading* is one channel (0..2, the existing pair-consistency errors of `evidence.pair_errors` /
`real_frp.pair_errors`) of one candidate (owner, member) pair, computed over one short trend slice
(sim: one day; real: one 4-hour block). Each slice carries the operating context it was taken in.
Nothing here looks at the documentation: a pool is a property of the physical building + sensors.

Pool layout (`SlotPool`): E[s, k, o, m] with NaN = channel uninformative in that slice (flat streams,
too few valid samples) -- the technician still spends the reading and learns nothing.
"""

from __future__ import annotations

import pickle
from dataclasses import dataclass, field
from pathlib import Path

import numpy as np

from ..data import SLOTS, Base, load_base
from ..evidence import make_context, make_evidence, pair_errors

CTX_NAMES = ("oat", "swing", "load")     # outdoor-air temp (slice mean), its diurnal swing, building load fraction
DAYS_PER_WINDOW_PICK = (0, 8, 16, 24, 32, 40)  # 6 day-slices per 6-week window (spread over weekdays)
SEASON_OF_WINDOW = {0: 0, 1: 0, 2: 1, 3: 1, 4: 2, 5: 2, 6: 3, 7: 3}
EVIDENCE_SLOTS = tuple(s for s in SLOTS if s != "fan_ahu")


@dataclass
class SlotPool:
    slot: str
    owners: list[str]
    members: list[str]
    truth: np.ndarray          # (M,) index into owners of the true owner of each member
    E: np.ndarray              # (S, 3, O, M)
    owner_class: list          # per owner: hashable class key (kind, brick, medium)
    owner_size: np.ndarray     # per owner: size proxy used by the plausibility filter (peak flow)


@dataclass
class Pool:
    name: str
    kind: str                  # "sim" | "real"
    ctx: np.ndarray            # (S, F) raw context per slice
    season: np.ndarray         # (S,) season group (leave-one-season-out)
    group: np.ndarray          # (S,) visit group: slices that would share one site visit (sim: window; real: day)
    slots: dict = field(default_factory=dict)  # slot -> SlotPool

    @property
    def n_slices(self) -> int:
        return len(self.ctx)


def compatible(sp: SlotPool, o: int, ref: int, lim: float = float("inf")) -> bool:
    """Hard filters relative to a reference owner: same class/medium (and, if `lim` is finite, within `lim` x in size).
    The size filter is OFF by default: peak-flow ratio is not the benchmark's capacity criterion and can exclude the true owner."""
    if sp.owner_class[o] != sp.owner_class[ref]:
        return False
    a, b = sp.owner_size[o], sp.owner_size[ref]
    return max(a, b) / max(min(a, b), 1e-9) <= lim


def hypotheses(sp: SlotPool, doc: int) -> list[int]:
    """Candidate owners the technician must consider for a member documented under `doc`."""
    return [doc] + [o for o in range(len(sp.owners)) if o != doc and compatible(sp, o, doc)]


# ------------------------------------------------------------------ simulation pools
def _slice_context(base: Base, day_slice_abs: slice, load_series: np.ndarray) -> list[float]:
    oat = base.ev["ENV|oat"][day_slice_abs]
    return [float(oat.mean()), float(oat.max() - oat.min()), float(load_series[day_slice_abs].mean())]


def build_sim_pool(tid: str, rep: int) -> Pool:
    base = load_base(tid)
    # building load fraction: fleet mean of AHU (or RTU) flow relative to its peak
    fl = [base.ev[f"{a}|flow"] / (np.abs(base.ev[f"{a}|flow"]).max() + 1e-9) for a in base.ids("AHU")]
    load = np.mean(fl, axis=0)

    slices = [(w, d) for w in range(8) for d in DAYS_PER_WINDOW_PICK]
    ctx = np.zeros((len(slices), len(CTX_NAMES)))
    season = np.zeros(len(slices), dtype=int)
    group = np.zeros(len(slices), dtype=int)
    for i, (w, d) in enumerate(slices):
        a = w * 1008 + d * 24
        ctx[i] = _slice_context(base, slice(a, a + 24), load)
        season[i] = SEASON_OF_WINDOW[w]
        group[i] = w
    pool = Pool(f"{tid}#r{rep}", "sim", ctx, season, group)

    evs = {w: make_evidence(base, w, seed=9000 + 97 * rep + w) for w in range(8)}
    for slot in EVIDENCE_SLOTS:
        if slot not in base.slot_edges:
            continue
        spec = SLOTS[slot]
        owners = base.ids(*spec["owner"])
        members = sorted({m for _, m in base.slot_edges[slot]})
        oi = {o: i for i, o in enumerate(owners)}
        truth = np.full(len(members), -1)
        for o, m in base.slot_edges[slot]:
            truth[members.index(m)] = oi[o]
        E = np.full((len(slices), 3, len(owners), len(members)), np.nan)
        for i, (w, d) in enumerate(slices):
            sl = slice(d * 24, (d + 1) * 24)
            ev = evs[w]
            c = make_context(base, ev, sl) if slot == "vav_zone" else None
            for a, o in enumerate(owners):
                for b, m in enumerate(members):
                    E[i, :, a, b] = pair_errors(base, ev, slot, o, m, sl, c)
        size = np.array([float(np.abs(base.ev[f"{o}|flow"]).max()) + 1e-9 for o in owners])
        pool.slots[slot] = SlotPool(slot, owners, members, truth, E, [base.cls(o) for o in owners], size)
    return pool


CACHE = Path(__file__).resolve().parents[4] / "results" / "docmismatch" / "active"


def load_or_build_sim(tid: str, rep: int) -> Pool:
    CACHE.mkdir(parents=True, exist_ok=True)
    f = CACHE / f"pool_{tid}_r{rep}.pkl"
    if f.exists():
        return pickle.loads(f.read_bytes())
    p = build_sim_pool(tid, rep)
    f.write_bytes(pickle.dumps(p))
    return p
