"""A fan-status confirm step, the lower-end gaps and a hedge for fan off, exactly as frozen in FANCONF_NOTES.md (read that first; this file implements it and changes nothing in it).

  .venv/bin/python doc_mismatch/live_demo_bldg11/study_fanconfirm.py                       # the registered run; refuses to run if FANCONF_NOTES.md changed since it was frozen
  .venv/bin/python doc_mismatch/live_demo_bldg11/study_fanconfirm.py --smoke --out DIR     # plumbing check (4 visits per family): prints timing and gates only, never accuracy

Outputs (results/docmismatch/fanconfirm_study/): report.md, summary.json. The Mortar Brick files must be in data_cache/ (not part of the repository); nothing here is committed or deployed.
"""
import argparse
import hashlib
import json
import sys
import time
from concurrent.futures import ProcessPoolExecutor
from pathlib import Path

import numpy as np

HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE))
import study_fanmix as FM  # noqa: E402
import study_folding as F  # noqa: E402
import study_mix as MX  # noqa: E402
from docmismatch.troubleshoot.v1 import data as D  # noqa: E402
from docmismatch.troubleshoot.v1.engine import Obs, Question  # noqa: E402
from docmismatch.troubleshoot.v2.joint import MAX_CHECKS_PER_COMPLAINT, JointModel, JointSettings  # noqa: E402
from docmismatch.troubleshoot.v2.policies import PriorSession  # noqa: E402

PROTOCOL, FROZEN = HERE / "FANCONF_NOTES.md", HERE / "FANCONF_NOTES.sha256"
OUT = HERE.parent.parent / "results" / "docmismatch" / "fanconfirm_study"
LS, FAN = FM.LS, FM.FAN
REAL, WORLDS, FAMILIES = FM.REAL, FM.WORLDS, FM.FAMILIES
RW = ((0.05, 0.4), (0.15, 0.2), (0.5, 0.2), (0.9, 0.2))
JS = {"TODAY": FM.ARMS["TODAY"], "FAN": FM.ARMS["FAN"], "FANC": FM.ARMS["FAN"], "RW": JointSettings(low_mix=RW), "LOW2": FM.ARMS["LOW2"]}
ARMS = tuple(JS)
CONFIRM_CHECK = "bas_ahu_fan"
STORED = {("TODAY", "A-LS"): {"bldg11": (84.4, 188), "bldg15": (75.2, 239), "bldg9": (81.1, 207)},
          ("FAN", "A-LS"): {"bldg11": (79.2, 195), "bldg15": (71.2, 227), "bldg9": (77.8, 209)},
          ("FAN", "A-FAN"): {"bldg11": (80.4, 178), "bldg15": (72.7, 214), "bldg9": (78.0, 199)},
          ("LOW2", "A-LS"): {"bldg11": (84.3, 186), "bldg15": (78.3, 214), "bldg9": (82.8, 197)}}


