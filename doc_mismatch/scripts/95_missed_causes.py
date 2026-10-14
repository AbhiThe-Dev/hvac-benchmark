"""Does generating candidate causes the fixed model may have missed increase its accuracy? (PREREGISTRATION_DR.md Addendum 44.) Simulation only.
  .venv/bin/python doc_mismatch/scripts/95_missed_causes.py PROPOSALS_DIR            # the registered run
  .venv/bin/python doc_mismatch/scripts/95_missed_causes.py PROPOSALS_DIR --smoke    # 60 complaints per cell, numbers meaningless
"""
import argparse
import pickle
import sys
from concurrent.futures import ProcessPoolExecutor
from pathlib import Path

import numpy as np

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "src"))
from docmismatch.troubleshoot.v2 import study_missed as X  # noqa: E402

OUT = ROOT.parent / "results/docmismatch/troubleshoot_missed"
PROPOSERS = (("p1", "proposer_1.json", "label_first"), ("p2", "proposer_2.json", "label_first"), ("p3", "proposer_3.json", "label_first"), ("p3f", "proposer_3.json", "frozen"))


def build_arms(pdir: Path, m: float) -> tuple[dict, list]:
    arms, audit = {"A": X.arm_models([])["A"]}, []
    for tag, fn, mode in PROPOSERS:
        prop = X.load_proposals(pdir / fn, mode)
        prop["proposer"] = tag
        mods = X.arm_models([prop])
        for (kind, who), a in ((k, v) for k, v in mods.items() if k != "A"):
            arms[f"{kind}:{who}"] = a
        audit += mods[("B_all", tag)]["rows"]
    arms["D"], arms["C"] = X.oracle_arm(m, False), X.oracle_arm(m, True)
    return arms, audit


def cell(args):
    pdir, m, tier, n = args
    arms, audit = build_arms(Path(pdir), m)
    res = X.run_cell(m, tier, arms, n=n)
    return m, tier, list(arms), res, audit


def arr(res, arm, key):
    return np.array([r[arm][key] for r in res], float)


def boot_diff(a, b, B=X.BOOT_B, seed=44):
    """95% paired-bootstrap interval of mean(b) - mean(a) over complaints."""
    d = np.asarray(b, float) - np.asarray(a, float)
    rng = np.random.default_rng(seed)
    idx = rng.integers(0, len(d), size=(B, len(d)))
    bs = d[idx].mean(axis=1)
    return d.mean(), np.percentile(bs, 2.5), np.percentile(bs, 97.5)


def pct(x):
    return f"{100 * x:5.1f}"


def summarize(res, arm):
    h = np.array([r["hidden"] for r in res])
    ok, okl, wc = arr(res, arm, "ok"), arr(res, arm, "ok_len"), arr(res, arm, "wc")
    return dict(overall=okl.mean(), inmodel=okl[~h].mean(), hid_strict=ok[h].mean() if h.any() else float("nan"), hid_len=okl[h].mean() if h.any() else float("nan"),
                wc=wc.mean(), minutes=arr(res, arm, "minutes").mean(), n=len(res), n_hidden=int(h.sum()))


def verdict(res, arm, ref="A"):
    h = np.array([r["hidden"] for r in res])
    okl_a, okl_b = arr(res, ref, "ok_len"), arr(res, arm, "ok_len")
    g, lo, hi = boot_diff(okl_a, okl_b)
    dloss = okl_b[~h].mean() - okl_a[~h].mean()
    dwc = arr(res, arm, "wc").mean() - arr(res, ref, "wc").mean()
    c1, c2, c3 = lo > X.BAR_GAIN, dloss >= -X.BAR_LOSS_IN, dwc <= X.BAR_LOSS_WC
    return dict(gain=g, lo=lo, hi=hi, in_delta=dloss, wc_delta=dwc, c1=c1, c2=c2, c3=c3, ok=c1 and c2 and c3)


