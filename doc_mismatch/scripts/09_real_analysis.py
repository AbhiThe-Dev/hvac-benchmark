"""Real-data analysis: rule-based evidence detector vs structure-only, with the same rule run on simulated cases for reference."""
import json, pickle, sys, warnings
from pathlib import Path
import numpy as np
warnings.filterwarnings("ignore")
ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "src"))
from docmismatch import real_frp as R

OUT = ROOT.parent / "results" / "docmismatch" / "real_frp"
RES = ROOT.parent / "results" / "docmismatch"
rng = np.random.default_rng(0)
NB = 2000

d = pickle.load(open(OUT / "rule_scores.pkl", "rb"))
events, wins, S, C = d["events"], d["wins"], d["score"], d["clean"]
Ev, W = S.shape
seas = np.array([w["season"] for w in wins]); held = seas != "fall"
fam = np.array([e.slot for e in events]); sf = np.array([e.same_floor for e in events])

# ---- day-level observability (per event, across all 14 days) ---------------------------------
full = R.load_windows()
bds = [R.make_bundle(w["series"]) for w in full]
def day_obs(ev):
    gaps = {(w, k): [] for w in range(2) for k in range(3)}
    for bd in bds:
        for w, (i, j) in enumerate(((ev.a, ev.b), (ev.b, ev.a))):
            et = R.pair_errors(bd, ev.slot, R.ROOMS[j], R.ROOMS[j]); ed = R.pair_errors(bd, ev.slot, R.ROOMS[i], R.ROOMS[j])
            for k in range(3):
                gaps[(w, k)].append(0.0 if (not np.isfinite(et[k]) or not np.isfinite(ed[k])) else (ed[k] - et[k]) / (abs(ed[k]) + abs(et[k]) + 1e-9))
    st = "unobservable"
    for g in gaps.values():
        g = np.array(g); wn, mean = int((g > 0).sum()), float(g.mean())
        if wn >= int(np.ceil(5 / 6 * len(g))) and mean >= 0.2: return "observable"
        if wn > len(g) // 2 and mean >= 0.08: st = "ambiguous"
    return st
obs = np.array([day_obs(e) for e in events])
print("day-level observability by family:", {f: {o: int(((fam == f) & (obs == o)).sum()) for o in ("observable", "ambiguous", "unobservable")} for f in R.SLOTS})

# ---- structure-only baseline: pretrained decoder, zero-shot, on the documented graph ---------------
import torch, networkx as nx
from docmismatch.encoder_io import EncoderKit
from hvac_benchmark.graph.networkx_build import TopologyGraph
from hvac_benchmark.pretrain.data import RELATIONS, example_from_topology
kit = EncoderKit()
TYPES = {"RTU": "RTU", "VAV": "VAV", "Zone": "HVAC_Zone", "SAT": "Discharge_Air_Temperature_Sensor", "PWR": "Electrical_Power_Sensor", "TEMP": "Zone_Air_Temperature_Sensor"}
def doc_graph(ev):
    g = nx.MultiDiGraph(); rel = {r: set() for r in RELATIONS}
    def node(n, k): g.add_node(n, brick_type=TYPES[k], brick_types=[TYPES[k]], location=None)
    node("RTU", "RTU")
    for r in R.ROOMS:
        for k in ("VAV", "Zone", "SAT", "PWR", "TEMP"): node(f"{k}{r}", k)
    def edge(a, b, rl): g.add_edge(a, b, relation=rl); rel[rl].add((a, b))
    swap = {}
    if ev is not None: swap = {(ev.slot, ev.a): ev.b, (ev.slot, ev.b): ev.a}
    for i, r in enumerate(R.ROOMS):
        edge("RTU", f"VAV{r}", "feeds")
        rr = lambda slot: R.ROOMS[swap.get((slot, i), i)]  # noqa: E731
        edge(f"VAV{r}", f"Zone{rr('vav_zone')}", "feeds")
        edge(f"VAV{r}", f"SAT{rr('vav_sat')}", "hasPoint"); edge(f"VAV{r}", f"PWR{rr('vav_pwr')}", "hasPoint")
        edge(f"Zone{r}", f"TEMP{rr('zone_temp')}", "hasPoint")
    return example_from_topology(TopologyGraph("frp", "real", g, rel), kit.ontology, kit.vocab)
