"""Fit the meta-learned shrinkage (PREREGISTRATION_DR.md Addendum 3): (trim, tau) via leave-one-building-out CV
across all 40 role=train DR buildings (regime+full+full_x3), against the baseline arm's population model.
  .venv/bin/python doc_mismatch/scripts/32_dr_sysid_meta_fit.py
"""
import json, sys, time
from pathlib import Path
ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "src"))
from docmismatch.dr import verifier_eval as V, sysid_meta as SM
from docmismatch.dr.pools import DR_DIR, load_pool
from docmismatch.dr.verifier_eval import EXISTING
from docmismatch.active.readiness import SimKind


def main():
    cfg = V.make_cfg(("active",))
    cfg["sim_reps"] = [0]
    ids = V.spec_ids()
    train_role = ids["regime"] + ids["full"] + ids["full_x3"]
    print(f"meta-training pool: {len(train_role)} role=train buildings", flush=True)

    baseline_pools = {t: {0: load_pool(t, 0, "legacy")} for t in EXISTING}
    sim_kind = SimKind(cfg, topos=EXISTING, pools=baseline_pools, cases=[])
    tr = sim_kind.train(EXISTING)
    slots = ["ahu_vav", "vav_zone", "loop_branch", "branch_coil", "loop_pump", "loop_source", "coil_ahu", "coil_vav", "ahu_sat", "vav_dat"]
    slot_models = {}
    for s in slots:
        mod, _ = sim_kind.fit_slot(tr, s, None)
        if mod:
            slot_models[s] = mod
    print("fitted reference model for slots:", sorted(slot_models), flush=True)

    buildings = {t: load_pool(t, 0, "spec") for t in train_role}
    t0 = time.time()
    examples = SM.build_examples(buildings, slot_models)
    print(f"{len(examples)} meta-training examples from {len({e['building'] for e in examples})} buildings, {time.time()-t0:.0f}s", flush=True)

    fit = SM.fit_shrinkage(examples)
    print(json.dumps({k: v for k, v in fit.items() if k not in ("cv_mse", "fold_best")}, indent=1))
    print("chosen (trim, tau) =", (fit["trim"], fit["tau"]), "vs hand-picked (0.10, 30):",
          "chosen_mse", round(fit["chosen_mse"], 5), "hand_picked_mse", round(fit["hand_picked_mse"], 5))
    print("fold-by-fold chosen (trim,tau), showing stability:", {k: v for k, v in list(fit["fold_best"].items())[:10]})
    (DR_DIR / "sysid").mkdir(parents=True, exist_ok=True)
    (DR_DIR / "sysid" / "meta_fit.json").write_text(json.dumps(
        dict(trim=fit["trim"], tau=fit["tau"], chosen_mse=fit["chosen_mse"], hand_picked_mse=fit["hand_picked_mse"],
             n_buildings=fit["n_buildings"], n_examples=fit["n_examples"],
             cv_mse={f"{k[0]}|{k[1]}": v for k, v in fit["cv_mse"].items()},
             fold_best={k: list(v) for k, v in fit["fold_best"].items()}), indent=1))


main()
