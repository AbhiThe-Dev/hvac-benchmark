"""Selective verification of rooms on a faulty handler (EXPLORATORY; FOLD_PROTOCOL.md was written and hashed before any variant ran).

  .venv/bin/python doc_mismatch/live_demo_bldg11/study_folding.py [n_visits]

The routine `tool_ticket_memo2` is replicated step for step (gate G1 proves the replica exact); a variant adds one verification step for a room whose session ends with low static leading and that has taken no
box-level static reading of its own. Results: results/docmismatch/fold_study/.
"""
import hashlib
import json
import sys
from pathlib import Path

import numpy as np

HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE))
import simulate as S  # noqa: E402
import visit as V  # noqa: E402
import world as Wd  # noqa: E402
from docmismatch.troubleshoot.v1 import data as D  # noqa: E402
from docmismatch.troubleshoot.v1.engine import Obs, Question  # noqa: E402
from docmismatch.troubleshoot.v2.joint import MAX_CHECKS_PER_COMPLAINT, JointModel  # noqa: E402
from docmismatch.troubleshoot.v2.policies import PriorSession, run_policy  # noqa: E402

OUT = HERE.parent.parent / "results" / "docmismatch" / "fold_study"
LS = ("low_static",)
WORLDS = {"W0": (0, 0.0), "W1": (1, 0.25)}
STORED = {"W0": (0.7483333333333333, 193.71), "W1": (0.5466666666666666, 204.81)}      # mix_study/summary.json, bldg11|W*|mix: accuracy, minutes per visit
VARIANTS = {                                                                        # name: (verify, how, budget per faulty handler per visit)
    "base": (False, None, None),
    "V1 verify all, box static": (True, "box", None),
    "V2 verify all, best per minute": (True, "best", None),
    "V3 verify two, box static": (True, "box", 2),
    "V4 verify two, best per minute": (True, "best", 2),
}


def run_ticket_v(cases, oracle, js, variant):
    verify, how, budget = VARIANTS[variant]
    model = JointModel(cases, js)
    at, memo, low_static_seen = None, {}, set()
    guess, concluded, per_room_min, own_static, checks, forced, skipped, counts = [], [], [], [], 0, 0, 0, {}
    for i, case in enumerate(cases):
        sess = PriorSession(case, (model.causes[i], model.marg0[i]))
        sess.at = at
        for (a, name), word in memo.items():
            if a == case.ahu:
                sess.log.append(Obs(name, case.doc, word, 0.0))
        if not verify and case.ahu in low_static_seen:                      # the routine's group-informing copy; verifying variants do not copy a box reading into other rooms
            sess.log.append(Obs("static_at_box", case.doc, "abnormal", 0.0))
        own = 0

        def ask(ck, target):
            return oracle.ask_ahu(case.ahu, ck) if ck.subject == "ahu" else oracle.ask_room(i, ck, target)

        def after(ck, word):
            if ck.subject == "ahu":
                memo[(case.ahu, ck.name)] = word
            elif ck.name == "static_at_box" and word == "abnormal":
                low_static_seen.add(case.ahu)

        def loop(own):
            while own < MAX_CHECKS_PER_COMPLAINT:
                step = sess.next_step()
                if step is None:
                    break
                if isinstance(step, Question):
                    raise RuntimeError(f"the tool asked {step.key!r}")
                ck = step.check
                word = ask(ck, step.target)
                assert word in ck.words                                         # gate G3
                sess.report(word)
                own += 1
                after(ck, word)
            return own

        own = loop(own)
        if verify:
            top = sess.status()["ranked"][0][0]
            if top == LS and not any(o.check == "static_at_box" for o in sess.log) and (budget is None or counts.get(case.ahu, 0) < budget):
                counts[case.ahu] = counts.get(case.ahu, 0) + 1
                ck, target = None, case.doc
                if how == "box":
                    c = sess._check("static_at_box")
                    if D.availability(c, sess.view(), sess._eq(c)).state != "unavailable":
                        ck = c
                else:
                    rec = sess.shortlist(2)["next"]
                    if rec is not None:
                        ck, target = rec.check, rec.target
                if ck is None or any((o.check, o.target) == (ck.name, target) for o in sess.log):
                    skipped += 1                                                # gate G3: counted, not hidden
                else:
                    word = ask(ck, target)
                    assert word in ck.words
                    sess.report(word, check=ck.name, target=target)
                    own += 1
                    forced += 1
                    after(ck, word)
                    own = loop(own)
        st = sess.status()
        guess.append(st["ranked"][0][0])
        concluded.append(bool(st["concluded"]))
        per_room_min.append(float(sess.elapsed))
        own_static.append(any(o.check == "static_at_box" and o.minutes > 0 for o in sess.log))     # the room took its own box-level static reading (added after the first run; changes no result)
        checks += own
        at = sess.at
    return dict(minutes=float(sum(per_room_min)), per_room_min=per_room_min, own_static=own_static, n_checks=checks, guess=guess, concluded=concluded, forced=forced, skipped=skipped)