@torch.no_grad()
def struct_score(ev):
    ex = doc_graph(ev); m = kit.pretrained; worst = -1e9
    for ri, rl in enumerate(RELATIONS):
        e = ex.edges[rl]
        for n in range(len(e)):
            keep = np.ones(len(e), bool); keep[n] = False
            h = m.encode(ex, {rl: keep})
            worst = max(worst, -m.score(h, torch.tensor([int(e[n, 0])]), torch.tensor([int(e[n, 1])]), ri).item())
    return worst
s0 = struct_score(None)
ss = np.array([struct_score(e) for e in events])
print("structure-only (pretrained decoder, zero-shot): clean %.3f; event scores distinct values %d" % (s0, len(np.unique(np.round(ss, 6)))))

# ---- AUROC with two-way cluster bootstrap (events x days) ------------------------------------------
def ind(score, clean_):  # (Ev,W) or (Ev,) -> pairwise indicator vs the same-window clean doc
    sc = score if score.ndim == 2 else np.broadcast_to(score[:, None], (Ev, W))
    cl = clean_ if np.ndim(clean_) else np.full(W, clean_)
    return (sc > cl[None, :]).astype(float) + 0.5 * (sc == cl[None, :])
I_rule, I_struct = ind(S, C), ind(ss, s0)
def auc(I, emask, wmask): 
    m = emask[:, None] & wmask[None, :]; return float(I[m].mean()) if m.any() else np.nan
def boot(emask, wmask, fn, nb=NB):
    out = []
    for _ in range(nb):
        ei = rng.integers(0, Ev, Ev); wi = rng.integers(0, W, W)
        out.append(fn(ei, wi, emask, wmask))
    out = np.array(out); return np.nanpercentile(out, [2.5, 97.5])
def a_pair(I): return lambda ei, wi, em, wm: (I[np.ix_(ei, wi)][em[ei][:, None] & wm[wi][None, :]].mean() if (em[ei][:, None] & wm[wi][None, :]).any() else np.nan)
def delta(I1, I2): return lambda ei, wi, em, wm: (a_pair(I1)(ei, wi, em, wm) - a_pair(I2)(ei, wi, em, wm))
ALLE, ALLW = np.ones(Ev, bool), np.ones(W, bool)
slices = {"all events, all days": (ALLE, ALLW), "held-out seasons (spring/summer/winter, 6 days)": (ALLE, held), "design season (fall, 8 days; channels were tuned here)": (ALLE, ~held),
          "same-floor swaps (plausible)": (sf, ALLW), "cross-floor swaps": (~sf, ALLW), "observable events (day-level audit)": (obs == "observable", ALLW),
          "not observable (ambiguous+unobservable)": (obs != "observable", ALLW)}
for f in R.SLOTS: slices[f"family: {R.FAMILY[f]}"] = (fam == f, ALLW)
rows = {}
for name, (em, wm) in slices.items():
    a, b = auc(I_rule, em, wm), auc(I_struct, em, wm)
    rows[name] = {"n_events": int(em.sum()), "n_days": int(wm.sum()), "rule": a, "rule_ci": boot(em, wm, a_pair(I_rule)).tolist(), "struct": b,
                  "delta": a - b, "delta_ci": boot(em, wm, delta(I_rule, I_struct)).tolist()}
    print(f"{name:58s} n_ev={em.sum():3d} days={wm.sum():2d} rule {a:.3f} [{rows[name]['rule_ci'][0]:.2f},{rows[name]['rule_ci'][1]:.2f}]  struct {b:.3f}  delta {a-b:+.3f} [{rows[name]['delta_ci'][0]:+.2f},{rows[name]['delta_ci'][1]:+.2f}]", flush=True)