# ---------------------------------------------------------------------------------------------- the routine with a confirm step
def run_ticket_confirm(cases, oracle, js, confirm=True):
    """`study_folding.run_ticket_v(..., "base")` step for step, and, with `confirm`, one extra step per room: if the room's leading cause is fan off or low static and the handler's fan status has not been
    read in this visit (and the check is available), read it once, as the room's own check; later rooms on that handler get it through the routine's air-handler memo, as any air-handler reading."""
    model = JointModel(cases, js)
    at, memo, low_static_seen = None, {}, set()
    guess, concluded, per_room_min, own_static, checks = [], [], [], [], 0
    asks, violations, skipped = {}, 0, 0
    for i, case in enumerate(cases):
        sess = PriorSession(case, (model.causes[i], model.marg0[i]))
        sess.at = at
        for (a, name), word in memo.items():
            if a == case.ahu:
                sess.log.append(Obs(name, case.doc, word, 0.0))
        if case.ahu in low_static_seen:
            sess.log.append(Obs("static_at_box", case.doc, "abnormal", 0.0))
        own = 0

        def ask(ck, target, i=i, case=case):
            return oracle.ask_ahu(case.ahu, ck) if ck.subject == "ahu" else oracle.ask_room(i, ck, target)

        def after(ck, word, case=case):
            if ck.subject == "ahu":
                memo[(case.ahu, ck.name)] = word
            elif ck.name == "static_at_box" and word == "abnormal":
                low_static_seen.add(case.ahu)

        def loop(own, sess=sess, ask=ask, after=after):
            while own < MAX_CHECKS_PER_COMPLAINT:
                step = sess.next_step()
                if step is None:
                    break
                if isinstance(step, Question):
                    raise RuntimeError(f"the tool asked {step.key!r}")
                ck = step.check
                word = ask(ck, step.target)
                assert word in ck.words                                         # gate G4
                sess.report(word)
                own += 1
                after(ck, word)
            return own

        own = loop(own)
        if confirm and sess.status()["ranked"][0][0] in (FAN, LS) and (case.ahu, CONFIRM_CHECK) not in memo:
            if CONFIRM_CHECK not in {c.name for c in case.checks}:
                skipped += 1
            else:
                ck = sess._check(CONFIRM_CHECK)
                if D.availability(ck, sess.view(), sess._eq(ck)).state == "unavailable" or any((o.check, o.target) == (ck.name, case.doc) for o in sess.log):
                    skipped += 1
                else:
                    if (case.ahu, CONFIRM_CHECK) in memo:
                        violations += 1
                    asks[case.ahu] = asks.get(case.ahu, 0) + 1
                    word = ask(ck, case.doc)
                    assert word in ck.words
                    sess.report(word, check=ck.name, target=case.doc)
                    own += 1
                    after(ck, word)
                    own = loop(own)
        st = sess.status()
        guess.append(st["ranked"][0][0])
        concluded.append(bool(st["concluded"]))
        per_room_min.append(float(sess.elapsed))
        own_static.append(any(o.check == "static_at_box" and o.minutes > 0 for o in sess.log))
        checks += own
        at = sess.at
    return dict(minutes=float(sum(per_room_min)), per_room_min=per_room_min, own_static=own_static, n_checks=checks, guess=guess, concluded=concluded, asks=asks, violations=violations, skipped=skipped)


# ---------------------------------------------------------------------------------------------- the runs
def run_arm(arm, cl, orc):
    if arm == "FANC":
        return run_ticket_confirm(cl, orc, JS[arm], True)
    return F.run_ticket_v(cl, orc, JS[arm], "base")


def run_chunk(args):
    fam, bld, wi, lo, hi = args
    visits, cases, checks = FM.family_visits(fam, bld, range(lo, hi))
    a = list(WORLDS.values())[wi][1]
    out = []
    for visit in visits:
        cl = [cases[r] for r in visit["rooms"]]
        orc = MX.FamOracle(visit, cl, wi, a, checks)
        rec = {}
        for arm in ARMS:
            r = run_arm(arm, cl, orc)
            rec[arm] = dict(guess=[tuple(g) for g in r["guess"]], conc=[bool(c) for c in r["concluded"]], own=[bool(x) for x in r["own_static"]], minutes=float(r["minutes"]),
                            asks=max(r.get("asks", {}).values(), default=0), violations=r.get("violations", 0))
        out.append((visit, rec))
    return args, out


def collect(results):
    by = {}
    for args, out in results:
        by.setdefault((args[0], args[1], args[2]), []).append((args[3], out))
    res = {}
    for key, chunks in by.items():
        pairs = [p for _, out in sorted(chunks, key=lambda c: c[0]) for p in out]
        d = {"visits": [p[0] for p in pairs], "truth": [tuple(c) for p in pairs for c in p[0]["causes"]], "seg": np.array([s for p in pairs for s in p[0]["seg"]]),
             "visit": np.array([i for i, p in enumerate(pairs) for _ in p[0]["rooms"]])}
        for arm in ARMS:
            g = [tuple(x) for p in pairs for x in p[1][arm]["guess"]]
            d[arm] = dict(guess=g, ok=np.array([x == t for x, t in zip(g, d["truth"])]), conc=np.array([c for p in pairs for c in p[1][arm]["conc"]]),
                          own=np.array([c for p in pairs for c in p[1][arm]["own"]]), vmin=np.array([p[1][arm]["minutes"] for p in pairs]),
                          asks=max(p[1][arm]["asks"] for p in pairs), violations=sum(p[1][arm]["violations"] for p in pairs))
        res[key] = d
    return res


