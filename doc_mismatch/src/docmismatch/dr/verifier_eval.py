"""Sequential-verifier (S-V) evaluation of the DR study. Reuses `active.readiness` machinery (frozen config, inner leave-one-building-out records,
reliability layer) with: arm-specific training pools, season-restricted fits, window-restricted (unseen-day) fits, several test telemetries.
Nothing here is tuned on a test building: the likelihood, beta tempering and the reliability layer are fitted on the ARM's training buildings only.
"""

from __future__ import annotations

import json
import pickle
from pathlib import Path

import numpy as np

from ..active import readiness as RD
from ..active.nested import build_sim_episodes
from ..active.pools import SEASON_OF_WINDOW
from ..active.readiness import SimKind, h32
from .cases import PROV  # noqa: F401
from .pools import DR_DIR, load_pool

REPS = (0, 1)
OUT = DR_DIR / "verifier"
EXISTING = ["sys03_psz_ac", "sys07_vav_reheat", "vav_2ahu_2loops", "vav_3ahu_2loops", "dev_E", "dev_F", "dev_G", "dev_H"]


def spec_ids() -> dict:
    s = json.loads((DR_DIR / "spec.json").read_text())
    return {k: [b["id"] for b in v["buildings"]] for k, v in s["suites"].items()}


def arms() -> dict:
    ids = spec_ids()
    return {"baseline": dict(train=EXISTING, tel="legacy"), "noise_only": dict(train=EXISTING, tel="wide"),
            "regime": dict(train=ids["regime"], tel="spec"), "full": dict(train=ids["full"], tel="spec"), "full_x3": dict(train=ids["full_x3"], tel="spec")}


def load_cases(set_name: str) -> list[dict]:
    return [json.loads(l) for l in open(DR_DIR / "cases" / f"cases_{set_name}.jsonl")]


def cases_for(tids: list[str]) -> list[dict]:
    """all hard+clean cases of the given buildings (from the per-set case files)"""
    want = set(tids)
    out = []
    for f in sorted((DR_DIR / "cases").glob("cases_*.jsonl")):
        out += [c for c in map(json.loads, open(f)) if c["topology_id"] in want]
    return out


class DRKind(SimKind):
    """SimKind with: season removed from training / test restricted to one season / train on even windows and test on odd windows."""

    def __init__(self, cfg, topos, pools, cases, drop_season=None, only_season=None, train_parity=None, test_parity=None):
        super().__init__(cfg, topos=topos, pools=pools, cases=cases)
        self.drop_season, self.only_season, self.train_parity, self.test_parity = drop_season, only_season, train_parity, test_parity

    def train(self, units):
        pools = [self.pools(t, r) for t in units for r in self.reps()]
        masks = []
        for p in pools:
            m = np.ones(p.n_slices, bool)
            if self.drop_season is not None:
                m &= p.season != self.drop_season
            if self.train_parity is not None:
                m &= (p.group % 2) == self.train_parity
            masks.append(m)
        return dict(pools=pools, masks=masks, units=list(units))

    def _window(self, e, rep):
        h = h32(e.ep_id) + 3 * rep
        if self.only_season is not None:
            wins = [k for k, s in SEASON_OF_WINDOW.items() if s == self.only_season]
            return wins[h % len(wins)]
        if self.test_parity is not None:
            return (h % 4) * 2 + self.test_parity
        return h % 8

    def slice_idx(self, e, setting, rep):
        return np.where(e.pool.group == self._window(e, rep))[0]

    def meta(self, e, setting, rep):
        w = self._window(e, rep)
        return dict(season="s%d" % SEASON_OF_WINDOW[w], family=e.meta.get("matched_to", e.meta["family"]), obs=e.meta["obs"], scenario="")


def test_episodes(tids: list[str], telemetry: str, cases: list[dict]) -> tuple[list, dict]:
    """(list of (rep, Episode), overlap map ep_id -> distractor overlap) on the given buildings under the given telemetry"""
    eps, ov = [], {}
    for rep in REPS:
        pools = {t: load_pool(t, rep, telemetry) for t in tids}
        cs = [c for c in cases if c["topology_id"] in pools]
        for e in build_sim_episodes(pools, cs):
            eps.append((rep, e))
            dn = getattr(e.pool, "distractor_nodes", set())
            sp = e.pool.slots[e.slot]
            nodes = {sp.members[e.member]} | {sp.owners[o] for o in range(len(sp.owners))}
            ov[e.ep_id] = bool(dn & nodes)
    return eps, ov


def run_fold(kind: DRKind, cfg: dict, train_units: list, test_sets: dict, procs: int) -> dict:
    RD._G["kind"], RD._G["cfg"] = kind, cfg
    beta = RD._beta_task(dict(train=train_units))
    jobs = [dict(kind="outer", train=train_units, test=name, beta=beta, test_pool=object(), eps=eps) for name, eps in test_sets.items()]
    jobs += [dict(kind="inner", train=[u for u in train_units if u != h], test=h, beta=beta, outer="fold") for h in train_units]
    res = RD._pmap(RD._run_task, jobs, procs)
    n = len(test_sets)
    return dict(outer=[r for x in res[:n] for r in x], inner=[r for x in res[n:] for r in x], beta=beta)


def make_cfg(policies=("active", "random")) -> dict:
    cfg = json.loads(json.dumps(RD.DEFAULT_CFG))
    fz = DR_DIR.parent / "active" / "frozen" / "config.json"
    if fz.exists():
        cfg.update({k: v for k, v in json.loads(fz.read_text()).items() if k in ("variant", "ctx", "tau", "nmax", "layer", "calibrate_beta")})
    cfg["policies"] = list(policies)
    cfg["sim_settings"] = ["visit"]
    cfg["sim_primary"] = "visit"
    cfg["sim_reps"] = list(REPS)
    return cfg
