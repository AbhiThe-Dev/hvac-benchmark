"""Does the reliability layer remove the overconfidence? (PREREGISTRATION_DR.md Addendum 14, Part B)
The frozen nested path (readiness.run_fold_records + apply_layers) over the 8 EXISTING train-role topologies, leave-one-topology-out, legacy telemetry, rep 0, one visit window,
`active` policy, frozen variant fit AND run options. Layers: `none` (plain rule), `new` (reliability layer; primary), `legacy` (abstain.py; descriptive).
Nothing is tuned. Never touches SEALED data, T1-T6 suites or real data.
  .venv/bin/python doc_mismatch/scripts/47_layer_check.py [procs]
Run scripts/44 first (Part A): its corrected `base` rows are used for the code-path consistency check.
"""
import pickle
import sys
import time
from collections import Counter
from pathlib import Path

import numpy as np

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "src"))
from docmismatch import evidence as EV  # noqa: E402
from docmismatch.active import readiness as RD  # noqa: E402
from docmismatch.active.readiness import SimKind  # noqa: E402
from docmismatch.dr import layer_eval as L  # noqa: E402
from docmismatch.dr.pools import DR_DIR, build_pool  # noqa: E402
from docmismatch.dr.verifier_eval import EXISTING, cases_for, make_cfg  # noqa: E402

OUT = DR_DIR / "caution"
TARGETS = ["branch_coil", "coil_ahu", "ahu_vav"]
CONTROL = "loop_branch"
LAYERS = ["none", "new", "legacy"]


def build_pools() -> dict:
    old = EV.MASK_CHANNELS
    EV.MASK_CHANNELS = True
    try:
        return {t: {0: build_pool(t, 0, None)} for t in EXISTING}       # exactly the pools scripts/44 uses for its masked variants
    finally:
        EV.MASK_CHANNELS = old


def compute(procs, t0):
    cfg = make_cfg(("active",))
    cfg["sim_reps"] = [0]
    kind = SimKind(cfg, topos=EXISTING, pools=build_pools(), cases=cases_for(EXISTING))
    rows, info = [], {}
    for h in EXISTING:
        fold = RD.run_fold_records(kind, cfg, [u for u in EXISTING if u != h], test_unit=h, procs=procs, use_cache=False)
        rows += RD.apply_layers(fold, cfg, layers=tuple(LAYERS))
        info[h] = dict(beta=fold["beta"], n_outer=len(fold["outer"]), n_inner=len(fold["inner"]))
        print(f"  held-out {h:18s} outer={len(fold['outer']):3d} inner={len(fold['inner']):4d} {time.time() - t0:.0f}s", flush=True)
    return dict(rows=rows, info=info, layer_cfg=cfg["layer"])


def consistency(rows):
    """Code-path check (Addendum 14, Deviation 1): every Part A wrong-documentation episode, and every right-documentation episode present in both, must match `none` exactly.
    (The two harnesses draw different samples of matched-correct episodes because build_sim_episodes consumes one RNG stream in topology order.)"""
    f = OUT / "caution.pkl"
    if not f.exists():
        raise SystemExit("run scripts/44 (Part A) first: its corrected caution.pkl is the reference for the consistency check")
    ref = pickle.loads(f.read_bytes())["rows"]
    none = {r["ep"]: r for r in rows if r["layer"] == "none"}
    bad, n_wrong, n_right_shared, n_right_ref = [], 0, 0, 0
    for slot in ["branch_coil", "loop_branch", "coil_ahu", "ahu_vav"]:
        for r in ref[(slot, "base")]:
            q = none.get(r["ep"])
            if r["wrong"]:
                n_wrong += 1
            else:
                n_right_ref += 1
                if q is None:
                    continue
                n_right_shared += 1
            if q is None or (q["state"] != "FLAGGED") != r["crossed"] or q["n"] != r["n"] or abs(q["p_stop"] - r["p_final"]) > 1e-9 \
                    or (r["crossed"] and (q["say_correct"] == (not q["wrong"])) != r["correct"]):
                bad.append(r["ep"])
    return dict(n_wrong=n_wrong, n_right_shared=n_right_shared, n_right_ref=n_right_ref, bad=bad)


def fmt_ci(ci):
    return "n/a" if not np.all(np.isfinite(ci)) else f"[{ci[0]:.2f}, {ci[1]:.2f}]"


def table(rows, slot, plain):
    md = ["| layer | n eps | answered | coverage | acc \\| answered [95% CI] | wrong & confident | false alarms (right docs) | missed faults (wrong docs) | retained vs plain |",
          "|---|---|---|---|---|---|---|---|---|"]
    out = {}
    for lay in LAYERS:
        sub = [r for r in rows if r["layer"] == lay and (slot is None or r["slot"] == slot)]
        s = L.summarize(sub)
        out[lay] = (sub, s)
        ret = "" if lay == "none" else f"{L.retained(sub, plain):.2f}"
        md.append(f"| {lay} | {s['n']} | {s['n_answered']}/{s['n']} | {s['coverage']:.2f} | {s['acc_answered']:.3f} {fmt_ci(L.boot_acc_answered(sub))} | {s['wrong_confident']:.1%} | "
                  f"{s['false_alarm']:.1%} ({s['n_right_docs']}) | {s['missed_fault']:.1%} ({s['n_wrong_docs']}) | {ret} |")
    return md, out