def stats(d, arm):
    x = d[arm]
    truth_fan = np.array([t == FAN for t in d["truth"]])
    g_ls = np.array([g == LS for g in x["guess"]])
    g_fan = np.array([g == FAN for g in x["guess"]])
    h_ls, h_fan = x["conc"] & g_ls & ~x["own"], x["conc"] & g_fan & ~x["own"]
    wrong_conc = (~x["ok"]) & x["conc"]
    sh = d["seg"] == "shared"
    return dict(acc=100 * x["ok"].mean(), shared=100 * x["ok"][sh].mean() if sh.any() else float("nan"), local=100 * x["ok"][~sh].mean() if (~sh).any() else float("nan"),
                minutes=float(x["vmin"].mean()), wc=100 * wrong_conc.mean(), wc_h=100 * (wrong_conc & ~h_ls).mean(), wc_h2=100 * (wrong_conc & ~h_ls & ~h_fan).mean(),
                hedged_right=int(((h_ls | h_fan) & x["ok"]).sum()), conc_right=int((x["conc"] & x["ok"]).sum()), false_fan=100 * (g_fan & ~truth_fan).mean(),
                fan_right=100 * g_fan[truth_fan].mean() if truth_fan.any() else float("nan"))


# ---------------------------------------------------------------------------------------------- gates
def gate_g2(n=10):
    bad, tot = 0, 0
    for fam, bld in (("A-LS", "bldg11"), ("A-FAN", "bldg15"), ("S2", "demo"), ("B", "bldg11")):
        visits, cases, checks = FM.family_visits(fam, bld, range(n))
        for visit in visits:
            cl = [cases[r] for r in visit["rooms"]]
            for wi, (wn, a) in enumerate(WORLDS.values()):
                orc = MX.FamOracle(visit, cl, wi, a, checks)
                for js in (JS["TODAY"], JS["FAN"]):
                    x, y = F.run_ticket_v(cl, orc, js, "base"), run_ticket_confirm(cl, orc, js, False)
                    tot += 1
                    bad += not ([tuple(u) for u in x["guess"]] == [tuple(u) for u in y["guess"]] and [bool(u) for u in x["concluded"]] == [bool(u) for u in y["concluded"]] and x["minutes"] == y["minutes"])
    return bad == 0, f"the confirm replica with the step switched off equals run_ticket_v on {tot} visit-world-setting runs: {'identical' if not bad else f'{bad} DIFFER'}"