def boot(d, B=2000, seed=11):
    rng = np.random.default_rng(seed); n = len(d)
    return np.percentile([d[rng.integers(n, size=n)].mean() for _ in range(B)], [2.5, 97.5])


def main():
    n = int(sys.argv[1]) if len(sys.argv) > 1 else 100
    S._init()
    cases = S._CASES
    sc = Wd.load_scenario()
    js = V.joint_settings(sc, "mixed")
    rec = {}                                                                         # (world, variant) -> per-room arrays
    g1_ok, g1_msg = True, []
    for wname, (wi, a) in WORLDS.items():
        for v in range(n):
            visit = S.draw_visit(v, cases)
            cl = [cases[r] for r in visit["rooms"]]
            truth = [tuple(c) for c in visit["causes"]]
            seg = []
            for r, t in zip(visit["rooms"], truth):
                s = S.segment(visit, t)
                seg.append("shared" if s == "shared" else "local, no shared cause" if s == "local_in_local" else ("local, faulty handler" if cases[r].ahu == S.SHARED_AHU else "local, healthy handler (shared visit)"))
            for var in VARIANTS:
                orc = S.NoisyOracle(visit, cl, wi, a)
                r = run_ticket_v(cl, orc, js, var)
                d = rec.setdefault((wname, var), dict(ok=[], conc=[], mins=[], seg=[], visit=[], vmin=[], vchk=[], forced=0, skipped=0))
                d["ok"] += [tuple(g) == t for g, t in zip(r["guess"], truth)]
                d["conc"] += r["concluded"]; d["mins"] += r["per_room_min"]; d["seg"] += seg; d["visit"] += [v] * len(cl)
                d["vmin"].append(r["minutes"]); d["vchk"].append(r["n_checks"]); d["forced"] += r["forced"]; d["skipped"] += r["skipped"]
                if var == "base":                                                    # G1: the replica equals the routine, exactly
                    ref = run_policy("tool_ticket_memo2", cl, S.NoisyOracle(visit, cl, wi, a), [S.CTX] * len(cl), js)
                    same = [tuple(x) for x in ref["guess"]] == [tuple(x) for x in r["guess"]] and abs(ref["minutes"] - r["minutes"]) < 1e-9 and [bool(c) for c in ref["concluded"]] == r["concluded"]
                    if not same:
                        g1_ok = False; g1_msg.append(f"{wname} v{v}")
    for k, d in rec.items():
        for key in ("ok", "conc", "mins", "visit", "vmin", "vchk"):
            d[key] = np.array(d[key], float if key not in ("visit",) else int)
        d["seg"] = np.array(d["seg"]); d["ok"] = d["ok"].astype(bool); d["conc"] = d["conc"].astype(bool)
    g2 = {}
    for w in WORLDS:
        b = rec[w, "base"]
        g2[w] = (abs(b["ok"].mean() - STORED[w][0]) <= 0.002, b["ok"].mean(), b["vmin"].mean())
    gates_pass = g1_ok and all(x[0] for x in g2.values()) and n == 100
    L = ["# Selective verification of rooms on a faulty handler (exploratory; FOLD_PROTOCOL.md hashed before any variant ran)", "",
         f"{n} visits x 6 rooms, the demo's default setting (mixed-severity joint model, `min_rate` 0.02, T3-noattr), noisy answers; W0 = checks as the tool assumes, W1 = every rate 25% toward 0.5.", "",
         "## Gates", "",
         f"- G1 the replica of the routine equals `run_policy('tool_ticket_memo2')` on every visit in both worlds: **{'PASS' if g1_ok else 'FAIL ' + ', '.join(g1_msg[:5])}**",
         *[f"- G2 base accuracy equals the stored mixture-study accuracy, {w}: **{'PASS' if g2[w][0] else 'FAIL'}** (replica {100*g2[w][1]:.2f}% / {g2[w][2]:.1f} min per visit, stored {100*STORED[w][0]:.2f}% / {STORED[w][1]:.1f})" for w in WORLDS],
         f"- G3 every answer in the check's vocabulary (asserted); verification checks that could not be taken (skipped, counted): {sum(rec[w, v]['skipped'] for w in WORLDS for v in VARIANTS)}", ""]
    if not gates_pass and n == 100:
        L += ["**REGISTERED OUTCOME: NO RESULT (a gate failed). Numbers below are shown for debugging only.**", ""]
    verdicts, res = {}, {}
    SEGS = ["shared", "local, faulty handler", "local, healthy handler (shared visit)", "local, no shared cause"]
    for w in WORLDS:
        b = rec[w, "base"]
        L += [f"## {w}", "", "| variant | accuracy (all rooms) | shared rooms | own fault, faulty handler | own fault, healthy handler | own fault, no shared cause | wrong and confident | minutes / visit | checks / visit | verification checks |", "|---|---|---|---|---|---|---|---|---|---|"]
        for var in VARIANTS:
            d = rec[w, var]
            wc = float(((~d["ok"]) & d["conc"]).mean())
            segacc = [100 * d["ok"][d["seg"] == s].mean() for s in SEGS]
            L.append(f"| {var} | {100*d['ok'].mean():.1f}% | " + " | ".join(f"{x:.1f}%" for x in segacc) + f" | {100*wc:.1f}% | {d['vmin'].mean():.0f} | {d['vchk'].mean():.1f} | {d['forced']} |")
        L += ["", "Against base, paired over visits (accuracy gain = percentage points of per-room accuracy; points per minute = that gain over the added minutes per visit):", "",
              "| variant | accuracy gain (95% CI) | added minutes / visit (95% CI) | points per added minute | share of added minutes on rooms base already had right | on shared-cause rooms | wrong-and-confident change, points (95% CI; interval added after the table was seen) | verdict at W0 |", "|---|---|---|---|---|---|---|---|"]
        vb = np.array([b["ok"][b["visit"] == v].mean() for v in range(n)])
        for var in list(VARIANTS)[1:]:
            d = rec[w, var]
            vo = np.array([d["ok"][d["visit"] == v].mean() for v in range(n)])
            gain = 100 * (vo - vb); ci = boot(gain)
            dm = d["vmin"] - b["vmin"]; cim = boot(dm)
            added = d["mins"] - b["mins"]
            tot = max(added.sum(), 1e-9)
            on_right = added[b["ok"]].sum() / tot; on_shared = added[b["seg"] == "shared"].sum() / tot
            ppm = gain.mean() / dm.mean() if dm.mean() > 0 else float("nan")
            dwc = 100 * (float(((~d["ok"]) & d["conc"]).mean()) - float(((~b["ok"]) & b["conc"]).mean()))
            wcb = np.array([((~b["ok"]) & b["conc"])[b["visit"] == v].mean() for v in range(n)])               # CI added after the first table was seen (post hoc)
            wcd = np.array([((~d["ok"]) & d["conc"])[d["visit"] == v].mean() for v in range(n)])
            dwc_ci = boot(100 * (wcd - wcb))
            worth = ci[0] > 0 and gain.mean() >= 3 and dm.mean() <= 0.15 * b["vmin"].mean() and ppm >= 0.3 and dwc <= 1
            trade = ci[0] > 0 and gain.mean() >= 3 and not worth
            verdict = "WORTH IT" if worth else "TRADE" if trade else "NEITHER"
            res[w, var] = dict(gain=float(gain.mean()), ci=ci.tolist(), added=float(dm.mean()), ppm=float(ppm), on_right=float(on_right), on_shared=float(on_shared), dwc=dwc, dwc_ci=dwc_ci.tolist(), verdict=verdict, acc=float(100 * d["ok"].mean()))
            L.append(f"| {var} | {gain.mean():+.1f} ({ci[0]:+.1f}, {ci[1]:+.1f}) | {dm.mean():+.0f} ({cim[0]:+.0f}, {cim[1]:+.0f}) | {ppm:.2f} | {100*on_right:.0f}% | {100*on_shared:.0f}% | {dwc:+.1f} ({dwc_ci[0]:+.1f}, {dwc_ci[1]:+.1f}) | {verdict if w == 'W0' else '(not part of the verdict)'} |")
        L.append("")
    # predictions
    r1, r2, r3, r4 = (res["W0", k] for k in list(VARIANTS)[1:])
    fh = 100 * rec["W0", list(VARIANTS)[1]]["ok"][rec["W0", list(VARIANTS)[1]]["seg"] == "local, faulty handler"].mean()
    P = [("P1 (V1: +4 to +8 points, faulty-handler own-fault rooms to at least 50%, +25 to +45 minutes / visit)", 4 <= r1["gain"] <= 8 and fh >= 50 and 25 <= r1["added"] <= 45, f"gain {r1['gain']:+.1f}, segment {fh:.1f}%, minutes {r1['added']:+.0f}"),
         ("P2 (at least 60% of V1's added minutes land on rooms base already had right)", r1["on_right"] >= 0.60, f"{100*r1['on_right']:.0f}%"),
         ("P3 (V2 gains less than V1 and its points per added minute are below 0.3)", r2["gain"] < r1["gain"] and r2["ppm"] < 0.3, f"V2 gain {r2['gain']:+.1f} vs V1 {r1['gain']:+.1f}; points per minute {r2['ppm']:.2f}"),
         ("P4 (V3 gets 30-70% of V1's gain for 30-70% of its added minutes)", 0.3 <= r3["gain"] / r1["gain"] <= 0.7 and 0.3 <= r3["added"] / r1["added"] <= 0.7, f"gain fraction {r3['gain']/r1['gain']:.2f}, minutes fraction {r3['added']/r1['added']:.2f}"),
         ("P5 (no variant is WORTH IT)", all(res['W0', k]['verdict'] != 'WORTH IT' for k in list(VARIANTS)[1:]), ", ".join(f"{k.split(' ')[0]} {res['W0', k]['verdict']}" for k in list(VARIANTS)[1:])),
         ("P6 (no variant lifts W0 overall accuracy above 85%)", all(res['W0', k]['acc'] <= 85 for k in list(VARIANTS)[1:]), f"best {max(res['W0', k]['acc'] for k in list(VARIANTS)[1:]):.1f}%"),
         ("P7 (at W1 every variant's gain is smaller than at W0)", all(res['W1', k]['gain'] < res['W0', k]['gain'] for k in list(VARIANTS)[1:]), ", ".join(f"{k.split(' ')[0]} {res['W1', k]['gain']:+.1f} vs {res['W0', k]['gain']:+.1f}" for k in list(VARIANTS)[1:]))]
    L += ["## Predictions (written before the first variant ran)", ""] + [f"- {p}: **{'HELD' if ok else 'FAILED'}** ({det})" for p, ok, det in P]
    L += ["", "Convention that flatters verification: the oracle answers a room-level check from the room's OWN first-order cause, so a room with its own fault on a low-static handler reads 'normal' at its box; in a real building it would also read low static. The gains above are upper bounds.", ""]
    OUT.mkdir(parents=True, exist_ok=True)
    (OUT / "report.md").write_text("\n".join(L))
    (OUT / "summary.json").write_text(json.dumps(dict(n=n, gates=dict(g1=g1_ok, g2={w: bool(x[0]) for w, x in g2.items()}), results={f"{w}|{k}": v for (w, k), v in res.items()}, protocol_sha256=hashlib.sha256((HERE / "FOLD_PROTOCOL.md").read_bytes()).hexdigest()), indent=1))
    print("\n".join(L))


if __name__ == "__main__":
    main()