# ---- same untrained rule on the SIMULATED benchmark (hard vs clean; pooled within topology) -------------
from docmismatch.data import load_base
from docmismatch.features import FEATURE_NAMES, case_rows
N = FEATURE_NAMES
def sim_doc_score(rows_):
    best = 0.0
    for r in rows_:
        if r["kind"] != "edge": continue
        x = r["x"]; vals = []
        for k in range(3):
            if x[N.index(f"ch{k}_missing")] > 0: continue
            vals.append(max(x[N.index(f"ch{k}_par_margin")], x[N.index(f"ch{k}_child_margin")]))
        best = max(best, float(np.mean(vals)) if vals else 0.0)
    return best
cases = [json.loads(l) for l in open(RES / "cases.jsonl")]
bases = {}
sim = []
for c in cases:
    if c["difficulty"] in ("hard", "clean"):
        b = bases.setdefault(c["topology_id"], load_base(c["topology_id"]))
        sim.append((c, sim_doc_score(case_rows(b, c))))
def sim_auc(pred, groups_boot=True):
    tot_c = tot_n = 0.0; per = {}
    for t in {c["topology_id"] for c, _ in sim}:
        pos = np.array([s for c, s in sim if c["topology_id"] == t and c["label"] == 1 and pred(c)]); neg = np.array([s for c, s in sim if c["topology_id"] == t and c["label"] == 0])
        if len(pos) and len(neg):
            d_ = pos[:, None] - neg[None, :]; tot_c += (d_ > 0).sum() + 0.5 * (d_ == 0).sum(); tot_n += d_.size
    return tot_c / tot_n if tot_n else np.nan
def sim_ci(pred):
    gs = sorted({c["group_id"] for c, _ in sim if c["label"] == 1 and pred(c)})
    vals = []
    for _ in range(1000):
        pick = {g: k for g, k in zip(*np.unique(rng.choice(gs, len(gs)), return_counts=True))}
        tc = tn = 0.0
        for t in {c["topology_id"] for c, _ in sim}:
            pos = np.array([s for c, s in sim if c["topology_id"] == t and c["label"] == 1 and pred(c) for _ in range(pick.get(c["group_id"], 0))]); neg = np.array([s for c, s in sim if c["topology_id"] == t and c["label"] == 0])
            if len(pos) and len(neg):
                d_ = pos[:, None] - neg[None, :]; tc += (d_ > 0).sum() + 0.5 * (d_ == 0).sum(); tn += d_.size
        vals.append(tc / tn)
    return np.percentile(vals, [2.5, 97.5]).tolist()
simrows = {}
for name, pred in {"all hard": lambda c: True, "hard, observable": lambda c: c["observable"] == "true", "VAV-zone swaps": lambda c: c["corruption_type"] == "vav_zone_swap",
                   "VAV point swaps (vav_dat)": lambda c: c["corruption_type"] == "sensor_mapping" and c["corruption_subtype"] == "vav_dat"}.items():
    simrows[name] = {"rule": sim_auc(pred), "ci": sim_ci(pred), "n": sum(1 for c, _ in sim if c["label"] == 1 and pred(c))}
    print(f"SIM rule  {name:30s} AUROC {simrows[name]['rule']:.3f} [{simrows[name]['ci'][0]:.2f},{simrows[name]['ci'][1]:.2f}] n={simrows[name]['n']}")
json.dump({"real": rows, "sim_rule": simrows, "structure_clean": s0, "day_obs": {f: {o: int(((fam == f) & (obs == o)).sum()) for o in ("observable", "ambiguous", "unobservable")} for f in R.SLOTS},
           "n_events": Ev, "n_days": W}, open(OUT / "real_results.json", "w"), indent=1)
