"""Dev-only ablation of the reliability layer on cached fold records (real: leave-one-season-out, variant sel_slice). Counts variants; every row is a
nested outer result (layer fitted on inner records only). Usage: 22_layer_ablation.py real|sim [variant]"""
import sys, glob, pickle, copy, json, os
from pathlib import Path
ROOT = Path(__file__).resolve().parents[1]; sys.path.insert(0, str(ROOT / "src"))
import numpy as np
from docmismatch.active import readiness as R, evalkit as K
from docmismatch.active.reliability import FEATURES

kind = sys.argv[1]; variant = sys.argv[2] if len(sys.argv) > 2 else "sel_slice"
cfg0 = copy.deepcopy(R.DEFAULT_CFG); cfg0["variant"] = variant
K_ = R.make_kind(kind, cfg0)
us = K_.units(); primary = "day" if kind == "real" else cfg0["sim_primary"]
folds = {}
for o in us:
    key = R._cache_key(K_, cfg0, dict(train=[str(u) for u in [x for x in us if x != o]], test=str(o), sealed=False))
    f = R.CACHE / f"fold_{kind}_{key}.pkl"
    if not f.exists():
        raise SystemExit(f"missing cache {f}; run 20_final_eval.py --data {kind}-dev-nested/sim-dev-loto --variant {variant} first")
    folds[o] = pickle.loads(f.read_bytes())
core = ("logit_abs", "agree", "agree_slices", "n_owners_info", "gap12", "oat_excess", "nn_dist", "say_correct", "slot_power")
variants = {
    "all_lb0.90": {}, "all_lb0.85": dict(lb_floor=0.85), "all_nominal0.93_lb0.85": dict(nominal=0.93, lb_floor=0.85), "core_lb0.90": dict(features=core),
    "margin_only": dict(features=("logit_abs", "say_correct", "slot_power")), "all_perslot_off": dict(per_slot=False), "all_q0.2": dict(q=0.2, lb_floor=0.85),
    "all_lam30": dict(lam=30.0),
}
out = {}
for name, kw in variants.items():
    cfg = copy.deepcopy(cfg0); cfg["layer"].update(kw)
    rows = []
    for o, fold in folds.items():
        rows += R.apply_layers(fold, cfg, layers=("new",))
    ev = K.evaluate(rows, primary, nboot=1000)["new"]
    a = ev["C2"]["all"]["all"]
    out[name] = dict(coverage=a["coverage"], acc=a["acc"], status=a["status"], C3=ev["C3"].get("status"), C4=ev["C4"]["status"], c4_viol=len(ev["C4"]["violations"]),
                     n_cells_notpass=ev["C4"]["n_not_supported"], c1={b: v.get("status") for b, v in ev["C1"].items()})
    print(name, K.fmt(a["coverage"]), K.fmt(a["acc"]), a["status"], "C3", out[name]["C3"], "C4", out[name]["C4"], out[name]["c4_viol"], flush=True)
(R.ACT / "final" / f"layer_ablation_{kind}_{variant}.json").write_text(json.dumps(K.to_jsonable(out), indent=1))
