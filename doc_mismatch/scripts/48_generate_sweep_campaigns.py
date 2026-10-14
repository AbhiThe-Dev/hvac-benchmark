"""Generate the fresh campaigns of PREREGISTRATION_DR.md Addendum 15 (needs `openstudio`: run from physics_pipeline/.venv).

  physics_pipeline/.venv/bin/python doc_mismatch/scripts/48_generate_sweep_campaigns.py

Code seeds 4, 5, 6 (never scored; Addendum 13 used 1-3, its design-shaping check used 0) for the 7 train-role topologies with VAVs, both seasons, over the grid
half-swing a in {0.5, 1.0, 1.5} K x override dropout p in {0, 0.25}: 252 EnergyPlus runs. Generation-level status only -- no identification statistic is computed here.
"""
import json
import sys
import time
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "src"))
from docmismatch import build_ext  # noqa: E402
from docmismatch.interventions import run_campaign  # noqa: E402

RES = ROOT.parent / "results" / "docmismatch"
OUT = RES / "perturbation" / "campaigns15"
BUILDINGS = ["sys07_vav_reheat", "vav_2ahu_2loops", "vav_3ahu_2loops", "dev_E", "dev_F", "dev_G", "dev_H"]
SEASONS = {"july": 7, "january": 1}
SEEDS = (4, 5, 6)
AMPLITUDES = (0.5, 1.0, 1.5)
DROPOUTS = (0.0, 0.25)


def cfg_name(a: float, p: float) -> str:
    return f"a{a}_p{p}"


def main():
    build_ext.register_from_spec(RES / "active" / "sim_spec.json", only=[b for b in BUILDINGS if b.startswith("dev_")])
    log, t0 = [], time.time()
    for a in AMPLITUDES:
        for p in DROPOUTS:
            for season, month in SEASONS.items():
                for s in SEEDS:
                    for tid in BUILDINGS:
                        out_root = OUT / cfg_name(a, p) / season / f"seed{s}"
                        if (out_root / tid / "evidence.npz").exists():
                            continue
                        try:
                            r = run_campaign(tid, out_root, month=month, seed=s, half_span=a, dropout=p)
                            log.append(dict(cfg=cfg_name(a, p), season=season, seed=s, tid=tid, ok=True, seconds=r["seconds"], n_hours=r["n_hours"]))
                        except Exception as e:  # noqa: BLE001 -- generation failures are reported, never silently dropped
                            log.append(dict(cfg=cfg_name(a, p), season=season, seed=s, tid=tid, ok=False, error=f"{type(e).__name__}: {e}"[:300]))
                        print(f"{cfg_name(a, p):10s} {season:8s} seed{s} {tid:18s} {log[-1].get('ok')} {time.time() - t0:.0f}s", flush=True)
    OUT.mkdir(parents=True, exist_ok=True)
    (OUT / "generation_log.json").write_text(json.dumps(log, indent=1))
    bad = [l for l in log if not l["ok"]]
    print(f"\n{len(log) - len(bad)} ok, {len(bad)} failed")
    for l in bad:
        print("  FAILED", l)


main()
