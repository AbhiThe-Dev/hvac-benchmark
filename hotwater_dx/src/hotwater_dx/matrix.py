"""Build the cause x check matrix from the physics model.

For each plant draw (a Latin-hypercube point of the parameter ranges) we build a commissioned healthy plant, apply one cause (re-drawing up to
MAX_ATTEMPTS times until the fault produces a complaint), and compare readings fault-vs-healthy at the *same* plant (a paired, design-referenced
comparison: the technician is assumed to know the as-designed value). z = effect / single-reading sd, where sd includes tool error, per-visit bias and
spot-reading randomness (pump on/off at arrival). Classification rules are frozen in THRESHOLDS (hash recorded in PREREGISTRATION.md).

Output is PHYSICS-MODEL output, not field evidence (provenance.DISCLAIMER).
"""
from __future__ import annotations

import hashlib
import json
from dataclasses import dataclass, field

import numpy as np

from . import causes as C
from . import checks as K
from .params import BY_NAME, NAMES
from .plant import Plant, build_plant
from .sampling import design_matrix, substream
from .solve import has_complaint

THRESHOLDS = {
    "N_THETA": 200,            # plant draws per cause
    "REPS": 24,                # noisy readings per plant and state
    "REPS_BINARY": 200,        # noisy readings per plant for 0/1 readouts (their sd is otherwise estimated from a handful of misreads)
    "MAX_ATTEMPTS": 6,         # re-draws of a fault until it produces a complaint
    "GATE_MIN": 40,            # fewer gated plants than this: cells use all plants and the cause is flagged 'weakly symptomatic'
    "Z_SEP": 3.0,              # |z| at or above this = separated from normal in one reading
    "Z_NULL": 1.0,             # |z| below this = indistinguishable from normal
    "P_DET": 0.95,             # share needed for DETERMINISTIC (seen)
    "P_NULL": 0.95,            # share needed for DETERMINISTIC (not seen)
    "SIGN": 0.95,              # sign consistency needed to call the direction known
    "D_STAR": 2.5,             # pair separation threshold (standardised median difference)
    "RHO_DOM": 0.5,            # |Spearman rho| above which one analyst-chosen parameter 'explains' a PARAM cell
    "MIN_APPLICABLE": 30,      # plants needed for an applicable check
    "SEED": 20261007,
}


def thresholds_hash() -> str:
    return hashlib.sha256(json.dumps(THRESHOLDS, sort_keys=True).encode()).hexdigest()


# claims from READ sources about specific cells; used only to flag agreement/conflict, never to set a class
SOURCE_CELL_CLAIMS = {
    ("crossover", "K17"): ("seen", "AYALA16", "lab-validated: flow continues / hot side repressurizes with the cold feed isolated"),
    ("crossover", "K18"): ("seen", "AYALA16", "lab-validated Eatherton method"),
    ("crossover", "K05"): ("not_deterministic", "AYALA16", "supply/return temperature logging judged 'invalid' as a crossover detector, 'can be indicative'"),
    ("tmv_starved_fouled", "K03"): ("seen", "POWERS", "outlet too low / flow drops when checkstops are limed"),
    ("pump_failed", "K05"): ("seen", "BED15", "a broken loop pump left the return at 35-40 C against ~60 C"),
    ("pump_control_fault", "K10"): ("seen", "HABITAT", "reversed aquastat set points: the pump never started; found by reading the controls"),
    ("balancing_valve_misset", "K05"): ("not_deterministic", "BED15", "a fine principal return can hide starved subordinate loops"),
    ("balancing_valve_misset", "K06"): ("seen", "BED15", "subordinate-return monitoring finds what the principal return masks"),
}


@dataclass
class Cell:
    cause: str
    check: str
    tool: str
    cls: str
    reason: str
    n: int
    gated: bool
    p_sep: float
    p_null: float
    sign_cons: float
    sign: int
    median_z: float
    median_effect: float
    p_blind: float
    top_params: list
    provenance: str
    source_claim: str = ""
    agrees: bool | None = None
    tool_fragile: bool = False
    requires_dynamics: bool = False
    conflict_sensitive: bool = False


def _ranks(x):
    return np.argsort(np.argsort(x)).astype(float)


