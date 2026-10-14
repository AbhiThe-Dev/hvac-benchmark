"""What does BAS access + a point map buy when attributes / design values are NOT documented? (PREREGISTRATION_DR.md Exploratory note E2.) The named tiers of Addendum 27 are
cumulative -- T3 always includes T2's attributes -- but a reported real-world profile has T1 and T3 commonly available and T2 rarely so. Adds one arm, "T3-noattr" (T1's items +
bas_access + point_map, no attributes), at the next free RNG channel; the four arms it is compared against (T1, T2, T2+access, T3) are verified byte-identical to a fresh run of
Addendum 27's own, untouched `run_cell`. Simulation only: same synthetic building and draws as Addendum 27; every minute and probability a placeholder.
  .venv/bin/python doc_mismatch/scripts/83_troubleshoot_tiers_ext.py                   # the run (about a minute)
  .venv/bin/python doc_mismatch/scripts/83_troubleshoot_tiers_ext.py --smoke           # plumbing check on 2 cells x 20 episodes; numbers meaningless
  .venv/bin/python doc_mismatch/scripts/83_troubleshoot_tiers_ext.py --from-pickle     # regenerate the report from the stored raw results
"""
import argparse
import csv
import pickle
import sys
import time
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "src"))
from docmismatch.troubleshoot.v1 import study_tiers as T  # noqa: E402
from docmismatch.troubleshoot.v1 import study_tiers_ext as E  # noqa: E402

REPO = ROOT.parent
OUT = REPO / "results/docmismatch/troubleshoot_tiers_ext"


def pct(x):
    return "n/a" if x is None or x != x else f"{100 * x:.0f}%"


def fmt(s, key, kind="min"):
    if s.get("n", 0) == 0:
        return "n/a"
    return {"min": f"{s[key]:.0f}", "pct": pct(s[key]), "num": f"{s[key]:.1f}"}[kind]


def cell_text(c):
    return f"{c.rel} / {c.mix} / {c.cover}"


def report(analyses: list[dict], verified: tuple[bool, str], n: int, wall: float) -> str:
    L = ["# What BAS access + a point map buy without documented attributes (Exploratory note E2)", "",
         "Same synthetic building, draws and seed as Addendum 27. Adds one arm, **T3-noattr** = T1's items (equipment list, drawings' claims) plus `bas_access` and `point_map`, but "
         "**no** `attributes` (no reheat type, K-factor, design airflow, inlet size, static setpoint on file). Motivation: the named tiers are cumulative (T3 = T2 + access + map, so "
         "T3 always has attributes too), but a reported real-world documentation profile has T1 and T3 commonly available and T2 rarely so -- a combination no existing tier covers. "
         "Simulation only; every minute and probability a placeholder; nothing here is evidence about real buildings or technicians.", "",
         "## Non-perturbation check", "", f"{'PASS' if verified[0] else 'FAIL'}: {verified[1]}", "",
         f"## The primary cell ({cell_text(T.Cell(**T.PRIMARY))}): hardware / configuration-cause episodes (n = {T.cell_of(analyses, **T.PRIMARY)['n_hw']})", "",
         "| arm | minutes | accuracy | right branch | wrong-and-confident | checks | questions asked |", "|---|---|---|---|---|---|---|"]
    pc = T.cell_of(analyses, **T.PRIMARY)
    for arm in E.CHAIN:
        s = pc["hw"][arm]
        L.append(f"| {arm} | {fmt(s, 'minutes')} | {fmt(s, 'accuracy', 'pct')} | {fmt(s, 'group_accuracy', 'pct')} | {fmt(s, 'wrong_confident', 'pct')} | {fmt(s, 'checks', 'num')} | "
                 f"{fmt(s, 'questions', 'num')} |")
    L += ["", "## The comparisons this note is about, over the 12 cells", "",
          "Labels are Addendum 21's frozen ones (IMPROVES / WORSE / TRADE / NEITHER at 5% minutes and 0.02 accuracy, paired 95% intervals); TRADE's bracket shows faster-but-less-accurate "
          "(F/L) or slower-but-more-accurate (S/M). SAFETY REG is the share of cells where wrong-and-confident is at least 0.02 higher with the interval clear of 0.", "",
          "| comparison | IMPROVES | WORSE | TRADE (F/L, S/M) | NEITHER | SAFETY REG | primary cell: d minutes | d accuracy | d wrong-and-confident |", "|---|---|---|---|---|---|---|---|---|"]
    for pair in E.PAIRS_EXT:
        sh = T.step_shares(analyses, pair)
        c = pc["cmp"][f"{pair[0]}|{pair[1]}"]
        L.append(f"| {E.PAIR_TEXT_EXT[pair]} | {pct(sh['IMPROVES'])} | {pct(sh['WORSE'])} | {pct(sh['TRADE'])} ({pct(sh['FASTER_LESS'])}, {pct(sh['SLOWER_MORE'])}) | {pct(sh['NEITHER'])} | "
                 f"{pct(sh['SAFETY_REGRESSION'])} | {c['d_min']:+.1f} ({100 * c['r_min']:+.0f}%) | {c['d_acc']:+.3f} | {c['d_wc']:+.3f} |")
    L += ["", "## Every cell: minutes / accuracy / wrong-and-confident (hardware / configuration-cause episodes)", "",
          "| reliability / mix / coverage | " + " | ".join(E.CHAIN) + " |", "|---|" + "---|" * len(E.CHAIN)]
    for a in analyses:
        L.append(f"| {cell_text(a['cell'])} | " + " | ".join(f"{fmt(a['hw'][arm], 'minutes')} / {fmt(a['hw'][arm], 'accuracy', 'pct')} / {fmt(a['hw'][arm], 'wrong_confident', 'pct')}" for arm in E.CHAIN) + " |")
    L += ["", f"Run time {wall:.0f} s."]
    return "\n".join(L)