def main():
    procs = int(sys.argv[1]) if len(sys.argv) > 1 else 8
    OUT.mkdir(parents=True, exist_ok=True)
    t0 = time.time()
    f = OUT / "layer_check.pkl"
    if f.exists():
        res = pickle.loads(f.read_bytes())
        print("loaded from cache", flush=True)
    else:
        res = compute(procs, t0)
        f.write_bytes(pickle.dumps(res))
        print(f"done {time.time() - t0:.0f}s", flush=True)
    rows = res["rows"]

    ck = consistency(rows)
    if ck["bad"]:
        raise SystemExit(f"CONSISTENCY CHECK FAILED: `none` differs from Part A's corrected base on {len(ck['bad'])} compared episodes (first: {ck['bad'][:3]}); nothing is read")
    ck_line = (f"Consistency check (Deviation 1): `none` equals Part A's corrected `base` exactly on all {ck['n_wrong']} wrong-documentation episodes and on the {ck['n_right_shared']} of "
               f"{ck['n_right_ref']} right-documentation episodes drawn identically by both harnesses (the rest are different draws of matched-correct negatives).")
    print(ck_line, flush=True)

    md = ["# Does the reliability layer remove the overconfidence? (Addendum 14, Part B)", "",
          "Frozen nested path over the 8 `EXISTING` train-role topologies (leave-one-topology-out), legacy telemetry, one visit window, `active` policy, tau 0.95, frozen `sel_slice` "
          "fit + run options and layer configuration. `none` = plain 0.95 rule; `new` = calibrated reliability layer (primary); `legacy` = `abstain.py` (descriptive). "
          "Accuracy and coverage are class-balanced over is_wrong / is_right episodes; a verdict is right when CONFIRMED on a right document or REFUTED on a wrong one; "
          "'retained' = answered-and-correct episodes / the plain rule's. CI = cluster bootstrap (1000, seed 0). Simulation only, small samples.", "",
          ck_line, ""]

    md += ["## All slots pooled", ""]
    m, _ = table(rows, None, [r for r in rows if r["layer"] == "none"])
    md += m + [""]

    verdicts = {}
    for slot in TARGETS + [CONTROL]:
        plain = [r for r in rows if r["layer"] == "none" and r["slot"] == slot]
        if not plain:
            continue
        m, out = table(rows, slot, plain)
        clusters = len({r["cluster"] for r in plain})
        md += [f"## {slot}{'  (control)' if slot == CONTROL else ''}  ({len(plain)} episodes, {clusters} clusters)", ""] + m + [""]
        newrows = out["new"][0]
        reasons = Counter(r["reason"] for r in newrows if r["state"] == "FLAGGED")
        md += ["`new` abstentions: " + ("; ".join(f"{k} x{v}" for k, v in reasons.most_common()) if reasons else "none"), ""]
        if slot in TARGETS:
            verdicts[slot] = L.slot_verdict(plain, newrows)

    others = sorted({r["slot"] for r in rows} - set(TARGETS) - {CONTROL})
    if others:
        md += ["## Other slots (descriptive only; not part of the frozen verdict)", "", "| slot | n eps | none: answered / acc | new: answered / acc / wrong&confident | legacy: answered / acc |", "|---|---|---|---|---|"]
        for slot in others:
            cells = []
            for lay in ("none", "new", "legacy"):
                s = L.summarize([r for r in rows if r["layer"] == lay and r["slot"] == slot])
                cells.append((s, f"{s['n_answered']}/{s['n']} / {s['acc_answered']:.2f}" + (f" / {s['wrong_confident']:.0%}" if lay == "new" else "")))
            md.append(f"| {slot} | {cells[0][0]['n']} | {cells[0][1]} | {cells[1][1]} | {cells[2][1]} |")
        md.append("")

    md += ["## Frozen reading rules (Addendum 14, Part B)", "", "| slot | verdict (layer `new`) |", "|---|---|"]
    md += [f"| {s} | {v} |" for s, v in verdicts.items()]
    md += ["", f"**Overall: {L.overall(list(verdicts.values()))}.**"]
    ctrl = [r for r in rows if r["layer"] == "new" and r["slot"] == CONTROL]
    cs = L.summarize(ctrl)
    if cs["n_answered"] >= 10 and cs["acc_answered"] < 0.90:
        md.append(f"\nControl `{CONTROL}`: REGRESSION -- the layer answers {cs['n_answered']} episodes at accuracy {cs['acc_answered']:.2f}.")
    else:
        md.append(f"\nControl `{CONTROL}`: no regression (`new` answers {cs['n_answered']}/{cs['n']}, accuracy among answered {cs['acc_answered']:.2f}).")
    (OUT / "layer_check_report.md").write_text("\n".join(md))
    print("\n".join(md))


main()
