"""Real-channel-validity check (PREREGISTRATION_DR.md Addendum 5a): for every real slot's channels, does the
zero-shot sim-fitted likelihood (baseline arm's existing training buildings, never any real row) actually
discriminate true from false pairs on real DEV data (never SEALED)?
  .venv/bin/python doc_mismatch/scripts/34_real_channel_validity.py
"""
import copy
import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "src"))
from docmismatch.active import measurement as M  # noqa: E402
from docmismatch.active.readiness import SimKind  # noqa: E402
from docmismatch.active.real_data import load_real_dev  # noqa: E402
from docmismatch.active.real_pool import REAL_SLOTS  # noqa: E402
from docmismatch.dr.pools import DR_DIR, load_pool  # noqa: E402
from docmismatch.dr.verifier_eval import EXISTING, cases_for, make_cfg  # noqa: E402

OUT = DR_DIR / "measurement"


def real_pool_sim_units():
    """Real DEV pool with context converted from the loader's native degF to the simulation's degC (same fix as
    Addendum 1's `real_vav_zone_episodes`, generalized to every slot -- the model was fit on sim-unit context)."""
    pool = load_real_dev()
    p2 = copy.copy(pool)
    ctx = pool.ctx.copy()
    ctx[:, 0] = (ctx[:, 0] - 32.0) * 5.0 / 9.0
    ctx[:, 1] = ctx[:, 1] * 5.0 / 9.0
    p2.ctx = ctx
    return p2


def main():
    OUT.mkdir(parents=True, exist_ok=True)
    cfg = make_cfg(("active",))
    cfg["sim_reps"] = [0]
    train = EXISTING
    train_pools = {t: {0: load_pool(t, 0, "legacy")} for t in train}
    sim_kind = SimKind(cfg, topos=train, pools=train_pools, cases=cases_for(train))
    tr_all = sim_kind.train(train)
    pool = real_pool_sim_units()

    report = {}
    md = ["# Real-channel-validity check (Addendum 5a)", "",
          "Zero-shot sim-fitted likelihood (baseline arm's existing training buildings, zero real rows), scored "
          "against every real DEV reading (32 days, never SEALED). Day-cluster bootstrap (B=1000) lower-bound "
          "(q=0.10) class-balanced accuracy vs. chance (0.5); refuses (not validated) below min_clusters=6 or "
          "min_rows=30, exactly like `reliability.ReliabilityLayer`.", "",
          "| slot | channel | validated | point bal-acc | lb bal-acc | n days | n rows | reason |",
          "|---|---|---|---|---|---|---|---|"]
    for slot in REAL_SLOTS:
        mod, beta = sim_kind.fit_slot(tr_all, slot, None)
        if not mod:
            md.append(f"| {slot} | - | - | - | - | - | - | no sim model for this slot |")
            continue
        val = M.real_channel_validity(pool, slot, mod)
        report[slot] = {str(k): vars(v) for k, v in val.items()}
        for k in sorted(val):
            v = val[k]
            md.append(f"| {slot} | {k} | {v.validated} | {v.point_bal_acc:.3f} | {v.lb_bal_acc:.3f} | {v.n_days} | {v.n_rows} | {v.reason} |")
    (OUT / "real_channel_validity.json").write_text(json.dumps(report, indent=2, default=str))
    (OUT / "real_channel_validity.md").write_text("\n".join(md))
    print("\n".join(md))


main()
