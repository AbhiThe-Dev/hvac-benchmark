"""Is the engine too cautious where the data are diagnosable? (PREREGISTRATION_DR.md Addendum 12)
Leave-one-topology-out over the 8 EXISTING train-role topologies; per slot, four frozen variants of the tempering / masking / budget levers,
scored on BOTH resolution and honesty (accuracy among resolved verdicts). Never touches SEALED data or T1-T6 suites.
  .venv/bin/python doc_mismatch/scripts/44_caution_check.py
"""
import pickle
import sys
import time
from pathlib import Path

import numpy as np

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "src"))
from docmismatch import evidence as EV  # noqa: E402
from docmismatch.active.engine import run_episode  # noqa: E402
from docmismatch.active.nested import build_sim_episodes  # noqa: E402
from docmismatch.active.readiness import SimKind, h32  # noqa: E402
from docmismatch.active.reliability import first_cross  # noqa: E402
from docmismatch.dr import caution_eval as C  # noqa: E402
from docmismatch.dr.pools import DR_DIR, build_pool  # noqa: E402
from docmismatch.dr.verifier_eval import EXISTING, cases_for, make_cfg  # noqa: E402

OUT = DR_DIR / "caution"
SLOTS = ["branch_coil", "loop_branch", "coil_ahu", "ahu_vav"]
VARIANTS = ["base", "beta1", "beta1_unmasked", "budget72"]
TAU = 0.95


def build_pools(mask: bool) -> dict:
    old = EV.MASK_CHANNELS
    EV.MASK_CHANNELS = mask
    try:
        return {t: {0: build_pool(t, 0, None)} for t in EXISTING}       # legacy telemetry, exactly the cached legacy pools when mask=True
    finally:
        EV.MASK_CHANNELS = old


def row(e, r, building):
    crossed, n = first_cross(r.traj, TAU)
    say = bool(r.traj[n] >= 0.5)
    return dict(ep=e.ep_id, building=building, wrong=bool(e.is_wrong), crossed=bool(crossed), n=int(n), correct=(say == (not e.is_wrong)),
                p_final=float(r.traj[n]), n_info=int(r.info_traj[min(n, len(r.info_traj) - 1)]))


def compute(t0):
    cfg = make_cfg(("active",))
    cfg["sim_reps"] = [0]
    cases_all = cases_for(EXISTING)
    pools = {True: build_pools(True), False: build_pools(False)}
    print(f"pools built {time.time() - t0:.0f}s", flush=True)
    kinds = {m: SimKind(cfg, topos=EXISTING, pools=pools[m], cases=cases_all) for m in (True, False)}
    rows = {(s, v): [] for s in SLOTS for v in VARIANTS}
    betas = {}
    for slot in SLOTS:
        for h in EXISTING:
            if slot not in pools[True][h][0].slots:
                continue
            train = [u for u in EXISTING if u != h]
            tr_m = kinds[True].train(train)
            mod_m, beta_cal = kinds[True].fit_slot(tr_m, slot, None)          # calibrated on the 7 training topologies only
            tr_u = kinds[False].train(train)
            mod_u, _ = kinds[False].fit_slot(tr_u, slot, 1.0)                 # beta given -> no calibration
            if not mod_m or not mod_u:
                continue
            betas[(slot, h)] = beta_cal
            cs = [c for c in cases_all if c["topology_id"] == h]
            eps_m = [e for e in build_sim_episodes({h: pools[True][h][0]}, cs) if e.slot == slot]
            eps_u = {e.ep_id: e for e in build_sim_episodes({h: pools[False][h][0]}, cs) if e.slot == slot}
            for e in eps_m:
                seed = h32(e.ep_id) % 10_000
                sl = kinds[True].slice_idx(e, "visit", 0)
                specs = {"base": (e, mod_m, beta_cal, 24), "beta1": (e, mod_m, 1.0, 24), "budget72": (e, mod_m, beta_cal, 72)}
                if e.ep_id in eps_u:
                    specs["beta1_unmasked"] = (eps_u[e.ep_id], mod_u, 1.0, 24)
                for v, (ee, mod, b, nmax) in specs.items():
                    r = run_episode(ee, mod, sl, "active", tau=2.0, nmax=nmax, seed=seed, beta=b, diag=True)
                    if r is not None:
                        rows[(slot, v)].append(row(ee, r, h))
            print(f"  {slot:12s} held-out {h:18s} eps={len(eps_m):3d} beta_cal={beta_cal:.2f} {time.time() - t0:.0f}s", flush=True)
    return dict(rows=rows, betas=betas)


def main():
    OUT.mkdir(parents=True, exist_ok=True)
    t0 = time.time()
    f = OUT / "caution.pkl"
    if f.exists():
        res = pickle.loads(f.read_bytes())
        print("loaded from cache", flush=True)
    else:
        res = compute(t0)
        f.write_bytes(pickle.dumps(res))
        print(f"done {time.time() - t0:.0f}s", flush=True)
    rows, betas = res["rows"], res["betas"]

    md = ["# Is the engine too cautious where the data are diagnosable? (Addendum 12)", "",
          "Leave-one-topology-out over the 8 `EXISTING` topologies, legacy telemetry, one visit window, `active` policy, tau 0.95. "
          "`base` = calibrated beta, masked, 24 reads; `beta1` = no tempering; `beta1_unmasked` = no tempering + channel masking off; "
          "`budget72` = calibrated beta with 72 reads. 'acc | resolved' is class-balanced over is_wrong / is_right episodes "
          "(stated confidence is 0.95). Simulation only, small samples.", ""]
    verdicts = []
    for slot in SLOTS:
        bl = [b for (s, h), b in betas.items() if s == slot]
        if not bl:
            continue
        md += [f"## {slot}  (calibrated beta per held-out fit: mean {np.mean(bl):.2f}, range {min(bl):.2f}-{max(bl):.2f})", "",
               "| variant | n eps | resolved | acc \\| resolved | wrong & confident | mean reads (resolved) | gained | lost | correct->wrong | wrong->correct |",
               "|---|---|---|---|---|---|---|---|---|---|"]
        base = C.summarize(rows[(slot, "base")])
        for v in VARIANTS:
            s = C.summarize(rows[(slot, v)])
            fl = C.flips(rows[(slot, "base")], rows[(slot, v)]) if v != "base" else {}
            md.append(f"| {v} | {s['n']} | {s['n_resolved']}/{s['n']} ({s['resolved']:.0%}) | {s['acc_resolved']:.3f} | {s['wrong_confident']:.1%} | "
                      f"{s['mean_reads']:.1f} | {fl.get('gained', '')} | {fl.get('lost', '')} | {fl.get('correct_to_wrong', '')} | {fl.get('wrong_to_correct', '')} |")
            if v != "base" and s["n"]:
                verdicts.append((slot, v, C.verdict(base, s)))
        md.append("")
    md += ["## Frozen reading rules (Addendum 12)", "", "| slot | variant | verdict |", "|---|---|---|"]
    md += [f"| {s} | {v} | {vd} |" for s, v, vd in verdicts]
    diag = [s for s in SLOTS[:3]]
    for v in VARIANTS[1:]:
        n_ok = sum(1 for s, vv, vd in verdicts if vv == v and s in diag and vd == "WORTH PURSUING")
        md.append(f"\n- `{v}`: worth pursuing in {n_ok} of 3 diagnosable slots -> " + ("WORTH PURSUING overall" if n_ok >= 2 else "not worth pursuing overall"))
    (OUT / "caution_report.md").write_text("\n".join(md))
    print("\n".join(md))


main()
