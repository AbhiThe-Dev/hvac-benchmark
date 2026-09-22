"""Draw the DR spec (frozen once written), simulate every building, run GENERATION-LEVEL checks only.

  physics_pipeline/.venv/bin/python doc_mismatch/scripts/23_generate_dr.py spec              # write spec + manifest (refuses to overwrite)
  physics_pipeline/.venv/bin/python doc_mismatch/scripts/23_generate_dr.py sim [suite ...] [--procs N]
No model, likelihood or verifier is run here. Checks: EnergyPlus success, component counts, non-constant flow/temperature series,
thermal sanity (zone temperatures within setback band +-2K), sizing sanity (AHU peak flow vs its VAVs), finite values.
"""
import hashlib, json, shutil, sys, time
import multiprocessing as mp
from pathlib import Path
import numpy as np

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "src"))
from docmismatch import physical  # noqa: E402
from docmismatch.dr import build as DB, spec as DS  # noqa: E402

DR = ROOT.parent / "results" / "docmismatch" / "dr"
SPEC, MAN = DR / "spec.json", DR / "spec_manifest.json"
BASE = DB.DR_ROOT / "base"
KEEP = {"in.idf", "eplusout.err", "evidence.npz", "graph.json", "run.json", "spec.json"}


def write_spec():
    if SPEC.exists():
        sys.exit(f"{SPEC} exists; the DR spec is frozen once written")
    DR.mkdir(parents=True, exist_ok=True)
    spec = DS.draw_all()
    SPEC.write_text(json.dumps(spec, indent=1, sort_keys=True))
    MAN.write_text(json.dumps(dict(spec_sha256=hashlib.sha256(SPEC.read_bytes()).hexdigest(), written_utc=time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime()),
                                   spec_py_sha256=hashlib.sha256((ROOT / "src/docmismatch/dr/spec.py").read_bytes()).hexdigest(),
                                   status="spec_written_before_any_dr_simulation", suites={s: [b["id"] for b in v["buildings"]] for s, v in json.loads(SPEC.read_text())["suites"].items()}), indent=1))
    print("spec sha256", hashlib.sha256(SPEC.read_bytes()).hexdigest(), {s: len(v["buildings"]) for s, v in json.loads(SPEC.read_text())["suites"].items()})


def check(tid: str, t: dict) -> dict:
    from docmismatch.data import load_base
    b = load_base(tid)
    prob, cnt = [], {}
    n = lambda *k: len(b.ids(*k))  # noqa: E731
    if (n("AHU"), n("VAV"), n("Zone"), n("HWL"), n("CHWL")) != (t["n_ahu"], t["n_vav"], t["n_vav"], t["n_hw"], t["n_chw"]):
        prob.append(f"component counts differ: AHU {n('AHU')} VAV {n('VAV')} Zone {n('Zone')} HWL {n('HWL')} CHWL {n('CHWL')}")
    per_ahu = sorted(sum(1 for o, m in b.slot_edges["ahu_vav"] if o == a) for a in b.ids("AHU"))
    if per_ahu != sorted(t["group_sizes"]):
        prob.append(f"VAVs per AHU {per_ahu} != {sorted(t['group_sizes'])}")
    n_el = sum(1 for v in b.ids("VAV") if any(b.nodes[m]["brick_type"] == "Heating_Coil" and b.nodes[m].get("medium") is None for o, m in b.slot_edges.get("coil_vav", []) if o == v))
    exp_el = {"hydronic": 0, "electric": t["n_vav"], "mixed": sum(t["electric_zones"] or [])}[t["reheat"]]
    if n_el != exp_el:
        prob.append(f"electric reheat coils {n_el} != expected {exp_el}")
    ev = b.ev
    if any(not np.isfinite(v).all() for v in ev.values()):
        prob.append("non-finite values")
    key = [k for k in ev if k.split("|")[1] in ("flow", "temp") and k.split("-")[0] in ("AHU", "VAV", "Zone")]
    bad = [k for k in key if np.nanstd(ev[k]) < 1e-6]
    cnt["n_series"], cnt["n_constant_flow_temp"] = len(ev), len(bad)
    if bad:
        prob.append(f"constant flow/temp series: {bad[:5]}")
    zt = np.stack([ev[z + "|temp"] for z in b.ids("Zone")])
    sp = t["setpoints"]
    out_frac = float(((zt < sp["heat_setback"] - 2.0) | (zt > sp["cool_setback"] + 2.0)).mean())
    cnt.update(zone_temp_p50=round(float(np.percentile(zt, 50)), 1), frac_zone_hours_outside_band=round(out_frac, 4))
    if out_frac > 0.05 or not (14 <= np.percentile(zt, 50) <= 29):
        prob.append(f"thermal sanity failed: {out_frac:.3f} outside band, median {np.median(zt):.1f}")
    ratios = []
    for a in b.ids("AHU"):
        vavs = [m for o, m in b.slot_edges["ahu_vav"] if o == a]
        ratios.append(float(ev[a + "|flow"].max() / sum(ev[v + "|flow"].max() for v in vavs)))
    cnt["ahu_peak_over_sum_vav_peak"] = [round(r, 2) for r in ratios]
    if min(ratios) < 0.3 or max(ratios) > 1.05:
        prob.append(f"sizing sanity failed {ratios}")
    sat = [ev[a + "|sat"] for a in b.ids("AHU")]
    cnt["sat_sd_within_ahu"] = [round(float(np.std(s[ev[a + "|flow"] > 0.05 * ev[a + "|flow"].max()])), 2) for s, a in zip(sat, b.ids("AHU"))]
    cnt["oat_range"] = [round(float(ev["ENV|oat"].min()), 1), round(float(ev["ENV|oat"].max()), 1)]
    return dict(ok=not prob, problems=prob, stats=cnt)