def report(cells, audit) -> str:
    L = ["# Addendum 44: do generated candidate causes the fixed model may have missed increase accuracy?", "",
         "Simulation only; the world's four hidden causes are my construction (not sourced). Accuracy = `ok_len` (truth, or `other` on a hidden complaint). All numbers are percent / minutes per complaint.", ""]
    L += ["## What the proposers wrote and what matched (rubric: id+label first, detail as fallback)", "", "| proposer | candidate | matched hidden cause |", "|---|---|---|"]
    for r in audit:
        L.append(f"| {r['proposer']} | {r['label']} | {r['matched'] or '— (decoy)'} |")
    L.append("")
    for tier in X.TIERS:
        for m in X.MS:
            res = cells[(m, tier)]["res"]
            names = cells[(m, tier)]["arms"]
            L += [f"## {tier}, m = {m} ({summarize(res, 'A')['n_hidden']} hidden of {len(res)} complaints)", "",
                  "| arm | overall | in-model | hidden strict | hidden lenient | wrong&confident | minutes | gain vs A (95% CI) | in-model Δ | w&c Δ |", "|---|---|---|---|---|---|---|---|---|---|"]
            for a in names:
                s = summarize(res, a)
                if a == "A":
                    L.append(f"| A fixed | {pct(s['overall'])} | {pct(s['inmodel'])} | {pct(s['hid_strict'])} | {pct(s['hid_len'])} | {pct(s['wc'])} | {s['minutes']:.1f} | — | — | — |")
                else:
                    v = verdict(res, a)
                    L.append(f"| {a} | {pct(s['overall'])} | {pct(s['inmodel'])} | {pct(s['hid_strict'])} | {pct(s['hid_len'])} | {pct(s['wc'])} | {s['minutes']:.1f} | "
                             f"{100 * v['gain']:+.1f} ({100 * v['lo']:+.1f}, {100 * v['hi']:+.1f}) | {100 * v['in_delta']:+.1f} | {100 * v['wc_delta']:+.1f} |")
            L.append("")
    L += ["## Frozen decision rule (m = 0.10): B_all vs A", "", "| tier | proposer | gain CI>0 | in-model loss ≤2 | w&c rise ≤1 | all three |", "|---|---|---|---|---|---|"]
    yes = {}
    for tier in X.TIERS:
        res = cells[(X.PRIMARY_M, tier)]["res"]
        for tag, _, _ in PROPOSERS:
            v = verdict(res, f"B_all:{tag}")
            L.append(f"| {tier} | {tag} | {v['c1']} ({100 * v['gain']:+.1f}) | {v['c2']} ({100 * v['in_delta']:+.1f}) | {v['c3']} ({100 * v['wc_delta']:+.1f}) | **{v['ok']}** |")
            if tag != "p3f":
                yes[(tier, tag)] = v["ok"]
    n_yes = sum(yes.values())
    L += ["", f"**Verdict:** {'YES' if n_yes == len(yes) else 'NO' if n_yes == 0 else 'MIXED'} ({n_yes} of {len(yes)} proposer×tier cases pass all three conditions; p3f is a sensitivity row, not counted)."]
    return "\n".join(L)


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("pdir")
    ap.add_argument("--smoke", action="store_true")
    ap.add_argument("--from-pickle", action="store_true")
    a = ap.parse_args()
    OUT.mkdir(parents=True, exist_ok=True)
    pk = OUT / ("raw_smoke.pkl" if a.smoke else "raw.pkl")
    if a.from_pickle:
        cells, audit = pickle.loads(pk.read_bytes())
    else:
        n = 60 if a.smoke else X.N_EPISODES
        jobs = [(a.pdir, m, t, n) for m in X.MS for t in X.TIERS]
        with ProcessPoolExecutor(max_workers=4) as ex:
            out = list(ex.map(cell, jobs))
        cells = {(m, t): dict(arms=names, res=res) for m, t, names, res, _ in out}
        audit = out[0][4]
        pk.write_bytes(pickle.dumps((cells, audit)))
    txt = report(cells, audit)
    (OUT / ("report_smoke.md" if a.smoke else "report.md")).write_text(txt)
    print(txt)


if __name__ == "__main__":
    main()
