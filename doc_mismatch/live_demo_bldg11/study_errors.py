"""Where do the errors come from, and what would a new measurement have to do? (EXPLORATORY; ERRORS_NOTES.md was written and hashed before any analysis.)

  .venv/bin/python doc_mismatch/live_demo_bldg11/study_errors.py

Part 1 sorts every wrong room of the registered 100 visits (mixed setting) into gap / not taken / misled / mixed / box-identity and clusters them by the symptoms the tool saw.
Part 2 adds one hypothetical, pair-specific check at a time and measures what it would be worth. Results: results/docmismatch/error_study/.
"""
import contextlib
import hashlib
import json
import sys
from collections import Counter, defaultdict
from pathlib import Path

import numpy as np

HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE))
import simulate as S  # noqa: E402
import study_folding as F  # noqa: E402
import study_trend as T  # noqa: E402
import visit as V  # noqa: E402
import world as Wd  # noqa: E402
from docmismatch.troubleshoot.v1 import catalogue as K  # noqa: E402
from docmismatch.troubleshoot.v2.policies import PriorSession  # noqa: E402

OUT = HERE.parent.parent / "results" / "docmismatch" / "error_study"
STORED = {"W0": (0.7483333333333333, 193.71), "W1": (0.5466666666666666, 204.81)}
WORLDS = {"W0": (0, 0.0), "W1": (1, 0.25)}
JMIN = 0.25
RF = S.M.RATE_FLOOR
SEGS = ["own fault, no shared cause", "own fault, faulty handler", "own fault, healthy handler", "shared"]
BUCKETS = ["gap", "not taken", "misled", "mixed", "box-identity"]
BYNAME = {c.name: c for c in V.CHECKS}


def jeff(pT, pG):
    return float((pT - pG) * np.log(pT * (1 - pG) / (pG * (1 - pT))))


def rate(ck, cause, doc):
    return float(np.clip(K.p_pos(ck, cause, doc, doc), RF, 1.0 - RF))


@contextlib.contextmanager
def capture():
    made = []
    old = F.PriorSession
    F.PriorSession = lambda case, prior=None: (made.append(PriorSession(case, prior)) or made[-1])
    try:
        yield made
    finally:
        F.PriorSession = old


def collect(cases, js, wi, a, checks=None, n=100):
    rows = []
    for v in range(n):
        visit = S.draw_visit(v, cases); cl = [cases[r] for r in visit["rooms"]]
        orc = S.NoisyOracle(visit, cl, wi, a) if checks is None else T.ArmOracle(visit, cl, wi, a, checks)
        with capture() as made:
            r = F.run_ticket_v(cl, orc, js, "base")
        for i, (room, t, g, sess) in enumerate(zip(visit["rooms"], visit["causes"], r["guess"], made)):
            sg = S.segment(visit, tuple(t))
            seg = "shared" if sg == "shared" else "own fault, no shared cause" if sg == "local_in_local" else ("own fault, faulty handler" if cases[room].ahu == S.SHARED_AHU else "own fault, healthy handler")
            obs = [(o.check, o.outcome, o.minutes) for o in sess.log]
            rows.append(dict(v=v, i=i, seg=seg, T=tuple(t), G=tuple(g), ok=tuple(t) == tuple(g), conc=bool(r["concluded"][i]), obs=obs, doc=cl[i].doc, minutes=r["per_room_min"][i]))
    return rows


def bucket(row):
    T_, G_ = row["T"], row["G"]
    if T_[0] in ("wrong", "unlisted") or G_[0] in ("wrong", "unlisted"):
        return "box-identity", None
    try:
        disc = []
        for ck in V.CHECKS:
            pT, pG = rate(ck, T_, row["doc"]), rate(ck, G_, row["doc"])
            j = jeff(pT, pG)
            if j >= JMIN:
                disc.append((j, ck, pT, pG))
    except Exception:  # a lump or tag the v0 truth rule does not know
        return "box-identity", None
    if not disc:
        return "gap", None
    taken = {name: out for name, out, _ in row["obs"]}
    dt = [(j, ck, pT, pG) for j, ck, pT, pG in disc if taken.get(ck.name) in ck.words]
    if not dt:
        return "not taken", max(disc, key=lambda x: x[0])
    lrs = []
    for j, ck, pT, pG in dt:
        abn = taken[ck.name] == ck.words[0]
        lrs.append((pT if abn else 1 - pT) / (pG if abn else 1 - pG))
    return ("misled" if all(x < 1 for x in lrs) else "mixed"), max(dt, key=lambda x: x[0])


