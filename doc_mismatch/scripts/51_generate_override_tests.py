"""Generate the technician-style single-box override runs of PREREGISTRATION_DR.md Addendum 16 (needs `openstudio`: run from physics_pipeline/.venv).

  physics_pipeline/.venv/bin/python doc_mismatch/scripts/51_generate_override_tests.py

For the 7 train-role VAV topologies, both seasons, test-order seeds 1-3 (seed 0 was the design-shaping probe and is excluded), and the three commands `full_cool`, `close`, `flow_only`:
126 EnergyPlus runs, each holding one 2-hour override test of every box (one box per day). Generation-level status only -- no identification statistic is computed here.
"""
import json
import sys
import time
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "src"))
from docmismatch import build_ext  # noqa: E402
from docmismatch.interventions import run_override_tests  # noqa: E402

RES = ROOT.parent / "results" / "docmismatch"
OUT = RES / "perturbation" / "overrides"
BUILDINGS = ["sys07_vav_reheat", "vav_2ahu_2loops", "vav_3ahu_2loops", "dev_E", "dev_F", "dev_G", "dev_H"]
SEASONS = {"july": 7, "january": 1}
SEEDS = (1, 2, 3)
KINDS = ("full_cool", "close", "flow_only")


def main():
    build_ext.register_from_spec(RES / "active" / "sim_spec.json", only=[b for b in BUILDINGS if b.startswith("dev_")])
    log, t0 = [], time.time()
    for kind in KINDS:
        for season, month in SEASONS.items():
            for s in SEEDS:
                for tid in BUILDINGS:
                    out_root = OUT / kind / season / f"seed{s}"
                    if (out_root / tid / "evidence.npz").exists():
                        continue
                    try:
                        r = run_override_tests(tid, out_root, month=month, seed=s, kind=kind)
                        log.append(dict(kind=kind, season=season, seed=s, tid=tid, ok=True, seconds=r["seconds"], n_steps=r["n_steps"]))
                    except Exception as e:  # noqa: BLE001 -- generation failures are reported, never silently dropped
                        log.append(dict(kind=kind, season=season, seed=s, tid=tid, ok=False, error=f"{type(e).__name__}: {e}"[:300]))
                    print(f"{kind:9s} {season:8s} seed{s} {tid:18s} {log[-1].get('ok')} {time.time() - t0:.0f}s", flush=True)
    OUT.mkdir(parents=True, exist_ok=True)
    (OUT / "generation_log.json").write_text(json.dumps(log, indent=1))
    bad = [l for l in log if not l["ok"]]
    print(f"\n{len(log) - len(bad)} ok, {len(bad)} failed")
    for l in bad:
        print("  FAILED", l)


main()
