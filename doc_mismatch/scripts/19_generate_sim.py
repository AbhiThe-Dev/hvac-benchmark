"""Build, simulate, extract and generation-check the expansion topologies of results/docmismatch/active/sim_spec.json.

  physics_pipeline/.venv/bin/python doc_mismatch/scripts/19_generate_sim.py [topology_id ...]

Generation-level checks ONLY (EnergyPlus success, sizing sanity via zone temperatures, non-constant evidence, graph structure).
No classifier / likelihood model / verifier is run here, on dev or sealed topologies.
Raw EnergyPlus outputs are pruned as for the original topologies (kept: in.idf, eplusout.err, evidence.npz, graph.json, run.json).
"""
import hashlib
import json
import sys
import time
from pathlib import Path

import numpy as np

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "src"))
from docmismatch import build_ext, physical  # noqa: E402

RES = ROOT.parent / "results" / "docmismatch"
ACT, BASE = RES / "active", RES / "base"
SPEC, MAN = ACT / "sim_spec.json", ACT / "sim_manifest.json"
KEEP = {"in.idf", "eplusout.err", "evidence.npz", "graph.json", "run.json"}
EXPECTED_SLOTS = {"loop_pump", "loop_source", "loop_branch", "branch_coil", "coil_ahu", "fan_ahu", "ahu_sat", "ahu_vav", "vav_zone", "coil_vav", "vav_dat"}


def check(tid: str, t: dict, out: Path) -> dict:
    """Generation-level validation; returns {'ok': bool, 'problems': [...], 'stats': {...}}."""
    from docmismatch.data import load_base
    b = load_base(tid)
    prob, warn = [], []
    n = lambda k: len(b.ids(k))
    if (n("AHU"), n("VAV"), n("Zone"), n("HWL"), n("CHWL")) != (t["n_ahu"], t["n_vav"], t["n_vav"], t["n_hw"], t["n_chw"]):
        prob.append(f"component counts differ from spec: AHU {n('AHU')} VAV {n('VAV')} Zone {n('Zone')} HWL {n('HWL')} CHWL {n('CHWL')}")
    if set(b.slot_edges) != EXPECTED_SLOTS:
        prob.append(f"slot set {sorted(set(b.slot_edges) ^ EXPECTED_SLOTS)} differs from the C/D structure")
    if len(b.slot_edges.get("ahu_vav", [])) != t["n_vav"]:
        prob.append("ahu_vav edge count != n_vav")
    per_ahu = sorted(sum(1 for o, m in b.slot_edges["ahu_vav"] if o == a) for a in b.ids("AHU"))
    if per_ahu != sorted(t["group_sizes"]):
        prob.append(f"VAVs per AHU {per_ahu} != spec group sizes {sorted(t['group_sizes'])}")
    coils = len(b.slot_edges.get("branch_coil", []))
    if coils != t["n_vav"] + 2 * t["n_ahu"] or len(b.slot_edges.get("loop_branch", [])) != coils:
        prob.append("branch/coil counts inconsistent")
    ev = b.ev
    cnt = {"n_series": len(ev)}
    const = [k for k, v in ev.items() if np.nanstd(v) < 1e-9]
    cnt["n_constant_series"] = len(const)
    cnt["constant_by_signal"] = {s: sum(1 for k in const if k.endswith("|" + s)) for s in sorted({k.split("|")[1] for k in const})}
    key = [k for k in ev if k.split("|")[1] in ("flow", "temp") and k.split("-")[0] in ("AHU", "VAV", "Zone")]
    bad = [k for k in key if np.nanstd(ev[k]) < 1e-6]
    if bad:
        prob.append(f"constant flow/temperature series: {bad[:6]}")
    if any(not np.isfinite(v).all() for v in ev.values()):
        prob.append("non-finite values in evidence")
    sp = t["setpoints"]
    zt = np.stack([ev[z + "|temp"] for z in b.ids("Zone")])
    lo, hi = sp["heat_setback"] - 2.0, sp["cool_setback"] + 2.0
    out_frac = float(((zt < lo) | (zt > hi)).mean())
    cnt.update(zone_temp_p01=round(float(np.percentile(zt, 1)), 1), zone_temp_p50=round(float(np.percentile(zt, 50)), 1),
               zone_temp_p99=round(float(np.percentile(zt, 99)), 1), frac_zone_hours_outside_setback_band_pm2K=round(out_frac, 4))
    if out_frac > 0.02 or not (14 <= np.percentile(zt, 50) <= 28):
        prob.append(f"sizing/thermal sanity failed: {out_frac:.3f} of zone-hours outside setback band +-2K, median {np.median(zt):.1f}")
    # sizing: AHU peak flow vs sum of its VAV peak flows (undersizing by ventilation-only sizing gave ~1/40)
    ratios = []
    for a in b.ids("AHU"):
        vavs = [m for o, m in b.slot_edges["ahu_vav"] if o == a]
        ratios.append(float(ev[a + "|flow"].max() / sum(ev[v + "|flow"].max() for v in vavs)))
    cnt["ahu_peak_over_sum_vav_peak"] = [round(r, 2) for r in ratios]
    if min(ratios) < 0.3 or max(ratios) > 1.05:
        prob.append(f"AHU peak flow / sum VAV peaks {ratios} outside [0.3, 1.05]")
    # dynamic range of a few flow / rate channels
    cnt["ahu_flow_max_kgs"] = [round(float(ev[a + "|flow"].max()), 2) for a in b.ids("AHU")]
    cnt["ahu_flow_min_over_max"] = [round(float(ev[a + "|flow"].min() / ev[a + "|flow"].max()), 2) for a in b.ids("AHU")]
    cnt["oat_range"] = [round(float(ev["ENV|oat"].min()), 1), round(float(ev["ENV|oat"].max()), 1)]
    cnt["annual_heating_coil_share"] = round(float(sum(ev[c + "|rate"].sum() for c in b.ids("Coil") if b.nodes[c]["brick_type"] == "Heating_Coil")
                                                  / (sum(ev[c + "|rate"].sum() for c in b.ids("Coil")) + 1e-9)), 3)
    err = (out / "eplusout.err").read_text(errors="replace")
    cnt["eplus_warnings"] = sum(1 for l in err.splitlines() if "** Warning" in l)
    cnt["group_mode"], cnt["sat_pattern"] = t["group_mode"], t["sat_pattern"]
    return {"ok": not prob, "problems": prob, "stats": cnt}