# ---------------------------------------------------------------------------------------------- the report
def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--smoke", action="store_true")
    ap.add_argument("--out", default=None)
    args = ap.parse_args()
    smoke = args.smoke
    if not smoke and hashlib.sha256(PROTOCOL.read_bytes()).hexdigest() != FROZEN.read_text().split()[0]:
        sys.exit("FANCONF_NOTES.md changed since it was frozen: refusing to run")
    out = Path(args.out) if args.out else OUT
    t0 = time.time()
    g2, g3, g4 = gate_g2(2 if smoke else 10), FM.gate_g3(smoke), FM.gate_g4()
    print(f"gates before the run ({time.time() - t0:.0f}s): G2 {g2[0]} | G3 {g3[0]} | G4 {g4[0]}", flush=True)
    for g in (g2, g3, g4):
        print("   ", g[1], flush=True)
    step = 4 if smoke else FM.CHUNK
    tasks = []
    for fam, bld in FAMILIES:
        n = FM.n_visits(fam, smoke)
        for w, (wi, _) in WORLDS.items():
            for lo in range(0, n, step):
                tasks.append((fam, bld, wi, lo, min(lo + step, n)))
    results = []
    with ProcessPoolExecutor(max_workers=9) as ex:
        for i, r in enumerate(ex.map(run_chunk, tasks)):
            results.append(r)
            if (i + 1) % 20 == 0 or i + 1 == len(tasks):
                print(f"  {i + 1}/{len(tasks)} chunks, {time.time() - t0:.0f}s", flush=True)
    if smoke:
        print("smoke run: plumbing only, accuracy deliberately not printed")
        return
    wname = {v[0]: k for k, v in WORLDS.items()}
    res = collect([((a[0], a[1], wname[a[2]], a[3], a[4]), o) for a, o in results])
    g1, g1ok = [], True
    for (arm, fam), want in STORED.items():
        for b, (acc, mins) in want.items():
            st = stats(res[fam, b, "W0"], arm)
            ok = f"{st['acc']:.1f}" == f"{acc:.1f}" and f"{st['minutes']:.0f}" == f"{mins:.0f}"
            g1ok &= ok
            g1.append(f"- G1 {arm} on {fam} {b} W0 reproduces the FANMIX study: **{'PASS' if ok else 'FAIL'}** ({st['acc']:.1f}% / {st['minutes']:.0f} min; stored {acc}% / {mins})")
    g5 = max(res[k]["FANC"]["asks"] for k in res) <= 1 and sum(res[k]["FANC"]["violations"] for k in res) == 0
    gates_ok = g1ok and g2[0] and g3[0] and g4[0] and g5
    L = ["# A fan-status confirm step, the lower-end gaps and a hedge for fan off (exploratory; FANCONF_NOTES.md hashed before any run; demos, pilot and shipped defaults untouched)", "",
         "Simulated causes and answers (the visit families are mine); real Mortar layouts for A-LS, A-FAN and B, the first demo's synthetic 3 x 8 building for S1-S4. W0 = checks as the tool assumes, W1 = every rate 25% toward 0.5. "
         "TODAY = low-static mixture 5/15/50/90%; FAN = TODAY + fan-off mixture; FANC = FAN + one fan-status read before an upstream conclusion; LOW2 = 2/5/15/50/90%; RW = the 5/15/50/90% levels with weights 40/20/20/20 (LOW2's weights without the new level). "
         "'hedge' = low-static hedge of the pilot; 'hedge+fan' = also a fan-off conclusion with no own box-level static reading counts as not confident. Nothing committed or deployed.", "", "## Gates", "", *g1,
         f"- G2 {g2[1]}: **{'PASS' if g2[0] else 'FAIL'}**", f"- G3 composition: **{'PASS' if g3[0] else 'FAIL'}** ({g3[1]})", f"- G4 {g4[1]}: **{'PASS' if g4[0] else 'FAIL'}**",
         f"- G5 the confirm step asked the fan status at most once per handler per visit and never after it was answered (largest count {max(res[k]['FANC']['asks'] for k in res)}, violations {sum(res[k]['FANC']['violations'] for k in res)}): **{'PASS' if g5 else 'FAIL'}**", ""]
    if not gates_ok:
        L += ["**REGISTERED OUTCOME: NO RESULT (a gate failed).**", ""]
    names = {"A-LS": "A-LS: 4 low-static rooms on the larger handler + 2 own-fault rooms", "A-FAN": "A-FAN: 4 fan-off rooms on the larger handler + 2 own-fault rooms", "B": "B: registered composition (50 shared / 50 local visits)",
             "S1": "S1: fan off, the model's own world (each of 8 rooms complains at 90%)", "S2": "S2: fan off, 2-4 of 8 rooms complain + 2 own-fault rooms", "S3": "S3: low static, 2-4 of 8 rooms + 2 own-fault rooms", "S4": "S4: 6 own-fault rooms, no shared cause"}
    for fam in ("A-LS", "A-FAN", "B", "S1", "S2", "S3", "S4"):
        L += [f"## {names[fam]}", "", "| building | answers | arm | accuracy | shared-cause rooms | minutes / visit | wrong and confident | with the hedge | with hedge+fan | right conclusions hedged | false fan-off | fan-off rooms called fan off | vs TODAY: accuracy (95% CI); minutes (95% CI) |",
              "|---|---|---|---|---|---|---|---|---|---|---|---|---|"]
        for f_, bld in [x for x in FAMILIES if x[0] == fam]:
            for w in WORLDS:
                d = res[fam, bld, w]
                for arm in ARMS:
                    s = stats(d, arm)
                    dd = ""
                    if arm != "TODAY":
                        g, gci, dm, dmci = FM.paired(d, arm, "TODAY")
                        dd = f"{g:+.1f} ({gci[0]:+.1f}, {gci[1]:+.1f}); {dm:+.0f} ({dmci[0]:+.0f}, {dmci[1]:+.0f})"
                    L.append(f"| {bld} | {w} | {arm} | {s['acc']:.1f}% | {s['shared']:.1f}% | {s['minutes']:.0f} | {s['wc']:.1f}% | {s['wc_h']:.1f}% | {s['wc_h2']:.1f}% | {s['hedged_right']}/{s['conc_right']} | {s['false_fan']:.1f}% | "
                             + (f"{s['fan_right']:.0f}%" if fam in ("A-FAN", "S1", "S2") else "-") + f" | {dd} |")
        L.append("")
    S_ = lambda fam, b, arm, w="W0": stats(res[fam, b, w], arm)                          # noqa: E731
    P_ = lambda fam, b, arm, w="W0": FM.paired(res[fam, b, w], arm, "TODAY")             # noqa: E731
    P = []
    c1 = {b: (S_("A-LS", b, "FANC")["false_fan"], P_("A-LS", b, "FANC")[0]) for b in REAL}
    P.append(("C1 (A-LS: FANC false fan-off at most 2% and accuracy within 3 points of TODAY)", all(v[0] <= 2 and abs(v[1]) <= 3 for v in c1.values()), ", ".join(f"{b} false {v[0]:.1f}%, {v[1]:+.1f}" for b, v in c1.items())))
    c2 = {b: (S_("A-FAN", b, "FANC")["shared"], S_("A-FAN", b, "FAN")["shared"]) for b in REAL}
    P.append(("C2 (A-FAN: FANC's fan-off rooms at least 80% of FAN's)", all(v[0] >= 0.8 * v[1] for v in c2.values()), ", ".join(f"{b} {v[0]:.1f}% vs {v[1]:.1f}%" for b, v in c2.items())))
    c3 = {(f_, b): (P_(f_, b, "FANC")[0], S_(f_, b, "FANC")["wc"] - S_(f_, b, "TODAY")["wc"]) for f_, b in (("B", "bldg15"), ("B", "bldg11"), ("S3", "demo"), ("S4", "demo"))}
    P.append(("C3 (B, S3, S4: FANC within 2 points of TODAY, wrong-and-confident at most +1)", all(abs(v[0]) <= 2 and v[1] <= 1 for v in c3.values()), ", ".join(f"{f_} {b} {v[0]:+.1f}, wc {v[1]:+.1f}" for (f_, b), v in c3.items())))
    c4 = P_("S1", "demo", "FANC")
    P.append(("C4 (S1, the model's own world: FANC within 3 points of TODAY)", abs(c4[0]) <= 3, f"{c4[0]:+.1f} ({c4[1][0]:+.1f}, {c4[1][1]:+.1f}); minutes {c4[2]:+.0f} on {S_('S1', 'demo', 'TODAY')['minutes']:.0f}"))
    c5 = {(f_, b): (S_(f_, b, "FANC")["minutes"] - S_(f_, b, "TODAY")["minutes"], S_(f_, b, "TODAY")["minutes"]) for f_, b in [("A-LS", x) for x in REAL] + [("B", "bldg15"), ("B", "bldg11")]}
    P.append(("C5 (minutes under FANC within +5% of TODAY in A-LS and B)", all(dm <= 0.05 * base for dm, base in c5.values()), ", ".join(f"{f_} {b} {dm:+.0f} ({100 * dm / base:+.0f}%)" for (f_, b), (dm, base) in c5.items())))
    g_rw, g_lo = S_("A-LS", "bldg15", "RW")["acc"] - S_("A-LS", "bldg15", "TODAY")["acc"], S_("A-LS", "bldg15", "LOW2")["acc"] - S_("A-LS", "bldg15", "TODAY")["acc"]
    P.append(("L1 (RW captures at least half of LOW2's bldg15 gain)", g_lo > 0 and g_rw >= 0.5 * g_lo, f"RW {g_rw:+.1f}, LOW2 {g_lo:+.1f} ({100 * g_rw / g_lo:.0f}% captured)" if g_lo else "LOW2 gain 0"))
    l2 = {b: (S_("A-FAN", b, "LOW2")["wc"] - S_("A-FAN", b, "TODAY")["wc"], S_("A-FAN", b, "RW")["wc"] - S_("A-FAN", b, "TODAY")["wc"]) for b in ("bldg15", "bldg9")}
    P.append(("L2 (A-FAN: LOW2's wrong-and-confident at least 3 above TODAY's, RW's rise smaller)", all(v[0] >= 3 and v[1] < v[0] for v in l2.values()), ", ".join(f"{b} LOW2 {v[0]:+.1f}, RW {v[1]:+.1f}" for b, v in l2.items())))
    h_cells = [("A-FAN", b) for b in REAL] + [("S1", "demo"), ("S2", "demo")] + [("A-LS", b) for b in REAL] + [("B", "bldg15"), ("B", "bldg11")]
    hs = {c: S_(c[0], c[1], "FAN") for c in h_cells}
    need = {c: s for c, s in hs.items() if s["wc_h"] >= 1}
    cut_ok = all(s["wc_h2"] <= 0.5 * s["wc_h"] for s in need.values())
    pooled = sum(s["hedged_right"] for s in hs.values()) / max(sum(s["conc_right"] for s in hs.values()), 1)
    P.append(("H1 (the extended hedge cuts the remaining wrong-and-confident by half where it is at least 1%, hedging at most 30% of right conclusions)", cut_ok and pooled <= 0.30,
              "; ".join(f"{c[0]} {c[1]} {s['wc_h']:.1f}% -> {s['wc_h2']:.1f}%" for c, s in need.items()) + f"; right conclusions hedged pooled {100 * pooled:.0f}%"))
    L += ["## Predictions (written before any run)", ""] + [f"- {p}: **{'HELD' if ok else 'FAILED'}** ({d})" for p, ok, d in P] + [""]
    held = {p[0].split(" ")[0]: p[1] for p in P}
    conf = "WORTH ADOPTING WITH THE FAN-OFF MIXTURE" if all(held[k] for k in ("C1", "C2", "C3", "C4", "C5")) else "NOT WORTH IT AS TESTED (" + ", ".join(k for k in ("C1", "C2", "C3", "C4", "C5") if not held[k]) + " failed)"
    hed = "WORTH ADDING IF THE FAN-OFF MIXTURE IS ADOPTED" if held["H1"] else "NOT WORTH IT AS TESTED (H1 failed)"
    if not gates_ok:
        conf = hed = "NO RESULT (a gate failed)"
    L += ["## Decision rule applied", "", f"- Fan-status confirm step: **{conf}**", f"- Hedge extended to fan off: **{hed}**", "- Lower-end gaps: reported against L1 and L2 above; they decide nothing alone.", ""]
    out.mkdir(parents=True, exist_ok=True)
    (out / "report.md").write_text("\n".join(L))
    (out / "summary.json").write_text(json.dumps(dict(gates_ok=bool(gates_ok), confirm=conf, hedge=hed, predictions={k: bool(v) for k, v in held.items()}, protocol_sha256=hashlib.sha256(PROTOCOL.read_bytes()).hexdigest()), indent=1))
    print("\n".join(L))


if __name__ == "__main__":
    main()
