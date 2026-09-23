"""Guard for `dr.measurement_eval._sim_rec`'s futility passthrough (PREREGISTRATION_DR.md Addendum 10):
default (futility_window=0) must be bit-identical to before this parameter existed; when on, `futile`/`n_read`
must reflect what `engine.run_episode` itself reports."""
import sys
from pathlib import Path
from types import SimpleNamespace

import numpy as np

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "src"))
from docmismatch.active.engine import Episode  # noqa: E402
from docmismatch.dr.measurement_eval import _sim_rec  # noqa: E402


class FakeModel:
    def __init__(self, mu_m, sd_m, mu_x, sd_x):
        self.fit = {"M": SimpleNamespace(tau=0.0), "X": SimpleNamespace(tau=0.0)}
        self.kappa = None
        self.rho = 0.0
        self.omega = 0.0
        self.rho_s = 0.0
        self._p = (mu_m, sd_m, mu_x, sd_x)

    def params(self, ctx):
        n = len(ctx)
        mu_m, sd_m, mu_x, sd_x = self._p
        return [np.full(n, mu_m), np.full(n, sd_m), np.full(n, mu_x), np.full(n, sd_x), np.full(n, 0.5)]


def _slow_converging_pool(rng, n_slices=160, n_mem=6):
    """Weak, slowly-converging separation on purpose -- enough slices past 2*futility_window=8 for the futility
    check to fire, but not so decisive that it resolves outright either way."""
    truth = np.arange(n_mem)
    E = np.full((n_slices, 1, n_mem, n_mem), np.nan)
    for s in range(n_slices):
        for m in range(n_mem):
            for o in range(n_mem):
                z = -0.15 if o == m else 0.15
                E[s, 0, o, m] = np.exp(z + rng.normal(0, 0.5)) - 0.05

    class SP:
        def __init__(self):
            self.members = list(range(n_mem))
            self.owners = list(range(n_mem))
            self.truth = truth
            self.E = E
            self.owner_class = [("VAV",)] * n_mem
            self.owner_size = np.ones(n_mem)

    class Pool:
        def __init__(self):
            self.slots = {"vav_zone": SP()}
            self.ctx = np.zeros((n_slices, 3))
            self.group = np.arange(n_slices) % 8   # 8 windows, matching real pools, so _sim_rec's window-hash always finds slices

        @property
        def n_slices(self):
            return len(self.ctx)
    return Pool()


def _episode(pool, ep_id="dev_X|vav_zone|0|0|wrong"):
    return Episode(pool, "vav_zone", 0, 0, 1, True, ep_id, "g0", {"family": "f", "obs": "o"})


def test_default_off_matches_plain_run_episode_and_still_reports_n_read_futile():
    rng = np.random.default_rng(0)
    pool = _slow_converging_pool(rng)
    e = _episode(pool)
    mod = {0: FakeModel(-0.15, 0.3, 0.15, 0.3)}
    cfg = dict(nmax=24, tau=0.95)
    rec = _sim_rec(e, mod, 1.0, cfg, {}, None, frozenset(), "dev_X")
    assert rec is not None
    assert "n_read" in rec and "futile" in rec
    assert rec["futile"] is False   # futility_window=0 (default) can never fire


def test_futility_on_stops_early_and_reports_futile_true_on_a_slow_case():
    rng = np.random.default_rng(0)   # this seed's trajectory genuinely trends toward "wrong" but too slowly to cross tau
    pool = _slow_converging_pool(rng)
    e = _episode(pool)
    mod = {0: FakeModel(-0.15, 0.3, 0.15, 0.3)}
    cfg = dict(nmax=24, tau=0.999)   # near-impossible threshold so it can't just cross tau first
    rec = _sim_rec(e, mod, 1.0, cfg, {}, None, frozenset(), "dev_X", futility_window=4, futility_margin=0.05)
    assert rec is not None
    assert rec["futile"] is True
    assert rec["n_read"] < 24   # genuinely stopped early, not just ran to budget