def signature(row):
    return frozenset(n for n, out, _ in row["obs"] if n in BYNAME and out == BYNAME[n].words[0])


def hyp(name, A, do_min, place, access):
    return K.CheckV1(name=name, family="control system" if place == "bas" else "at the box", text=f"Hypothetical check specific to {A}", kind="reading", place=place, subject="box",
                     access_min=access, do_min=do_min, wait_min=0.0, detects={A: 0.80}, bg=0.08)


def boot(d, B=2000, seed=19):
    rng = np.random.default_rng(seed); n = len(d)
    return np.percentile([d[rng.integers(n, size=n)].mean() for _ in range(B)], [2.5, 97.5])


def per_visit(rows, key, n=100):
    arr = np.zeros(n); cnt = np.zeros(n)
    for r in rows:
        arr[r["v"]] += key(r); cnt[r["v"]] += 1
    return arr / np.maximum(cnt, 1)


def main():
    S._init(); cases = S._CASES; js = V.joint_settings(Wd.load_scenario(), "mixed")
    base = {w: collect(cases, js, wi, a) for w, (wi, a) in WORLDS.items()}
    g1 = {w: abs(np.mean([r["ok"] for r in base[w]]) - STORED[w][0]) <= 0.002 for w in WORLDS}
    wrong0 = [r for r in base["W0"] if not r["ok"]]
    segwrong = Counter(r["seg"] for r in wrong0)
    g2 = (segwrong["own fault, no shared cause"], segwrong["own fault, faulty handler"], segwrong["own fault, healthy handler"], segwrong["shared"]) == (75, 51, 10, 15)
    L = ["# Where the errors come from, and what a new measurement would have to do (exploratory; ERRORS_NOTES.md hashed before any analysis)", "",
         "The registered 100 visits x 6 rooms, the demo's mixed setting. A check is DISCRIMINATING for a pair of causes when its Jeffreys divergence is at least 0.25; each wrong room goes into one bucket (protocol).", "", "## Gates", ""]
    res_b = {}
    bk = {}
    for w in WORLDS:
        wr = [r for r in base[w] if not r["ok"]]
        b = [(r,) + bucket(r) for r in wr]
        bk[w] = b
    g3 = all(sum(1 for x in bk[w] if x[1] in BUCKETS) == len([r for r in base[w] if not r["ok"]]) for w in WORLDS)
    L += [*[f"- G1 base equals the stored accuracy, {w}: **{'PASS' if g1[w] else 'FAIL'}** ({100*np.mean([r['ok'] for r in base[w]]):.2f}%)" for w in WORLDS],
          f"- G2 wrong rooms by segment at W0 = the earlier decomposition (75 / 51 / 10 / 15): **{'PASS' if g2 else 'FAIL'}** ({segwrong['own fault, no shared cause']} / {segwrong['own fault, faulty handler']} / {segwrong['own fault, healthy handler']} / {segwrong['shared']})",
          f"- G3 buckets exhaustive and exclusive: **{'PASS' if g3 else 'FAIL'}**", ""]
    gates = all(g1.values()) and g2 and g3
    if not gates:
        L += ["**REGISTERED OUTCOME: NO RESULT (a gate failed).**", ""]
    # ---------------- part 1
    for w in WORLDS:
        L += [f"## Part 1, {w}: every wrong room, by bucket", "", "| segment | wrong rooms | gap | not taken | misled | mixed | box-identity |", "|---|---|---|---|---|---|---|"]
        tot = Counter()
        for sg in SEGS:
            c = Counter(x[1] for x in bk[w] if x[0]["seg"] == sg); n = sum(c.values()); tot.update(c)
            L.append(f"| {sg} | {n} | " + " | ".join(f"{c[bn]} ({100*c[bn]/max(n,1):.0f}%)" for bn in BUCKETS) + " |")
        n = sum(tot.values())
        L += [f"| **all** | **{n}** | " + " | ".join(f"**{tot[bn]}** ({100*tot[bn]/n:.0f}%)" for bn in BUCKETS) + " |", "",
              "Ceiling if every error of one bucket were turned right (accuracy points added; base " + f"{100*np.mean([r['ok'] for r in base[w]]):.1f}%): " + "; ".join(f"{bn} +{100*tot[bn]/600:.1f}" for bn in BUCKETS), ""]
        res_b[w] = dict(tot=dict(tot), by_seg={sg: dict(Counter(x[1] for x in bk[w] if x[0]["seg"] == sg)) for sg in SEGS})
    # symptom clusters at W0, ordinary errors
    ordn = [x for x in bk["W0"] if x[0]["seg"] == SEGS[0]]
    allrows_ord = [r for r in base["W0"] if r["seg"] == SEGS[0]]
    sig_all = Counter(signature(r) for r in allrows_ord)
    by_sig = defaultdict(list)
    for x in ordn:
        by_sig[signature(x[0])].append(x)
    top = sorted(by_sig.items(), key=lambda kv: -len(kv[1]))
    L += ["## Part 1: symptom clusters of the ordinary errors (own fault, no shared cause), W0", "",
          "A room's signature is the set of checks that came back abnormal / yes. Top signatures by number of errors:", "", "| signature (abnormal checks) | rooms with it | wrong | error rate | most common truth to guess confusions | buckets |", "|---|---|---|---|---|---|"]
    for sg, xs in top[:10]:
        pairs = Counter((x[0]["T"][0], x[0]["G"][0]) for x in xs).most_common(3)
        L.append(f"| {', '.join(sorted(sg)) or '(none abnormal)'} | {sig_all[sg]} | {len(xs)} | {100*len(xs)/sig_all[sg]:.0f}% | " + "; ".join(f"{a} to {b} ({c})" for (a, b), c in pairs) + " | " + ", ".join(f"{k} {v}" for k, v in Counter(x[1] for x in xs).most_common()) + " |")
    top5 = sum(len(xs) for _, xs in top[:5])
    L += ["", f"The five most common signatures hold {top5} of the {len(ordn)} ordinary errors ({100*top5/len(ordn):.0f}%); {len(by_sig)} different signatures in all.", ""]
    # most-confused pairs (ordinary rooms) and the best discriminating check
    pair_err = Counter()
    truth_cnt = defaultdict(Counter)
    for x in ordn:
        T_, G_ = x[0]["T"][0], x[0]["G"][0]
        if T_ in ("wrong", "unlisted", "low_static") or G_ in ("wrong", "unlisted", "low_static"):
            continue
        k = frozenset((T_, G_)); pair_err[k] += 1; truth_cnt[k][T_] += 1
    L += ["## Part 1: the most confused ordinary pairs, and the best check the catalogue has for each (W0)", "", "| pair | errors | best discriminating check (J, hit rates on the two causes, indicative minutes) | where the errors sit |", "|---|---|---|---|"]
    top_pairs = pair_err.most_common(5)
    doc0 = base["W0"][0]["doc"]
    for k, n_err in pair_err.most_common(8):
        a, b = sorted(k)
        best = max(((jeff(rate(ck, (a,), doc0), rate(ck, (b,), doc0)), ck, rate(ck, (a,), doc0), rate(ck, (b,), doc0)) for ck in V.CHECKS), key=lambda x: x[0])
        bs = Counter(x[1] for x in ordn if frozenset((x[0]["T"][0], x[0]["G"][0])) == k)
        L.append(f"| {a} / {b} | {n_err} | {best[1].name} (J {best[0]:.2f}; {best[2]:.2f} vs {best[3]:.2f}; {best[1].access_min + best[1].do_min + best[1].wait_min:.0f} min) | " + ", ".join(f"{bk_} {c}" for bk_, c in bs.most_common()) + " |")
    L.append("")
    # ---------------- part 2
    arms_cfg = {"3 min, control system": ("bas", 0.0, 3.0), "10 min, at the box": ("box", 6.0, 4.0)}
    part2 = {}
    for cname, (place, acc, do) in arms_cfg.items():
        singles = []
        for k, _ in top_pairs:
            A = truth_cnt[k].most_common(1)[0][0]
            singles.append((k, A))
        for w, (wi, a) in WORLDS.items():
            ref = base[w]
            vref = per_visit(ref, lambda r: r["ok"]); mref = np.array([sum(r["minutes"] for r in ref if r["v"] == v) for v in range(100)])
            for label, As in [(f"pair {i + 1}: {'/'.join(sorted(k))} (check specific to {A})", [A]) for i, (k, A) in enumerate(singles)] + [("all five together", [A for _, A in singles])]:
                extra = tuple(hyp(f"hyp_{A}_{j}", A, do, place, acc) for j, A in enumerate(As))
                checks = V.CHECKS + extra
                cs = T.make_cases(checks)
                rows = collect(cs, js, wi, a, checks)
                vo = per_visit(rows, lambda r: r["ok"]); mo = np.array([sum(r["minutes"] for r in rows if r["v"] == v) for v in range(100)])
                gain = 100 * (vo - vref); ci = boot(gain); dm = mo - mref
                wc = float(np.mean([(not r["ok"]) and r["conc"] for r in rows])); wc0 = float(np.mean([(not r["ok"]) and r["conc"] for r in ref]))
                part2[cname, w, label] = dict(acc=100 * float(np.mean([r["ok"] for r in rows])), gain=float(gain.mean()), ci=ci.tolist(), dmin=float(dm.mean()), dwc=100 * (wc - wc0))
    for cname in arms_cfg:
        for w in WORLDS:
            L += [f"## Part 2, {w}: one hypothetical check specific to the cause on the left of each pair (fires 0.80 on it, 0.08 on everything else), {cname}", "", "| arm | accuracy | gain vs base (95% CI) | added minutes / visit | wrong-and-confident change |", "|---|---|---|---|---|"]
            for (cn, ww, lab), r in part2.items():
                if cn == cname and ww == w:
                    L.append(f"| {lab} | {r['acc']:.1f}% | {r['gain']:+.1f} ({r['ci'][0]:+.1f}, {r['ci'][1]:+.1f}) | {r['dmin']:+.0f} | {r['dwc']:+.1f} |")
            L.append("")
    # ---------------- predictions
    t0 = res_b["W0"]["by_seg"][SEGS[0]]; n_ord_reg = sum(v for k, v in t0.items() if k != "box-identity")
    t0all = res_b["W0"]["tot"]; fold = res_b["W0"]["by_seg"][SEGS[1]]
    a3 = "3 min, control system"
    first_lab = [lab for (cn, ww, lab) in part2 if cn == a3 and ww == "W0"][0]
    all_lab = "all five together"
    P = [("E1 (ordinary errors that are not box-identity: 'not taken' the largest bucket and at least 40%, 'gap' at most 20%)", t0.get("not taken", 0) / n_ord_reg >= 0.40 and t0.get("not taken", 0) == max(v for k, v in t0.items() if k != "box-identity") and t0.get("gap", 0) / n_ord_reg <= 0.20,
          f"not taken {100*t0.get('not taken', 0)/n_ord_reg:.0f}%, gap {100*t0.get('gap', 0)/n_ord_reg:.0f}%, misled {100*t0.get('misled', 0)/n_ord_reg:.0f}%, mixed {100*t0.get('mixed', 0)/n_ord_reg:.0f}%"),
         ("E2 (gap errors at most 25% of all wrong rooms)", t0all.get("gap", 0) / sum(t0all.values()) <= 0.25, f"{100*t0all.get('gap', 0)/sum(t0all.values()):.0f}%"),
         ("E3 (the five most common signatures hold at most 50% of the ordinary errors)", top5 / len(ordn) <= 0.50, f"{100*top5/len(ordn):.0f}%"),
         ("E4 (one hypothetical check for the most-confused pair raises W0 accuracy by at most 1.5 points; 3-minute version)", part2[a3, "W0", first_lab]["gain"] <= 1.5, f"{part2[a3, 'W0', first_lab]['gain']:+.1f}"),
         ("E5 (all five together raise W0 accuracy by 2 to 6 points and stay below 85%; 3-minute version)", 2 <= part2[a3, "W0", all_lab]["gain"] <= 6 and part2[a3, "W0", all_lab]["acc"] < 85, f"{part2[a3, 'W0', all_lab]['gain']:+.1f}, {part2[a3, 'W0', all_lab]['acc']:.1f}%"),
         ("E6 (the ceiling for fixing every gap error is at most 4 points)", 100 * t0all.get("gap", 0) / 600 <= 4, f"+{100*t0all.get('gap', 0)/600:.1f}"),
         ("E7 (folded rooms mostly 'not taken', at least 60%)", fold.get("not taken", 0) / max(sum(fold.values()), 1) >= 0.60, f"{100*fold.get('not taken', 0)/max(sum(fold.values()), 1):.0f}%")]
    L += ["## Predictions (written before any analysis)", ""] + [f"- {p}: **{'HELD' if ok else 'FAILED'}** ({d})" for p, ok, d in P] + [""]
    OUT.mkdir(parents=True, exist_ok=True)
    (OUT / "report.md").write_text("\n".join(L))
    (OUT / "summary.json").write_text(json.dumps(dict(gates=dict(g1={w: bool(x) for w, x in g1.items()}, g2=bool(g2), g3=bool(g3)), part1=res_b, part2={f"{c}|{w}|{lab}": v for (c, w, lab), v in part2.items()}, protocol_sha256=hashlib.sha256((HERE / "ERRORS_NOTES.md").read_bytes()).hexdigest()), indent=1, default=str))
    print("\n".join(L))


if __name__ == "__main__":
    main()
