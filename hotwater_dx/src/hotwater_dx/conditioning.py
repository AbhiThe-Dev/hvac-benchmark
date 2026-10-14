"""Conditioning the engine on facts a technician can read on arrival (idea 7 of the robustness brief). Simulation only.

The engine's likelihoods are Gaussians over *absolute* readings fitted on a population of plants. A plant whose known set points, static pressure or dead-leg length differ from the
population shifts every reading, which the engine reads as evidence about the cause. Here each (hypothesis, check) mean becomes a ridge regression on facts the technician can read
or estimate at the door (relative readings are a special case: a coefficient of one on a set point). A ladder isolates what conditioning buys:

    R   same readings, no facts (the family-refit control of Addendum 6)
    C1  one fact (cold-side static pressure, the strongest driver found in Addendum 6)
    C3  the three knowable facts with the largest Addendum 6 statistic
    C15 all fifteen arrival facts
    O   oracle: every one of the 25 design parameters (not obtainable in a building; the ceiling)

Fact inputs can be noisy, unknown or wrongly entered (`FACT_NOISE`); the decision test uses noisy facts. Facts only move the means of readings; they are not themselves treated
as evidence about the cause (a conservative choice). Everything is inside the simulator.
"""
from __future__ import annotations

import csv
import hashlib
import json
from dataclasses import dataclass
from pathlib import Path

import numpy as np

from . import adversary as AD
from . import causes as C
from . import checks as K
from . import measurement as M
from . import stress as S
from .engine import ENGINE_CHECKS, ENGINE_CONFIG, OTHER, PAIRS, Likelihoods, _strkeys, fit, parts, run_case
from .matrix import THRESHOLDS, _reads, build_world
from .provenance import DISCLAIMER
from .sampling import substream

COND_CONFIG = {
    "FIT": {"n_plants": 600, "noise": 1.5, "latent_p": 0.25, "ridge": 1.0, "min_rows": 60, "clip_margin": 0.05},
    "FACT_SETS": {"C1": ("p_cold",), "C3": ("p_cold", "tmv_margin_min", "len_scale"), "C15": tuple(AD.ADV_CONFIG["ARRIVAL"])},
    "INTAKE_MIN": {"C1": 2.0, "C3": 4.0, "C15": 10.0, "O": 0.0},     # ANALYST: minutes to collect the facts at the door (added to every visit of that variant)
    # (kind, magnitude, probability the fact is unknown and set to the population mean); ANALYST
    "FACT_NOISE": {"p_cold": ("abs", 3.0, 0.0), "t_amb": ("abs", 3.0, 0.0), "t_cold": ("abs", 2.0, 0.0), "t_set_heater": ("abs", 1.0, 0.0), "t_set_tmv": ("abs", 1.0, 0.0),
                   "deadband": ("abs", 0.5, 0.2), "heater_cap": ("rel", 0.10, 0.2), "storage_gal": ("rel", 0.10, 0.1), "tmv_margin_min": ("abs", 0.0, 0.3),
                   "len_scale": ("rel", 0.20, 0.0), "dT_design": ("abs", 1.0, 0.4), "t_min_circ": ("abs", 0.0, 0.3), "valve_thermal": ("abs", 0.0, 0.0),
                   "pump_oversize": ("rel", 0.15, 0.4), "deadleg_ft": ("rel", 0.25, 0.1)},
    "WILD": 0.05,                       # chance a known fact is entered wrongly: a uniform draw over the family range
    "WORLDS": {"HELD": 6, "EXT2": 2, "N_PLANTS": 200},
    "BAR": {"oracle_gain": 0.08, "arrival_gain": 0.03, "arrival_wc_slack": 0.005, "share": 0.5, "noisy_wc_slack": 0.02, "minutes_rel": 1.15},
    "SEED": 20261601,
}
CFG = COND_CONFIG
ORACLE = tuple(AD.PLANT_FEATS)
STATE_FACT = {"p_cold": lambda P: P.p_cold, "t_set_heater": lambda P: P.t_set_display, "t_set_tmv": lambda P: P.t_set_tmv, "deadband": lambda P: P.deadband,
              "deadleg_ft": lambda P: P.deadleg_ft, "t_cold": lambda P: P.t_cold, "t_amb": lambda P: P.t_amb, "valve_thermal": lambda P: float(P.thermal)}