def spearman(a, b) -> float:
    ra, rb = _ranks(a), _ranks(b)
    sa, sb = ra.std(), rb.std()
    if sa < 1e-12 or sb < 1e-12:
        return 0.0
    return float(np.corrcoef(ra, rb)[0, 1])


@dataclass
class World:
    seed: int
    design: list
    plants: list
    ctx_h: list
    cause_plants: dict = field(default_factory=dict)    # cause id -> list[Plant]
    cause_draws: dict = field(default_factory=dict)
    cause_gated: dict = field(default_factory=dict)
    cause_gate_rate: dict = field(default_factory=dict)
    cause_ctx: dict = field(default_factory=dict)


def build_world(n_theta: int | None = None, seed: int | None = None, causes: tuple[str, ...] | None = None, overrides: dict | None = None,
                latent=None, sev_mult: float = 1.0, sev_floor: float = 0.0) -> World:
    """`overrides`, `latent` (a function (plant, rng) that adds a hidden condition to the healthy plant), `sev_mult` and `sev_floor` are for stress tests;
    the frozen matrix uses the defaults (no change)."""
    n_theta = n_theta or THRESHOLDS["N_THETA"]
    seed = seed or THRESHOLDS["SEED"]
    design = design_matrix(n_theta, seed, overrides)
    plants = [build_plant(design[j], substream(seed, 1, j)) for j in range(n_theta)]
    if latent is not None:
        for j, P in enumerate(plants):
            latent(P, substream(seed, 6, j))
    w = World(seed=seed, design=design, plants=plants, ctx_h=[K.Ctx(P) for P in plants])
    for ki, cid in enumerate(C.IDS):
        if causes is not None and cid not in causes:
            continue
        spec = C.BY_ID[cid]
        fps, draws, gated, attempts, passes = [], [], [], 0, 0
        for j, P in enumerate(plants):
            first = None
            ok = False
            for a in range(THRESHOLDS["MAX_ATTEMPTS"]):
                d = spec.draw(substream(seed, 2, ki, j, a), P)
                if sev_mult != 1.0 or sev_floor > 0.0:
                    d["sev"] = float(min(max(d["sev"] * sev_mult, sev_floor, 1e-3), 1.0))
                Q = spec.apply(P, d)
                attempts += 1
                g = has_complaint(Q)
                passes += g
                if first is None:
                    first = (Q, d)
                if g:
                    fps.append(Q)
                    draws.append(d)
                    gated.append(True)
                    ok = True
                    break
            if not ok:
                fps.append(first[0])
                draws.append(first[1])
                gated.append(False)
        w.cause_plants[cid] = fps
        w.cause_draws[cid] = draws
        w.cause_gated[cid] = np.array(gated)
        w.cause_gate_rate[cid] = passes / max(attempts, 1)
        w.cause_ctx[cid] = [K.Ctx(Q) for Q in fps]
    return w


def _nreps(check: K.CheckSpec) -> int:
    return THRESHOLDS["REPS_BINARY"] if check.binary else THRESHOLDS["REPS"]


def _reads(check: K.CheckSpec, ctx: K.Ctx, tool: str, rng, R: int | None = None) -> np.ndarray:
    return np.array([check.read(ctx, rng, tool) for _ in range(R or _nreps(check))])


def cell_stats(w: World, cid: str, check: K.CheckSpec, tool: str):
    """Per-plant effect, sd and z for one (cause, check, tool). Returns dict of arrays (applicable plants only) or None."""
    R = _nreps(check)
    ci = C.IDS.index(cid)
    k_i = K.IDS.index(check.id)
    t_i = ((check.tool,) + check.tools_alt).index(tool)
    n = len(w.plants)
    idx = [j for j in range(n) if check.applies(w.plants[j])]
    if len(idx) < THRESHOLDS["MIN_APPLICABLE"]:
        return None
    eff, sd, hs, fs = [], [], [], []
    for j in idx:
        h = _reads(check, w.ctx_h[j], tool, substream(w.seed, 3, 0, k_i, t_i, j), R)
        f = _reads(check, w.cause_ctx[cid][j], tool, substream(w.seed, 3, ci + 1, k_i, t_i, j), R)
        e = f.mean() - h.mean()
        s = max(np.sqrt(0.5 * (f.var(ddof=1) + h.var(ddof=1))), check.sigma_min)
        eff.append(e)
        sd.append(s)
        hs.append(h)
        fs.append(f)
    eff, sd = np.array(eff), np.array(sd)
    return dict(idx=np.array(idx), eff=eff, sd=sd, z=eff / sd, h=np.array(hs), f=np.array(fs))


