"""Generate the setpoint-perturbation campaigns of PREREGISTRATION_DR.md Addendum 13 (needs `openstudio`: run from physics_pipeline/.venv).

  physics_pipeline/.venv/bin/python doc_mismatch/scripts/45_run_perturbation_campaigns.py

For each train-role topology with VAVs, each season (July = cooling, January = heating): one undithered baseline campaign and dithered campaigns for code seeds 1-3
(seed 0 was the design-shaping feasibility check and is excluded from evaluation). Generation-level status only -- no identification statistic is computed here.
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
OUT = RES / "perturbation" / "campaigns"
BUILDINGS = ["sys07_vav_reheat", "vav_2ahu_2loops", "vav_3ahu_2loops", "dev_E", "dev_F", "dev_G", "dev_H"]
SEASONS = {"july": 7, "january": 1}
SEEDS = (1, 2, 3)


def main():
    build_ext.register_from_spec(RES / "active" / "sim_spec.json", only=[b for b in BUILDINGS if b.startswith("dev_")])
    log, t0 = [], time.time()
    for season, month in SEASONS.items():
        jobs = [("baseline", dict(dither=False, seed=0))] + [(f"seed{s}", dict(dither=True, seed=s)) for s in SEEDS]
        for label, kw in jobs:
            for tid in BUILDINGS:
                out_root = OUT / season / label
                if (out_root / tid / "evidence.npz").exists():
                    continue
                try:
                    r = run_campaign(tid, out_root, month=month, **kw)
                    log.append(dict(season=season, label=label, tid=tid, ok=True, seconds=r["seconds"], n_hours=r["n_hours"]))
                except Exception as e:  # noqa: BLE001 -- generation failures are reported, never silently dropped
                    log.append(dict(season=season, label=label, tid=tid, ok=False, error=f"{type(e).__name__}: {e}"[:300]))
                print(f"{season:8s} {label:9s} {tid:18s} {log[-1].get('ok')} {time.time() - t0:.0f}s", flush=True)
    (OUT / "generation_log.json").write_text(json.dumps(log, indent=1))
    bad = [l for l in log if not l["ok"]]
    print(f"\n{len(log) - len(bad)} ok, {len(bad)} failed")
    for l in bad:
        print("  FAILED", l)


main()