def frozen_hash() -> str:
    blob = dict(cond=_strkeys(COND_CONFIG), oracle=ORACLE, adv=AD.frozen_hash())
    return hashlib.sha256(json.dumps(blob, sort_keys=True, default=str).encode()).hexdigest()


# ------------------------------------------------------------------------------------------------ readings, collected once
@dataclass
class Collected:
    hyps: list
    checks: list
    thetas: list           # design parameters per plant
    plant_of: list         # per hypothesis: {plant index: faulted Plant}
    rows: dict             # (hi, ci) -> (plant indices per reading, readings)


def collect(w, reps: int | None = None) -> Collected:
    """The same readings engine.fit draws (same streams), kept with the plant each reading came from."""
    reps = reps or ENGINE_CONFIG["FIT_REPS"]
    singles = list(w.cause_plants)
    hyps = singles + [p for p in PAIRS if all(x in w.cause_plants for x in parts(p))]
    ctxs = {}
    for cid in singles:
        g = w.cause_gated[cid]
        keep = g if g.sum() >= THRESHOLDS["GATE_MIN"] else np.ones(len(g), bool)
        ctxs[cid] = [(j, w.cause_ctx[cid][j]) for j in np.where(keep)[0]]
    for pi, h in enumerate([p for p in PAIRS if p in hyps]):
        a, b = (C.BY_ID[x] for x in parts(h))
        lst = []
        for j, P in enumerate(w.plants):
            da, db = a.draw(substream(w.seed, 7, pi, j, 0), P), b.draw(substream(w.seed, 7, pi, j, 1), P)
            lst.append((j, K.Ctx(b.apply(a.apply(P, da), db))))
        ctxs[h] = lst
    plant_of = [{j: ctx.P for j, ctx in ctxs[h]} for h in hyps]
    rows = {}
    for hi, h in enumerate(hyps):
        for ci, cid in enumerate(ENGINE_CHECKS):
            ch = K.BY_ID[cid]
            js, ys = [], []
            for j, ctx in ctxs[h]:
                if not ch.applies(w.plants[j]):
                    continue
                v = _reads(ch, ctx, ch.tool, substream(w.seed, 8, hi, ci, j), (THRESHOLDS["REPS_BINARY"] // 8) if ch.binary else reps)
                js += [j] * len(v)
                ys.append(v)
            rows[(hi, ci)] = (np.array(js, int), np.concatenate(ys) if ys else np.zeros(0))
    return Collected(hyps, list(ENGINE_CHECKS), list(w.design), plant_of, rows)


def _finish_other(hyps_mean: np.ndarray, hyps_sd: np.ndarray) -> tuple[np.ndarray, np.ndarray]:
    mo = hyps_mean.mean(axis=0)
    so = np.sqrt((hyps_sd ** 2).mean(axis=0) + hyps_mean.var(axis=0)) * ENGINE_CONFIG["OTHER_SD_MULT"]
    return mo, so


def fit_plain(col: Collected) -> Likelihoods:
    """Unconditioned likelihoods from the collected readings; identical to engine.fit on the same world."""
    H, Cn = len(col.hyps), len(col.checks)
    mean, sd = np.zeros((H, Cn)), np.zeros((H, Cn))
    for hi in range(H):
        for ci, cid in enumerate(col.checks):
            _, y = col.rows[(hi, ci)]
            v = y if len(y) else np.array([0.0, 1.0])
            mean[hi, ci], sd[hi, ci] = float(v.mean()), max(float(v.std()), K.BY_ID[cid].sigma_min)
    mo, so = _finish_other(mean, sd)
    return Likelihoods(col.hyps + [OTHER], col.checks, np.vstack([mean, mo]), np.vstack([sd, so]), {"K12": True, "K13": False})


# ------------------------------------------------------------------------------------------------ conditioning on facts
def raw_facts(theta: dict, P, names: tuple, source: str) -> np.ndarray:
    """What the technician can read: gauge and controller values come from the faulted plant; nameplate and design facts from the design."""
    return np.array([STATE_FACT[n](P) if source == "state" and n in STATE_FACT else float(theta[n]) for n in names], float)


@dataclass
class Conditioner:
    names: tuple
    source: str
    mu: np.ndarray
    sd: np.ndarray
    zlo: np.ndarray
    zhi: np.ndarray
    cont: np.ndarray

    def feats(self, f: np.ndarray) -> np.ndarray:
        z = np.where(np.isnan(f), 0.0, (f - self.mu) / self.sd)       # an unknown fact is imputed at the population mean
        z = np.clip(z, self.zlo, self.zhi)                            # never extrapolate beyond the facts seen in fitting
        return np.concatenate([z, z[self.cont] ** 2])


def make_conditioner(F: np.ndarray, names: tuple, source: str) -> Conditioner:
    mu, sd = F.mean(0), F.std(0)
    sd = np.where(sd < 1e-9, 1.0, sd)
    z = (F - mu) / sd
    m = CFG["FIT"]["clip_margin"]
    span = z.max(0) - z.min(0)
    cont = np.array([len(np.unique(F[:, k])) > 2 for k in range(F.shape[1])])
    return Conditioner(names, source, mu, sd, z.min(0) - m * span, z.max(0) + m * span, cont)


def _ridge(X: np.ndarray, y: np.ndarray, lam: float):
    xm, ym = X.mean(0), float(y.mean())
    Xc = X - xm
    b = np.linalg.solve(Xc.T @ Xc + lam * np.eye(X.shape[1]), Xc.T @ (y - ym))
    return ym - float(xm @ b), b


@dataclass
class CondLikelihoods:
    cond: Conditioner
    hyps: list
    checks: list
    icpt: np.ndarray       # [H, C]
    beta: np.ndarray       # [H, C, F]
    sd: np.ndarray         # [H, C]
    ymin: np.ndarray
    ymax: np.ndarray
    thermal_only: dict

    def at(self, f: np.ndarray) -> Likelihoods:
        x = self.cond.feats(f)
        mean = np.clip(self.icpt + self.beta @ x, self.ymin, self.ymax)
        mo, so = _finish_other(mean, self.sd)
        return Likelihoods(self.hyps + [OTHER], self.checks, np.vstack([mean, mo]), np.vstack([self.sd, so]), self.thermal_only)


def fit_conditional(col: Collected, names: tuple, source: str) -> CondLikelihoods:
    H, Cn = len(col.hyps), len(col.checks)
    pool = np.array([raw_facts(col.thetas[j], P, names, source) for hi in range(H) for j, P in col.plant_of[hi].items()])
    cond = make_conditioner(pool, names, source)
    nf = len(cond.zlo) + int(cond.cont.sum())
    icpt, beta, sd = np.zeros((H, Cn)), np.zeros((H, Cn, nf)), np.zeros((H, Cn))
    ymin, ymax = np.zeros((H, Cn)), np.ones((H, Cn))
    fc = CFG["FIT"]
    for hi in range(H):
        Fh = np.zeros((len(col.thetas), nf))
        for j, P in col.plant_of[hi].items():
            Fh[j] = cond.feats(raw_facts(col.thetas[j], P, names, source))
        for ci, cid in enumerate(col.checks):
            js, y = col.rows[(hi, ci)]
            floor = K.BY_ID[cid].sigma_min
            if len(y) < fc["min_rows"]:
                v = y if len(y) else np.array([0.0, 1.0])
                icpt[hi, ci], sd[hi, ci], ymin[hi, ci], ymax[hi, ci] = float(v.mean()), max(float(v.std()), floor), float(v.min()), float(v.max())
                continue
            X = Fh[js]
            c0, b = _ridge(X, y, fc["ridge"])
            res = y - (c0 + X @ b)
            icpt[hi, ci], beta[hi, ci], sd[hi, ci] = c0, b, max(float(res.std()), floor)
            ymin[hi, ci], ymax[hi, ci] = float(y.min()), float(y.max())
    return CondLikelihoods(cond, col.hyps, col.checks, icpt, beta, sd, ymin, ymax, {"K12": True, "K13": False})


# ------------------------------------------------------------------------------------------------ what the technician enters
def observe(raw: np.ndarray, names: tuple, rng: np.random.Generator) -> np.ndarray:
    """Noisy, missing and occasionally wrong fact entries (FACT_NOISE, WILD). Unknown facts come back as NaN (imputed by the conditioner)."""
    ov = AD.ext_overrides(AD.ADV_CONFIG["EXT_FACTOR"])
    out = raw.copy()
    for k, n in enumerate(names):
        kind, mag, p_unknown = CFG["FACT_NOISE"][n]
        if rng.random() < p_unknown:
            out[k] = np.nan
            continue
        if rng.random() < CFG["WILD"]:
            if n in ov:
                out[k] = rng.uniform(*ov[n])
            else:
                out[k] = 1.0 - raw[k] if n == "valve_thermal" else (144.0 - raw[k] if n == "t_min_circ" else raw[k])
            continue
        if mag > 0:
            out[k] = raw[k] + rng.normal(0.0, mag if kind == "abs" else mag * abs(raw[k]))
    return out


def evaluate_cond(cl: CondLikelihoods, cases: list, config: dict, seed: int, garbage_lk: Likelihoods, noisy: bool, fact_seed: int) -> list:
    out = []
    try:
        for i, c in enumerate(cases):
            raw = raw_facts(c.theta, c.ctx.P, cl.cond.names, cl.cond.source)
            f = observe(raw, cl.cond.names, np.random.default_rng(np.random.SeedSequence([fact_seed, i]))) if noisy else raw
            M.NOISE["scale"] = c.noise
            rng = np.random.default_rng(np.random.SeedSequence([seed, i]))
            out.append(run_case(cl.at(f), c.ctx, c.truth, rng, c.thermal, p_skip=c.p_skip, p_garbage=c.p_garbage, garbage_lk=garbage_lk, **config))
    finally:
        M.NOISE["scale"] = 1.0
    return out


# ------------------------------------------------------------------------------------------------ the run
def _ms(res: list, intake: float = 0.0) -> dict:
    m = AD._ms(res)
    m["minutes"] = m["minutes"] + intake
    return m


def run_all(out: Path, quick: bool = False) -> dict:
    seed0 = CFG["SEED"]
    wk = CFG["WORLDS"]
    if quick:
        n_pl, n_he, n_e2, fit_n, boot = 40, 1, 1, 80, 50
    else:
        n_pl, n_he, n_e2, fit_n, boot = wk["N_PLANTS"], wk["HELD"], wk["EXT2"], CFG["FIT"]["n_plants"], 500
    out.mkdir(parents=True, exist_ok=True)
    CONF = dict(S.CONFIGS)
    lk_m = fit(build_world(n_theta=S.N_FIT, seed=S.SEED_FIT))
    M.NOISE["scale"] = CFG["FIT"]["noise"]
    try:
        fw = AD.family_world(AD.ADV_CONFIG["EXT_FACTOR"], seed0 + 1, n=fit_n, latent_p=CFG["FIT"]["latent_p"])
        col = collect(fw)
    finally:
        M.NOISE["scale"] = 1.0
    del fw
    plain = fit_plain(col)
    cl = {k: fit_conditional(col, names, "state") for k, names in CFG["FACT_SETS"].items()}
    cl["O"] = fit_conditional(col, ORACLE, "design")
    intake = CFG["INTAKE_MIN"]

    def world_set(factor, base, count):
        cases = []
        for k in range(count):
            w = AD.family_world(factor, seed0 + base + k, n=n_pl)
            cases += AD.family_cases(w, k, seed0 + base + 500 + k)
            del w
        return cases

    def uncond(cases, seed):
        return {"A_plain": AD.evaluate_family(lk_m, cases, CONF["A_plain"], seed, lk_m), "B_robust": AD.evaluate_family(lk_m, cases, CONF["B_robust"], seed, lk_m),
                "R_A": AD.evaluate_family(plain, cases, CONF["A_plain"], seed, lk_m), "R_B": AD.evaluate_family(plain, cases, CONF["B_robust"], seed, lk_m)}

    def cond_noisy(cases, seed, fseed):
        r = {}
        for k in ("C3", "C15"):
            for s, cfgname in (("A", "A_plain"), ("B", "B_robust")):
                r[f"{k}_{s}_n"] = evaluate_cond(cl[k], cases, CONF[cfgname], seed, lk_m, True, fseed)
        return r

    def intake_of(name: str) -> float:
        return intake[name.split("_")[0]] if name[0] in "CO" else 0.0

    held = world_set(AD.ADV_CONFIG["EXT_FACTOR"], 400, n_he)
    ext2 = world_set(AD.ADV_CONFIG["EXT2_FACTOR"], 500, n_e2)
    sh, se = seed0 + 2100, seed0 + 2200
    hr = uncond(held, sh)
    for k in ("C1", "C3", "C15", "O"):                                  # the ladder, clean facts, engine A settings
        hr[f"{k}_A"] = evaluate_cond(cl[k], held, CONF["A_plain"], sh, lk_m, False, 0)
    hr.update(cond_noisy(held, sh, seed0 + 3100))
    er = uncond(ext2, se)
    er.update(cond_noisy(ext2, se, seed0 + 3200))
    h2 = {}
    for wname in ("matched", "param_shift", "latent_and_noise", "technician_error", "composite_1.00"):
        wi = next(i for i, s in enumerate(S.WORLDS) if s.name == wname)
        spec = S.WORLDS[wi]
        w = S.build_test_world(spec, S.SEED_TEST + wi)
        cs = AD.spec_cases(w, wi, spec, S.SEED_TEST + 1000 + wi)
        r = uncond(cs, S.SEED_TEST + 2000 + wi)
        r.update(cond_noisy(cs, S.SEED_TEST + 2000 + wi, seed0 + 3300 + wi))
        h2[wname] = {v: _ms(x, intake_of(v)) for v, x in r.items()}
        del w
    res = dict(quick=quick, hash=frozen_hash(), held_n=len(held), ext2_n=len(ext2), fit_plants=fit_n,
               held={v: _ms(r, intake_of(v)) for v, r in hr.items()}, ext2={v: _ms(r, intake_of(v)) for v, r in er.items()}, h2=h2)
    pid = AD.plant_ids(held)
    diffs = {}
    one = np.ones(len(held))
    for x, y_ in (("C15_A", "R_A"), ("C3_A", "R_A"), ("C1_A", "R_A"), ("O_A", "R_A"), ("C15_A_n", "R_A"), ("C15_A_n", "B_robust"), ("C15_B_n", "B_robust"), ("C3_A_n", "B_robust"), ("C3_B_n", "B_robust"),
                  ("R_A", "B_robust"), ("A_plain", "B_robust")):
        ax, ay = AD.arr(hr[x]), AD.arr(hr[y_])
        diffs[f"{x} - {y_}"] = dict(wrong_conf=AD.boot_ci(pid, [(ax["wc"], one, 1.0), (ay["wc"], one, -1.0)], boot, seed0 + 41),
                                    top1=AD.boot_ci(pid, [(ax["correct"], ax["single"], 1.0), (ay["correct"], ay["single"], -1.0)], boot, seed0 + 42),
                                    confident=AD.boot_ci(pid, [(ax["conf"], one, 1.0), (ay["conf"], one, -1.0)], boot, seed0 + 43))
    res["diffs"] = diffs
    # which facts carry the signal: standardised slope magnitude of the C15 regression averaged over cells (descriptive)
    c15 = cl["C15"]
    nf = len(c15.cond.names)
    imp = np.abs(c15.beta[:, :, :nf]) / np.maximum(c15.sd[:, :, None], 1e-9)
    res["fact_weight"] = {n: float(imp[:, :, k].mean()) for k, n in enumerate(c15.cond.names)}
    res["scorecard"] = scorecard(res)
    write(out, res)
    return res


# ------------------------------------------------------------------------------------------------ scorecard (rules frozen in PREREGISTRATION.md Addendum 7)
def _passes(res: dict, x: str) -> tuple[bool, list[str]]:
    B = CFG["BAR"]
    A6 = AD.ADV_CONFIG["BAR"]
    h, h2 = res["held"], res["h2"]
    i = h[x]["wrong_conf"] <= h["B_robust"]["wrong_conf"] + A6["wc_slack"]
    ii = h[x]["top1"] >= h["B_robust"]["top1"] + A6["top1_gain"] or h[x]["confident"] >= h["B_robust"]["confident"] + A6["conf_gain"]
    iii = h2["matched"][x]["top1"] >= h2["matched"]["A_plain"]["top1"] - A6["matched_top1_drop"]
    iv = all(h2[w][x]["wrong_conf"] <= h2[w]["B_robust"]["wrong_conf"] + A6["wc_slack"] for w in ("composite_1.00", "technician_error"))
    v = h[x]["minutes"] <= B["minutes_rel"] * h["B_robust"]["minutes"]
    notes = [f"(i) wrong-conf {h[x]['wrong_conf']:.3f} vs B {h['B_robust']['wrong_conf']:.3f}: {i}", f"(ii) top-1 {h[x]['top1']:.3f} vs B {h['B_robust']['top1']:.3f}, confident {h[x]['confident']:.2f} vs {h['B_robust']['confident']:.2f}: {ii}",
             f"(iii) matched top-1 {h2['matched'][x]['top1']:.3f} vs A {h2['matched']['A_plain']['top1']:.3f}: {iii}",
             "(iv) " + ", ".join(f"{w} {h2[w][x]['wrong_conf']:.3f} vs {h2[w]['B_robust']['wrong_conf']:.3f}" for w in ("composite_1.00", "technician_error")) + f": {iv}",
             f"(v) minutes incl. intake {h[x]['minutes']:.0f} vs B {h['B_robust']['minutes']:.0f} (x{B['minutes_rel']}): {v}"]
    return bool(i and ii and iii and iv and v), notes


def scorecard(res: dict) -> list[tuple[str, bool, str]]:
    B = CFG["BAR"]
    h, e2, h2 = res["held"], res["ext2"], res["h2"]
    t = lambda v: h[v]["top1"]  # noqa: E731
    out = []
    out.append(("Q1", t("O_A") >= t("R_A") + B["oracle_gain"], f"ceiling: oracle-conditioned O_A top-1 {t('O_A'):.3f} vs unconditioned R_A {t('R_A'):.3f} (needs +{B['oracle_gain']})"))
    ok2 = t("C15_A") >= t("R_A") + B["arrival_gain"] and h["C15_A"]["wrong_conf"] <= h["R_A"]["wrong_conf"] + B["arrival_wc_slack"]
    out.append(("Q2", ok2, f"15 arrival facts (clean) C15_A top-1 {t('C15_A'):.3f} vs R_A {t('R_A'):.3f} (needs +{B['arrival_gain']}); wrong-conf {h['C15_A']['wrong_conf']:.3f} vs {h['R_A']['wrong_conf']:.3f} (+{B['arrival_wc_slack']})"))
    g15, go = t("C15_A") - t("R_A"), t("O_A") - t("R_A")
    out.append(("Q3", g15 >= B["share"] * go and go > 0, f"arrival facts capture {g15 / go * 100 if go else float('nan'):.0f}% of the ceiling's top-1 gain (+{g15:.3f} of +{go:.3f}; needs >= {B['share'] * 100:.0f}%)"))
    g3 = t("C3_A") - t("R_A")
    out.append(("Q4", g3 >= B["share"] * g15 and g15 > 0, f"three facts capture {g3 / g15 * 100 if g15 else float('nan'):.0f}% of the 15-fact gain (+{g3:.3f} of +{g15:.3f}); one fact (p_cold) gives {t('C1_A') - t('R_A'):+.3f}"))
    gn = t("C15_A_n") - t("R_A")
    out.append(("Q5", g15 > 0 and gn >= B["share"] * g15 and h["C15_A_n"]["wrong_conf"] <= h["R_A"]["wrong_conf"] + B["noisy_wc_slack"],
                f"noisy, missing and wrong fact entries: C15_A top-1 {t('C15_A_n'):.3f} (gain {gn:+.3f} = {gn / g15 * 100 if g15 else float('nan'):.0f}% of clean; needs >= {B['share'] * 100:.0f}%); wrong-conf {h['C15_A_n']['wrong_conf']:.3f} vs R_A {h['R_A']['wrong_conf']:.3f} (+{B['noisy_wc_slack']})"))
    ver = {x: _passes(res, x) for x in ("C15_A_n", "C15_B_n", "C3_A_n", "C3_B_n")}
    passing = [x for x, (ok, _) in ver.items() if ok]
    rec = min(passing, key=lambda x: h[x]["wrong_conf"]) if passing else "B_robust"
    out.append(("Q6", bool(passing), "improvement over B_robust with noisy facts under the frozen rule (i)-(v): " + (", ".join(passing) if passing else "none passes") + " | " + " || ".join(f"{x}: " + "; ".join(n) for x, (_, n) in ver.items())))
    out.append(("Q7", e2["C15_A_n"]["wrong_conf"] <= e2["A_plain"]["wrong_conf"], f"extrapolation family, noisy facts: C15_A wrong-conf {e2['C15_A_n']['wrong_conf']:.3f} vs A {e2['A_plain']['wrong_conf']:.3f}"))
    m = h2["matched"]
    out.append(("Q8", m["C15_A_n"]["top1"] >= m["A_plain"]["top1"] - AD.ADV_CONFIG["BAR"]["matched_top1_drop"] and m["C15_A_n"]["wrong_conf"] <= AD.ADV_CONFIG["BAR"]["matched_wc_max"],
                f"matched world, noisy facts: C15_A top-1 {m['C15_A_n']['top1']:.3f} vs A {m['A_plain']['top1']:.3f} (within 0.05); wrong-conf {m['C15_A_n']['wrong_conf']:.3f} (<= 0.05)"))
    out.append(("RECOMMENDED", rec != "B_robust", f"frozen decision rule recommends {rec}"))
    return out


def write(out: Path, res: dict) -> None:
    (out / "conditioning.json").write_text(json.dumps(dict(disclaimer=DISCLAIMER, **res), indent=1, default=lambda o: o.tolist() if hasattr(o, "tolist") else float(o)) + "\n")
    with open(out / "conditioning_variants.csv", "w", newline="") as f:
        wr = csv.writer(f)
        wr.writerow(["# " + DISCLAIMER])
        cols = ["set", "variant", "n_single", "n_pair", "top1", "top3_marginal", "pair_hit", "wrong_conf", "confident", "acc_when_confident", "checks", "minutes", "ece"]
        wr.writerow(cols)
        for sn, d in [("held_family", res["held"]), ("ext2_family", res["ext2"])] + [(f"A3:{w}", d) for w, d in res["h2"].items()]:
            for v, m in d.items():
                wr.writerow([sn, v] + [f"{m[c]:.4f}" if isinstance(m[c], float) else m[c] for c in cols[2:]])
    L = ["# Conditioning the engine on arrival facts (simulation only)", "", f"**{DISCLAIMER}**", "",
         "Idea 7: likelihood means become ridge regressions on facts a technician can read at the door. The adversary's family is used for fitting and testing, so the Addendum 3 worlds and the extrapolation family are the generalisation checks. "
         "Facts are never evidence about the cause here, only about how the readings shift.", ""]
    if res.get("quick"):
        L += ["**QUICK SMOKE RUN: tiny sizes, numbers are not results.**", ""]
    L += [f"Frozen hash `{res['hash']}`. Fit on {res['fit_plants']} family plants. Held-out visits {res['held_n']}, extrapolation {res['ext2_n']}. Minutes include the intake time of each variant "
          f"({', '.join(f'{k} {v:g}' for k, v in CFG['INTAKE_MIN'].items())} min). `_n` = noisy, missing and wrongly entered facts.", "",
          "## Scorecard (rules and predictions frozen before the run)", "", "| | holds | evidence |", "|---|---|---|"]
    L += [f"| {k} | {'yes' if ok else 'NO'} | {ev} |" for k, ok, ev in res["scorecard"]]
    L += ["", "## Held-out broad family: the ladder and the candidates", "", "| variant | top-1 | pair hit | wrong-conf | confident | acc when confident | checks | minutes | ECE |", "|---|---|---|---|---|---|---|---|---|"]
    order = ["A_plain", "B_robust", "R_A", "R_B", "C1_A", "C3_A", "C15_A", "O_A", "C3_A_n", "C3_B_n", "C15_A_n", "C15_B_n"]
    for v in order:
        m = res["held"][v]
        L.append(f"| {v} | {m['top1']:.3f} | {m['pair_hit']:.2f} | {m['wrong_conf']:.3f} | {m['confident']:.2f} | {m['acc_when_confident']:.2f} | {m['checks']:.1f} | {m['minutes']:.0f} | {m['ece']:.3f} |")
    L += ["", "## Out-of-family checks (noisy facts)", "", "| set | variant | top-1 | wrong-conf | confident | minutes | ECE |", "|---|---|---|---|---|---|---|"]
    ov = ["A_plain", "B_robust", "R_A", "R_B", "C3_A_n", "C3_B_n", "C15_A_n", "C15_B_n"]
    for sn, d in [("extrapolation (full span)", res["ext2"])] + [(f"Addendum 3: {w}", d) for w, d in res["h2"].items()]:
        for v in ov:
            m = d[v]
            L.append(f"| {sn} | {v} | {m['top1']:.3f} | {m['wrong_conf']:.3f} | {m['confident']:.2f} | {m['minutes']:.0f} | {m['ece']:.3f} |")
    L += ["", "## Paired differences on the held-out family (95% interval, whole plants resampled)", "", "| comparison | d wrong-conf | d top-1 | d confident |", "|---|---|---|---|"]
    f_ = lambda t_: f"{t_[0]:+.3f} [{t_[1]:+.3f}, {t_[2]:+.3f}]"  # noqa: E731
    for k, d in res["diffs"].items():
        L.append(f"| {k} | {f_(d['wrong_conf'])} | {f_(d['top1'])} | {f_(d['confident'])} |")
    L += ["", "## Which facts the regressions lean on (mean |slope| / residual sd over all hypothesis-check cells, C15)", "", "| fact | weight |", "|---|---|"]
    L += [f"| {n} | {w:.3f} |" for n, w in sorted(res["fact_weight"].items(), key=lambda kv: -kv[1])]
    L += ["", "Limits: facts shift reading means only (no evidence about the cause from the facts themselves); the fact noise, unknown-probabilities and intake minutes are my estimates; "
          "the oracle O conditions on all design parameters and cannot be had in a building; everything is inside this simulator."]
    (out / "CONDITIONING_REPORT.md").write_text("\n".join(L) + "\n")