def classify(w: World, cid: str, check: K.CheckSpec, tool: str, healthy_band=None) -> Cell:
    cause = C.BY_ID[cid]
    gated_all = w.cause_gated[cid]
    use_gated = int(gated_all.sum()) >= THRESHOLDS["GATE_MIN"]
    base = dict(cause=cid, check=check.id, tool=tool, requires_dynamics=cause.requires_dynamics)
    if not check.physics_readable:
        rel = cid in check.relevant
        return Cell(**base, cls="NEEDS_ELIC" if rel else "DET_NOT_SEEN", reason=("check is not physics-readable (declared relevant)" if rel else "declared not relevant (analyst)"),
                    n=0, gated=use_gated, p_sep=float("nan"), p_null=float("nan"), sign_cons=float("nan"), sign=0, median_z=float("nan"), median_effect=float("nan"),
                    p_blind=float("nan"), top_params=[], provenance="analyst")
    st = cell_stats(w, cid, check, tool)
    if st is None:
        return Cell(**base, cls="N/A", reason="check applies to too few plants", n=0, gated=use_gated, p_sep=float("nan"), p_null=float("nan"), sign_cons=float("nan"), sign=0,
                    median_z=float("nan"), median_effect=float("nan"), p_blind=float("nan"), top_params=[], provenance="physics")
    idx = st["idx"]
    keep = gated_all[idx] if use_gated else np.ones(len(idx), bool)
    if int(keep.sum()) < 5:
        return Cell(**base, cls="N/A", reason="too few applicable symptomatic plants", n=int(keep.sum()), gated=use_gated, p_sep=float("nan"), p_null=float("nan"), sign_cons=float("nan"),
                    sign=0, median_z=float("nan"), median_effect=float("nan"), p_blind=float("nan"), top_params=[], provenance="physics")
    z, eff = st["z"][keep], st["eff"][keep]
    sel = idx[keep]
    n = len(z)
    T = THRESHOLDS
    pos, neg = float((z > 0).mean()), float((z < 0).mean())
    sign = 1 if pos >= neg else -1
    sign_cons = max(pos, neg)
    p_sep = float(((np.abs(z) >= T["Z_SEP"]) & (np.sign(z) == sign)).mean())
    p_null = float((np.abs(z) < T["Z_NULL"]).mean())
    # blind separability: single fault readings against the pooled healthy band (technician has no as-designed value)
    lo, hi = np.percentile(st["h"].ravel(), [1, 99])
    p_blind = float(((st["f"][keep][:, 0] < lo) | (st["f"][keep][:, 0] > hi)).mean())
    # which parameter drives the effect
    cols = np.array([[w.design[j][nm] for nm in NAMES] for j in sel])
    rhos = [(nm, spearman(z, cols[:, c])) for c, nm in enumerate(NAMES)]
    top = sorted(rhos, key=lambda x: -abs(x[1]))[:3]
    top_params = [(nm, round(r, 2), BY_NAME[nm].prov) for nm, r in top]
    reason = ""
    if p_sep >= T["P_DET"] and sign_cons >= T["SIGN"]:
        cls = "DET_SEEN"
    elif p_null >= T["P_NULL"]:
        cls = "DET_NOT_SEEN"
    else:
        cls = "PARAM"
        if cause.requires_dynamics:
            cls, reason = "NEEDS_ELIC", "real fault is time-dependent (hunting / instability) and the model is steady-state"
        elif top and abs(top[0][1]) >= T["RHO_DOM"] and BY_NAME[top[0][0]].prov in ("ANALYST", "PLACEHOLDER"):
            cls, reason = "NEEDS_ELIC", f"separation depends on an analyst-chosen range: {top[0][0]} (rho {top[0][1]})"
        elif sign_cons < T["SIGN"]:
            reason = "sign of the effect changes with plant parameters"
    return Cell(**base, cls=cls, reason=reason, n=n, gated=use_gated, p_sep=p_sep, p_null=p_null, sign_cons=sign_cons, sign=sign, median_z=float(np.median(z)),
                median_effect=float(np.median(eff)), p_blind=p_blind, top_params=top_params, provenance="physics")