def sim_once(t: dict) -> dict:
    tid = t["id"]
    DB.register(t)
    out = BASE / tid
    if out.exists():
        shutil.rmtree(out)
    t0 = time.time()
    try:
        physical.simulate_topology(tid, BASE)
    except Exception as e:  # noqa: BLE001
        return dict(id=tid, ok=False, problems=[f"simulation failed: {str(e)[:300]}"], seconds=round(time.time() - t0, 1))
    for f in out.iterdir():
        if f.name not in KEEP:
            f.unlink() if f.is_file() else shutil.rmtree(f)
    (out / "spec.json").write_text(json.dumps(t, indent=1))
    res = check(tid, t)
    res.update(id=tid, seconds=round(time.time() - t0, 1), suite=t["suite"])
    return res


MAX_ATTEMPTS = 6


def sim_one(job) -> dict:
    """Simulate (suite, idx); when the generation-level PHYSICS checks (no model involved) reject a draw, use the next deterministic re-draw. All rejections are logged."""
    suite, idx = job
    rejected = []
    for attempt in range(MAX_ATTEMPTS):
        t = DS.draw_building(suite, idx, attempt)
        res = sim_once(t)
        if res["ok"]:
            res.update(attempts=attempt + 1, rejected=rejected, spec_attempt=attempt)
            return res
        rejected.append(dict(attempt=attempt, problems=res["problems"]))
    res.update(attempts=MAX_ATTEMPTS, rejected=rejected, ok=False)
    return res


def main():
    if sys.argv[1] == "spec":
        return write_spec()
    args = [a for a in sys.argv[2:] if not a.startswith("--")]
    procs = int(sys.argv[sys.argv.index("--procs") + 1]) if "--procs" in sys.argv else 1
    if procs != 1 and str(procs) in args:
        args.remove(str(procs))
    spec = json.loads(SPEC.read_text())
    todo = [(s, i) for s, v in spec["suites"].items() if not args or s in args for i in range(len(v["buildings"]))]
    BASE.mkdir(parents=True, exist_ok=True)
    if procs > 1:
        with mp.get_context("fork").Pool(procs) as P:
            res = P.map(sim_one, todo, chunksize=1)
    else:
        res = [sim_one(t) for t in todo]
    log = json.loads((DR / "generation_log.json").read_text()) if (DR / "generation_log.json").exists() else {}
    for r in res:
        log[r["id"]] = r
        print(r["id"], "OK" if r["ok"] else "PROBLEM", "attempts", r["attempts"], [x["problems"] for x in r["rejected"]] if r["rejected"] else "", r.get("seconds"), flush=True)
    (DR / "generation_log.json").write_text(json.dumps(log, indent=1))
    print(f"{sum(r['ok'] for r in res)}/{len(res)} ok")


main()