def main(ids):
    spec_hash = hashlib.sha256(SPEC.read_bytes()).hexdigest()
    man = json.loads(MAN.read_text())
    assert man["spec_sha256"] == spec_hash, "spec changed after its hash was recorded"
    reg = build_ext.register_from_spec(SPEC)
    specs = {t["id"]: t for t in json.loads(SPEC.read_text())["topologies"]}
    gen = man.setdefault("generation", {})
    for tid in (ids or reg):
        t0 = time.time()
        rec = {"attempts": gen.get(tid, {}).get("attempts", 0) + 1, "started_utc": time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime())}
        try:
            run = physical.simulate_topology(tid, BASE)
            rec["energyplus"] = run
            res = check(tid, specs[tid], BASE / tid)
            rec["checks"] = res
            rec["status"] = "ok" if res["ok"] else "failed_generation_checks"
        except Exception as e:  # recorded, never silent
            rec["status"], rec["error"] = "error", repr(e)[:2000]
        rec["wall_seconds"] = round(time.time() - t0, 1)
        d = BASE / tid
        if d.exists():
            for f in d.iterdir():
                if f.name not in KEEP:
                    f.unlink() if f.is_file() else __import__("shutil").rmtree(f)
        gen[tid] = rec
        print(tid, rec["status"], rec.get("checks", {}).get("problems"), rec.get("error"), f'{rec["wall_seconds"]}s', flush=True)
        MAN.write_text(json.dumps(man, indent=1))


if __name__ == "__main__":
    main(sys.argv[1:])