def build_matrix(w: World, tools_alt: bool = True) -> list[Cell]:
    cells = []
    for cid in w.cause_plants:
        for check in K.CHECKS:
            cell = classify(w, cid, check, check.tool)
            claim = SOURCE_CELL_CLAIMS.get((cid, check.id))
            if claim:
                kind, src, why = claim
                cell.source_claim = f"{src}: {why}"
                seen = cell.cls == "DET_SEEN" or (cell.cls in ("PARAM", "NEEDS_ELIC") and cell.p_sep >= 0.5)
                cell.agrees = seen if kind == "seen" else (cell.cls != "DET_SEEN")
                if cell.provenance == "physics" and cell.agrees:
                    cell.provenance = "physics+source"
            if tools_alt and check.physics_readable and check.tools_alt and cell.cls == "DET_SEEN":
                for t in check.tools_alt:
                    if classify(w, cid, check, t).cls != "DET_SEEN":
                        cell.tool_fragile = True
                        break
            cells.append(cell)
    return cells


# ------------------------------------------------------------------------------------------------ pairs of causes
def pair_confusion(w: World, d_star: float | None = None) -> list[dict]:
    """For each check and cause pair: standardised separation D of their median effects (effect = fault minus healthy at the same plant)."""
    d_star = d_star or THRESHOLDS["D_STAR"]
    out = []
    cids = list(w.cause_plants)
    for check in K.CHECKS:
        if not check.physics_readable:
            continue
        stats = {}
        for cid in cids:
            st = cell_stats(w, cid, check, check.tool)
            if st is None:
                continue
            gated = w.cause_gated[cid]
            keep = gated[st["idx"]] if gated.sum() >= THRESHOLDS["GATE_MIN"] else np.ones(len(st["idx"]), bool)
            e = st["eff"][keep]
            mad = 1.4826 * np.median(np.abs(e - np.median(e)))
            stats[cid] = (float(np.median(e)), float(np.sqrt(np.median(st["sd"][keep]) ** 2 + mad ** 2)))
        for i, a in enumerate(cids):
            for b in cids[i + 1:]:
                if a in stats and b in stats:
                    (ma, sa), (mb, sb) = stats[a], stats[b]
                    D = abs(ma - mb) / np.sqrt(0.5 * (sa ** 2 + sb ** 2))
                    out.append(dict(check=check.id, a=a, b=b, D=float(D), separated=bool(D >= d_star)))
    return out


def ambiguous_pairs(pairs: list[dict]) -> list[dict]:
    best = {}
    for p in pairs:
        k = (p["a"], p["b"])
        if k not in best or p["D"] > best[k]["D"]:
            best[k] = p
    return sorted([dict(a=a, b=b, best_check=v["check"], best_D=v["D"]) for (a, b), v in best.items() if not v["separated"]], key=lambda x: x["best_D"])


# ------------------------------------------------------------------------------------------------ multi-fault interactions
KEY_CHECKS = ("K01", "K03", "K05", "K06", "K07", "K08", "K10", "K16", "K17", "K19")