def write_csv(path, analyses):
    with open(path, "w", newline="") as f:
        w = csv.writer(f)
        w.writerow(["cell", "rel", "mix", "cover", "arm", "n", "minutes", "accuracy", "group_accuracy", "wrong_confident", "checks", "questions"])
        for a in analyses:
            c = a["cell"]
            for arm in E.CHAIN:
                s = a["hw"][arm]
                w.writerow([a["idx"], c.rel, c.mix, c.cover, arm, s.get("n", 0)] + [f"{s[k]:.4f}" if s.get("n", 0) else "" for k in
                           ("minutes", "accuracy", "group_accuracy", "wrong_confident", "checks", "questions")])


def main(argv=None):
    ap = argparse.ArgumentParser()
    ap.add_argument("--smoke", action="store_true")
    ap.add_argument("--out", type=Path, default=OUT)
    ap.add_argument("--from-pickle", action="store_true")
    a = ap.parse_args(argv)
    a.out.mkdir(parents=True, exist_ok=True)
    t0 = time.time()
    if a.from_pickle:
        results = pickle.loads((a.out / "tiers_ext_raw.pkl").read_bytes())
    else:
        cells = list(enumerate(T.all_cells()))
        n = T.N_EPISODES
        if a.smoke:
            cells, n = cells[:2], 20
        results = E.compute_cells_ext(cells, n)
        (a.out / "tiers_ext_raw.pkl").write_bytes(pickle.dumps(results))
    n = results[0]["n"]
    analyses = [E.analyze_cell_ext(r) for r in results]
    verified = E.verify_non_perturbation(30 if not a.smoke else 6)
    text = report(analyses, verified, n, time.time() - t0)
    (a.out / "tiers_ext_report.md").write_text(text + "\n")
    (a.out / "tiers_ext_analysis.pkl").write_bytes(pickle.dumps(analyses))
    write_csv(a.out / "tiers_ext_cells.csv", analyses)
    print(f"wrote {a.out / 'tiers_ext_report.md'}; non-perturbation: {'PASS' if verified[0] else 'FAIL'}")
    if not a.smoke and not verified[0]:
        sys.exit(1)


if __name__ == "__main__":
    main()