def interactions(w: World, n_pairs: int = 100) -> list[dict]:
    out = []
    n = min(n_pairs, len(w.plants))
    for pi, it in enumerate(C.INTERACTIONS):
        a, b = C.BY_ID[it["a"]], C.BY_ID[it["b"]]
        ctx_a, ctx_b, ctx_ab = [], [], []
        for j in range(n):
            P = w.plants[j]
            da, db = a.draw(substream(w.seed, 4, pi, j, 0), P), b.draw(substream(w.seed, 4, pi, j, 1), P)
            Pa, Pb = a.apply(P, da), b.apply(P, db)
            Pab = b.apply(Pa, db)
            ctx_a.append(K.Ctx(Pa))
            ctx_b.append(K.Ctx(Pb))
            ctx_ab.append(K.Ctx(Pab))
        for cname in KEY_CHECKS:
            ch = K.BY_ID[cname]
            e = {"a": [], "b": [], "ab": []}
            sds = []
            for j in range(n):
                if not ch.applies(w.plants[j]):
                    continue
                rngs = lambda t: substream(w.seed, 5, pi, K.IDS.index(cname), j, t)  # noqa: E731
                h = _reads(ch, w.ctx_h[j], ch.tool, rngs(0))
                fa, fb, fab = (_reads(ch, c[j], ch.tool, rngs(t)) for t, c in ((1, ctx_a), (2, ctx_b), (3, ctx_ab)))
                e["a"].append(fa.mean() - h.mean())
                e["b"].append(fb.mean() - h.mean())
                e["ab"].append(fab.mean() - h.mean())
                sds.append(max(np.sqrt(0.5 * (fab.var(ddof=1) + h.var(ddof=1))), ch.sigma_min))
            if len(sds) < 20:
                continue
            ea, eb, eab = (float(np.median(e[k])) for k in ("a", "b", "ab"))
            sd = float(np.median(sds))
            big = max(abs(ea), abs(eb))
            if big < 1.5 * sd:
                kind = "both_invisible" if abs(eab) < 1.5 * sd else "emergent"
            elif abs(eab) < 0.3 * big:
                kind = "masks"
            elif abs(eab - (ea + eb)) < 1.0 * sd:
                kind = "additive"
            elif abs(eab) > 1.3 * big and abs(eab) > abs(ea + eb) + sd:
                kind = "compounds"
            elif abs(eab - ea) < 1.0 * sd:
                kind = "looks_like_a"
            elif abs(eab - eb) < 1.0 * sd:
                kind = "looks_like_b"
            else:
                kind = "mixed"
            out.append(dict(a=it["a"], b=it["b"], seeded_kind=it["kind"], note=it["note"], check=cname, e_a=ea, e_b=eb, e_ab=eab, sd=sd, observed=kind))
    return out


# ------------------------------------------------------------------------------------------------ uncertainty ranking and leverage
TIER = {"NEEDS_ELIC": 0, "PARAM": 1, "DET_SEEN": 2, "DET_NOT_SEEN": 3, "N/A": 4}


def uncertainty_rows(cells: list[Cell], w: World, ambiguous: list[dict]) -> list[dict]:
    amb_checks = {}
    for p in ambiguous:
        amb_checks.setdefault(p["a"], set()).add(p["b"])
    rows = []
    for c in cells:
        if c.cls in ("DET_SEEN", "DET_NOT_SEEN", "N/A") and not c.tool_fragile:
            continue
        score = 1.0 if c.cls == "NEEDS_ELIC" else (1.0 - abs(2 * c.p_sep - 1.0) if c.p_sep == c.p_sep else 0.5)
        if c.cls == "NEEDS_ELIC" and c.top_params and c.top_params[0][2] in ("ANALYST", "PLACEHOLDER"):
            score += 0.1
        if c.tool_fragile:
            score += 0.1
        if c.sign_cons == c.sign_cons and c.sign_cons < THRESHOLDS["SIGN"]:
            score += 0.2
        if c.agrees is False:
            score += 1.0
        rows.append(dict(tier=TIER[c.cls], score=round(score, 3), cause=c.cause, check=c.check, cls=c.cls, reason=c.reason, p_sep=c.p_sep, sign_cons=c.sign_cons,
                         top_param=c.top_params[0][0] if c.top_params else "", conflict=c.agrees is False))
    rows.sort(key=lambda r: (not r["conflict"], r["tier"], -r["score"], r["cause"], r["check"]))
    return rows


def parameter_leverage(cells: list[Cell]) -> list[dict]:
    cnt = {}
    for c in cells:
        if c.cls in ("PARAM", "NEEDS_ELIC") and c.top_params:
            nm, rho, prov = c.top_params[0]
            e = cnt.setdefault(nm, dict(param=nm, prov=prov, cells=0, sum_abs_rho=0.0))
            e["cells"] += 1
            e["sum_abs_rho"] += abs(rho)
    return sorted(cnt.values(), key=lambda r: -r["cells"])
